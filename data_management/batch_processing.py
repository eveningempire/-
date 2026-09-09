"""
鎵归噺鏂囦欢澶勭悊鍜屾娴嬫湇鍔?
鏀寔寮傛澶勭悊澶ф枃浠讹紝骞舵彁渚涘疄鏃惰繘搴﹀弽棣?
"""

import os
import csv
import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils import timezone
from django.db import transaction
from django.conf import settings
from openpyxl import load_workbook
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import PHM, PHMData, ImportSession
from .config import get_config
from health_management.ims_service import run_ims_detection
from health_management.detection_frequency_controller import detection_frequency_controller
from rule_detection.service import evaluate_rules_for_data_point
from rule_detection.algorithms.rule.enhanced_rule_detector import EnhancedRuleDetector
from msfg_analysis.models import MSFGDefinition
from msfg_analysis.algorithms.msfg.fusion import fuse_test_to_fault, summarize_system

logger = logging.getLogger(__name__)

# 鎬ц兘閰嶇疆鍙傛暟
DETECTION_CONFIG = {
    # 鎵归噺鎿嶄綔閰嶇疆
    'BATCH_SIZE_FOR_SAVE': get_config('batch_size_for_save', 1000),  # 鎵归噺淇濆瓨鐨勬壒娆″ぇ灏?
    'PROGRESS_UPDATE_INTERVAL': 50,      # 杩涘害鏇存柊闂撮殧
    
    # 鎬ц兘鐩戞帶閰嶇疆
    'ENABLE_PERFORMANCE_MONITORING': True,  # 鏄惁鍚敤鎬ц兘鐩戞帶
    'DETAILED_LOGGING': True,               # 鏄惁鍚敤璇︾粏鏃ュ織
}


