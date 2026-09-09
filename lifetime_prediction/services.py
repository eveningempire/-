"""
瀵垮懡棰勬祴鏈嶅姟灞?
璇ユā鍧楁彁渚涘鍛介娴嬬殑涓氬姟閫昏緫鏈嶅姟锛屽寘鎷暟鎹幏鍙栥€侀澶勭悊鍜岄娴嬫墽琛屻€?"""

from typing import Dict, List, Optional
from django.db.models import Q
from data_management.models import PHM, PHMData
from .algorithms import LifetimePredictionAlgorithm, AdvancedLifetimePredictionAlgorithm, get_available_algorithms
import logging

logger = logging.getLogger(__name__)


class LifetimePredictionService:
    """瀵垮懡棰勬祴鏈嶅姟绫?""
    
    def __init__(self):
        self.algorithm = LifetimePredictionAlgorithm()
    
    def get_available_algorithms(self) -> List[Dict]:
        """鑾峰彇鍙敤鐨勭畻娉曞垪琛?""
        try:
            return get_available_algorithms()
        except Exception as e:
            logger.error(f"鑾峰彇绠楁硶鍒楄〃澶辫触: {str(e)}")
            return []
    
    def get_available_cmgs(self) -> List[Dict]:
        """鑾峰彇鍙敤鐨凜MG鍒楄〃"""
        try:
            cmgs = PHM.objects.filter(enabled=True).select_related('cmg_model')
            return [
                {
                    'id': cmg.id,
                    'cmg_id': cmg.cmg_id,
                    'name': cmg.name,
                    'model_name': cmg.cmg_model.model_name if cmg.cmg_model else 'Unknown',
                    'enabled': cmg.enabled
                }
                for cmg in cmgs
            ]
        except Exception as e:
            logger.error(f"鑾峰彇PHM鍒楄〃澶辫触: {str(e)}")
            return []
    
    def get_cmg_data(self, cmg_id: int, limit: int = 100, start_time: str = None, end_time: str = None, use_time_range: bool = False) -> List[Dict]:
        """
        鑾峰彇鎸囧畾PHM鐨勯仴娴嬫暟鎹?        
        Args:
            cmg_id: PHM鐨勬暟鎹簱ID
            limit: 鑾峰彇鐨勬暟鎹潯鏁伴檺鍒?            start_time: 寮€濮嬫椂闂达紙ISO鏍煎紡瀛楃涓诧級
            end_time: 缁撴潫鏃堕棿锛圛SO鏍煎紡瀛楃涓诧級
            
        Returns:
            閬ユ祴鏁版嵁鍒楄〃
        """
        try:
            # 棣栧厛閫氳繃鏁版嵁搴揑D鑾峰彇PHM瀵硅薄
            try:
                cmg = PHM.objects.get(id=cmg_id)
            except PHM.DoesNotExist:
                logger.error(f"PHM ID {cmg_id} 涓嶅瓨鍦?)
                return []
            
            # 鏋勫缓鏌ヨ鏉′欢 - 浣跨敤PHM鐨勬爣璇嗙杩涜鏌ヨ
            query = PHMData.objects.filter(cmg__cmg_id=cmg.cmg_id)
            
            # 濡傛灉鎸囧畾浜嗘椂闂磋寖鍥达紝娣诲姞鏃堕棿杩囨护
            if start_time and end_time:
                # 纭繚鏃堕棿鏍煎紡姝ｇ‘锛岃浆鎹负Django鏈熸湜鐨勬牸寮?                from django.utils import timezone
                from datetime import datetime
                
                try:
                    # 瑙ｆ瀽鏃堕棿瀛楃涓?- 鏀寔澶氱鏍煎紡
                    def parse_datetime_flexible(time_str):
                        """鐏垫椿瑙ｆ瀽鏃堕棿瀛楃涓诧紝鏀寔澶氱鏍煎紡"""
                        if not time_str:
                            return None
                        
                        # 澶勭悊ISO鏍煎紡
                        if 'T' in time_str:
                            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        
                        # 灏濊瘯澶氱甯歌鏍煎紡
                        formats = [
                            '%Y-%m-%d %H:%M:%S',  # 2024-03-30 18:41:14
                            '%Y/%m/%d %H:%M:%S',  # 2024/03/30 18:41:14
                            '%Y-%m-%d %H:%M:%S.%f',  # 甯﹀井绉?                            '%Y/%m/%d %H:%M:%S.%f',  # 甯﹀井绉?                            '%Y-%m-%d %H:%M',  # 涓嶅甫绉?                            '%Y/%m/%d %H:%M',  # 涓嶅甫绉?                        ]
                        
                        for fmt in formats:
                            try:
                                return datetime.strptime(time_str, fmt)
                            except ValueError:
                                continue
                        
                        # 濡傛灉鎵€鏈夋牸寮忛兘澶辫触锛屽皾璇昿andas瑙ｆ瀽
                        try:
                            import pandas as pd
                            return pd.to_datetime(time_str).to_pydatetime()
                        except:
                            raise ValueError(f"鏃犳硶瑙ｆ瀽鏃堕棿鏍煎紡: {time_str}")
                    
                    start_dt = parse_datetime_flexible(start_time)
                    end_dt = parse_datetime_flexible(end_time)
                    
                    # 纭繚鏃跺尯鎰熺煡
                    if timezone.is_naive(start_dt):
                        start_dt = timezone.make_aware(start_dt)
                    if timezone.is_naive(end_dt):
                        end_dt = timezone.make_aware(end_dt)
                    
                    query = query.filter(
                        timestamp__gte=start_dt,
                        timestamp__lte=end_dt
                    )
                    
                    logger.info(f"鏃堕棿杩囨护: {start_dt} 鍒?{end_dt}")
                    
                except Exception as e:
                    logger.error(f"鏃堕棿鏍煎紡瑙ｆ瀽澶辫触: {e}")
                    # 濡傛灉鏃堕棿瑙ｆ瀽澶辫触锛屼笉杩涜鏃堕棿杩囨护
            
            # 鑾峰彇鏁版嵁锛屾寜鏃堕棿鍊掑簭鎺掑垪
            # 濡傛灉浣跨敤鏃堕棿娈佃繃婊わ紝涓嶉檺鍒舵暟鎹暟閲忥紱鍚﹀垯搴旂敤limit闄愬埗
            if use_time_range and start_time and end_time:
                data_records = query.order_by('-timestamp')
            else:
                data_records = query.order_by('-timestamp')[:limit]
            
            # 杞崲涓哄瓧鍏告牸寮?            data_list = []
            for record in data_records:
                data_dict = {
                    'id': record.id,
                    'timestamp': record.timestamp.isoformat(),
                    'data': record.data,
                    'created_at': record.created_at.isoformat()
                }
                data_list.append(data_dict)
            
            # 鎸夋椂闂存搴忔帓鍒?            data_list.reverse()
            
            logger.info(f"鑾峰彇PHM {cmg.cmg_id} (鏁版嵁搴揑D: {cmg_id}) 鏁版嵁鎴愬姛锛屽叡 {len(data_list)} 鏉¤褰?)
            return data_list
            
        except Exception as e:
            logger.error(f"鑾峰彇PHM鏁版嵁澶辫触: {str(e)}")
            return []
    
    
    def predict_lifetime(self, cmg_id: str, design_life, start_time: str = None, data_start_time: str = None, end_time: str = None, use_time_range: bool = False, algorithm: str = "strategy0") -> Dict:
        """
        鎵ц瀵垮懡棰勬祴
        
        Args:
            cmg_id: PHM鐨処D
            design_life: 璁捐瀵垮懡锛堝勾锛?            start_time: PHM寮€濮嬩娇鐢ㄦ椂闂达紙YYYY/MM/DD HH:mm:ss鏍煎紡锛?            data_start_time: 鏁版嵁鏌ヨ寮€濮嬫椂闂达紙ISO鏍煎紡瀛楃涓诧級
            end_time: 鏁版嵁鏌ヨ缁撴潫鏃堕棿锛圛SO鏍煎紡瀛楃涓诧級
            use_time_range: 鏄惁浣跨敤鏃堕棿娈佃繃婊ゆ暟鎹紙True鐢ㄤ簬PHM璇︽儏椤甸潰锛孎alse鐢ㄤ簬瀵垮懡棰勬祴鐣岄潰锛?            algorithm: 閫夋嫨鐨勭畻娉曪紙strategy0/strategy1/strategy2/strategy3锛?            
        Returns:
            棰勬祴缁撴灉瀛楀吀
        """
        try:
            # 娣诲姞鍙傛暟杩借釜鏃ュ織
            logger.info(f"[鍙傛暟杩借釜] Service灞傛帴鏀跺埌鐨勫弬鏁?- cmg_id: {cmg_id}, design_life: {design_life} (绫诲瀷: {type(design_life)}), start_time: {start_time}, algorithm: {algorithm}")
            
            # 纭繚design_life鏄诞鐐规暟绫诲瀷
            try:
                design_life = float(design_life)
                logger.info(f"[鍙傛暟杩借釜] 璁捐瀵垮懡杞崲鍚? {design_life} (绫诲瀷: {type(design_life)})")
            except (ValueError, TypeError):
                return {
                    'status': 'error',
                    'message': f'璁捐瀵垮懡鍙傛暟鏃犳晥: {design_life}锛岃杈撳叆鏈夋晥鐨勬暟瀛?,
                    'rul_value': 0.0
                }
            
            # 鑾峰彇PHM淇℃伅
            try:
                cmg = PHM.objects.get(cmg_id=cmg_id)
            except PHM.DoesNotExist:
                return {
                    'status': 'error',
                    'message': f'PHM ID {cmg_id} 涓嶅瓨鍦?,
                    'rul_value': 0.0
                }
            
            # 鏍规嵁use_time_range鍙傛暟鍐冲畾鏁版嵁鑾峰彇鏂瑰紡
            if use_time_range and data_start_time and end_time:
                # 浣跨敤鐢ㄦ埛鎸囧畾鐨勬椂闂存 - 鑾峰彇璇ユ椂闂存鍐呯殑鎵€鏈夋暟鎹紝涓嶉檺鍒舵暟閲?                data = self.get_cmg_data(cmg.id, limit=1000, start_time=data_start_time, end_time=end_time, use_time_range=True)
                logger.info(f"PHM ID {cmg_id} (鍚嶇О: {cmg.cmg_id}) 鍦ㄦ暟鎹煡璇㈡椂闂存 {data_start_time} 鍒?{end_time} 鍐呰幏鍙栧埌 {len(data)} 鏉℃暟鎹?)
            else:
                # 瀵垮懡棰勬祴鐣岄潰锛氬彧鑾峰彇鏈€鍚?000鏉℃暟鎹紝涓嶈繘琛屾椂闂存杩囨护
                # 娉ㄦ剰锛氳繖閲屼笉闇€瑕佷紶閫抯tart_time鍜宔nd_time鍙傛暟锛岃get_cmg_data鏂规硶鑷姩鑾峰彇鏈€鏂版暟鎹?                data = self.get_cmg_data(cmg.id, limit=1000, use_time_range=False)
                logger.info(f"PHM ID {cmg_id} (鍚嶇О: {cmg.cmg_id}) 鑾峰彇鏈€鍚?{len(data)} 鏉℃暟鎹紙鏃犳椂闂存杩囨护锛?)
            
            # 濡傛灉娌℃湁鏁版嵁锛屾鏌MG鏄惁瀛樺湪鏁版嵁
            if len(data) == 0:
                total_cmg_data = PHMData.objects.filter(cmg__cmg_id=cmg.cmg_id).count()
                if use_time_range:
                    logger.warning(f"PHM {cmg.cmg_id} (鏁版嵁搴揑D: {cmg_id}) 鍦ㄦ暟鎹煡璇㈡椂闂存 {data_start_time} 鍒?{end_time} 鍐呮棤鏁版嵁锛屼絾璇MG鎬诲叡鏈?{total_cmg_data} 鏉℃暟鎹?)
                else:
                    logger.warning(f"PHM {cmg.cmg_id} (鏁版嵁搴揑D: {cmg_id}) 鏃犱换浣曟暟鎹紝鎬诲叡鏈?{total_cmg_data} 鏉℃暟鎹?)
            
            # 鍩烘湰鏁版嵁楠岃瘉锛堟柊绠楁硶浼氳嚜鍔ㄥ鐞嗛仴娴嬮噺瀛楁鏄犲皠锛?            if len(data) == 0:
                total_cmg_data = PHMData.objects.filter(cmg__cmg_id=cmg.cmg_id).count()
                if use_time_range:
                    error_message = f"鍦ㄦ寚瀹氱殑鏃堕棿娈靛唴娌℃湁鎵惧埌浠讳綍閬ユ祴鏁版嵁銆俓n\n璇婃柇淇℃伅锛歕n- PHM: {cmg.cmg_id} (鏁版嵁搴揑D: {cmg_id})\n- 鏁版嵁鏌ヨ鏃堕棿娈? {data_start_time} 鍒?{end_time}\n- PHM鍚敤鏃堕棿: {start_time}\n- 璇MG鎬绘暟鎹噺: {total_cmg_data} 鏉n\n璇锋鏌ワ細\n1. 鏁版嵁鏌ヨ鏃堕棿娈垫槸鍚︽纭甛n2. 璇MG鍦ㄦ寚瀹氭椂闂存鍐呮槸鍚︽湁鏁版嵁\n3. 灏濊瘯閫夋嫨鍏朵粬鏃堕棿娈?
                else:
                    error_message = f"璇MG娌℃湁浠讳綍閬ユ祴鏁版嵁銆俓n\n璇婃柇淇℃伅锛歕n- PHM: {cmg.cmg_id} (鏁版嵁搴揑D: {cmg_id})\n- PHM鍚敤鏃堕棿: {start_time}\n- 璇MG鎬绘暟鎹噺: {total_cmg_data} 鏉n\n璇锋鏌ワ細\n1. 璇MG鏄惁宸叉纭厤缃甛n2. 鏄惁鏈夋暟鎹噰闆嗙郴缁熷湪杩愯\n3. 鏁版嵁鏄惁姝ｇ‘瀵煎叆鍒版暟鎹簱\n4. 纭璇MG鏄惁鏈夊巻鍙叉暟鎹?
                
                return {
                    'status': 'error',
                    'message': error_message,
                    'rul_value': 0.0,
                    'data_count': len(data),
                    'time_range': {'start': start_time, 'end': end_time}
                }
            
            # 妫€鏌ユ暟鎹熀鏈粨鏋?            if not data[0].get('data'):
                return {
                    'status': 'error',
                    'message': '鏁版嵁璁板綍缂哄皯閬ユ祴鏁版嵁瀛楁',
                    'rul_value': 0.0,
                    'data_count': len(data)
                }
            
            # 鎵ц棰勬祴锛屼紶閫掔湡瀹炵殑PHM鍨嬪彿鍚嶇О
            cmg_model_name = cmg.cmg_model.model_name if cmg.cmg_model else "500NM"
            logger.info(f"浣跨敤PHM鍨嬪彿 {cmg_model_name} 鍜岀畻娉?{algorithm} 杩涜瀵垮懡棰勬祴")
            logger.info(f"[鍙傛暟杩借釜] 浼犻€掔粰绠楁硶鐨勫弬鏁?- design_life: {design_life} (绫诲瀷: {type(design_life)}), start_time: {start_time}, cmg_model: {cmg_model_name}, algorithm: {algorithm}")
            
            prediction_result = self.algorithm.predict(
                data, 
                design_life=design_life, 
                start_time=start_time,
                cmg_model_name=cmg_model_name,
                algorithm=algorithm
            )
            
            # 娣诲姞PHM淇℃伅
            prediction_result.update({
                'cmg_id': cmg.cmg_id,
                'cmg_name': cmg.name,
                'cmg_model': cmg_model_name,
                'used_cmg_type': cmg_model_name  # 鏄庣‘璁板綍浣跨敤鐨凜MG鍨嬪彿
            })
            
            logger.info(f"PHM {cmg.cmg_id} 瀵垮懡棰勬祴瀹屾垚: RUL={prediction_result.get('rul_value', 0):.2f}")
            return prediction_result
            
        except Exception as e:
            logger.error(f"瀵垮懡棰勬祴澶辫触: {str(e)}")
            return {
                'status': 'error',
                'message': f'棰勬祴杩囩▼涓彂鐢熼敊璇? {str(e)}',
                'rul_value': 0.0
            }
    
    def get_prediction_summary(self, cmg_id: int) -> Dict:
        """
        鑾峰彇棰勬祴鎽樿淇℃伅
        
        Args:
            cmg_id: PHM鐨処D
            
        Returns:
            鎽樿淇℃伅瀛楀吀
        """
        try:
            cmg = PHM.objects.get(id=cmg_id)
            
            # 鑾峰彇鏁版嵁缁熻
            total_records = PHMData.objects.filter(cmg__cmg_id=cmg.cmg_id).count()
            latest_record = PHMData.objects.filter(cmg__cmg_id=cmg.cmg_id).order_by('-timestamp').first()
            
            summary = {
                'cmg_id': cmg.cmg_id,
                'cmg_name': cmg.name,
                'cmg_model': cmg.cmg_model.model_name if cmg.cmg_model else 'Unknown',
                'total_records': total_records,
                'latest_data_time': latest_record.timestamp.isoformat() if latest_record else None,
                'window_size': self.algorithm.window_size,
                'prediction_ready': total_records >= self.algorithm.window_size
            }
            
            return summary
            
        except PHM.DoesNotExist:
            return {
                'error': f'PHM ID {cmg_id} 涓嶅瓨鍦?
            }
        except Exception as e:
            logger.error(f"鑾峰彇棰勬祴鎽樿澶辫触: {str(e)}")
            return {
                'error': f'鑾峰彇鎽樿淇℃伅澶辫触: {str(e)}'
            }
    
    def finetune_model(
        self, 
        cmg_id: int, 
        algorithm: str = 'strategy0',
        data_source: str = 'database',
        data_start_time: str = None,
        data_end_time: str = None,
        uploaded_file = None,
        epochs: int = 50,
        batch_size: int = 64,
        learning_rate: float = 1e-4
    ) -> Dict:
        """
        妯″瀷寰皟锛堝閲忓涔狅級
        
        Args:
            cmg_id: PHM鐨勬暟鎹簱ID
            algorithm: 绠楁硶绫诲瀷 (strategy0=AE, strategy1=VAE)
            data_source: 鏁版嵁鏉ユ簮 ('database' 鎴?'file')
            data_start_time: 鏂版暟鎹紑濮嬫椂闂达紙鏁版嵁搴撴ā寮忥級
            data_end_time: 鏂版暟鎹粨鏉熸椂闂达紙鏁版嵁搴撴ā寮忥級
            uploaded_file: 涓婁紶鐨勬枃浠跺璞★紙鏂囦欢妯″紡锛?            epochs: 寰皟杞暟
            batch_size: 鎵瑰ぇ灏?            learning_rate: 瀛︿範鐜?            
        Returns:
            寰皟缁撴灉瀛楀吀
        """
        try:
            import pandas as pd
            import sys
            from pathlib import Path
            
            # 鑾峰彇PHM瀵硅薄锛坈mg_id鏄瓧绗︿覆锛屽"15-01"锛?            try:
                cmg = PHM.objects.get(cmg_id=cmg_id)
            except PHM.DoesNotExist:
                return {
                    'status': 'error',
                    'message': f'PHM ID {cmg_id} 涓嶅瓨鍦?
                }
            
            # 鑾峰彇PHM鍨嬪彿
            cmg_model_name = cmg.cmg_model.model_name if cmg.cmg_model else "500NM"
            logger.info(f"寮€濮嬫ā鍨嬪井璋?- PHM: {cmg.cmg_id} ({cmg_model_name}), 绠楁硶: {algorithm}")
            
            # 鏍规嵁鏁版嵁鏉ユ簮鑾峰彇鏁版嵁
            if data_source == 'database':
                # 浠庢暟鎹簱鑾峰彇鏁版嵁
                if data_start_time and data_end_time:
                    data = self.get_cmg_data(cmg.id, limit=100000, start_time=data_start_time, end_time=data_end_time, use_time_range=True)
                    logger.info(f"浠庢暟鎹簱鏃堕棿娈?{data_start_time} 鍒?{data_end_time} 鑾峰彇鍒?{len(data)} 鏉℃暟鎹敤浜庡井璋?)
                else:
                    # 濡傛灉娌℃湁鎸囧畾鏃堕棿鑼冨洿锛屼娇鐢ㄦ渶鏂扮殑1000鏉℃暟鎹?                    data = self.get_cmg_data(cmg.id, limit=1000, use_time_range=False)
                    logger.info(f"浠庢暟鎹簱鑾峰彇鏈€鏂?{len(data)} 鏉℃暟鎹敤浜庡井璋?)
                
                if len(data) == 0:
                    return {
                        'status': 'error',
                        'message': '鏁版嵁搴撲腑娌℃湁鎵惧埌鍙敤鐨勬暟鎹繘琛屽井璋?
                    }
                
                # 鍑嗗DataFrame
                df = pd.DataFrame([{
                    'timestamp': record['timestamp'],
                    **record['data']
                } for record in data])
                
            elif data_source == 'file':
                # 浠庝笂浼犳枃浠惰幏鍙栨暟鎹?                if not uploaded_file:
                    return {
                        'status': 'error',
                        'message': '鏂囦欢涓婁紶妯″紡闇€瑕佹彁渚涙枃浠?
                    }
                
                try:
                    # 璇诲彇CSV鏂囦欢
                    df = pd.read_csv(uploaded_file)
                    logger.info(f"浠庝笂浼犳枃浠惰幏鍙栧埌 {len(df)} 鏉℃暟鎹敤浜庡井璋?)
                    
                    if len(df) == 0:
                        return {
                            'status': 'error',
                            'message': '涓婁紶鐨勬枃浠朵腑娌℃湁鏁版嵁'
                        }
                    
                except Exception as e:
                    logger.error(f"璇诲彇涓婁紶鏂囦欢澶辫触: {str(e)}")
                    return {
                        'status': 'error',
                        'message': f'璇诲彇涓婁紶鏂囦欢澶辫触: {str(e)}'
                    }
            
            # 娣诲姞rul_predict_250917_v2鍒皊ys.path
            rul_path = Path(__file__).parent / 'rul_predict_250917_v2'
            rul_path_str = str(rul_path)
            if rul_path_str not in sys.path:
                sys.path.insert(0, rul_path_str)
            
            # 瀵煎叆寰皟鎺ュ彛妯″潡
            import finetune_interface
            
            # 鏍规嵁绠楁硶閫夋嫨寰皟鍑芥暟
            if algorithm == 'strategy0':
                # AE寰皟
                logger.info(f"寮€濮婣E妯″瀷寰皟: epochs={epochs}, batch_size={batch_size}, lr={learning_rate}")
                finetune_interface.finetune_ae_model(
                    data_df=df,
                    cmg_type=cmg_model_name.upper(),
                    epochs=epochs,
                    batch_size=batch_size,
                    lr=learning_rate
                )
                
                result_message = f"AE妯″瀷寰皟瀹屾垚 - 浣跨敤{len(df)}鏉℃暟鎹紝璁粌{epochs}杞?
                
            elif algorithm == 'strategy1':
                # VAE寰皟
                logger.info(f"寮€濮媀AE妯″瀷寰皟: epochs={epochs}, batch_size={batch_size}, lr={learning_rate}")
                finetune_interface.finetune_vae_model(
                    data_df=df,
                    cmg_type=cmg_model_name.upper(),
                    epochs=epochs,
                    batch_size=batch_size,
                    lr=learning_rate
                )
                
                result_message = f"VAE妯″瀷寰皟瀹屾垚 - 浣跨敤{len(df)}鏉℃暟鎹紝璁粌{epochs}杞?
            
            else:
                return {
                    'status': 'error',
                    'message': f'涓嶆敮鎸佺殑绠楁硶: {algorithm}'
                }
            
            logger.info(f"妯″瀷寰皟鎴愬姛: {result_message}")
            
            return {
                'status': 'success',
                'message': result_message,
                'data': {
                    'cmg_id': cmg.cmg_id,
                    'cmg_name': cmg.name,
                    'cmg_model': cmg_model_name,
                    'algorithm': algorithm,
                    'data_count': len(data),
                    'epochs': epochs,
                    'batch_size': batch_size,
                    'learning_rate': learning_rate
                }
            }
            
        except Exception as e:
            logger.error(f"妯″瀷寰皟澶辫触: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'妯″瀷寰皟澶辫触: {str(e)}'
            }