class BatchFileProcessor:
    """鎵归噺鏂囦欢澶勭悊鍣?""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self._active_sessions = {}  # session_id -> processor_thread
        
    def process_import_session_async(self, session_id: int) -> None:
        """寮傛澶勭悊瀵煎叆浼氳瘽"""
        def _process():
            try:
                self._process_import_session(session_id)
            except Exception as e:
                logger.error(f"澶勭悊瀵煎叆浼氳瘽 {session_id} 鏃跺嚭閿? {e}")
                self._update_session_status(session_id, ImportSession.ProcessingStatus.FAILED, 
                                          error_message=str(e))
        
        thread = threading.Thread(target=_process, daemon=True)
        self._active_sessions[session_id] = thread
        thread.start()
    
    def process_file_for_detection(
        self, 
        file_path: str, 
        cmg: PHM, 
        detection_mode: str = 'full',
        save_to_db: bool = False,
        return_details: bool = True,
        max_rows: Optional[int] = None,
        add_milliseconds: bool = False
    ) -> Dict[str, Any]:
        """
        澶勭悊鏂囦欢骞舵墽琛屾娴嬶紙鐢ㄤ簬瀹炴椂妫€娴嬶級
        
        瀹屽叏澶嶇敤鍘熸湁娴佺▼锛?
        1. 鐩存帴瑙ｆ瀽鏂囦欢锛堜笉閫氳繃session.file锛?
        2. 鍒涘缓PHMData瀵硅薄骞朵繚瀛樺埌鏁版嵁搴?
        3. 杩愯鍘熸湁妫€娴嬫祦绋?
        4. 鏀堕泦缁撴灉骞惰繑鍥烇紙濮嬬粓淇濆瓨鍒版暟鎹簱锛?
        
        娉ㄦ剰锛?
        - 妫€娴嬬粨鏋滃缁堜繚瀛樺埌鏁版嵁搴擄紙渚涘叾浠栨ā鍧椾娇鐢紝濡傚鍛介娴嬨€侀仴娴嬪垎鏋愮瓑锛?
        - 杩斿洖鐨勭粨鏋滃寘鍚椂闂磋寖鍥翠俊鎭紙渚涘墠绔缃畉imeRange锛?
        
        Args:
            file_path: 鏂囦欢璺緞锛堢郴缁熶复鏃剁洰褰曪級
            cmg: PHM瀵硅薄
            detection_mode: 妫€娴嬫ā寮?('full', 'ims_only', 'rule_only', 'msfg_only')
            save_to_db: 鏄惁淇濆瓨锛堝凡寮哄埗涓篢rue锛屽弬鏁颁繚鐣欑敤浜庡吋瀹规€э級
            return_details: 鏄惁杩斿洖璇︾粏缁撴灉
            max_rows: 鏈€澶у鐞嗚鏁帮紙None琛ㄧず澶勭悊鍏ㄩ儴锛?
            add_milliseconds: 鏄惁涓洪噸澶嶆椂闂存埑娣诲姞姣
            
        Returns:
            妫€娴嬬粨鏋滃瓧鍏革紝鍖呭惈time_range瀛楁
        """
        logger.debug(f"[瀹炴椂妫€娴媇 寮€濮嬪鐞嗘枃浠? {file_path}, PHM: {cmg.cmg_id}, 妯″紡: {detection_mode}, "
                    f"淇濆瓨: {save_to_db}, 鏈€澶ц鏁? {max_rows}, 鏃堕棿鎴冲鐞? {add_milliseconds}")
        
        temp_session = None
        stored_records = []
        
        try:
            # 1. 鐩存帴瑙ｆ瀽鏂囦欢锛堜笉渚濊禆ImportSession.file锛?
            parsed_data = self._parse_file_direct(file_path, max_rows=max_rows)
            if not parsed_data:
                raise ValueError("鏂囦欢瑙ｆ瀽澶辫触鎴栨棤鏈夋晥鏁版嵁")
            
            total_frames = len(parsed_data)
            logger.debug(f"[瀹炴椂妫€娴媇 瑙ｆ瀽瀹屾垚锛屽叡 {total_frames} 鏉℃暟鎹?)
            
            # 1.5. 鏃堕棿鎴冲幓閲嶅鐞嗭紙濡傛灉闇€瑕侊級
            if add_milliseconds:
                parsed_data = self._add_milliseconds_to_duplicate_timestamps(parsed_data)
                logger.debug(f"[瀹炴椂妫€娴媇 鏃堕棿鎴冲幓閲嶅畬鎴?)
            
            # 2. 鍒涘缓涓存椂瀵煎叆浼氳瘽锛堢敤浜庢爣璇嗚繖鎵规暟鎹級
            temp_session = ImportSession.objects.create(
                cmg=cmg,
                method=ImportSession.Method.FILE,
                import_mode=ImportSession.ImportMode.IMPORT_AND_DETECT,
                processing_status=ImportSession.ProcessingStatus.STORING,
                total_records=total_frames,
                max_rows=max_rows,  # 璁剧疆鏈€澶ц鏁?
                add_milliseconds=add_milliseconds,  # 璁剧疆鏃堕棿鎴冲鐞嗛€夐」
                detection_summary={'is_realtime': True, 'save_to_db': save_to_db}
            )
            
            # 3. 鎵归噺鍒涘缓PHMData瀵硅薄
            stored_records = self._create_cmg_data_batch(cmg, parsed_data, temp_session)
            if not stored_records:
                raise ValueError("鏁版嵁鍒涘缓澶辫触")
            
            logger.debug(f"[瀹炴椂妫€娴媇 鏁版嵁鍒涘缓瀹屾垚锛屽叡 {len(stored_records)} 鏉MGData璁板綍")
            
            # 4. 杩愯妫€娴嬫祦绋嬶紙澶嶇敤鍘熸湁閫昏緫锛?
            temp_session.processing_status = ImportSession.ProcessingStatus.DETECTING
            temp_session.processed_records = len(stored_records)
            temp_session.save()
            
            detection_summary = self._run_detection_pipeline(temp_session, stored_records)
            
            # 5. 鏀堕泦妫€娴嬬粨鏋滐紙浠庢暟鎹簱璇诲彇锛?
            results = self._collect_detection_results(
                cmg=cmg,
                records=stored_records,
                detection_summary=detection_summary,
                return_details=return_details
            )
            
            # 6. 娣诲姞鏃堕棿鑼冨洿淇℃伅锛堜緵鍓嶇鍏朵粬妯″潡浣跨敤锛?
            if stored_records:
                # 鑾峰彇瀹為檯澶勭悊鐨勬暟鎹殑鏃堕棿鑼冨洿
                first_record = stored_records[0]
                last_record = stored_records[-1]
                
                results['time_range'] = {
                    'start': first_record.timestamp.isoformat(),
                    'end': last_record.timestamp.isoformat()
                }
                
                logger.debug(f"[瀹炴椂妫€娴媇 鏃堕棿鑼冨洿: {results['time_range']['start']} 鑷?{results['time_range']['end']}")
            
            logger.debug(f"[瀹炴椂妫€娴媇 妫€娴嬪畬鎴? 寮傚父鐜?{results.get('anomaly_ratio', 0):.2%}")
            
            # 7. 鏍囪浼氳瘽涓哄畬鎴愶紙寮哄埗淇濆瓨锛?
            temp_session.processing_status = ImportSession.ProcessingStatus.COMPLETED
            temp_session.completed_at = timezone.now()
            temp_session.save()
            
            logger.info(f"[瀹炴椂妫€娴媇 缁撴灉宸蹭繚瀛樺埌鏁版嵁搴擄紝浼氳瘽ID: {temp_session.id}")
            
            return results
            
        except Exception as e:
            logger.error(f"[瀹炴椂妫€娴媇 妫€娴嬪け璐? {e}", exc_info=True)
            # 娓呯悊澶辫触鐨勪細璇濆拰鏁版嵁
            if temp_session:
                try:
                    # 鏍囪涓哄け璐?
                    temp_session.processing_status = ImportSession.ProcessingStatus.FAILED
                    temp_session.error_message = str(e)
                    temp_session.save()
                except Exception as save_error:
                    logger.error(f"淇濆瓨澶辫触鐘舵€佸け璐? {save_error}")
            raise
    
    def _parse_file_direct(self, file_path: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        鐩存帴瑙ｆ瀽鏂囦欢锛堜笉渚濊禆ImportSession.file瀛楁锛?
        澶嶅埗鍘熸湁_parse_file鐨勬牳蹇冮€昏緫
        """
        from pathlib import Path
        from django.utils import timezone as tz
        
        parsed_data = []
        
        def detect_encoding(file_path: str) -> str:
            """妫€娴嬫枃浠剁紪鐮?""
            try:
                import chardet
                with open(file_path, 'rb') as f:
                    raw_data = f.read(10000)  # 璇诲彇鍓?0KB鏉ユ娴嬬紪鐮?
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']
                    confidence = result['confidence']
                    
                    if confidence > 0.7:
                        logger.info(f"[瀹炴椂妫€娴媇 妫€娴嬪埌鏂囦欢缂栫爜: {encoding} (缃俊搴? {confidence:.2f})")
                        return encoding
                    else:
                        logger.warning(f"[瀹炴椂妫€娴媇 缂栫爜妫€娴嬬疆淇″害杈冧綆: {encoding} (缃俊搴? {confidence:.2f})锛屼娇鐢╱tf-8")
                        return 'utf-8'
            except ImportError:
                logger.warning("[瀹炴椂妫€娴媇 chardet鏈畨瑁咃紝浣跨敤榛樿utf-8缂栫爜")
                return 'utf-8'
            except Exception as e:
                logger.warning(f"[瀹炴椂妫€娴媇 缂栫爜妫€娴嬪け璐? {e}锛屼娇鐢ㄩ粯璁tf-8缂栫爜")
                return 'utf-8'
        
        def parse_ts(value) -> datetime:
            """鏃堕棿鎴宠В鏋愶紙瀹屾暣澶嶅埗鍘熸湁閫昏緫锛?""
            if isinstance(value, datetime):
                ts = value
            else:
                s = str(value).strip()
                s_iso = s.replace("Z", "+00:00")
                try:
                    ts = datetime.fromisoformat(s_iso)
                except Exception:
                    try:
                        if s.isdigit():
                            iv = int(s)
                            if len(s) >= 13:
                                ts = datetime.fromtimestamp(iv / 1000)
                            else:
                                ts = datetime.fromtimestamp(iv)
                        else:
                            raise ValueError
                    except Exception:
                        # 瀹屾暣鐨勬牸寮忓€欓€夊垪琛紙涓庡師鏈夐€昏緫涓€鑷达級
                        candidates = [
                            "%Y-%m-%d %H:%M:%S.%f",
                            "%Y-%m-%d %H:%M:%S",
                            "%Y-%m-%d %H:%M",
                            "%Y/%m/%d %H:%M:%S.%f",
                            "%Y/%m/%d %H:%M:%S",
                            "%Y/%m/%d %H:%M",
                            "%Y_%m_%d_%H:%M:%S",     # 鉁?鍏抽敭鏍煎紡锛氫笅鍒掔嚎鍒嗛殧
                            "%Y %m %d %H:%M:%S",
                            "%Y:%m:%d %H:%M:%S.%f",
                            "%Y:%m:%d %H:%M:%S",
                            "%Y:%m:%d %H:%M",
                            "%Y:%m:%d",
                            "%Y-%m-%d",
                            "%Y/%m/%d",
                        ]
                        
                        # 鐗规畩澶勭悊锛氭娴嬪苟杞崲鍐掑彿鍒嗛殧鐨勬绉掓牸寮忥紙濡?2024-8-2 10:55:37:65锛?
                        if ':' in s and s.count(':') >= 3:
                            try:
                                parts = s.split(':')
                                if len(parts) >= 4:
                                    date_time_part = ':'.join(parts[:-1])
                                    milliseconds = parts[-1]
                                    microseconds = int(milliseconds) * 1000
                                    s_converted = f"{date_time_part}.{microseconds:06d}"
                                    ts = datetime.strptime(s_converted, "%Y-%m-%d %H:%M:%S.%f")
                                    if ts.tzinfo is None:
                                        ts = tz.make_aware(ts)
                                    return ts
                            except (ValueError, IndexError):
                                pass  # 缁х画灏濊瘯鍏朵粬鏍煎紡
                        
                        # 褰掍竴鍖栦竴浜涘垎闅旂锛屼究浜庡尮閰?
                        s_norm = s.replace("T", " ")
                        ts = None
                        for fmt in candidates:
                            try:
                                ts = datetime.strptime(s_norm, fmt)
                                break
                            except:
                                continue
                        if ts is None:
                            raise ValueError(f"鏃犳硶瑙ｆ瀽鏃堕棿鎴? {s}")
            
            if ts.tzinfo is None:
                ts = tz.make_aware(ts)
            return ts
        
        suffix = Path(file_path).suffix.lower()
        
        try:
            if suffix == ".csv":
                # 妫€娴嬫枃浠剁紪鐮?
                encoding = detect_encoding(file_path)
                with open(file_path, 'r', encoding=encoding) as fh:
                    reader = csv.reader(fh)
                    rows = list(reader)
                    if not rows:
                        return []
                    headers = rows[0]
                    param_names = headers[1:]
                    
                    for row_num, r in enumerate(rows[1:], 2):
                        if max_rows and len(parsed_data) >= max_rows:
                            break
                        if not r:
                            continue
                        try:
                            ts = parse_ts(r[0])
                            data_dict = {}
                            for i, name in enumerate(param_names, start=1):
                                val = r[i] if i < len(r) else None
                                try:
                                    data_dict[name] = float(val) if val not in (None, "") else None
                                except (ValueError, TypeError):
                                    data_dict[name] = val
                            parsed_data.append({
                                'timestamp': ts,
                                'data': data_dict
                            })
                        except Exception as e:
                            logger.warning(f"瑙ｆ瀽绗?{row_num} 琛屽け璐? {e}")
                            
            elif suffix in {".xlsx", ".xlsm", ".xls"}:
                wb = load_workbook(file_path, read_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
                if not rows:
                    wb.close()
                    return []
                headers = list(rows[0])
                param_names = [h for h in headers[1:] if h is not None]
                
                for row_num, r in enumerate(rows[1:], 2):
                    if max_rows and len(parsed_data) >= max_rows:
                        break
                    if not r or r[0] is None:
                        continue
                    try:
                        ts = parse_ts(r[0])
                        data_dict = {}
                        for i, name in enumerate(param_names, start=1):
                            val = r[i] if i < len(r) else None
                            try:
                                data_dict[name] = float(val) if (val is not None and val != "") else None
                            except (ValueError, TypeError):
                                data_dict[name] = val
                        parsed_data.append({
                            'timestamp': ts,
                            'data': data_dict
                        })
                    except Exception as e:
                        logger.warning(f"瑙ｆ瀽绗?{row_num} 琛屽け璐? {e}")
                
                wb.close()
            else:
                raise ValueError(f"涓嶆敮鎸佺殑鏂囦欢鏍煎紡: {suffix}")
            
            logger.debug(f"鏂囦欢瑙ｆ瀽鎴愬姛锛屽叡 {len(parsed_data)} 鏉℃湁鏁堟暟鎹?)
            return parsed_data
            
        except Exception as e:
            logger.error(f"鏂囦欢瑙ｆ瀽澶辫触: {e}", exc_info=True)
            raise
    
    def _create_cmg_data_batch(
        self, 
        cmg: PHM, 
        parsed_data: List[Dict[str, Any]], 
        session: ImportSession
    ) -> List[PHMData]:
        """
        鎵归噺鍒涘缓PHMData瀵硅薄
        澶嶇敤_store_data鐨勯€昏緫锛屼絾绠€鍖栦簡涓€浜涙鏌?
        """
        BATCH_SIZE = get_config('batch_size_for_save', 2000)
        total_records = len(parsed_data)
        
        logger.debug(f"寮€濮嬫壒閲忓垱寤?{total_records} 鏉MGData璁板綍锛屾壒閲忓ぇ灏? {BATCH_SIZE}")
        
        # 鍒嗘壒鍒涘缓
        for i in range(0, total_records, BATCH_SIZE):
            batch_data = parsed_data[i:i + BATCH_SIZE]
            batch_to_create = []
            
            for item in batch_data:
                batch_to_create.append(PHMData(
                    cmg=cmg,
                    timestamp=item['timestamp'],
                    data=item['data'],
                    import_session=session
                ))
            
            if batch_to_create:
                try:
                    with transaction.atomic():
                        PHMData.objects.bulk_create(batch_to_create, ignore_conflicts=True)
                    
                    logger.debug(f"鎴愬姛鍒涘缓鎵规 {i//BATCH_SIZE + 1}/{(total_records + BATCH_SIZE - 1)//BATCH_SIZE}锛?
                               f"鍖呭惈 {len(batch_to_create)} 鏉¤褰?)
                except Exception as e:
                    logger.error(f"鎵归噺鍒涘缓鏁版嵁澶辫触: {e}")
                    raise
        
        # 鏌ヨ鎵€鏈夊垱寤虹殑璁板綍
        created_records = list(
            PHMData.objects.filter(
                cmg=cmg,
                import_session=session
            ).order_by("timestamp")
        )
        
        logger.debug(f"鎴愬姛鍒涘缓 {len(created_records)} 鏉MGData璁板綍")
        return created_records
    
    def _collect_detection_results(
        self,
        cmg: PHM,
        records: List[PHMData],
        detection_summary: Dict[str, Any],
        return_details: bool = True
    ) -> Dict[str, Any]:
        """
        浠庢暟鎹簱鏀堕泦妫€娴嬬粨鏋?
        
        Args:
            cmg: PHM瀵硅薄
            records: PHMData璁板綍鍒楄〃
            detection_summary: 妫€娴嬫憳瑕?
            return_details: 鏄惁杩斿洖璇︾粏缁撴灉
            
        Returns:
            鍖呭惈鎵€鏈夋娴嬬粨鏋滅殑瀛楀吀
        """
        from health_management.models import IMSDetectionResult
        from rule_detection.models import RuleDetectionResult
        from msfg_analysis.models import MSFGAnalysisResult
        
        total_frames = len(records)
        
        # 鑾峰彇鎵€鏈夋娴嬬粨鏋?
        record_ids = [r.id for r in records]
        
        # IMS妫€娴嬬粨鏋?
        ims_results = IMSDetectionResult.objects.filter(data_point__id__in=record_ids)
        anomaly_ims = ims_results.filter(is_anomaly=True)
        
        # 瑙勫垯妫€娴嬬粨鏋?
        rule_results = RuleDetectionResult.objects.filter(data_point__id__in=record_ids)
        
        # MSFG妫€娴嬬粨鏋?
        msfg_results = MSFGAnalysisResult.objects.filter(data_point__id__in=record_ids)
        
        # 鏋勫缓缁撴灉
        results = {
            'total_frames': total_frames,
            'anomaly_count': anomaly_ims.count(),
            'anomaly_ratio': anomaly_ims.count() / total_frames if total_frames > 0 else 0.0,
            'anomaly_frames': [],
            'frame_details': [] if return_details else None,
            'component_health': {},
            'overall_health': None,
            'detection_summary': detection_summary
        }
        
        # 鏀堕泦寮傚父甯т俊鎭?
        for ims_result in anomaly_ims:
            results['anomaly_frames'].append({
                'id': ims_result.data_point.id,
                'frame_number': None,  # 鍙互浠巖ecords涓壘鍒扮储寮?
                'timestamp': ims_result.data_point.timestamp.isoformat(),
                'anomaly_type': 'ims',
                'anomaly_score': float(ims_result.anomaly_score) if ims_result.anomaly_score else 0.0,
                'severity': 'high' if ims_result.anomaly_score and ims_result.anomaly_score > 0.7 else 'medium'
            })
        
        # 濡傛灉闇€瑕佽缁嗙粨鏋滐紝鏀堕泦姣忎竴甯х殑妫€娴嬭鎯?
        if return_details:
            for idx, record in enumerate(records):
                # 鏌ユ壘璇ヨ褰曠殑妫€娴嬬粨鏋?
                ims_res = ims_results.filter(data_point=record).first()
                
                # 瑙勫垯妫€娴嬬粨鏋滐細涓€涓暟鎹偣鍙兘鏈夊涓鍒欑粨鏋?
                rule_res_list = rule_results.filter(data_point=record)
                
                # MSFG妫€娴嬬粨鏋?
                msfg_res = msfg_results.filter(data_point=record).first()
                
                # 鏋勫缓IMS缁撴灉
                ims_result_data = None
                if ims_res:
                    ims_result_data = {
                        'is_anomaly': ims_res.is_anomaly,
                        'anomaly_score': float(ims_res.anomaly_score) if ims_res.anomaly_score else 0.0,
                        'parameter_scores': ims_res.parameter_scores if ims_res.parameter_scores else {},
                        'detection_details': ims_res.detection_details if ims_res.detection_details else {}
                    }
                
                # 鏋勫缓瑙勫垯妫€娴嬬粨鏋?
                rule_result_data = None
                if rule_res_list.exists():
                    triggered_rules = []
                    for rule_res in rule_res_list:
                        triggered_rules.append({
                            'rule_id': rule_res.rule_definition.rule_id if rule_res.rule_definition else 'Unknown',  # 鉁?姝ｇ‘瀛楁
                            'rule_expression': rule_res.rule_definition.rule_expression if rule_res.rule_definition else '',
                            'fault_name': rule_res.fault_definition.fault_name if rule_res.fault_definition else 'Unknown',  # 鉁?姝ｇ‘瀛楁
                            'is_triggered': rule_res.is_triggered,
                            'confidence_score': float(rule_res.confidence_score) if rule_res.confidence_score else 0.0,
                            'detection_details': rule_res.detection_details if rule_res.detection_details else {}
                        })
                    
                    rule_result_data = {
                        'has_violation': any(r['is_triggered'] for r in triggered_rules),
                        'triggered_count': sum(1 for r in triggered_rules if r['is_triggered']),
                        'triggered_rules': triggered_rules
                    }
                
                # 鏋勫缓MSFG缁撴灉
                msfg_result_data = None
                if msfg_res:
                    msfg_result_data = {
                        'component_health': msfg_res.component_results if msfg_res.component_results else {},
                        'overall_health': msfg_res.system_results.get('overall_health') if msfg_res.system_results else None,
                        'overall_health_score': float(msfg_res.overall_health_score) if msfg_res.overall_health_score else 1.0,
                        'test_results': msfg_res.test_results if msfg_res.test_results else {},
                        'fault_results': msfg_res.fault_results if msfg_res.fault_results else {},
                        'detected_faults': msfg_res.detected_faults if msfg_res.detected_faults else [],
                        'critical_components': msfg_res.critical_components if msfg_res.critical_components else []
                    }
                
                frame_detail = {
                    'frame_number': idx + 1,
                    'timestamp': record.timestamp.isoformat(),
                    'is_anomaly': ims_res.is_anomaly if ims_res else False,
                    'ims_result': ims_result_data,
                    'rule_result': rule_result_data,
                    'msfg_result': msfg_result_data
                }
                
                results['frame_details'].append(frame_detail)
            
            # 鑱氬悎閮ㄤ欢鍋ュ悍搴?
            results['component_health'] = self._aggregate_component_health(results['frame_details'])
            results['overall_health'] = self._calculate_overall_health(results['component_health'])
        
        return results
    
    def _aggregate_component_health(self, frame_details: List[Dict]) -> Dict[str, Dict]:
        """浠庡抚璇︽儏涓仛鍚堥儴浠跺仴搴峰害"""
        if not frame_details:
            return {}
        
        # 鏀堕泦鎵€鏈夊抚鐨凪SFG缁撴灉
        component_scores = {}
        
        for frame in frame_details:
            msfg_result = frame.get('msfg_result')
            if not msfg_result or not msfg_result.get('component_health'):
                continue
            
            for comp_name, comp_data in msfg_result['component_health'].items():
                if comp_name not in component_scores:
                    component_scores[comp_name] = []
                
                # 鎻愬彇health_score
                health_score = comp_data.get('health_score', 1.0) if isinstance(comp_data, dict) else 1.0
                component_scores[comp_name].append(health_score)
        
        # 璁＄畻骞冲潎鍋ュ悍搴?
        component_health = {}
        for comp_name, scores in component_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                min_score = min(scores)
                max_score = max(scores)
                
                component_health[comp_name] = {
                    'name': comp_name,
                    'health_score': round(avg_score, 3),
                    'min_score': round(min_score, 3),
                    'max_score': round(max_score, 3),
                    'status': 'healthy' if avg_score >= 0.7 else 'warning' if avg_score >= 0.5 else 'critical',
                    'sample_count': len(scores)
                }
        
        return component_health
    
    def _calculate_overall_health(self, component_health: Dict) -> float:
        """璁＄畻鏁翠綋鍋ュ悍搴?""
        if not component_health:
            return 1.0
        
        scores = [comp['health_score'] for comp in component_health.values()]
        return round(sum(scores) / len(scores), 3) if scores else 1.0
    
    def _cleanup_temp_detection_data(self, session: ImportSession, records: List[PHMData]):
        """
        娓呯悊涓存椂妫€娴嬫暟鎹?
        
        Args:
            session: 瀵煎叆浼氳瘽
            records: PHMData璁板綍鍒楄〃
        """
        from health_management.models import IMSDetectionResult
        from rule_detection.models import RuleDetectionResult
        from msfg_analysis.models import MSFGAnalysisResult
        
        try:
            if records:
                record_ids = [r.id for r in records]
                
                # 鍒犻櫎妫€娴嬬粨鏋?
                deleted_ims = IMSDetectionResult.objects.filter(data_point__id__in=record_ids).delete()
                deleted_rule = RuleDetectionResult.objects.filter(data_point__id__in=record_ids).delete()
                deleted_msfg = MSFGAnalysisResult.objects.filter(data_point__id__in=record_ids).delete()
                
                logger.debug(f"[娓呯悊] 鍒犻櫎妫€娴嬬粨鏋? IMS={deleted_ims[0]}, 瑙勫垯={deleted_rule[0]}, MSFG={deleted_msfg[0]}")
                
                # 鍒犻櫎鍘熷鏁版嵁
                deleted_data = PHMData.objects.filter(id__in=record_ids).delete()
                logger.debug(f"[娓呯悊] 鍒犻櫎鍘熷鏁版嵁: {deleted_data[0]} 鏉¤褰?)
            
        except Exception as e:
            logger.error(f"[娓呯悊] 娓呯悊涓存椂鏁版嵁澶辫触: {e}")
    
    def _process_import_session(self, session_id: int) -> None:
        """澶勭悊鍗曚釜瀵煎叆浼氳瘽"""
        try:
            session = ImportSession.objects.get(id=session_id)
        except ImportSession.DoesNotExist:
            logger.error(f"瀵煎叆浼氳瘽 {session_id} 涓嶅瓨鍦?)
            return
            
        if not session.file:
            logger.error(f"瀵煎叆浼氳瘽 {session_id} 娌℃湁鏂囦欢")
            self._update_session_status(session_id, ImportSession.ProcessingStatus.FAILED,
                                      error_message="娌℃湁涓婁紶鏂囦欢")
            return
        
        try:
            # 鏇存柊鐘舵€佷负寮€濮嬪鐞?
            self._update_session_status(session_id, ImportSession.ProcessingStatus.PARSING,
                                      started_at=timezone.now())
            
            # 瑙ｆ瀽鏂囦欢鑾峰彇鏁版嵁
            parsed_data = self._parse_file(session)
            if not parsed_data:
                self._update_session_status(session_id, ImportSession.ProcessingStatus.FAILED,
                                          error_message="鏂囦欢瑙ｆ瀽澶辫触鎴栨棤鏈夋晥鏁版嵁")
                return
            
            # 鏇存柊鎬昏褰曟暟
            session.total_records = len(parsed_data)
            session.save(update_fields=['total_records'])
            
            # 瀛樺偍鏁版嵁
            self._update_session_status(session_id, ImportSession.ProcessingStatus.STORING)
            stored_records = self._store_data(session, parsed_data)
            
            if not stored_records:
                self._update_session_status(session_id, ImportSession.ProcessingStatus.FAILED,
                                          error_message="鏁版嵁瀛樺偍澶辫触")
                return
            
            # 鏇存柊宸插鐞嗚褰曟暟涓烘€诲抚鏁帮紙鎵€鏈夊抚閮借杩涜妫€娴嬶級
            session.processed_records = len(stored_records)
            session.save(update_fields=['processed_records'])
            
            # 鏍规嵁瀵煎叆妯″紡鍐冲畾鏄惁杩涜妫€娴?
            if session.import_mode == ImportSession.ImportMode.IMPORT_ONLY:
                # 浠呭鍏ユā寮忥細璺宠繃妫€娴?
                logger.info(f"瀵煎叆浼氳瘽 {session_id} 涓轰粎瀵煎叆妯″紡锛岃烦杩囨娴嬫楠?)
                detection_summary = {
                    'import_only': True,
                    'message': '浠呭鍏ユā寮忥紝鏈繘琛屾娴?,
                    'total_records': len(stored_records),
                    'imported_records': len(stored_records)
                }
                # 鐩存帴瀹屾垚澶勭悊
                self._update_session_status(session_id, ImportSession.ProcessingStatus.COMPLETED,
                                          completed_at=timezone.now(),
                                          detection_summary=detection_summary)
            else:
                # 瀵煎叆骞舵娴嬫ā寮忥細杩涜姝ｅ父妫€娴?
                self._update_session_status(session_id, ImportSession.ProcessingStatus.DETECTING)
                detection_summary = self._run_detection_pipeline(session, stored_records)
                
                # 瀹屾垚澶勭悊
                self._update_session_status(session_id, ImportSession.ProcessingStatus.COMPLETED,
                                          completed_at=timezone.now(),
                                          detection_summary=detection_summary)
            
            # 鏇存柊缁熻淇℃伅
            try:
                from .models import DatabaseStatistics
                # 鏇存柊PHM鏁版嵁缁熻
                DatabaseStatistics.update_statistics('cmg_data', session.cmg)
                DatabaseStatistics.update_statistics('total_frames', session.cmg)
                # 鏇存柊鍏ㄥ眬缁熻
                DatabaseStatistics.update_statistics('cmg_data')
                DatabaseStatistics.update_statistics('total_frames')
                
                # 浠呭湪闈炰粎瀵煎叆妯″紡涓嬫洿鏂版娴嬬浉鍏崇粺璁?
                if session.import_mode != ImportSession.ImportMode.IMPORT_ONLY:
                    # 鏇存柊妫€娴嬬粨鏋滅粺璁?
                    DatabaseStatistics.update_statistics('ims_results', session.cmg)
                    DatabaseStatistics.update_statistics('rule_results', session.cmg)
                    DatabaseStatistics.update_statistics('msfg_results', session.cmg)
                    DatabaseStatistics.update_statistics('anomaly_frames', session.cmg)
                    # 鏇存柊鍏ㄥ眬妫€娴嬬粺璁?
                    DatabaseStatistics.update_statistics('ims_results')
                    DatabaseStatistics.update_statistics('rule_results')
                    DatabaseStatistics.update_statistics('msfg_results')
                    DatabaseStatistics.update_statistics('anomaly_frames')
                
                logger.info(f"宸叉洿鏂癈MG {session.cmg.cmg_id} 鐨勭粺璁′俊鎭?)
            except Exception as e:
                logger.error(f"鏇存柊缁熻淇℃伅澶辫触: {e}")
            
        except Exception as e:
            logger.error(f"澶勭悊瀵煎叆浼氳瘽 {session_id} 鏃跺嚭閿? {e}")
            self._update_session_status(session_id, ImportSession.ProcessingStatus.FAILED,
                                      error_message=str(e))
        finally:
            # 娓呯悊娲诲姩浼氳瘽璁板綍
            self._active_sessions.pop(session_id, None)
    
    def _parse_file(self, session: ImportSession) -> List[Dict[str, Any]]:
        """瑙ｆ瀽涓婁紶鐨勬枃浠?- 鏀寔澶氱缂栫爜鍜屾牸寮?""
        file_path = session.file.path
        parsed_data = []
        max_rows = session.max_rows  # 鑾峰彇鏈€澶ц鏁伴檺鍒?
        
        try:
            def detect_encoding(file_path: str) -> str:
                """妫€娴嬫枃浠剁紪鐮?""
                try:
                    import chardet
                    with open(file_path, 'rb') as f:
                        raw_data = f.read(10000)  # 璇诲彇鍓?0KB鏉ユ娴嬬紪鐮?
                        result = chardet.detect(raw_data)
                        encoding = result['encoding']
                        confidence = result['confidence']
                        
                        if confidence > 0.7:
                            logger.info(f"妫€娴嬪埌鏂囦欢缂栫爜: {encoding} (缃俊搴? {confidence:.2f})")
                            return encoding
                        else:
                            logger.warning(f"缂栫爜妫€娴嬬疆淇″害杈冧綆: {encoding} (缃俊搴? {confidence:.2f})")
                            return 'utf-8'
                except ImportError:
                    logger.warning("chardet鏈畨瑁咃紝浣跨敤榛樿utf-8缂栫爜")
                    return 'utf-8'
                except Exception as e:
                    logger.warning(f"缂栫爜妫€娴嬪け璐? {e}锛屼娇鐢ㄩ粯璁tf-8缂栫爜")
                    return 'utf-8'
            
            def parse_ts(value: str | datetime) -> datetime:
                """杈冧负椴佹鐨勬椂闂存埑瑙ｆ瀽锛氭敮鎸佸绉嶅垎闅旂/缂虹/姣/ISO/Unix鏃堕棿鎴炽€?""
                if isinstance(value, datetime):
                    ts = value
                else:
                    s = str(value).strip()

                    # 澶勭悊 ISO 灏鹃儴 Z
                    s_iso = s.replace("Z", "+00:00")
                    # 鍏堝皾璇?fromisoformat锛堟敮鎸佸甫鍋忕Щ锛?
                    try:
                        ts = datetime.fromisoformat(s_iso)
                    except Exception:
                        # 灏濊瘯 Unix 鏃堕棿鎴筹紙绉?姣锛?
                        try:
                            if s.isdigit():
                                iv = int(s)
                                # 姣绾?
                                if len(s) >= 13:
                                    ts = datetime.fromtimestamp(iv / 1000)
                                else:
                                    ts = datetime.fromtimestamp(iv)
                            else:
                                raise ValueError
                        except Exception:
                            # 甯歌鏍煎紡鍊欓€?
                            candidates = [
                                "%Y-%m-%d %H:%M:%S.%f",
                                "%Y-%m-%d %H:%M:%S",
                                "%Y-%m-%d %H:%M",
                                "%Y/%m/%d %H:%M:%S.%f",
                                "%Y/%m/%d %H:%M:%S",
                                "%Y/%m/%d %H:%M",
                                "%Y_%m_%d_%H:%M:%S",
                                "%Y %m %d %H:%M:%S",
                                "%Y:%m:%d %H:%M:%S.%f",  # 鏂板锛氬啋鍙峰垎闅旂殑鏃ユ湡鏃堕棿鏍煎紡锛堝甫寰锛?
                                "%Y:%m:%d %H:%M:%S",     # 鏂板锛氬啋鍙峰垎闅旂殑鏃ユ湡鏃堕棿鏍煎紡锛堟棤寰锛?
                                "%Y:%m:%d %H:%M",        # 鏂板锛氬啋鍙峰垎闅旂殑鏃ユ湡鏃堕棿鏍煎紡锛堟棤绉掞級
                                "%Y:%m:%d",              # 鏂板锛氬啋鍙峰垎闅旂殑鏃ユ湡鏍煎紡
                                "%Y-%m-%d",
                                "%Y/%m/%d",
                            ]
                            
                            # 鐗规畩澶勭悊锛氭娴嬪苟杞崲鍐掑彿鍒嗛殧鐨勬绉掓牸寮忥紙濡?2024-8-2 10:55:37:65锛?
                            if ':' in s and s.count(':') >= 3:
                                try:
                                    # 鍒嗗壊鏃堕棿鎴筹紝鏌ユ壘鏈€鍚庝竴涓啋鍙峰悗鐨勬绉掗儴鍒?
                                    parts = s.split(':')
                                    if len(parts) >= 4:
                                        # 閲嶆瀯鏃堕棿鎴筹紝灏嗘绉掕浆鎹负寰
                                        date_time_part = ':'.join(parts[:-1])  # 2024-8-2 10:55:37
                                        milliseconds = parts[-1]  # 65
                                        
                                        # 灏嗘绉掕浆鎹负寰锛堟绉?* 1000锛?
                                        microseconds = int(milliseconds) * 1000
                                        
                                        # 閲嶆瀯鏃堕棿鎴冲瓧绗︿覆锛屼娇鐢ㄧ偣鍒嗛殧寰
                                        s_converted = f"{date_time_part}.{microseconds:06d}"
                                        
                                        # 灏濊瘯瑙ｆ瀽杞崲鍚庣殑鏃堕棿鎴?
                                        ts = datetime.strptime(s_converted, "%Y-%m-%d %H:%M:%S.%f")
                                        logger.debug(f"鎴愬姛瑙ｆ瀽鍐掑彿鍒嗛殧鐨勬绉掓椂闂存埑: {s} -> {s_converted}")
                                        # 鎴愬姛瑙ｆ瀽锛岃烦杩囧悗缁牸寮忓皾璇?
                                        if ts.tzinfo is None:
                                            ts = timezone.make_aware(ts)
                                        return ts
                                except (ValueError, IndexError) as e:
                                    logger.debug(f"鍐掑彿鍒嗛殧鐨勬绉掓椂闂存埑瑙ｆ瀽澶辫触: {s}, 閿欒: {e}")
                                    # 缁х画灏濊瘯鍏朵粬鏍煎紡
                            # 褰掍竴鍖栦竴浜涘垎闅旂锛屼究浜庡尮閰?
                            s_norm = s.replace("T", " ")
                            last_exc = None
                            ts = None
                            for fmt in candidates:
                                try:
                                    ts = datetime.strptime(s_norm, fmt)
                                    break
                                except Exception as e:
                                    last_exc = e
                                    continue
                            if ts is None:
                                raise ValueError(f"鏃犳硶瑙ｆ瀽鏃堕棿鎴? {s}")

                if ts.tzinfo is None:
                    ts = timezone.make_aware(ts)
                return ts
            
            suffix = Path(file_path).suffix.lower()
            
            if suffix in {".json", ".ndjson"}:
                # 妫€娴嬬紪鐮?
                encoding = detect_encoding(file_path)
                with open(file_path, "r", encoding=encoding) as fh:
                    for line_num, line in enumerate(fh, 1):
                        # 妫€鏌ヨ鏁伴檺鍒?
                        if max_rows and len(parsed_data) >= max_rows:
                            logger.info(f"宸茶揪鍒版渶澶ц鏁伴檺鍒?{max_rows}锛屽仠姝㈣В鏋?)
                            break
                            
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data_dict = json.loads(line)
                            timestamp_str = data_dict.pop("timestamp")
                            ts = parse_ts(timestamp_str)
                            parsed_data.append({
                                'timestamp': ts,
                                'data': data_dict,
                                'line_number': line_num
                            })
                        except Exception as e:
                            logger.warning(f"瑙ｆ瀽绗?{line_num} 琛屽け璐? {e}")
                            
            elif suffix == ".csv":
                # 妫€娴嬬紪鐮?
                encoding = detect_encoding(file_path)
                with open(file_path, "r", encoding=encoding) as fh:
                    reader = csv.reader(fh)
                    rows = list(reader)
                    if not rows:
                        return []
                    headers = rows[0]
                    param_names = headers[1:]
                    
                    for row_num, r in enumerate(rows[1:], 2):
                        # 妫€鏌ヨ鏁伴檺鍒?
                        if max_rows and len(parsed_data) >= max_rows:
                            logger.info(f"宸茶揪鍒版渶澶ц鏁伴檺鍒?{max_rows}锛屽仠姝㈣В鏋?)
                            break
                            
                        if not r:
                            continue
                        try:
                            ts = parse_ts(r[0])
                            data_dict = {}
                            for i, name in enumerate(param_names, start=1):
                                val = r[i] if i < len(r) else None
                                try:
                                    data_dict[name] = float(val) if val not in (None, "") else None
                                except (ValueError, TypeError):
                                    data_dict[name] = val
                            parsed_data.append({
                                'timestamp': ts,
                                'data': data_dict,
                                'line_number': row_num
                            })
                        except Exception as e:
                            logger.warning(f"瑙ｆ瀽绗?{row_num} 琛屽け璐? {e}")
                            
            elif suffix in {".xlsx", ".xlsm", ".xls"}:
                try:
                    from openpyxl import load_workbook
                    wb = load_workbook(file_path, read_only=True)
                    ws = wb.active
                    rows = list(ws.iter_rows(values_only=True))
                    if not rows:
                        return []
                    headers = list(rows[0])
                    param_names = [h for h in headers[1:] if h is not None]
                    
                    for row_num, r in enumerate(rows[1:], 2):
                        # 妫€鏌ヨ鏁伴檺鍒?
                        if max_rows and len(parsed_data) >= max_rows:
                            logger.info(f"宸茶揪鍒版渶澶ц鏁伴檺鍒?{max_rows}锛屽仠姝㈣В鏋?)
                            break
                            
                        if not r or r[0] is None:
                            continue
                        try:
                            ts = parse_ts(r[0])
                            data_dict = {}
                            for i, name in enumerate(param_names, start=1):
                                val = r[i] if i < len(r) else None
                                try:
                                    data_dict[name] = float(val) if (val is not None and val != "") else None
                                except (ValueError, TypeError):
                                    data_dict[name] = val
                            parsed_data.append({
                                'timestamp': ts,
                                'data': data_dict,
                                'line_number': row_num
                            })
                        except Exception as e:
                            logger.warning(f"瑙ｆ瀽绗?{row_num} 琛屽け璐? {e}")
                except ImportError:
                    logger.error("openpyxl鏈畨瑁咃紝鏃犳硶瑙ｆ瀽Excel鏂囦欢")
                    return []
                except Exception as e:
                    logger.error(f"瑙ｆ瀽Excel鏂囦欢澶辫触: {e}")
                    return []
            
            # 鏍规嵁鐢ㄦ埛閫夋嫨澶勭悊閲嶅鏃堕棿鎴?
            if session.add_milliseconds:
                parsed_data = self._add_milliseconds_to_duplicate_timestamps(parsed_data)
                logger.info("鐢ㄦ埛閫夋嫨鑷姩娣诲姞姣锛屽凡澶勭悊閲嶅鏃堕棿鎴?)
            else:
                logger.info("鐢ㄦ埛閫夋嫨涓嶆坊鍔犳绉掞紝淇濇寔鍘熷鏃堕棿鎴?)
            
            logger.info(f"鏂囦欢瑙ｆ瀽瀹屾垚锛屽叡瑙ｆ瀽 {len(parsed_data)} 鏉¤褰?)
            return parsed_data
            
        except Exception as e:
            logger.error(f"瑙ｆ瀽鏂囦欢 {file_path} 澶辫触: {e}")
            return []
    
    def _add_milliseconds_to_duplicate_timestamps(self, parsed_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """涓洪噸澶嶇殑鏃堕棿鎴虫坊鍔犳绉掞紝纭繚姣忓抚閮芥湁鍞竴鐨勬椂闂存埑"""
        if not parsed_data:
            return parsed_data
        
        # 妫€娴嬫槸鍚︽湁鍘熷鏃堕棿鎴冲凡缁忓寘鍚绉掍俊鎭?
        has_milliseconds = False
        for item in parsed_data:
            if item['timestamp'].microsecond > 0:
                has_milliseconds = True
                break
        
        if has_milliseconds:
            logger.info("妫€娴嬪埌鍘熷鏃堕棿鎴冲凡鍖呭惈姣淇℃伅锛岃烦杩囪嚜鍔ㄦ坊鍔犳绉掗€昏緫")
            return parsed_data
        
        # 鎸夋椂闂存埑鍒嗙粍锛堢簿纭埌绉掞級
        timestamp_groups = {}
        for item in parsed_data:
            ts = item['timestamp']
            # 灏嗘椂闂存埑绮剧‘鍒扮浣滀负閿紝浣嗕繚鐣欏師濮嬫椂闂存埑鐢ㄤ簬鍚庣画澶勭悊
            ts_key = ts.replace(microsecond=0)
            if ts_key not in timestamp_groups:
                timestamp_groups[ts_key] = []
            timestamp_groups[ts_key].append(item)
        
        # 澶勭悊閲嶅鏃堕棿鎴?
        processed_data = []
        duplicate_count = 0
        
        for ts_key, items in timestamp_groups.items():
            if len(items) == 1:
                # 鍗曚釜鏃堕棿鎴筹紝鐩存帴娣诲姞锛屼繚鐣欏師濮嬪井绉掍俊鎭?
                item = items[0]
                # 濡傛灉鍘熷鏃堕棿鎴虫病鏈夊井绉掍俊鎭紝鍒欒缃负0
                if item['timestamp'].microsecond == 0:
                    item['timestamp'] = ts_key
                processed_data.append(item)
            else:
                # 澶氫釜鐩稿悓鏃堕棿鎴筹紝娣诲姞姣
                duplicate_count += len(items)
                logger.debug(f"鍙戠幇 {len(items)} 涓浉鍚屾椂闂存埑 {ts_key}锛岃嚜鍔ㄦ坊鍔犳绉?)
                for i, item in enumerate(items):
                    # 娣诲姞姣锛屾瘡甯ч棿闅?姣锛屼粠0寮€濮?
                    new_ts = ts_key.replace(microsecond=i * 1000)
                    item['timestamp'] = new_ts
                    processed_data.append(item)
        
        if duplicate_count > 0:
            logger.debug(f"鎬诲叡澶勭悊浜?{duplicate_count} 涓噸澶嶆椂闂存埑锛屾坊鍔犳绉掑悗纭繚姣忓抚鍞竴")
        
        return processed_data
    
    def _store_data(self, session: ImportSession, parsed_data: List[Dict[str, Any]]) -> List[PHMData]:
        """瀛樺偍瑙ｆ瀽鐨勬暟鎹埌鏁版嵁搴?""
        from django.db import connection
        
        # 閰嶇疆鎵归噺澶у皬
        BATCH_SIZE = get_config('batch_size_for_save', 1000)
        total_records = len(parsed_data)
        created_records = []
        
        logger.info(f"寮€濮嬪瓨鍌?{total_records} 鏉℃暟鎹褰曪紝鎵归噺澶у皬: {BATCH_SIZE}")
        
        # 鍒嗘壒澶勭悊鏁版嵁
        for i in range(0, total_records, BATCH_SIZE):
            batch_data = parsed_data[i:i + BATCH_SIZE]
            batch_to_create = []
            
            # 鍑嗗褰撳墠鎵规鐨勬暟鎹?
            for item in batch_data:
                batch_to_create.append(PHMData(
                    cmg=session.cmg,
                    timestamp=item['timestamp'],
                    data=item['data'],
                    import_session=session
                ))
            
            if batch_to_create:
                # 妫€鏌ユ暟鎹簱杩炴帴
                try:
                    connection.ensure_connection()
                except Exception as e:
                    logger.warning(f"鏁版嵁搴撹繛鎺ユ鏌ュけ璐ワ紝灏濊瘯閲嶆柊杩炴帴: {e}")
                    try:
                        connection.close()
                        connection.ensure_connection()
                    except Exception as reconnect_error:
                        logger.error(f"閲嶆柊杩炴帴鏁版嵁搴撳け璐? {reconnect_error}")
                        raise
                
                # 鎵归噺鍒涘缓褰撳墠鎵规
                try:
                    with transaction.atomic():
                        PHMData.objects.bulk_create(batch_to_create, ignore_conflicts=True)
                    
                    logger.info(f"鎴愬姛瀛樺偍鎵规 {i//BATCH_SIZE + 1}/{(total_records + BATCH_SIZE - 1)//BATCH_SIZE}锛?
                              f"鍖呭惈 {len(batch_to_create)} 鏉¤褰?)
                    
                    # 鏇存柊杩涘害
                    progress = min(100, (i + len(batch_data)) / total_records * 100)
                    self._update_session_progress(session.id, i + len(batch_data), progress)
                    
                except Exception as e:
                    logger.error(f"鎵归噺鍒涘缓鏁版嵁璁板綍澶辫触 (鎵规 {i//BATCH_SIZE + 1}): {e}")
                    # 濡傛灉鏄繛鎺ラ棶棰橈紝灏濊瘯閲嶈瘯
                    if "Server has gone away" in str(e) or "Lost connection" in str(e):
                        logger.info("妫€娴嬪埌鏁版嵁搴撹繛鎺ラ棶棰橈紝灏濊瘯閲嶆柊杩炴帴骞堕噸璇?..")
                        try:
                            connection.close()
                            connection.ensure_connection()
                            # 閲嶈瘯涓€娆?
                            with transaction.atomic():
                                PHMData.objects.bulk_create(batch_to_create, ignore_conflicts=True)
                            logger.info(f"閲嶈瘯鎴愬姛锛屽瓨鍌ㄦ壒娆?{i//BATCH_SIZE + 1}")
                        except Exception as retry_error:
                            logger.error(f"閲嶈瘯澶辫触: {retry_error}")
                            raise
                    else:
                        raise
        
        # 閲嶆柊鏌ヨ鎵€鏈夊垱寤虹殑璁板綍
        try:
            created_records = list(
                PHMData.objects.filter(
                    cmg=session.cmg,
                    import_session=session
                ).order_by("timestamp")
            )
            
            logger.info(f"鎴愬姛瀛樺偍 {len(created_records)} 鏉℃暟鎹褰?)
            
            # 鏇存柊缁熻淇℃伅
            try:
                from .models import DatabaseStatistics
                DatabaseStatistics.update_statistics('cmg_data', session.cmg)
                DatabaseStatistics.update_statistics('total_frames', session.cmg)
                DatabaseStatistics.update_statistics('cmg_data')
                DatabaseStatistics.update_statistics('total_frames')
            except Exception as e:
                logger.error(f"鏇存柊鏁版嵁缁熻淇℃伅澶辫触: {e}")
            
            return created_records
            
        except Exception as e:
            logger.error(f"鏌ヨ鍒涘缓鐨勮褰曞け璐? {e}")
            return []
    
    # 鍒犻櫎閲嶅鐨勬柟娉曞畾涔?
    
    def _run_detection_pipeline(self, session: ImportSession, records: List[PHMData]) -> Dict[str, Any]:
        """杩愯妫€娴嬫祦姘寸嚎 - 娴佸紡澶勭悊鐗堟湰"""
        detection_summary = {
            'total_records': len(records),
            'ims_evaluations': 0,
            'ims_anomalies': 0,
            'rule_evaluations': 0,
            'rule_triggers': 0,
            'msfg_evaluations': 0,
            'detection_errors': 0,
            'processing_time': 0,
            'performance_metrics': {}
        }
        
        if not records:
            return detection_summary
        
        start_time = time.time()
        cmg = records[0].cmg
        
        # 鍒ゆ柇鏄惁闇€瑕佹祦寮忓鐞嗭紙瓒呰繃閰嶇疆闃堝€硷級
        STREAMING_THRESHOLD = get_config('streaming_threshold', 1000)
        use_streaming = len(records) > STREAMING_THRESHOLD
        
        if use_streaming:
            logger.info(f"鏁版嵁閲忚緝澶?{len(records)}甯?锛屽惎鐢ㄦ祦寮忓鐞嗘ā寮?)
            return self._run_streaming_detection_pipeline(session, records, detection_summary, start_time)
        else:
            logger.info(f"鏁版嵁閲忚緝灏?{len(records)}甯?锛屼娇鐢ㄦ壒閲忓鐞嗘ā寮?)
            return self._run_batch_detection_pipeline(session, records, detection_summary, start_time)
    
    def _run_streaming_detection_pipeline(self, session: ImportSession, records: List[PHMData], 
                                        detection_summary: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """娴佸紡妫€娴嬫祦姘寸嚎 - 鍒嗘壒澶勭悊锛屽疄鏃朵繚瀛橈紝闆嗘垚妫€娴嬮鐜囨帶鍒?""
        cmg = records[0].cmg
        BATCH_SIZE = get_config('batch_size', 500)  # 姣忔壒澶勭悊甯ф暟
        
        try:
            # 1. 搴旂敤妫€娴嬮鐜囨帶鍒讹紝閫夋嫨闇€瑕佹娴嬬殑甯?
            logger.info(f"寮€濮嬪簲鐢ㄦ娴嬮鐜囨帶鍒?..")
            selected_frame_indices = detection_frequency_controller.select_frames_for_detection(records)
            detection_summary['frequency_control'] = detection_frequency_controller.get_detection_summary(
                len(records), len(selected_frame_indices)
            )
            logger.info(f"妫€娴嬮鐜囨帶鍒跺畬鎴愶紝閫夋嫨甯ф暟: {len(selected_frame_indices)}/{len(records)}")
            
            # 2. 棰勫姞杞芥墍鏈夐渶瑕佺殑妯″瀷鍜岄厤缃紙涓€娆℃€у姞杞斤級
            logger.info(f"寮€濮嬮鍔犺浇妫€娴嬫ā鍨嬪拰閰嶇疆...")
            preload_start = time.time()
            models_config = self._preload_detection_models(cmg)
            preload_time = time.time() - preload_start
            detection_summary['performance_metrics']['preload_time'] = preload_time
            logger.info(f"妯″瀷棰勫姞杞藉畬鎴愶紝鑰楁椂: {preload_time:.2f}绉?)
            
            # 3. 鍒嗘壒澶勭悊锛堝彧澶勭悊閫変腑鐨勫抚锛?
            selected_records = [records[i] for i in selected_frame_indices]
            total_batches = (len(selected_records) + BATCH_SIZE - 1) // BATCH_SIZE
            logger.info(f"寮€濮嬫祦寮忓鐞嗭紝鍏眥len(selected_records)}甯э紙閫変腑锛夛紝鍒唟total_batches}鎵瑰鐞嗭紝姣忔壒{BATCH_SIZE}甯?)
            
            for batch_index in range(total_batches):
                batch_start = batch_index * BATCH_SIZE
                batch_end = min(batch_start + BATCH_SIZE, len(selected_records))
                batch_records = selected_records[batch_start:batch_end]
                
                logger.info(f"澶勭悊绗瑊batch_index + 1}/{total_batches}鎵癸紝甯batch_start + 1}-{batch_end}锛堥€変腑甯э級")
                
                # 2.1 瀵瑰綋鍓嶆壒娆¤繘琛孖MS妫€娴?
                batch_ims_start = time.time()
                batch_ims_results = self._run_batch_ims_detection_optimized(batch_records, models_config)
                batch_ims_time = time.time() - batch_ims_start
                
                detection_summary['ims_evaluations'] += len(batch_records)
                batch_anomalies = sum(1 for r in batch_ims_results if r and r.get('is_anomaly'))
                detection_summary['ims_anomalies'] += batch_anomalies
                
                logger.info(f"鎵规{batch_index + 1} IMS妫€娴嬪畬鎴愶紝鑰楁椂: {batch_ims_time:.2f}绉掞紝寮傚父甯? {batch_anomalies}")
                
                # 2.2 瀵规墍鏈夊抚杩涜瑙勫垯鍜孧SFG妫€娴嬶紙寮傚父甯э細瀹為檯妫€娴嬶紝姝ｅ父甯э細榛樿鍊硷級
                batch_anomaly_records = []
                batch_normal_records = []
                for i, result in enumerate(batch_ims_results):
                    if result and result.get('is_anomaly'):
                        batch_anomaly_records.append((i, batch_records[i]))
                    else:
                        batch_normal_records.append((i, batch_records[i]))
                
                # 瑙勫垯妫€娴?
                batch_rule_start = time.time()
                batch_rule_results = []
                
                # 瀵瑰紓甯稿抚杩涜瀹為檯瑙勫垯妫€娴?
                if batch_anomaly_records:
                    anomaly_rule_results = self._run_batch_rule_detection_optimized(batch_anomaly_records, models_config)
                    batch_rule_results.extend(anomaly_rule_results)
                
                # 涓烘甯稿抚鐢熸垚榛樿瑙勫垯缁撴灉
                if batch_normal_records:
                    normal_rule_results = self._generate_default_rule_results(batch_normal_records, models_config)
                    batch_rule_results.extend(normal_rule_results)
                
                batch_rule_time = time.time() - batch_rule_start
                
                # 缁熻瑙勫垯璇勪及鏁伴噺
                batch_rule_evaluations = len(batch_rule_results)
                detection_summary['rule_evaluations'] += batch_rule_evaluations
                batch_triggers = sum(1 for r in batch_rule_results if r and r.get('is_triggered'))
                detection_summary['rule_triggers'] += batch_triggers
                
                logger.info(f"鎵规{batch_index + 1} 瑙勫垯妫€娴嬪畬鎴愶紝鑰楁椂: {batch_rule_time:.2f}绉掞紝瑙勫垯璇勪及: {batch_rule_evaluations}锛岃Е鍙戣鍒? {batch_triggers}")
                
                # MSFG妫€娴嬶紙浣跨敤浼樺寲鐗堟湰锛?
                batch_msfg_start = time.time()
                batch_msfg_results = []
                
                # 瀵瑰紓甯稿抚杩涜瀹為檯MSFG妫€娴嬶紙浣跨敤浼樺寲鐗堟湰锛?
                if batch_anomaly_records:
                    # 鈿?鍦ㄧ涓€鎵规椂棰勫姞杞組SFG鍏变韩鏁版嵁
                    if batch_index == 0:
                        logger.info(f"鈿?棣栨壒娆★細棰勫姞杞組SFG鍏变韩鏁版嵁")
                        msfg_shared_data = self._preload_msfg_shared_data(cmg, models_config.get('msfg_definitions'))
                        # 灏嗗叡浜暟鎹瓨鍌ㄥ湪妫€娴嬫憳瑕佷腑锛屼緵鍚庣画鎵规澶嶇敤
                        detection_summary['_msfg_shared_data'] = msfg_shared_data
                    else:
                        # 澶嶇敤绗竴鎵规棰勫姞杞界殑鏁版嵁
                        msfg_shared_data = detection_summary.get('_msfg_shared_data', {})
                    
                    if msfg_shared_data.get('msfg_definition'):
                        # 鈿?浣跨敤浼樺寲鐨勬壒閲廙SFG妫€娴嬶紙澶嶇敤棰勫姞杞芥暟鎹級
                        batch_msfg_results = self._run_batch_msfg_detection_optimized(batch_anomaly_records, msfg_shared_data)
                        detection_summary['msfg_evaluations'] += len(batch_msfg_results)
                    else:
                        logger.warning("MSFG瀹氫箟涓嶅瓨鍦紝璺宠繃MSFG妫€娴?)
                
                # 涓烘甯稿抚鐢熸垚榛樿MSFG缁撴灉
                if batch_normal_records:
                    normal_msfg_results = self._generate_default_msfg_results(batch_normal_records, models_config)
                    batch_msfg_results.extend(normal_msfg_results)
                    detection_summary['msfg_evaluations'] += len(normal_msfg_results)
                
                batch_msfg_time = time.time() - batch_msfg_start
                logger.info(f"鎵规{batch_index + 1} MSFG妫€娴嬪畬鎴愶紙浼樺寲鐗堬級锛岃€楁椂: {batch_msfg_time:.2f}绉掞紝鎴愬姛妫€娴? {len(batch_msfg_results)}")
                
                # 2.3 绔嬪嵆淇濆瓨褰撳墠鎵规鐨勭粨鏋?
                batch_save_start = time.time()
                self._batch_save_detection_results(batch_records, batch_ims_results, batch_rule_results, batch_msfg_results)
                batch_save_time = time.time() - batch_save_start
                
                logger.info(f"鎵规{batch_index + 1} 缁撴灉淇濆瓨瀹屾垚锛岃€楁椂: {batch_save_time:.2f}绉?)
                
                # 2.4 鏇存柊杩涘害锛堣€冭檻妫€娴嬮鐜囨帶鍒讹級
                processed_count = batch_end
                session.processed_records = processed_count
                session.save(update_fields=['processed_records'])
                
                # 鏇存柊杩涘害 - 鍩轰簬閫変腑鐨勫抚鏁拌绠楄繘搴?
                progress = (processed_count / len(selected_records)) * 100
                self._update_redis_progress(session.id, progress, processed_count, len(selected_records))
                
                logger.info(f"鎵规{batch_index + 1} 澶勭悊瀹屾垚锛岀疮璁″鐞? {processed_count}/{len(records)} 甯?)
            
            detection_summary['processing_time'] = time.time() - start_time
            logger.info(f"娴佸紡澶勭悊瀹屾垚锛屾€昏€楁椂: {detection_summary['processing_time']:.2f}绉?)
            
            return detection_summary
            
        except Exception as e:
            logger.error(f"娴佸紡妫€娴嬫祦姘寸嚎澶辫触: {e}")
            detection_summary['detection_errors'] += 1
            detection_summary['processing_time'] = time.time() - start_time
            return detection_summary
    
    def _run_batch_detection_pipeline(self, session: ImportSession, records: List[PHMData], 
                                    detection_summary: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """鎵归噺妫€娴嬫祦姘寸嚎 - 闆嗘垚妫€娴嬮鐜囨帶鍒?""
        cmg = records[0].cmg
        
        # 鍒濆鍖栨墍鏈夋椂闂村彉閲忥紝閬垮厤鏈祴鍊奸敊璇?
        preload_time = 0
        ims_time = 0
        rule_time = 0
        msfg_time = 0
        save_time = 0
        
        try:
            # 1. 搴旂敤妫€娴嬮鐜囨帶鍒讹紝閫夋嫨闇€瑕佹娴嬬殑甯?
            logger.info(f"寮€濮嬪簲鐢ㄦ娴嬮鐜囨帶鍒?..")
            selected_frame_indices = detection_frequency_controller.select_frames_for_detection(records)
            detection_summary['frequency_control'] = detection_frequency_controller.get_detection_summary(
                len(records), len(selected_frame_indices)
            )
            logger.info(f"妫€娴嬮鐜囨帶鍒跺畬鎴愶紝閫夋嫨甯ф暟: {len(selected_frame_indices)}/{len(records)}")
            
            # 2. 棰勫姞杞芥墍鏈夐渶瑕佺殑妯″瀷鍜岄厤缃紙涓€娆℃€у姞杞斤級
            logger.info(f"寮€濮嬮鍔犺浇妫€娴嬫ā鍨嬪拰閰嶇疆...")
            preload_start = time.time()
            models_config = self._preload_detection_models(cmg)
            preload_time = time.time() - preload_start
            detection_summary['performance_metrics']['preload_time'] = preload_time
            logger.info(f"妯″瀷棰勫姞杞藉畬鎴愶紝鑰楁椂: {preload_time:.2f}绉?)
            
            # 3. 鎵归噺IMS妫€娴嬶紙鍙鐞嗛€変腑鐨勫抚锛?
            selected_records = [records[i] for i in selected_frame_indices]
            logger.info(f"寮€濮嬫壒閲廔MS妫€娴嬶紝鍏眥len(selected_records)}鏉¤褰曪紙閫変腑锛?..")
            ims_start = time.time()
            ims_results = self._run_batch_ims_detection_optimized(selected_records, models_config)
            ims_time = time.time() - ims_start
            detection_summary['performance_metrics']['ims_time'] = ims_time
            detection_summary['ims_evaluations'] = len(selected_records)  # 淇锛氬彧瀵归€変腑鐨勫抚杩涜IMS妫€娴?
            detection_summary['ims_anomalies'] = sum(1 for r in ims_results if r and r.get('is_anomaly'))
            logger.info(f"IMS妫€娴嬪畬鎴愶紝鑰楁椂: {ims_time:.2f}绉掞紝寮傚父甯? {detection_summary['ims_anomalies']}")
            
            # 4. 瀵规墍鏈夊抚杩涜瑙勫垯妫€娴嬶紙寮傚父甯э細瀹為檯妫€娴嬶紝姝ｅ父甯э細榛樿鍊硷級
            anomaly_records = []
            normal_records = []
            for i, result in enumerate(ims_results):
                original_index = selected_frame_indices[i]
                if result and result.get('is_anomaly'):
                    anomaly_records.append((original_index, records[original_index]))
                else:
                    normal_records.append((original_index, records[original_index]))
            
            logger.info(f"寮€濮嬫壒閲忚鍒欐娴嬶紝寮傚父甯? {len(anomaly_records)}涓紝姝ｅ父甯? {len(normal_records)}涓?..")
            rule_start = time.time()
            
            # 4.1 瀵瑰紓甯稿抚杩涜瀹為檯瑙勫垯妫€娴?
            rule_results = []
            if anomaly_records:
                anomaly_rule_results = self._run_batch_rule_detection_optimized(anomaly_records, models_config)
                rule_results.extend(anomaly_rule_results)
                logger.info(f"寮傚父甯ц鍒欐娴嬪畬鎴愶紝妫€娴嬪埌 {len(anomaly_rule_results)} 涓粨鏋?)
            
            # 4.2 涓烘甯稿抚鐢熸垚榛樿瑙勫垯缁撴灉
            if normal_records:
                normal_rule_results = self._generate_default_rule_results(normal_records, models_config)
                rule_results.extend(normal_rule_results)
                logger.info(f"姝ｅ父甯ч粯璁よ鍒欑粨鏋滅敓鎴愬畬鎴愶紝鐢熸垚 {len(normal_rule_results)} 涓粨鏋?)
            
            rule_time = time.time() - rule_start
            detection_summary['performance_metrics']['rule_time'] = rule_time
            
            # 缁熻瑙勫垯璇勪及鏁伴噺
            total_rule_evaluations = len(rule_results)
            detection_summary['rule_evaluations'] = total_rule_evaluations
            detection_summary['rule_triggers'] = sum(1 for r in rule_results if r and r.get('is_triggered'))
            logger.info(f"瑙勫垯妫€娴嬪畬鎴愶紝鑰楁椂: {rule_time:.2f}绉掞紝瑙勫垯璇勪及: {total_rule_evaluations}锛岃Е鍙戣鍒? {detection_summary['rule_triggers']}")
            
            # 5. 瀵规墍鏈夊抚杩涜MSFG妫€娴嬶紙寮傚父甯э細瀹為檯妫€娴嬶紝姝ｅ父甯э細榛樿鍊硷級
            logger.info(f"寮€濮嬫壒閲廙SFG妫€娴嬶紝寮傚父甯? {len(anomaly_records)}涓紝姝ｅ父甯? {len(normal_records)}涓?..")
            msfg_start = time.time()
            msfg_results = []
            
            # 5.1 瀵瑰紓甯稿抚杩涜瀹為檯MSFG妫€娴嬶紙浣跨敤浼樺寲鐗堟湰锛?
            if anomaly_records:
                # 鈿?棰勫姞杞組SFG鍏变韩鏁版嵁锛堜竴娆℃€у姞杞斤紝鎵€鏈夊抚澶嶇敤锛?
                msfg_shared_data = self._preload_msfg_shared_data(cmg, models_config.get('msfg_definitions'))
                
                if msfg_shared_data.get('msfg_definition'):
                    # 鈿?浣跨敤浼樺寲鐨勬壒閲廙SFG妫€娴嬶紙澶嶇敤棰勫姞杞芥暟鎹級
                    msfg_results = self._run_batch_msfg_detection_optimized(anomaly_records, msfg_shared_data)
                    detection_summary['msfg_evaluations'] += len(msfg_results)
                    logger.info(f"鉁?寮傚父甯SFG妫€娴嬪畬鎴愶紙浼樺寲鐗堬級锛屾娴嬪埌 {len(msfg_results)} 涓粨鏋?)
                else:
                    logger.warning("MSFG瀹氫箟涓嶅瓨鍦紝璺宠繃MSFG妫€娴?)
                    msfg_results = []
            
            # 5.2 涓烘甯稿抚鐢熸垚榛樿MSFG缁撴灉
            if normal_records:
                normal_msfg_results = self._generate_default_msfg_results(normal_records, models_config)
                msfg_results.extend(normal_msfg_results)
                detection_summary['msfg_evaluations'] += len(normal_msfg_results)
                logger.info(f"姝ｅ父甯ч粯璁SFG缁撴灉鐢熸垚瀹屾垚锛岀敓鎴?{len(normal_msfg_results)} 涓粨鏋?)
            
            msfg_time = time.time() - msfg_start
            detection_summary['performance_metrics']['msfg_time'] = msfg_time
            logger.info(f"MSFG妫€娴嬪畬鎴愶紝鑰楁椂: {msfg_time:.2f}绉掞紝鎴愬姛妫€娴? {len(msfg_results)}")
            
            # 鍒濆鍖栫┖鍒楄〃锛堝吋瀹规€э級
            if not rule_results:
                rule_results = []
            if not msfg_results:
                msfg_results = []
            
            # 5. 鎵归噺淇濆瓨缁撴灉鍒版暟鎹簱
            logger.info("寮€濮嬫壒閲忎繚瀛樻娴嬬粨鏋?..")
            save_start = time.time()
            
            # 涓烘墍鏈夎褰曞垱寤虹粨鏋滄槧灏勶紙鏈娴嬬殑璁板綍璁句负None锛?
            all_ims_results = [None] * len(records)
            for i, result in enumerate(ims_results):
                original_index = selected_frame_indices[i]
                all_ims_results[original_index] = result
            
            self._batch_save_detection_results(records, all_ims_results, rule_results, msfg_results)
            save_time = time.time() - save_start
            detection_summary['performance_metrics']['save_time'] = save_time
            logger.info(f"缁撴灉淇濆瓨瀹屾垚锛岃€楁椂: {save_time:.2f}绉?)
            
            detection_summary['processing_time'] = time.time() - start_time
            
            # 杈撳嚭鎬ц兘缁熻
            total_time = detection_summary['processing_time']
            fps = len(records) / total_time if total_time > 0 else 0
            freq_control = detection_summary.get('frequency_control', {})
            
            # 瀹夊叏鑾峰彇鎵€鏈夋€ц兘鎸囨爣
            performance_metrics = detection_summary.get('performance_metrics', {})
            preload_time = performance_metrics.get('preload_time', preload_time)
            ims_time = performance_metrics.get('ims_time', ims_time)
            rule_time = performance_metrics.get('rule_time', rule_time)
            msfg_time = performance_metrics.get('msfg_time', msfg_time)
            save_time = performance_metrics.get('save_time', save_time)
            
            logger.info(f"=== 妫€娴嬫€ц兘缁熻 ===")
            logger.info(f"鎬昏褰曟暟: {len(records)}")
            logger.info(f"妫€娴嬭褰曟暟: {len(selected_records)}")
            logger.info(f"妫€娴嬫瘮渚? {freq_control.get('detection_ratio', 0)*100:.1f}%")
            logger.info(f"鏃堕棿鑺傜渷: {freq_control.get('estimated_time_saving', '0%')}")
            logger.info(f"妫€娴嬫ā寮? {freq_control.get('mode', 'unknown')}")
            logger.info(f"鎬昏€楁椂: {total_time:.2f}绉?)
            logger.info(f"澶勭悊閫熷害: {fps:.1f} 甯?绉?)
            logger.info(f"妯″瀷棰勫姞杞? {preload_time:.2f}绉?({preload_time/total_time*100:.1f}%)" if total_time > 0 else "妯″瀷棰勫姞杞? {preload_time:.2f}绉?)
            logger.info(f"IMS妫€娴? {ims_time:.2f}绉?({ims_time/total_time*100:.1f}%)" if total_time > 0 else f"IMS妫€娴? {ims_time:.2f}绉?)
            logger.info(f"瑙勫垯妫€娴? {rule_time:.2f}绉?({rule_time/total_time*100:.1f}%)" if total_time > 0 else f"瑙勫垯妫€娴? {rule_time:.2f}绉?)
            logger.info(f"MSFG妫€娴? {msfg_time:.2f}绉?({msfg_time/total_time*100:.1f}%)" if total_time > 0 else f"MSFG妫€娴? {msfg_time:.2f}绉?)
            logger.info(f"缁撴灉淇濆瓨: {save_time:.2f}绉?({save_time/total_time*100:.1f}%)" if total_time > 0 else f"缁撴灉淇濆瓨: {save_time:.2f}绉?)
            logger.info(f"寮傚父甯ф瘮渚? {detection_summary['ims_anomalies']/len(selected_records)*100:.1f}%" if len(selected_records) > 0 else "寮傚父甯ф瘮渚? 0.0%")
            
        except Exception as e:
            logger.error(f"鎵归噺妫€娴嬪け璐? {e}")
            detection_summary['detection_errors'] = len(records)
        
        return detection_summary
    
    def _preload_detection_models(self, cmg: PHM) -> Dict[str, Any]:
        """棰勫姞杞芥墍鏈夋娴嬫ā鍨嬪拰閰嶇疆"""
        config = {
            'ims_models': [],
            'rule_definitions': [],
            'fault_definitions': {},
            'msfg_definitions': None
        }
        
        try:
            # 棰勫姞杞絀MS妯″瀷
            from health_management.ims_service import ims_service
            config['ims_models'] = ims_service.get_active_models_for_cmg(cmg.cmg_id)
            
            # 棰勫姞杞借鍒欏畾涔?
            from rule_detection.models import RuleDefinition, FaultDefinition
            config['rule_definitions'] = list(RuleDefinition.objects.filter(
                cmg_model=cmg.cmg_model, 
                is_online=True
            ).select_related('fault_definition'))
            
            # 棰勫姞杞芥晠闅滃畾涔?
            fault_defs = FaultDefinition.objects.filter(cmg_model=cmg.cmg_model)
            config['fault_definitions'] = {f.fault_name: f for f in fault_defs}
            
            # 棰勫姞杞組SFG瀹氫箟
            from msfg_analysis.models import MSFGDefinition
            config['msfg_definitions'] = MSFGDefinition.objects.filter(
                cmg_model=cmg.cmg_model, 
                is_active=True
            ).order_by('-updated_at').first()
            
            logger.info(f"棰勫姞杞藉畬鎴? IMS妯″瀷{len(config['ims_models'])}涓? 瑙勫垯{len(config['rule_definitions'])}涓?)
            
        except Exception as e:
            logger.warning(f"棰勫姞杞芥ā鍨嬪け璐? {e}")
        
        return config
    
    def _preload_msfg_shared_data(self, cmg: PHM, msfg_definition) -> Dict[str, Any]:
        """
        棰勫姞杞組SFG妫€娴嬫墍闇€鐨勬墍鏈夊叡浜暟鎹?
        
        浼樺寲绛栫暐锛?
        1. 涓€娆℃€у姞杞借妭鐐广€佽竟銆佽鍒欙紙閬垮厤閲嶅鏁版嵁搴撴煡璇級
        2. 棰勬瀯寤篋鐭╅樀鍜孋鐭╅樀锛堥伩鍏嶉噸澶嶇煩闃垫瀯寤猴級
        3. 鍒涘缓鍗曚竴铻嶅悎绠楁硶瀹炰緥鍜岃瘎鍒嗘湇鍔″疄渚嬶紙閬垮厤閲嶅瀵硅薄鍒涘缓锛?
        
        Args:
            cmg: PHM瀵硅薄
            msfg_definition: MSFG瀹氫箟
            
        Returns:
            鍖呭惈鎵€鏈夊叡浜暟鎹殑瀛楀吀
        """
        shared_data = {
            'msfg_definition': msfg_definition,
            'fusion': None,
            'scoring_service': None,
            'test_nodes': [],
            'fault_nodes': [],
            'component_nodes': [],
            'edges': [],
            'D_matrix': None,
            'C_matrix': None,
            'component_mappings': {},
            'component_names': [],
            'test_name_to_idx': {},
            'fault_name_to_idx': {},
            'test_point_rules': []
        }
        
        try:
            if not msfg_definition:
                logger.warning("娌℃湁MSFG瀹氫箟锛岃烦杩囬鍔犺浇")
                return shared_data
            
            logger.info(f"鈿?寮€濮嬮鍔犺浇MSFG鍏变韩鏁版嵁: {msfg_definition.name}")
            start_time = time.time()
            
            # 1. 鍒涘缓铻嶅悎绠楁硶瀹炰緥锛堝鐢級
            from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
            fusion = AdvancedMSFGFusion()
            shared_data['fusion'] = fusion
            
            # 2. 鍒涘缓璇勫垎鏈嶅姟瀹炰緥锛堝鐢級
            from msfg_analysis.services.testpoint_scoring import TestPointScoringService
            scoring_service = TestPointScoringService()
            shared_data['scoring_service'] = scoring_service
            
            # 3. 涓€娆℃€ц幏鍙栬妭鐐瑰拰杈癸紙閬垮厤閲嶅鏌ヨ锛?
            test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg_definition)
            edges = list(msfg_definition.edges.all())
            
            shared_data['test_nodes'] = test_nodes
            shared_data['fault_nodes'] = fault_nodes
            shared_data['component_nodes'] = component_nodes
            shared_data['edges'] = edges
            
            logger.info(f"鉁?鑺傜偣鍔犺浇瀹屾垚: 娴嬬偣={len(test_nodes)}, 鏁呴殰={len(fault_nodes)}, 杈?{len(edges)}")
            
            # 4. 棰勬瀯寤篋鐭╅樀锛堟祴鐐光啋鏁呴殰鏄犲皠锛?
            D_matrix, test_name_to_idx, fault_name_to_idx = fusion.build_d_matrix(
                test_nodes, fault_nodes, edges, msfg_definition
            )
            shared_data['D_matrix'] = D_matrix
            shared_data['test_name_to_idx'] = test_name_to_idx
            shared_data['fault_name_to_idx'] = fault_name_to_idx
            
            logger.info(f"鉁?D鐭╅樀鏋勫缓瀹屾垚: {D_matrix.shape}")
            
            # 5. 鏋勫缓閮ㄤ欢鏄犲皠
            component_mappings = fusion._build_component_mappings(msfg_definition)
            if not component_mappings:
                component_mappings = self._create_default_component_mappings(fault_nodes)
            shared_data['component_mappings'] = component_mappings
            
            # 6. 棰勬瀯寤篊鐭╅樀锛堟晠闅溾啋閮ㄤ欢鏄犲皠锛?
            C_matrix, component_names = fusion.build_c_matrix(fault_nodes, component_mappings)
            shared_data['C_matrix'] = C_matrix
            shared_data['component_names'] = component_names
            
            logger.info(f"鉁?C鐭╅樀鏋勫缓瀹屾垚: {C_matrix.shape}, 閮ㄤ欢鏁?{len(component_names)}")
            
            # 7. 棰勫姞杞芥祴鐐硅鍒?
            from msfg_analysis.models import TestPointRule
            test_point_rules = list(TestPointRule.objects.filter(
                msfg_definition=msfg_definition,
                is_online=True
            ).order_by('test_name', 'weight'))
            shared_data['test_point_rules'] = test_point_rules
            
            logger.info(f"鉁?娴嬬偣瑙勫垯鍔犺浇瀹屾垚: {len(test_point_rules)}鏉?)
            
            elapsed = time.time() - start_time
            logger.info(f"鈿?MSFG鍏变韩鏁版嵁棰勫姞杞藉畬鎴愶紝鑰楁椂: {elapsed:.3f}绉?)
            logger.info(f"馃搳 棰勫姞杞界粺璁? 娴嬬偣{len(test_nodes)}, 鏁呴殰{len(fault_nodes)}, "
                       f"閮ㄤ欢{len(component_names)}, 杈箋len(edges)}, 瑙勫垯{len(test_point_rules)}")
            
        except Exception as e:
            logger.error(f"棰勫姞杞組SFG鍏变韩鏁版嵁澶辫触: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return shared_data
    
    def _run_batch_msfg_detection_optimized(self, anomaly_records: List[Tuple[int, PHMData]], 
                                           shared_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        鎵归噺MSFG妫€娴?- 浼樺寲鐗堟湰
        
        浼樺寲绛栫暐锛?
        1. 澶嶇敤棰勫姞杞界殑鍏变韩鏁版嵁锛堣妭鐐广€佽竟銆佺煩闃点€佽鍒欙級
        2. 澶嶇敤铻嶅悎绠楁硶瀹炰緥鍜岃瘎鍒嗘湇鍔″疄渚?
        3. 閬垮厤閲嶅鏁版嵁搴撴煡璇㈠拰鐭╅樀鏋勫缓
        
        Args:
            anomaly_records: 寮傚父璁板綍鍒楄〃 [(record_index, PHMData), ...]
            shared_data: 棰勫姞杞界殑鍏变韩鏁版嵁
            
        Returns:
            MSFG妫€娴嬬粨鏋滃垪琛?
        """
        import numpy as np
        
        results = []
        
        try:
            # 鎻愬彇鍏变韩鏁版嵁
            msfg_definition = shared_data['msfg_definition']
            fusion = shared_data['fusion']
            scoring_service = shared_data['scoring_service']
            test_nodes = shared_data['test_nodes']
            fault_nodes = shared_data['fault_nodes']
            D_matrix = shared_data['D_matrix']
            C_matrix = shared_data['C_matrix']
            component_mappings = shared_data['component_mappings']
            component_names = shared_data['component_names']
            test_name_to_idx = shared_data['test_name_to_idx']
            fault_name_to_idx = shared_data['fault_name_to_idx']
            
            if not msfg_definition or not fusion:
                logger.warning("MSFG鍏变韩鏁版嵁涓嶅畬鏁达紝璺宠繃鎵归噺妫€娴?)
                return results
            
            logger.info(f"鈿?寮€濮嬫壒閲廙SFG妫€娴嬶紙浼樺寲鐗堬級锛屽叡{len(anomaly_records)}涓紓甯稿抚")
            start_time = time.time()
            
            # 鎵归噺澶勭悊姣忎竴甯э紙澶嶇敤鎵€鏈夐鍔犺浇鏁版嵁锛?
            for i, (record_index, record) in enumerate(anomaly_records):
                try:
                    # 1. 璁＄畻娴嬬偣鍒嗘暟锛堜娇鐢ㄩ鍔犺浇鐨勮鍒欙級
                    test_scores_dict = scoring_service.calculate_test_scores(record, msfg_definition)
                    
                    if not test_scores_dict:
                        logger.warning(f"璁板綍 {record.id} 鏃犳硶璁＄畻娴嬬偣鍒嗘暟锛岃烦杩?)
                        continue
                    
                    # 2. 杞崲娴嬬偣鍒嗘暟鏍煎紡
                    test_scores_array = np.array([
                        test_scores_dict.get(test_node.name, 0.0) 
                        for test_node in test_nodes
                    ], dtype=np.float32)
                    
                    # 3. 浣跨敤棰勬瀯寤虹殑D鐭╅樀璁＄畻鏁呴殰姒傜巼
                    fault_prob = fusion.calculate_fault_probability(D_matrix, test_scores_array)
                    
                    # 4. 璁＄畻妯＄硦姒傜巼
                    fuzzy_prob = fusion.calculate_fuzzy_probability(D_matrix, fault_prob)
                    
                    # 5. 浣跨敤棰勬瀯寤虹殑C鐭╅樀璁＄畻閮ㄤ欢鍋ュ悍搴?
                    component_health = fusion.calculate_component_health_with_cmatrix(
                        fault_prob, fuzzy_prob, C_matrix, component_names, fault_nodes
                    )
                    
                    # 6. 璁＄畻鏁翠綋绯荤粺鍋ュ悍搴?
                    overall_health = fusion.calculate_overall_system_health(fault_prob)
                    
                    # 7. 鏋勫缓娴嬬偣缁撴灉
                    test_results = {}
                    for test_node in test_nodes:
                        test_score = test_scores_dict.get(test_node.name, 0.0)
                        test_results[test_node.name] = {
                            'test_name': test_node.name,
                            'score': float(test_score),  # 鉁?淇锛氫娇鐢?score'瀛楁鍚嶏紙涓嶢PI涓€鑷达級
                            'status': 'abnormal' if test_score > 0.5 else 'normal',
                            'threshold': 0.5
                        }
                    
                    # 8. 鏋勫缓鏁呴殰缁撴灉
                    fault_results = {}
                    for j, fault_node in enumerate(fault_nodes):
                        fault_results[fault_node.name] = {
                            'fault_name': fault_node.name,
                            'fault_probability': float(fault_prob[j]),
                            'fuzzy_probability': float(fuzzy_prob[j]),
                            'contributing_tests': [],
                            'severity': 'high' if fault_prob[j] > 0.7 else 'medium' if fault_prob[j] > 0.5 else 'low'
                        }
                    
                    # 9. 鏋勫缓閮ㄤ欢缁撴灉
                    component_results = {
                        comp_name: {
                            'health_score': float(comp_data.get('health_score', 1.0)),
                            'status': 'critical' if comp_data.get('health_score', 1.0) < 0.7 else 'healthy',
                            'fault_probability': float(comp_data.get('fault_probability', 0.0)),
                            'fuzzy_probability': float(comp_data.get('fuzzy_probability', 0.0)),
                            'fault_count': int(comp_data.get('fault_count', 0)),
                            'max_fault_prob': float(comp_data.get('max_fault_prob', 0.0)),
                            'avg_fault_prob': float(comp_data.get('avg_fault_prob', 0.0)),
                            'method': 'standard_cmatrix_optimized'
                        }
                        for comp_name, comp_data in component_health.items()
                    }
                    
                    # 10. 绯荤粺缁撴灉
                    system_results = {
                        'overall_health': float(overall_health),
                        'status': 'critical' if overall_health < 0.7 else 'healthy',
                        'method': 'standard_cmatrix_optimized',
                        'component_count': len(component_results),
                        'worst_component': min(component_results.items(), key=lambda x: x[1]['health_score'])[0] if component_results else None,
                        'min_health': min([c['health_score'] for c in component_results.values()]) if component_results else 1.0,
                        'max_health': max([c['health_score'] for c in component_results.values()]) if component_results else 1.0,
                        'avg_health': np.mean([c['health_score'] for c in component_results.values()]) if component_results else 1.0
                    }
                    
                    # 11. 鎻愬彇鍏抽敭淇℃伅
                    detected_faults = [
                        name for name, data in fault_results.items() 
                        if data['fault_probability'] > 0.7
                    ]
                    
                    critical_components = [
                        name for name, data in component_results.items() 
                        if data['health_score'] < 0.7
                    ]
                    
                    # 12. 鏋勫缓瀹屾暣缁撴灉
                    result = {
                        'data_point_id': record.id,
                        'data_point_timestamp': record.timestamp.isoformat(),
                        'msfg_definition_id': msfg_definition.id,
                        'msfg_definition_name': msfg_definition.name,
                        'test_results': test_results,
                        'fault_results': fault_results,
                        'system_results': system_results,
                        'component_results': component_results,
                        'overall_health_score': float(overall_health),
                        'detected_faults': detected_faults,
                        'critical_components': critical_components,
                        'analysis_details': {
                            "source": "batch_processing_optimized",
                            "method": "standard_cmatrix_optimized",
                            "algorithm": "log_probability_with_cmatrix",
                            "total_test_nodes": len(test_nodes),
                            "total_fault_nodes": len(fault_nodes),
                            "total_edges": len(shared_data['edges']),
                            "component_mappings_count": len(component_mappings),
                            "detection_summary": {
                                'total_test_points': len(test_nodes),
                                'abnormal_test_points': len([t for t in test_results.values() if t.get('status') == 'abnormal']),
                                'total_faults': len(fault_nodes),
                                'detected_faults_count': len(detected_faults),
                                'total_components': len(component_results),
                                'critical_components_count': len(critical_components)
                            },
                            'optimization_note': '浣跨敤棰勫姞杞芥暟鎹拰棰勬瀯寤虹煩闃碉紝閬垮厤閲嶅鏌ヨ鍜岃绠?
                        }
                    }
                    
                    results.append(result)
                    
                    # 姣?0甯ц緭鍑轰竴娆¤繘搴?
                    if (i + 1) % 50 == 0:
                        logger.info(f"鎵归噺MSFG妫€娴嬭繘搴? {i + 1}/{len(anomaly_records)}")
                    
                except Exception as e:
                    logger.warning(f"鎵归噺MSFG妫€娴嬭褰?{record.id} 澶辫触: {e}")
                    continue
            
            elapsed = time.time() - start_time
            fps = len(anomaly_records) / elapsed if elapsed > 0 else 0
            logger.info(f"鈿?鎵归噺MSFG妫€娴嬪畬鎴? {len(results)}/{len(anomaly_records)}甯? "
                       f"鑰楁椂: {elapsed:.2f}绉? 閫熷害: {fps:.1f}甯?绉?)
            
        except Exception as e:
            logger.error(f"鎵归噺MSFG妫€娴嬪け璐? {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return results
    
    def _run_batch_ims_detection_optimized(self, records: List[PHMData], models_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """浼樺寲鐨勬壒閲廔MS妫€娴?- 涓茶浼樺寲鐗堟湰"""
        results = [None] * len(records)
        
        if not models_config.get('ims_models'):
            logger.info("娌℃湁鍙敤鐨処MS妯″瀷锛岃烦杩嘔MS妫€娴?)
            return results
        
        ims_model = models_config['ims_models'][0]
        from health_management.ims_service import ims_service
        
        # 棰勫姞杞芥ā鍨嬪埌鍐呭瓨
        algorithm = ims_service.load_model(ims_model.id)
        if not algorithm:
            logger.warning("IMS妯″瀷鍔犺浇澶辫触")
            return results
        
        # 涓茶澶勭悊锛屼絾浼樺寲鏁版嵁搴撴搷浣?
        for i, record in enumerate(records):
            try:
                result = ims_service.detect_anomaly(record, ims_model.id)
                if result:
                    results[i] = {
                        'is_anomaly': result.is_anomaly,
                        'anomaly_score': result.anomaly_score,
                        'model_name': result.ims_model.name,
                        'result_object': result
                    }
                    
                # 鏇存柊杩涘害
                if (i + 1) % DETECTION_CONFIG['PROGRESS_UPDATE_INTERVAL'] == 0:
                    progress = ((i + 1) / len(records)) * 100
                    self._update_session_progress(record.import_session.id, i + 1, progress)
                    # 灏嗚繘搴﹀啓鍏edis渚涘墠绔疆璇?
                    self._update_redis_progress(record.import_session.id, progress, i + 1, len(records))
                    
            except Exception as e:
                logger.warning(f"IMS妫€娴嬭褰?{record.id} 澶辫触: {e}")
        
        return results
    
    def _run_batch_rule_detection_optimized(self, anomaly_records: List[Tuple[int, PHMData]], models_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """浼樺寲鐨勬壒閲忚鍒欐娴?- 鏀寔澧炲己鐗堣鍒欐娴嬪櫒"""
        results = []
        
        if not models_config.get('rule_definitions'):
            logger.info("娌℃湁鍙敤鐨勮鍒欏畾涔夛紝璺宠繃瑙勫垯妫€娴?)
            return []
        
        # 妫€鏌ユ槸鍚︽湁浣跨敤楂樼骇缁熻鍑芥暟鐨勮鍒?
        has_advanced_rules = False
        for rule_def in models_config['rule_definitions']:
            rule_expression = rule_def.rule_expression
            if any(func in rule_expression for func in ['mean(', 'std(', 'var(', 'mad(', 'rms(', 'slope(', 'diffmean(', 'diffstd(', 'ma(', 'ma_diff(', 'autocorr(']):
                has_advanced_rules = True
                break
        
        if has_advanced_rules:
            logger.info("妫€娴嬪埌楂樼骇缁熻鍑芥暟瑙勫垯锛屼娇鐢ㄥ寮虹増瑙勫垯妫€娴嬪櫒")
            return self._run_enhanced_rule_detection(anomaly_records, models_config)
        else:
            logger.info("浣跨敤浼犵粺瑙勫垯妫€娴嬪櫒")
            return self._run_traditional_rule_detection(anomaly_records, models_config)
    
    def _run_enhanced_rule_detection(self, anomaly_records: List[Tuple[int, PHMData]], models_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """浣跨敤澧炲己鐗堣鍒欐娴嬪櫒杩涜妫€娴?""
        results = []
        
        try:
            # 鑾峰彇PHM瀵硅薄
            if not anomaly_records:
                return results
            
            cmg = anomaly_records[0][1].cmg
            
            # 鍒涘缓澧炲己鐗堣鍒欓厤缃?
            rule_config = {
                "rules": [],
                "parameter_names": [],
                "fault_name_map": {}
            }
            
            # 鏀堕泦鍙傛暟鍚?
            parameter_names = set()
            for _, record in anomaly_records:
                if isinstance(record.data, dict):
                    for param_name in record.data.keys():
                        # 杩囨护鎺夋暟鍊煎舰寮忕殑鍙傛暟鍚?
                        if isinstance(param_name, str):
                            try:
                                float(param_name)  # 灏濊瘯杞崲涓烘暟鍊?
                                # 濡傛灉鎴愬姛杞崲锛岃鏄庢槸鏁板€硷紝璺宠繃
                                continue
                            except (ValueError, TypeError):
                                # 濡傛灉杞崲澶辫触锛岃鏄庢槸鏈夋晥鐨勫弬鏁板悕
                                parameter_names.add(param_name)
                        elif isinstance(param_name, (int, float)):
                            # 鏁板€肩被鍨嬬殑閿紝璺宠繃
                            continue
                        else:
                            # 鍏朵粬绫诲瀷锛岃浆鎹负瀛楃涓?
                            parameter_names.add(str(param_name))
            
            rule_config["parameter_names"] = list(parameter_names)
            
            # 鏋勫缓瑙勫垯閰嶇疆
            for rule_def in models_config['rule_definitions']:
                rule_config["rules"].append({
                    "rule_id": rule_def.rule_id,
                    "fault_name": rule_def.fault_definition.fault_name,
                    "fault_level": rule_def.fault_definition.fault_level,
                    "component": rule_def.fault_definition.component,
                    "expression": rule_def.rule_expression,
                    "related_parameters": list(parameter_names),  # 绠€鍖栧鐞嗭紝鍖呭惈鎵€鏈夊弬鏁?
                    "is_online": rule_def.is_online,
                    "source": rule_def.source,
                    "plan_description": rule_def.plan_description
                })
            
            # 鍒涘缓澧炲己鐗堟娴嬪櫒
            from rule_detection.algorithms.rule.enhanced_rule_detector import EnhancedRuleDetector
            detector = EnhancedRuleDetector(rule_config)
            
            # 涓烘娴嬪櫒鎻愪緵鍘嗗彶鏁版嵁锛堜粠鏁版嵁搴撹幏鍙栨渶杩戠殑鏁版嵁锛?
            self._warmup_enhanced_detector(detector, cmg, parameter_names)
            
            # 瀵规瘡涓紓甯稿抚杩涜妫€娴?
            for record_index, record in anomaly_records:
                try:
                    # 鍑嗗鏁版嵁甯?
                    data_frame = {}
                    if isinstance(record.data, dict):
                        data_frame = record.data
                    elif hasattr(record, 'numeric_params'):
                        data_frame = record.numeric_params
                    
                    # 馃敡 淇锛氳缃甤urrent_data閬垮厤lambda閿欒
                    detector.current_data = data_frame
                    
                    # 鎵ц妫€娴?
                    detection_results = detector.detect(data_frame, record.timestamp)
                    
                    # 鏍煎紡鍖栫粨鏋?
                    for result in detection_results:
                        if result.get('is_triggered'):
                            results.append({
                                'rule_name': result.get('rule_id', ''),
                                'fault_name': result.get('fault_name', ''),
                                'is_triggered': True,
                                'confidence_score': result.get('confidence_score', 0.0),
                                'fault_level': result.get('fault_level', 1),
                                'component': result.get('component', ''),
                                'details': result,
                                'record_index': record_index
                            })
                    
                    logger.debug(f"澧炲己瑙勫垯妫€娴嬭褰?{record.id}: 妫€娴嬪埌 {len(detection_results)} 涓Е鍙戣鍒?)
                    
                except Exception as e:
                    logger.warning(f"澧炲己瑙勫垯妫€娴嬭褰?{record.id} 澶辫触: {e}")
            
            logger.info(f"澧炲己瑙勫垯妫€娴嬪畬鎴愶紝鍏卞鐞?{len(anomaly_records)} 涓紓甯稿抚锛屾娴嬪埌 {len(results)} 涓Е鍙戣鍒?)
            
        except Exception as e:
            logger.error(f"澧炲己瑙勫垯妫€娴嬪け璐? {e}")
        
        return results
    
    def _run_traditional_rule_detection(self, anomaly_records: List[Tuple[int, PHMData]], models_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """浣跨敤浼犵粺瑙勫垯妫€娴嬪櫒杩涜妫€娴?""
        results = []
        
        # 鎵归噺澶勭悊寮傚父甯?
        for i, (record_index, record) in enumerate(anomaly_records):
            try:
                # 浣跨敤鐜版湁鐨勮鍒欐娴嬫湇鍔?
                from rule_detection.service import evaluate_rules_for_data_point
                rule_results = evaluate_rules_for_data_point(record)
                
                # 鏍煎紡鍖栫粨鏋?
                formatted_results = []
                for r in rule_results:
                    if r.get('is_triggered'):
                        formatted_results.append({
                            'rule_name': r.get('rule_id', ''),
                            'fault_name': r.get('fault_name', ''),
                            'is_triggered': True,
                            'confidence_score': r.get('score', 0.0),
                            'fault_level': r.get('fault_level', 1),
                            'component': r.get('component', ''),
                            'details': r,
                            'record_index': record_index
                        })
                
                results.extend(formatted_results)
                logger.debug(f"浼犵粺瑙勫垯妫€娴嬭褰?{record.id}: 妫€娴嬪埌 {len(formatted_results)} 涓Е鍙戣鍒?)
                
            except Exception as e:
                logger.warning(f"浼犵粺瑙勫垯妫€娴嬭褰?{record.id} 澶辫触: {e}")
        
        logger.info(f"浼犵粺瑙勫垯妫€娴嬪畬鎴愶紝鍏卞鐞?{len(anomaly_records)} 涓紓甯稿抚锛屾娴嬪埌 {len(results)} 涓Е鍙戣鍒?)
        return results
    
    def _warmup_enhanced_detector(self, detector: EnhancedRuleDetector, cmg: PHM, parameter_names: set) -> None:
        """涓哄寮虹増妫€娴嬪櫒鎻愪緵鍘嗗彶鏁版嵁"""
        try:
            # 鑾峰彇鏈€杩戠殑鍘嗗彶鏁版嵁锛堟渶澶?000甯э級
            from data_management.models import PHMData
            recent_data = PHMData.objects.filter(
                cmg=cmg
            ).order_by('-timestamp')[:1000]
            
            if not recent_data:
                logger.info("娌℃湁鍘嗗彶鏁版嵁鐢ㄤ簬澧炲己妫€娴嬪櫒棰勭儹")
                return
            
            # 鎸夋椂闂撮『搴忔帓搴?
            recent_data = list(reversed(recent_data))
            
            logger.info(f"涓哄寮烘娴嬪櫒鎻愪緵 {len(recent_data)} 甯у巻鍙叉暟鎹?)
            
            # 閫愬抚鏇存柊妫€娴嬪櫒
            for i, record in enumerate(recent_data):
                if isinstance(record.data, dict):
                    detector.update_data(record.data, record.timestamp, i)
                
                # 姣?00甯ц緭鍑轰竴娆¤繘搴?
                if (i + 1) % 100 == 0:
                    logger.info(f"澧炲己妫€娴嬪櫒棰勭儹杩涘害: {i + 1}/{len(recent_data)}")
            
            logger.info("澧炲己妫€娴嬪櫒棰勭儹瀹屾垚")
            
        except Exception as e:
            logger.warning(f"澧炲己妫€娴嬪櫒棰勭儹澶辫触: {e}")
    
    def _batch_save_detection_results(self, records: List[PHMData], ims_results: List[Dict], rule_results: List[Dict], msfg_results: List[Dict] = None) -> None:
        """鎵归噺淇濆瓨妫€娴嬬粨鏋滃埌鏁版嵁搴?""
        from health_management.models import IMSDetectionResult
        from rule_detection.models import RuleDetectionResult
        
        # 鎵归噺鍒涘缓IMS缁撴灉
        ims_objects_to_create = []
        for i, (record, ims_result) in enumerate(zip(records, ims_results)):
            if ims_result and ims_result.get('result_object'):
                # 妫€鏌ユ槸鍚﹀凡瀛樺湪缁撴灉 - 浣跨敤filter().first()閬垮厤閲嶅
                existing_result = IMSDetectionResult.objects.filter(
                    data_point=record,
                    ims_model=ims_result['result_object'].ims_model
                ).first()
                
                if existing_result:
                    # 鏇存柊鐜版湁缁撴灉
                    existing_result.is_anomaly = ims_result['result_object'].is_anomaly
                    existing_result.anomaly_score = ims_result['result_object'].anomaly_score
                    existing_result.parameter_scores = ims_result['result_object'].parameter_scores
                    existing_result.detection_details = ims_result['result_object'].detection_details
                    existing_result.save()
                else:
                    # 鍒涘缓鏂扮粨鏋?
                    ims_objects_to_create.append(ims_result['result_object'])
        
        if ims_objects_to_create:
            IMSDetectionResult.objects.bulk_create(ims_objects_to_create, ignore_conflicts=True)
            logger.info(f"鎵归噺淇濆瓨浜?{len(ims_objects_to_create)} 涓狪MS妫€娴嬬粨鏋?)
            
            # 鏇存柊IMS缁熻淇℃伅
            try:
                from .models import DatabaseStatistics
                if records and len(records) > 0:
                    cmg = records[0].cmg
                    DatabaseStatistics.update_statistics('ims_results', cmg)
                    DatabaseStatistics.update_statistics('anomaly_frames', cmg)
                    DatabaseStatistics.update_statistics('ims_results')
                    DatabaseStatistics.update_statistics('anomaly_frames')
            except Exception as e:
                logger.error(f"鏇存柊IMS缁熻淇℃伅澶辫触: {e}")
        
        # 鎵归噺鍒涘缓瑙勫垯缁撴灉
        # 馃敡 淇锛氫繚瀛樻墍鏈夎鍒欑粨鏋滐紝涓嶄粎浠呮槸is_triggered=True鐨勭粨鏋?
        # 杩欐牱鍙互淇濆瓨杩炵画璇勫垎淇℃伅锛屽嵆浣胯鍒欐湭瑙﹀彂
        rule_objects_to_create = []
        for rule_result in rule_results:
            # 绉婚櫎is_triggered鏉′欢妫€鏌ワ紝淇濆瓨鎵€鏈夎鍒欑粨鏋?
            record_index = rule_result.get('record_index', 0)
            if record_index < len(records):
                record = records[record_index]
                
                # 鑾峰彇鏁呴殰瀹氫箟鍜岃鍒欏畾涔?
                from rule_detection.models import FaultDefinition, RuleDefinition
                fault_def = FaultDefinition.objects.filter(
                    cmg_model=record.cmg.cmg_model,
                    fault_name=rule_result.get('fault_name', '')
                ).first()
                
                rule_def = RuleDefinition.objects.filter(
                    cmg_model=record.cmg.cmg_model,
                    rule_id=rule_result.get('rule_name', '')
                ).first()
                
                if fault_def and rule_def:
                    # 妫€鏌ユ槸鍚﹀凡瀛樺湪缁撴灉 - 浣跨敤filter().first()閬垮厤閲嶅
                    existing_rule_result = RuleDetectionResult.objects.filter(
                        data_point=record,
                        rule_definition=rule_def,
                        fault_definition=fault_def
                    ).first()
                    
                    # 纭繚confidence_score鍦ㄦ湁鏁堣寖鍥村唴
                    confidence_score = max(0.0, min(1.0, float(rule_result.get('confidence_score', 0.0))))
                    is_triggered = bool(rule_result.get('is_triggered', False))
                    
                    if existing_rule_result:
                        # 鏇存柊鐜版湁缁撴灉
                        existing_rule_result.is_triggered = is_triggered
                        existing_rule_result.confidence_score = confidence_score
                        existing_rule_result.detection_details = rule_result.get('details', {})
                        existing_rule_result.save()
                    else:
                        # 鍒涘缓鏂扮粨鏋?
                        rule_objects_to_create.append(RuleDetectionResult(
                            data_point=record,
                            rule_definition=rule_def,
                            fault_definition=fault_def,
                            is_triggered=is_triggered,
                            confidence_score=confidence_score,
                            detection_details=rule_result.get('details', {})
                        ))
        
        if rule_objects_to_create:
            RuleDetectionResult.objects.bulk_create(rule_objects_to_create, ignore_conflicts=True)
            logger.info(f"鎵归噺淇濆瓨浜?{len(rule_objects_to_create)} 涓鍒欐娴嬬粨鏋?)
            
            # 鏇存柊瑙勫垯缁熻淇℃伅
            try:
                from .models import DatabaseStatistics
                if records and len(records) > 0:
                    cmg = records[0].cmg
                    DatabaseStatistics.update_statistics('rule_results', cmg)
                    DatabaseStatistics.update_statistics('rule_results')
            except Exception as e:
                logger.error(f"鏇存柊瑙勫垯缁熻淇℃伅澶辫触: {e}")
        
        # 鎵归噺鍒涘缓MSFG缁撴灉
        if msfg_results:
            from msfg_analysis.models import MSFGAnalysisResult
            msfg_objects_to_create = []
            
            for msfg_result in msfg_results:
                if msfg_result:
                    # 鏍规嵁ID鑾峰彇PHMData瀵硅薄
                    try:
                        data_point = PHMData.objects.get(id=msfg_result['data_point_id'])
                        msfg_definition = MSFGDefinition.objects.get(id=msfg_result['msfg_definition_id'])
                    except (PHMData.DoesNotExist, MSFGDefinition.DoesNotExist) as e:
                        logger.warning(f"鏃犳硶鎵惧埌MSFG缁撴灉鐩稿叧鐨勬暟鎹偣鎴朚SFG瀹氫箟: {e}")
                        continue
                    
                    # 妫€鏌ユ槸鍚﹀凡瀛樺湪缁撴灉
                    existing_msfg_result = MSFGAnalysisResult.objects.filter(
                        data_point=data_point,
                        msfg_definition=msfg_definition
                    ).first()
                    
                    if existing_msfg_result:
                        # 鏇存柊鐜版湁缁撴灉
                        existing_msfg_result.test_results = msfg_result['test_results']
                        existing_msfg_result.fault_results = msfg_result['fault_results']
                        existing_msfg_result.system_results = msfg_result['system_results']
                        existing_msfg_result.component_results = msfg_result['component_results']
                        existing_msfg_result.overall_health_score = msfg_result['overall_health_score']
                        existing_msfg_result.detected_faults = msfg_result['detected_faults']
                        existing_msfg_result.critical_components = msfg_result['critical_components']
                        existing_msfg_result.analysis_details = msfg_result['analysis_details']
                        existing_msfg_result.save()
                    else:
                        # 鍒涘缓鏂扮粨鏋?
                        msfg_objects_to_create.append(MSFGAnalysisResult(
                            data_point=data_point,
                            msfg_definition=msfg_definition,
                            test_results=msfg_result['test_results'],
                            fault_results=msfg_result['fault_results'],
                            system_results=msfg_result['system_results'],
                            component_results=msfg_result['component_results'],
                            overall_health_score=msfg_result['overall_health_score'],
                            detected_faults=msfg_result['detected_faults'],
                            critical_components=msfg_result['critical_components'],
                            analysis_details=msfg_result['analysis_details']
                        ))
            
            if msfg_objects_to_create:
                MSFGAnalysisResult.objects.bulk_create(msfg_objects_to_create, ignore_conflicts=True)
                logger.info(f"鎵归噺淇濆瓨浜?{len(msfg_objects_to_create)} 涓狹SFG妫€娴嬬粨鏋?)
                
                # 鏇存柊MSFG缁熻淇℃伅
                try:
                    from .models import DatabaseStatistics
                    if records and len(records) > 0:
                        cmg = records[0].cmg
                        DatabaseStatistics.update_statistics('msfg_results', cmg)
                        DatabaseStatistics.update_statistics('msfg_results')
                except Exception as e:
                    logger.error(f"鏇存柊MSFG缁熻淇℃伅澶辫触: {e}")
    
    def _detect_single_record(self, record: PHMData, cmg: PHM) -> Dict[str, Any]:
        """瀵瑰崟鏉¤褰曡繘琛屾娴?""
        result = {
            'ims_result': None,
            'rule_results': [],
            'msfg_result': None,
            'has_models': False
        }
        
        try:
            # 1. IMS妫€娴?- 浣跨敤鐙珛鐨勬壒閲忔娴嬮€昏緫
            ims_results = self._run_batch_ims_detection(record, cmg)
            if ims_results:
                ims_result = ims_results[0]  # 鍙栫涓€涓粨鏋?
                result['ims_result'] = {
                    'is_anomaly': ims_result.is_anomaly,
                    'anomaly_score': ims_result.anomaly_score,
                    'model_name': ims_result.ims_model.name
                }
                result['has_models'] = True
                
                # 2. 鍙湁妫€娴嬪埌寮傚父鏃舵墠杩涜瑙勫垯妫€娴?
                if ims_result.is_anomaly:
                    try:
                        rule_results = self._run_batch_rule_detection(record, cmg)
                        result['rule_results'] = rule_results
                    except Exception as e:
                        logger.warning(f"鎵归噺瑙勫垯妫€娴嬪け璐? {e}")
                    
                    # 3. MSFG铻嶅悎妫€娴嬶紙鏆傛椂璺宠繃锛屽洜涓虹洰鍓嶆病鏈夊彲鐢ㄦā鍨嬶級
                    try:
                        msfg_result = self._run_msfg_detection(record, cmg)
                        if msfg_result:
                            result['msfg_result'] = msfg_result
                        else:
                            logger.debug(f"MSFG妫€娴嬭烦杩? 鏆傛椂娌℃湁鍙敤鐨勫鐞嗛€昏緫")
                    except Exception as e:
                        logger.warning(f"MSFG妫€娴嬪け璐? {e}")
            else:
                # 娌℃湁IMS妯″瀷鍙敤锛岃褰曚絾涓嶈涓洪敊璇?
                logger.info(f"PHM {cmg.cmg_id} 娌℃湁鍙敤鐨処MS妯″瀷杩涜鎵归噺妫€娴?)
                        
        except Exception as e:
            logger.error(f"妫€娴嬭褰?{record.id} 鏃跺嚭閿? {e}")
            # 涓嶆姏鍑哄紓甯革紝杩斿洖閿欒淇℃伅
            result['error'] = str(e)
        
        return result
    
    def _run_batch_ims_detection(self, record: PHMData, cmg: PHM) -> List:
        """杩愯鎵归噺IMS妫€娴?- 鍒╃敤鐜版湁鐨処MS鏈嶅姟"""
        try:
            logger.debug(f"寮€濮嬫壒閲廔MS妫€娴? PHM {cmg.cmg_id}, 璁板綍 {record.id}")
            
            # 浣跨敤鐜版湁鐨処MS鏈嶅姟鑾峰彇娲昏穬妯″瀷
            from health_management.ims_service import ims_service
            active_models = ims_service.get_active_models_for_cmg(cmg.cmg_id)
            
            if not active_models:
                logger.info(f"PHM {cmg.cmg_id} 娌℃湁婵€娲荤殑IMS妯″瀷鍙敤浜庢壒閲忔娴?)
                return []
            
            # 瀵逛簬鎵归噺澶勭悊锛屾垜浠娇鐢ㄧ涓€涓縺娲荤殑妯″瀷
            ims_model = active_models[0]
            logger.debug(f"浣跨敤IMS妯″瀷: {ims_model.name} (ID: {ims_model.id})")
            
            # 鎵ц妫€娴?
            result = ims_service.detect_anomaly(record, ims_model.id)
            return [result] if result else []
            
        except Exception as e:
            logger.warning(f"鎵归噺IMS妫€娴嬪け璐? {e}")
            return []
    
    def _run_batch_rule_detection(self, record: PHMData, cmg: PHM) -> List[Dict[str, Any]]:
        """杩愯鎵归噺瑙勫垯妫€娴?- 鏍规湰鎬ч噸鏋勶紝鐩存帴浣跨敤鎴戜滑淇鐨勫寮鸿鍒欐娴嬪櫒
        
        閲嶆瀯瑕佺偣锛?
        1. 鉁?鐩存帴浣跨敤淇鐨凟nhancedRuleDetector锛堣繛缁瘎鍒嗭紝闈炰簩鍊煎寲锛?
        2. 鉁?浣跨敤淇鐨処mprovedRuleScoring锛堝寘鍚浐瀹氱殑level鍑芥暟锛?
        3. 鉁?纭繚lambda鍑芥暟鍙傛暟姝ｇ‘锛堝凡淇*args鏀寔锛?
        4. 鉁?閬垮厤鏃х殑evaluate_rules_for_data_point鍑芥暟
        """
        try:
            logger.debug(f"寮€濮嬫壒閲忚鍒欐娴? PHM {cmg.cmg_id}, 璁板綍 {record.id}")
            
            # 妫€鏌ユ槸鍚︽湁娲昏穬鐨勮鍒欏畾涔?
            from rule_detection.models import RuleDefinition
            active_rules = RuleDefinition.objects.filter(
                cmg_model=cmg.cmg_model, 
                is_online=True
            )
            
            if not active_rules.exists():
                logger.info(f"PHM妯″瀷 {cmg.cmg_model.model_name} 娌℃湁婵€娲荤殑瑙勫垯鍙敤浜庢壒閲忔娴?)
                return []
            
            # 馃敡 鏍规湰鎬ч噸鏋勶細鐩存帴浣跨敤鎴戜滑淇鐨勫寮鸿鍒欐娴嬪櫒
            from rule_detection.algorithms.rule.enhanced_rule_detector import EnhancedRuleDetector
            from datetime import datetime, timezone
            import pandas as pd
            
            # 1. 鏋勫缓瑙勫垯閰嶇疆锛屼粠涓婁紶鏂囦欢鏁版嵁涓彁鍙栧弬鏁板悕
            # 馃敡 淇锛氱洿鎺ヤ粠涓婁紶鐨勬枃浠舵暟鎹腑鑾峰彇鍙傛暟鍚嶏紝閬垮厤"鏈煡鍙傛暟"璀﹀憡
            parameter_names = set()
            if hasattr(record, 'data') and isinstance(record.data, dict):
                parameter_names = set(record.data.keys())
                logger.debug(f"浠庝笂浼犳枃浠舵彁鍙栧弬鏁板悕: {sorted(parameter_names)}")
            else:
                logger.warning(f"璁板綍 {record.id} 娌℃湁鏁版嵁锛屾棤娉曟彁鍙栧弬鏁板悕")
                return []
            
            rule_config = {
                'rules': [
                    {
                        'rule_id': rule.rule_id,
                        'expression': rule.rule_expression,  # 馃敡 淇锛氫娇鐢ㄦ纭殑瀛楁鍚?
                        'fault_name': rule.fault_definition.fault_name,
                        'fault_level': rule.fault_definition.fault_level,
                        'component': rule.fault_definition.component,
                        'description': getattr(rule, 'plan_description', '')
                    }
                    for rule in active_rules
                ],
                'parameter_names': list(parameter_names)  # 鐩存帴浣跨敤涓婁紶鏂囦欢涓殑鍙傛暟鍚?
            }
            
            logger.debug(f"鏋勫缓瑙勫垯閰嶇疆瀹屾垚: {len(rule_config['rules'])} 鏉¤鍒?)
            
            # 2. 鍒涘缓澧炲己瑙勫垯妫€娴嬪櫒锛堜娇鐢ㄦ垜浠慨澶嶇殑閫昏緫锛?
            detector = EnhancedRuleDetector(rule_config)
            
            # 3. 鍑嗗鏁版嵁 - 杞崲涓篋ataFrame鏍煎紡
            if hasattr(record, 'data') and isinstance(record.data, dict):
                # 浣跨敤data瀛楁涓殑鏁板€兼暟鎹?
                data_dict = {}
                for param_name, param_value in record.data.items():
                    try:
                        # 灏濊瘯杞崲涓烘暟鍊?
                        numeric_value = float(param_value)
                        data_dict[param_name] = numeric_value
                    except (ValueError, TypeError):
                        # 璺宠繃闈炴暟鍊煎弬鏁?
                        continue
                
                if not data_dict:
                    logger.warning(f"璁板綍 {record.id} 娌℃湁鍙敤鐨勬暟鍊兼暟鎹?)
                    return []
                
                # 杞崲涓篋ataFrame
                data_frame = pd.DataFrame([data_dict])
                
            else:
                logger.warning(f"璁板綍 {record.id} 娌℃湁data瀛楁鎴栨牸寮忎笉姝ｇ‘")
                return []
            
            # 4. 馃敡 鍏抽敭淇锛氳缃甤urrent_data浠ラ伩鍏峫ambda閿欒
            detector.current_data = data_dict
            
            # 5. 鎵ц妫€娴嬶紙浣跨敤鎴戜滑淇鐨勮繛缁瘎鍒嗛€昏緫锛?
            rule_results = detector.detect(data_dict, datetime.now(timezone.utc))
            
            # 6. 杞崲缁撴灉鏍煎紡
            formatted_results = []
            for result in rule_results:
                formatted_results.append({
                    'rule_name': result.get('rule_id', ''),
                    'fault_name': result.get('fault_name', ''),
                    'is_triggered': bool(result.get('is_triggered', False)),
                    'confidence_score': max(0.0, min(1.0, float(result.get('confidence_score', 0.0)))),
                    'fault_level': result.get('fault_level', 1),
                    'component': result.get('component', ''),
                    'details': result
                })
            
            logger.debug(f"涓撳瑙勫垯妫€娴嬪畬鎴? {len(formatted_results)} 涓粨鏋?)
            
            # 7. 璁板綍鍒嗘暟鍒嗗竷浠ラ獙璇佽繛缁瘎鍒嗘晥鏋?
            if formatted_results:
                scores = [r['confidence_score'] for r in formatted_results]
                unique_scores = set(scores)
                logger.debug(f"瑙勫垯鍒嗘暟鍒嗗竷: {len(unique_scores)} 绉嶄笉鍚屽垎鏁板€硷紝鑼冨洿: {min(scores):.3f}-{max(scores):.3f}")
                
                # 妫€鏌ユ槸鍚﹁繕鏈変簩鍊煎寲瓒嬪娍
                if len(unique_scores) <= 2 and unique_scores.issubset({0.0, 1.0}):
                    logger.warning(f"妫€娴嬪埌浜屽€煎寲瓒嬪娍锛屽彲鑳借鍒欒〃杈惧紡闇€瑕佷紭鍖?)
                else:
                    logger.debug(f"鉁?浣跨敤杩炵画璇勫垎锛岄伩鍏嶄簡浜屽€煎寲瓒嬪娍")
            
            return formatted_results
            
        except Exception as e:
            logger.warning(f"鎵归噺瑙勫垯妫€娴嬪け璐? {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def _run_msfg_detection(self, record: PHMData, cmg: PHM) -> Optional[Dict[str, Any]]:
        """杩愯MSFG妫€娴?- 浣跨敤鏍囧噯MSFG鎺ㄧ悊鏂规硶
        
        鏍囧噯鏂规硶鐗圭偣锛?
        1. 鉁?浣跨敤瀵规暟姒傜巼鏂规硶璁＄畻鏁呴殰姒傜巼锛堢鍚堟鐜囪锛?
        2. 鉁?浣跨敤C鐭╅樀杩涜绯荤粺绾ц仛鍚堬紙鑰冭檻绯荤粺灞傛缁撴瀯锛?
        3. 鉁?浣跨敤鍑犱綍骞冲潎璁＄畻鏁翠綋鍋ュ悍搴︼紙瀵规瀬绔€兼晱鎰燂級
        4. 鉁?鍩轰簬鏍囧噯MSFG鎺ㄧ悊閫昏緫锛屼笌鍙傝€冨疄鐜伴珮搴︿竴鑷?
        5. 鉁?鏁板鍩虹涓ヨ皑锛屾娴嬬粨鏋滄洿鍑嗙‘
        """
        try:
            logger.debug(f"寮€濮婱SFG妫€娴? PHM {cmg.cmg_id}, 璁板綍 {record.id}")
            
            # 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
            msfg = MSFGDefinition.objects.filter(
                cmg_model=cmg.cmg_model, 
                is_active=True
            ).order_by('-updated_at').first()
            
            if not msfg:
                logger.info(f"PHM妯″瀷 {cmg.cmg_model.model_name} 娌℃湁婵€娲荤殑MSFG鍙敤浜庢壒閲忔娴?)
                return None
            
            logger.debug(f"浣跨敤MSFG: {msfg.name} (ID: {msfg.id})")
            
            # 馃敡 淇锛氫娇鐢ㄧ粺涓€鐨勮妭鐐规彁鍙栭€昏緫鍜屼慨澶嶅悗鐨勮瀺鍚堢畻娉?
            from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
            
            fusion = AdvancedMSFGFusion()
            test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg)
            edges = list(msfg.edges.all())
            
            if not test_nodes or not fault_nodes or not edges:
                logger.warning(f"MSFG {msfg.name} 缂哄皯娴嬭瘯鑺傜偣銆佹晠闅滆妭鐐规垨杈瑰畾涔?)
                return None
            
            # 馃敡 淇1锛氫娇鐢ㄤ慨澶嶅悗鐨勬祴鐐硅瘎鍒嗘湇鍔?
            from msfg_analysis.services.testpoint_scoring import TestPointScoringService
            
            scoring_service = TestPointScoringService()
            
            # 馃敡 淇锛氭纭闂瓹MGData鐨勬暟鎹瓧娈?
            test_data = {}
            if hasattr(record, 'data') and isinstance(record.data, dict):
                # 浣跨敤data瀛楁涓殑鏁板€兼暟鎹?
                for param_name, param_value in record.data.items():
                    try:
                        # 灏濊瘯杞崲涓烘暟鍊?
                        numeric_value = float(param_value)
                        test_data[param_name] = numeric_value
                    except (ValueError, TypeError):
                        # 璺宠繃闈炴暟鍊煎弬鏁?
                        continue
            elif hasattr(record, 'numeric_params') and isinstance(record.numeric_params, dict):
                # 澶囩敤锛氬鏋滄湁numeric_params灞炴€?
                for param_name, param_value in record.numeric_params.items():
                    test_data[param_name] = param_value
            else:
                logger.warning(f"璁板綍 {record.id} 娌℃湁鍙敤鐨勬暟鍊兼暟鎹?)
            
            # 馃敡 淇锛氫娇鐢ㄦ纭殑鏂规硶鍚嶅拰鍙傛暟
            test_scores_dict = scoring_service.calculate_test_scores(record, msfg)
            # 鍚屾瀵煎嚭0/1浜屽€肩姸鎬侊紙鐢ㄤ簬璇婃柇缁撴瀯鍒嗘瀽涓庡彲瑙嗗寲锛?
            try:
                from msfg_analysis.services.testpoint_scoring import calculate_msfg_test_binary_states
                test_binary = calculate_msfg_test_binary_states(record, msfg)
            except Exception:
                test_binary = {}
            
            if not test_scores_dict:
                logger.warning(f"鏃犳硶璁＄畻娴嬬偣鍒嗘暟")
                return None
            
            # 馃敡 浣跨敤鏂扮殑鏍囧噯MSFG鎺ㄧ悊鏂规硶锛堝鏁版鐜?+ C鐭╅樀锛?
            import numpy as np
            
            logger.debug(f"娴嬬偣璇勫垎瀹屾垚: {len(test_scores_dict)} 涓祴鐐癸紝鍒嗘暟鑼冨洿: {min(test_scores_dict.values()):.3f}-{max(test_scores_dict.values()):.3f}")
            
            # 鏋勫缓閮ㄤ欢鏄犲皠锛堟爣鍑嗗垎鏋愰渶瑕侊級
            component_mappings = fusion._build_component_mappings(msfg)
            if not component_mappings:
                logger.info(f"MSFG {msfg.name} 娌℃湁閮ㄤ欢鏄犲皠锛屽垱寤哄鐢ㄦ槧灏?)
                component_mappings = self._create_default_component_mappings(fault_nodes)
            
            # 杞崲娴嬬偣鍒嗘暟鏍煎紡涓哄瓧鍏稿垪琛紙鏍囧噯鍒嗘瀽闇€瑕佺殑鏍煎紡锛?
            test_scores_for_analysis = {
                node.name: [test_scores_dict.get(node.name, 0.0)]
                for node in test_nodes
            }
            
            # 馃殌 浣跨敤鏍囧噯MSFG鍒嗘瀽鏂规硶
            logger.info("浣跨敤鏍囧噯MSFG鎺ㄧ悊鏂规硶锛堝鏁版鐜?+ C鐭╅樀锛?)
            analysis_result = fusion.run_standard_analysis(
                test_scores=test_scores_for_analysis,
                test_nodes=test_nodes,
                fault_nodes=fault_nodes,
                edges=edges,
                component_mappings=component_mappings,
                msfg_definition=msfg,
                use_cmatrix=True  # 浣跨敤C鐭╅樀鏂规硶
            )
            
            # 鎻愬彇缁撴灉锛堟爣鍑嗘柟娉曞凡鍖呭惈瀹屾暣缁撴灉锛?
            test_results = analysis_result['test_results']
            fault_results = analysis_result['fault_results']
            component_health = analysis_result['component_health']
            system_health = analysis_result['system_health']
            
            # 鏋勫缓閮ㄤ欢缁撴灉锛堢敤浜庢暟鎹簱瀛樺偍锛?
            component_results = {
                comp_name: {
                    'health_score': float(comp_data.get('health_score', 1.0)),
                    'status': 'critical' if comp_data.get('health_score', 1.0) < 0.7 else 'healthy',
                    'fault_probability': float(comp_data.get('fault_probability', 0.0)),
                    'fuzzy_probability': float(comp_data.get('fuzzy_probability', 0.0)),
                    'fault_count': int(comp_data.get('fault_count', 0)),
                    'max_fault_prob': float(comp_data.get('max_fault_prob', 0.0)),
                    'avg_fault_prob': float(comp_data.get('avg_fault_prob', 0.0)),
                    'method': comp_data.get('method', 'standard_cmatrix')  # 鏍囪瘑浣跨敤鐨勬柟娉?
                }
                for comp_name, comp_data in component_health.items()
            }
            
            # 绯荤粺缁撴灉
            overall_health = float(system_health.get('overall_health', 1.0))
            system_results = {
                'overall_health': overall_health,
                'status': 'critical' if overall_health < 0.7 else 'healthy',
                'method': system_health.get('method', 'standard_cmatrix'),
                'component_count': system_health.get('component_count', 0),
                'worst_component': system_health.get('worst_component'),
                'min_health': system_health.get('min_health', 1.0),
                'max_health': system_health.get('max_health', 1.0),
                'avg_health': system_health.get('avg_health', 1.0)
            }
            
            # 鎻愬彇鍏抽敭淇℃伅
            detected_faults = [
                name for name, data in fault_results.items() 
                if data['fault_probability'] > 0.7
            ]
            
            critical_components = [
                name for name, data in component_results.items() 
                if data['health_score'] < 0.7
            ]
            
            logger.debug(f"MSFG妫€娴嬪畬鎴? PHM {cmg.cmg_id}, 鍋ュ悍鍒嗘暟 {overall_health:.3f}, "
                        f"妫€娴嬪埌 {len(detected_faults)} 涓晠闅? {len(critical_components)} 涓叧閿儴浠?)
            
            return {
                'data_point_id': record.id,
                'data_point_timestamp': record.timestamp.isoformat(),
                'msfg_definition_id': msfg.id,
                'msfg_definition_name': msfg.name,
                'test_results': test_results,
                'fault_results': fault_results,
                'system_results': system_results,
                'component_results': component_results,
                'overall_health_score': overall_health,
                'detected_faults': detected_faults,
                'critical_components': critical_components,
                'analysis_details': {
                    "source": "batch_processing_standard_msfg",
                    "method": "standard_cmatrix",
                    "algorithm": "log_probability_with_cmatrix",
                    "total_test_nodes": len(test_nodes), 
                    "total_fault_nodes": len(fault_nodes),
                    "total_edges": len(edges),
                    "component_mappings_count": len(component_mappings),
                    "test_binary_states": test_binary,
                    "detection_summary": {
                        'total_test_points': len(test_nodes),
                        'abnormal_test_points': len([t for t in test_results.values() if t.get('status') == 'abnormal']),
                        'total_faults': len(fault_nodes),
                        'detected_faults_count': len(detected_faults),
                        'total_components': len(component_results),
                        'critical_components_count': len(critical_components)
                    },
                    "system_health_details": system_health.get('health_distribution', {})
                }
            }
            
        except Exception as e:
            logger.error(f"MSFG妫€娴嬪け璐? {e}")
            import traceback
            logger.error(f"璇︾粏閿欒: {traceback.format_exc()}")
            return None
    
    def _update_session_status(self, session_id: int, status: str, **kwargs) -> None:
        """鏇存柊浼氳瘽鐘舵€?""
        try:
            update_fields = ['processing_status']
            update_data = {'processing_status': status}
            
            for key, value in kwargs.items():
                if hasattr(ImportSession, key):
                    update_data[key] = value
                    update_fields.append(key)
            
            ImportSession.objects.filter(id=session_id).update(**update_data)
            
        except Exception as e:
            logger.error(f"鏇存柊浼氳瘽鐘舵€佸け璐? {e}")
    
    def _update_session_progress(self, session_id: int, processed: int, progress: float) -> None:
        """鏇存柊浼氳瘽杩涘害"""
        try:
            ImportSession.objects.filter(id=session_id).update(
                processed_records=processed,
                processing_progress=progress
            )
        except Exception as e:
            logger.error(f"鏇存柊浼氳瘽杩涘害澶辫触: {e}")
    
    def _update_redis_progress(self, session_id: int, progress: float, processed: int, total: int, 
                              status: str = None, message: str = None) -> None:
        """灏嗚繘搴︽洿鏂板埌Redis渚涘墠绔疆璇?""
        try:
            from .redis_service import redis_service
            redis_service.update_processing_progress(
                session_id=session_id,
                progress=progress,
                processed=processed,
                total=total,
                status=status,
                message=message
            )
            logger.debug(f"杩涘害宸叉洿鏂板埌Redis: 浼氳瘽{session_id}, 杩涘害{progress:.1f}%")
        except Exception as e:
            # Redis鏇存柊澶辫触涓嶅簲璇ュ奖鍝嶄富娴佺▼锛屽彧璁板綍璀﹀憡
            logger.warning(f"Redis杩涘害鏇存柊澶辫触: {e}锛岀户缁鐞?..")
    
    def _broadcast_progress(self, session_id: int, progress: float, processed: int, total: int) -> None:
        """骞挎挱杩涘害鍒癢ebSocket (宸插純鐢紝淇濈暀鍏煎鎬?"""
        # 鐜板湪浣跨敤Redis瀛樺偍杩涘害锛屽墠绔€氳繃杞鑾峰彇
        self._update_redis_progress(session_id, progress, processed, total)
    
    def get_session_status(self, session_id: int) -> Optional[Dict[str, Any]]:
        """鑾峰彇浼氳瘽鐘舵€?""
        try:
            session = ImportSession.objects.get(id=session_id)
            return {
                'id': session.id,
                'status': session.processing_status,
                'progress': session.processing_progress,
                'total_records': session.total_records,
                'processed_records': session.processed_records,
                'failed_records': session.failed_records,
                'error_message': session.error_message,
                'detection_summary': session.detection_summary,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            }
        except ImportSession.DoesNotExist:
            return None
    
    def is_session_active(self, session_id: int) -> bool:
        """妫€鏌ヤ細璇濇槸鍚︽鍦ㄥ鐞嗕腑"""
        return session_id in self._active_sessions and self._active_sessions[session_id].is_alive()
    
    def _generate_default_rule_results(self, normal_records: List[Tuple[int, PHMData]], 
                                      models_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        涓烘甯稿抚鐢熸垚榛樿瑙勫垯缁撴灉
        
        姝ｅ父甯х殑瑙勫垯缁撴灉榛樿鍊硷細
        - is_triggered: False锛堟湭瑙﹀彂锛?
        - confidence_score: 1.0锛堟渶楂樼疆淇″害锛岃〃绀烘甯革級
        - 鍏朵粬鍙傛暟鎸夌収瑙勫垯鍏蜂綋淇℃伅濉啓
        
        Args:
            normal_records: 姝ｅ父甯ц褰曞垪琛?[(record_index, PHMData), ...]
            models_config: 棰勫姞杞界殑妯″瀷閰嶇疆
            
        Returns:
            榛樿瑙勫垯缁撴灉鍒楄〃
        """
        default_results = []
        
        try:
            # 鑾峰彇鎵€鏈夋縺娲荤殑瑙勫垯瀹氫箟
            rule_definitions = models_config.get('rule_definitions', [])
            
            if not rule_definitions:
                logger.info("娌℃湁婵€娲荤殑瑙勫垯瀹氫箟锛岃烦杩囩敓鎴愰粯璁よ鍒欑粨鏋?)
                return default_results
            
            logger.info(f"涓?{len(normal_records)} 涓甯稿抚鐢熸垚榛樿瑙勫垯缁撴灉锛岃鍒欐暟閲? {len(rule_definitions)}")
            
            # 涓烘瘡涓甯稿抚鐨勬瘡鏉¤鍒欑敓鎴愰粯璁ょ粨鏋?
            for record_index, record in normal_records:
                for rule_def in rule_definitions:
                    default_result = {
                        'rule_name': rule_def.rule_id,
                        'fault_name': rule_def.fault_definition.fault_name if rule_def.fault_definition else 'Unknown',
                        'is_triggered': False,  # 姝ｅ父甯э紝瑙勫垯鏈Е鍙?
                        'confidence_score': 1.0,  # 鏈€楂樼疆淇″害锛岃〃绀烘甯?
                        'fault_level': rule_def.fault_definition.fault_level if rule_def.fault_definition else 1,
                        'component': rule_def.fault_definition.component if rule_def.fault_definition else '',
                        'details': {
                            'rule_id': rule_def.rule_id,
                            'rule_expression': rule_def.rule_expression,
                            'fault_name': rule_def.fault_definition.fault_name if rule_def.fault_definition else 'Unknown',
                            'is_triggered': False,
                            'confidence_score': 1.0,
                            'evaluation_method': 'default_for_normal_frame',
                            'description': '姝ｅ父甯ч粯璁ょ粨鏋滐細瑙勫垯鏈Е鍙?
                        },
                        'record_index': record_index
                    }
                    default_results.append(default_result)
            
            logger.info(f"鎴愬姛鐢熸垚 {len(default_results)} 涓粯璁よ鍒欑粨鏋?)
            
        except Exception as e:
            logger.error(f"鐢熸垚榛樿瑙勫垯缁撴灉澶辫触: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return default_results
    
    def _generate_default_msfg_results(self, normal_records: List[Tuple[int, PHMData]], 
                                      models_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        涓烘甯稿抚鐢熸垚榛樿MSFG缁撴灉
        
        姝ｅ父甯х殑MSFG缁撴灉榛樿鍊硷細
        - 鎵€鏈夋祴鐐瑰垎鏁? 0锛堟棤寮傚父锛?
        - 鎵€鏈夐儴浠跺仴搴峰垎鏁? 1.0锛堝畬鍏ㄥ仴搴凤級
        - 鏁呴殰鍙兘鎬? 0锛堟棤鏁呴殰锛?
        - 鏁翠綋绯荤粺鍒嗘暟: 1.0锛堝畬鍏ㄥ仴搴凤級
        - 妫€娴嬪埌鐨勬晠闅? []锛堟棤鏁呴殰锛?
        
        Args:
            normal_records: 姝ｅ父甯ц褰曞垪琛?[(record_index, PHMData), ...]
            models_config: 棰勫姞杞界殑妯″瀷閰嶇疆
            
        Returns:
            榛樿MSFG缁撴灉鍒楄〃
        """
        default_results = []
        
        try:
            # 鑾峰彇MSFG瀹氫箟
            msfg_definition = models_config.get('msfg_definitions')
            
            if not msfg_definition:
                logger.info("娌℃湁婵€娲荤殑MSFG瀹氫箟锛岃烦杩囩敓鎴愰粯璁SFG缁撴灉")
                return default_results
            
            logger.info(f"涓?{len(normal_records)} 涓甯稿抚鐢熸垚榛樿MSFG缁撴灉")
            
            # 鑾峰彇MSFG鑺傜偣淇℃伅
            from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
            fusion = AdvancedMSFGFusion()
            test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg_definition)
            
            # 馃搳 璁板綍鑺傜偣淇℃伅锛堢敤浜庨獙璇侊級
            logger.info(f"MSFG鑺傜偣淇℃伅: 娴嬬偣鏁?{len(test_nodes)}, 鏁呴殰鏁?{len(fault_nodes)}, 閮ㄤ欢鏁?{len(component_nodes)}")
            logger.info(f"娴嬬偣鍒楄〃: {[node.name for node in test_nodes]}")
            logger.info(f"鏁呴殰鍒楄〃: {[node.name for node in fault_nodes]}")
            
            # 鏋勫缓榛樿娴嬬偣缁撴灉锛堟墍鏈夋祴鐐瑰垎鏁颁负0锛?
            default_test_results = {}
            for test_node in test_nodes:
                default_test_results[test_node.name] = {
                    'test_name': test_node.name,
                    'score': 0.0,  # 鉁?淇锛氫娇鐢?score'瀛楁鍚嶏紙涓嶢PI涓€鑷达級锛屾甯稿抚娴嬬偣鍒嗘暟涓?
                    'status': 'normal',
                    'threshold': test_node.threshold if hasattr(test_node, 'threshold') else 0.5,
                    'description': '姝ｅ父甯ч粯璁ゅ€?
                }
            
            logger.info(f"鉁?宸叉瀯寤?{len(default_test_results)} 涓祴鐐圭殑榛樿缁撴灉")
            
            # 鏋勫缓榛樿鏁呴殰缁撴灉锛堟墍鏈夋晠闅滄鐜囦负0锛?
            default_fault_results = {}
            for fault_node in fault_nodes:
                default_fault_results[fault_node.name] = {
                    'fault_name': fault_node.name,
                    'fault_probability': 0.0,  # 姝ｅ父甯э紝鏁呴殰姒傜巼涓?
                    'fuzzy_probability': 0.0,
                    'contributing_tests': [],
                    'severity': 'none',
                    'description': '姝ｅ父甯ч粯璁ゅ€?
                }
            
            logger.info(f"鉁?宸叉瀯寤?{len(default_fault_results)} 涓晠闅滅殑榛樿缁撴灉")
            
            # 鏋勫缓榛樿閮ㄤ欢缁撴灉锛堟墍鏈夐儴浠跺仴搴峰垎鏁颁负1.0锛?
            component_mappings = fusion._build_component_mappings(msfg_definition)
            if not component_mappings:
                component_mappings = self._create_default_component_mappings(fault_nodes)
            
            default_component_results = {}
            for comp_name in component_mappings.keys():
                default_component_results[comp_name] = {
                    'health_score': 1.0,  # 姝ｅ父甯э紝鍋ュ悍鍒嗘暟涓?.0
                    'status': 'healthy',
                    'fault_probability': 0.0,
                    'fuzzy_probability': 0.0,
                    'fault_count': 0,
                    'max_fault_prob': 0.0,
                    'avg_fault_prob': 0.0,
                    'method': 'default_for_normal_frame'
                }
            
            # 鏋勫缓榛樿绯荤粺缁撴灉
            default_system_results = {
                'overall_health': 1.0,  # 姝ｅ父甯э紝绯荤粺鍋ュ悍鍒嗘暟涓?.0
                'status': 'healthy',
                'method': 'default_for_normal_frame',
                'component_count': len(default_component_results),
                'worst_component': None,
                'min_health': 1.0,
                'max_health': 1.0,
                'avg_health': 1.0
            }
            
            # 涓烘瘡涓甯稿抚鐢熸垚榛樿MSFG缁撴灉锛堜娇鐢ㄦ繁鎷疯礉纭繚鏁版嵁鐙珛锛?
            import copy
            
            for record_index, record in normal_records:
                # 馃敡 浣跨敤娣辨嫹璐濈‘淇濇瘡涓褰曢兘鏈夊畬鍏ㄧ嫭绔嬬殑鏁版嵁鍓湰
                default_result = {
                    'data_point_id': record.id,
                    'data_point_timestamp': record.timestamp.isoformat(),
                    'msfg_definition_id': msfg_definition.id,
                    'msfg_definition_name': msfg_definition.name,
                    'test_results': copy.deepcopy(default_test_results),      # 鉁?娣辨嫹璐?
                    'fault_results': copy.deepcopy(default_fault_results),    # 鉁?娣辨嫹璐?
                    'system_results': copy.deepcopy(default_system_results),  # 鉁?娣辨嫹璐?
                    'component_results': copy.deepcopy(default_component_results),  # 鉁?娣辨嫹璐?
                    'overall_health_score': 1.0,  # 姝ｅ父甯э紝鏁翠綋鍋ュ悍鍒嗘暟涓?.0
                    'detected_faults': [],  # 姝ｅ父甯э紝鏃犳娴嬪埌鐨勬晠闅?
                    'critical_components': [],  # 姝ｅ父甯э紝鏃犲叧閿儴浠?
                    'analysis_details': {
                        "source": "batch_processing_default_normal_frame",
                        "method": "default_values",
                        "algorithm": "none",
                        "total_test_nodes": len(test_nodes),
                        "total_fault_nodes": len(fault_nodes),
                        "total_edges": 0,
                        "component_mappings_count": len(component_mappings),
                        "test_binary_states": {},
                        "detection_summary": {
                            'total_test_points': len(test_nodes),
                            'abnormal_test_points': 0,  # 姝ｅ父甯э紝鏃犲紓甯告祴鐐?
                            'total_faults': len(fault_nodes),
                            'detected_faults_count': 0,  # 姝ｅ父甯э紝鏃犳娴嬪埌鐨勬晠闅?
                            'total_components': len(default_component_results),
                            'critical_components_count': 0  # 姝ｅ父甯э紝鏃犲叧閿儴浠?
                        },
                        'description': '姝ｅ父甯ч粯璁ょ粨鏋滐細鎵€鏈夋祴鐐规甯革紝鏃犳晠闅滄娴?
                    }
                }
                default_results.append(default_result)
            
            # 馃搳 楠岃瘉鐢熸垚鐨勭粨鏋?
            if default_results:
                sample_result = default_results[0]
                logger.info(f"鉁?鎴愬姛鐢熸垚 {len(default_results)} 涓粯璁SFG缁撴灉")
                logger.info(f"姣忎釜缁撴灉鍖呭惈: 娴嬬偣鏁?{len(sample_result['test_results'])}, "
                          f"鏁呴殰鏁?{len(sample_result['fault_results'])}, "
                          f"閮ㄤ欢鏁?{len(sample_result['component_results'])}")
                # 楠岃瘉鏁版嵁鐙珛鎬?
                if len(default_results) > 1:
                    first_test_results = default_results[0]['test_results']
                    second_test_results = default_results[1]['test_results']
                    if first_test_results is second_test_results:
                        logger.warning("鈿狅笍 璀﹀憡锛氭娴嬪埌娴呮嫹璐濋棶棰橈紝澶氫釜璁板綍鍏变韩鍚屼竴涓瓧鍏稿璞?)
                    else:
                        logger.info("鉁?鏁版嵁鐙珛鎬ч獙璇侀€氳繃锛屾瘡涓褰曢兘鏈夌嫭绔嬬殑鏁版嵁鍓湰")
            
        except Exception as e:
            logger.error(f"鐢熸垚榛樿MSFG缁撴灉澶辫触: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return default_results
    
    def _create_default_component_mappings(self, fault_nodes):
        """鍒涘缓榛樿鐨勯儴浠舵槧灏?""
        component_mappings = {
            '杞瓙杞存壙': [],
            '杞瓙椹卞姩鐢垫満': [],
            '鐢垫簮鏉?: [],
            '妗嗘灦鎺у埗鍣?: [],
            '杞瓙鐢垫祦閲囨牱': []
        }
        
        # 鏍规嵁鏁呴殰鍚嶇О杩涜鏅鸿兘鏄犲皠
        for fault_node in fault_nodes:
            fault_name = fault_node.name.lower()
            
            if '杞存壙' in fault_name or '杞存俯' in fault_name:
                component_mappings['杞瓙杞存壙'].append(fault_node.name)
            elif '鐢垫満' in fault_name or '杞€? in fault_name:
                component_mappings['杞瓙椹卞姩鐢垫満'].append(fault_node.name)
            elif '鐢靛帇' in fault_name or 'v' in fault_name:
                component_mappings['鐢垫簮鏉?].append(fault_node.name)
            elif '妗嗘灦' in fault_name or '澹虫俯' in fault_name:
                component_mappings['妗嗘灦鎺у埗鍣?].append(fault_node.name)
            elif '鐢垫祦' in fault_name:
                component_mappings['杞瓙鐢垫祦閲囨牱'].append(fault_node.name)
            else:
                # 榛樿鏄犲皠鍒拌浆瀛愯酱鎵?
                component_mappings['杞瓙杞存壙'].append(fault_node.name)
        
        # 绉婚櫎绌虹殑閮ㄤ欢
        component_mappings = {k: v for k, v in component_mappings.items() if v}
        
        return component_mappings


# 鍏ㄥ眬澶勭悊鍣ㄥ疄渚?
batch_processor = BatchFileProcessor()

