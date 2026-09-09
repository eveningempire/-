"""
IMS寮傚父妫€娴嬫湇鍔?澶勭悊IMS妯″瀷鍔犺浇銆佸疄鏃舵娴嬪拰缁撴灉瀛樺偍
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from django.db import transaction

from data_management.models import PHM, PHMData, PHMModel
from .models import IMSModel, IMSDetectionResult
from .algorithms.IMS.ims_algorithm import IMSModel as IMSAlgorithm
from .algorithms.IMS.ims_kmeans_adapter import IMSKMeansAdapter
from rule_detection.service import evaluate_rules_for_data_point
from msfg_analysis.models import MSFGDefinition
from msfg_analysis.algorithms.msfg.fusion import fuse_test_to_fault, summarize_system
from msfg_analysis.models import TestPointRule, MSFGAnalysisResult, TestPointRuleMapping
from rule_detection.models import RuleDetectionResult
from rule_detection.algorithms.rule.rule_detector import SafeEvaluator  # 澶嶇敤瀹夊叏琛ㄨ揪寮忔眰鍊?
logger = logging.getLogger(__name__)


class IMSService:
    """IMS妫€娴嬫湇鍔?""
    
    def __init__(self):
        self._loaded_models: Dict[int, IMSAlgorithm] = {}  # model_id -> algorithm instance
        self._model_cache: Dict[int, IMSModel] = {}       # model_id -> database model
    
    def load_model(self, ims_model_id: int) -> Optional[IMSAlgorithm]:
        """鍔犺浇IMS妯″瀷"""
        try:
            # 浠庣紦瀛樹腑鑾峰彇
            if ims_model_id in self._loaded_models:
                return self._loaded_models[ims_model_id]
            
            # 浠庢暟鎹簱鑾峰彇妯″瀷
            try:
                ims_model = IMSModel.objects.get(id=ims_model_id, is_active=True)
            except IMSModel.DoesNotExist:
                logger.warning(f"IMS妯″瀷 {ims_model_id} 涓嶅瓨鍦ㄦ垨鏈縺娲?)
                return None
            
            # 閫夋嫨瀹炵幇锛氳€両MS(KMeans-瓒呯洅) 鎴?鐜拌IsolationForest
            impl_type = str((ims_model.model_config or {}).get('type', 'isolation_forest')).lower()
            if impl_type in ('kmeans_ims', 'legacy_kmeans', 'legacy_ims'):
                # 閫傞厤鍣ㄧ洿鎺ョ敤浜岃繘鍒秊oblib
                algorithm = IMSKMeansAdapter(
                    pnames=ims_model.parameters,
                    model_bytes=ims_model.model_data,
                    threshold=float(ims_model.threshold or 0.5)
                )
                # 缂撳瓨鍚庣洿鎺ヨ繑鍥?                self._loaded_models[ims_model_id] = algorithm  # type: ignore[assignment]
                self._model_cache[ims_model_id] = ims_model
                logger.info(f"鎴愬姛鍔犺浇Legacy IMS妯″瀷 {ims_model_id} ({ims_model.name})")
                return algorithm  # type: ignore[return-value]
            else:
                # 鍒涘缓IsolationForest瀹炵幇
                algorithm = IMSAlgorithm(
                    index=ims_model.id,
                    name=ims_model.name,
                    pnames=ims_model.parameters,
                    component=ims_model.cmg_model.model_name,
                    config=ims_model.model_config
                )
            
            # 浠庢ā鍨嬫暟鎹仮澶嶏紙浠匢solationForest璺緞锛?            try:
                algorithm.from_json(ims_model.model_data)
                iso = getattr(algorithm, "isolation_forest", None)
                if iso is None or not hasattr(iso, "estimators_") or not hasattr(iso, "_max_features"):
                    raise ValueError("IMS妯″瀷鏈寘鍚凡璁粌鐨処solationForest锛岃閲嶆柊璁粌骞朵繚瀛?)
                algorithm.trained = True
            except Exception as e:
                logger.error(f"鍔犺浇IMS妯″瀷 {ims_model_id} 澶辫触: {e}")
                return None
            
            # 缂撳瓨妯″瀷
            self._loaded_models[ims_model_id] = algorithm
            self._model_cache[ims_model_id] = ims_model
            
            logger.info(f"鎴愬姛鍔犺浇IMS妯″瀷 {ims_model_id} ({ims_model.name})")
            return algorithm
            
        except Exception as e:
            logger.error(f"鍔犺浇IMS妯″瀷 {ims_model_id} 鏃跺嚭閿? {e}")
            return None
    
    def detect_anomaly(self, cmg_data: PHMData, ims_model_id: int) -> Optional[IMSDetectionResult]:
        """瀵瑰崟涓暟鎹偣杩涜寮傚父妫€娴?- 鎬ц兘浼樺寲鐗堟湰"""
        try:
            # 鍔犺浇妯″瀷
            algorithm = self.load_model(ims_model_id)
            if algorithm is None:
                return None
            
            ims_model = self._model_cache[ims_model_id]
            
            # 鍑嗗鏁版嵁 - 鍙娇鐢ㄦā鍨嬭缁冩椂鐨勫弬鏁?            raw_data = cmg_data.data
            model_params = ims_model.parameters
            
            # 鎸夌収妯″瀷鍙傛暟椤哄簭鎻愬彇鏁版嵁
            filtered_data = {param: raw_data.get(param, float('nan')) for param in model_params}
            timestamp = cmg_data.timestamp.timestamp() if cmg_data.timestamp else timezone.now().timestamp()
            
            # 杩涜妫€娴?            result = algorithm.onlineValidate(filtered_data, timestamp)
            if not isinstance(result, dict) or "result" not in result:
                raise ValueError("IMS鍦ㄧ嚎妫€娴嬭繑鍥炴牸寮忔棤鏁?)
            
            # 瑙ｆ瀽缁撴灉
            detection_result = result.get("result") or {}
            is_anomaly = detection_result.get("state", False)
            anomaly_score = detection_result.get("score", 0.0)
            parameter_scores = detection_result.get("parameter_scores") or {}
            
            # 鍒涘缓缁撴灉瀵硅薄浣嗕笉绔嬪嵆淇濆瓨鍒版暟鎹簱
            ims_result = IMSDetectionResult(
                data_point=cmg_data,
                ims_model=ims_model,
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                parameter_scores=parameter_scores,
                detection_details=detection_result
            )
            
            return ims_result
            
        except Exception as e:
            logger.error(f"IMS妫€娴嬪け璐? {e}")
            return None
    
    def batch_detect(self, cmg_data_list: List[PHMData], ims_model_id: int) -> List[IMSDetectionResult]:
        """鎵归噺寮傚父妫€娴?""
        results = []
        for cmg_data in cmg_data_list:
            result = self.detect_anomaly(cmg_data, ims_model_id)
            if result:
                results.append(result)
        return results
    
    def get_active_models_for_cmg(self, cmg_id: str) -> List[IMSModel]:
        """鑾峰彇PHM鐨勬縺娲籌MS妯″瀷"""
        try:
            cmg = PHM.objects.get(cmg_id=cmg_id)
            models = list(IMSModel.objects.filter(
                cmg_model=cmg.cmg_model,
                is_active=True
            ))
            logger.info(f"鎵惧埌 {len(models)} 涓縺娲荤殑IMS妯″瀷鐢ㄤ簬PHM {cmg_id}")
            return models
        except PHM.DoesNotExist:
            logger.warning(f"PHM {cmg_id} 涓嶅瓨鍦?)
            return []
    
    def create_model_from_file(self, model_file_path: str, cmg_model_id: int, 
                              name: str = None) -> Optional[IMSModel]:
        """浠庤缁冨ソ鐨勬ā鍨嬫枃浠跺垱寤烘暟鎹簱璁板綍"""
        try:
            model_path = Path(model_file_path)
            if not model_path.exists():
                logger.error(f"妯″瀷鏂囦欢涓嶅瓨鍦? {model_file_path}")
                return None
            
            # 璇诲彇妯″瀷鏁版嵁
            with open(model_path, 'rb') as f:
                model_data = f.read()
            
            # 璇诲彇鍏冩暟鎹?            metadata_path = model_path.with_suffix('.metadata.json')
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            # 鑾峰彇PHM妯″瀷
            try:
                cmg_model = PHMModel.objects.get(id=cmg_model_id)
            except PHMModel.DoesNotExist:
                logger.error(f"PHM妯″瀷 {cmg_model_id} 涓嶅瓨鍦?)
                return None
            
            # 鍒涘缓鏁版嵁搴撹褰?            ims_model = IMSModel.objects.create(
                cmg_model=cmg_model,
                name=name or f"IMS_{cmg_model.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                parameters=metadata.get('parameters', []),
                model_config=metadata.get('config', {}),
                model_data=model_data,
                threshold=metadata.get('threshold', 0.5),
                is_active=True
            )
            
            logger.info(f"鎴愬姛鍒涘缓IMS妯″瀷: {ims_model}")
            return ims_model
            
        except Exception as e:
            logger.error(f"鍒涘缓IMS妯″瀷澶辫触: {e}")
            return None
    
    def clear_cache(self):
        """娓呯┖妯″瀷缂撳瓨"""
        self._loaded_models.clear()
        self._model_cache.clear()
        logger.info("IMS妯″瀷缂撳瓨宸叉竻绌?)
    
    def get_detection_statistics(self, cmg_id: str, hours: int = 24) -> Dict[str, Any]:
        """鑾峰彇妫€娴嬬粺璁′俊鎭?""
        try:
            cmg = PHM.objects.get(cmg_id=cmg_id)
            
            # 璁＄畻鏃堕棿鑼冨洿
            end_time = timezone.now()
            start_time = end_time - timezone.timedelta(hours=hours)
            
            # 鏌ヨ妫€娴嬬粨鏋?            results = IMSDetectionResult.objects.filter(
                data_point__cmg=cmg,
                created_at__gte=start_time,
                created_at__lte=end_time
            )
            
            total_detections = results.count()
            anomaly_count = results.filter(is_anomaly=True).count()
            
            # 鎸夋ā鍨嬬粺璁?            model_stats = {}
            for ims_model in IMSModel.objects.filter(cmg_model=cmg.cmg_model, is_active=True):
                model_results = results.filter(ims_model=ims_model)
                from django.db import models as django_models
                model_stats[ims_model.name] = {
                    'total': model_results.count(),
                    'anomalies': model_results.filter(is_anomaly=True).count(),
                    'avg_score': model_results.aggregate(
                        avg_score=django_models.Avg('anomaly_score')
                    )['avg_score'] or 0.0
                }
            
            return {
                'period_hours': hours,
                'total_detections': total_detections,
                'anomaly_count': anomaly_count,
                'anomaly_rate': anomaly_count / total_detections if total_detections > 0 else 0.0,
                'model_statistics': model_stats
            }
            
        except Exception as e:
            logger.error(f"鑾峰彇妫€娴嬬粺璁″け璐? {e}")
            return {}


# 鍏ㄥ眬IMS鏈嶅姟瀹炰緥
ims_service = IMSService()


def run_ims_detection(cmg_data: PHMData) -> List[IMSDetectionResult]:
    """瀵笴MGData杩愯鎵€鏈夋縺娲荤殑IMS妫€娴?""
    results: List[IMSDetectionResult] = []
    try:
        # 鑾峰彇璇MG鐨勬墍鏈夋縺娲籌MS妯″瀷锛屽彧浣跨敤绗竴涓縺娲绘ā鍨嬩互鍖归厤OneToOne绾︽潫
        active_models = ims_service.get_active_models_for_cmg(cmg_data.cmg.cmg_id)
        if not active_models:
            logger.warning(f"PHM {cmg_data.cmg.cmg_id} 娌℃湁婵€娲荤殑IMS妯″瀷")
            return results
            
        ims_model = active_models[0]
        logger.info(f"浣跨敤IMS妯″瀷 {ims_model.name} (ID: {ims_model.id}) 妫€娴婥MG {cmg_data.cmg.cmg_id}")
        
        try:
            result = ims_service.detect_anomaly(cmg_data, ims_model.id)
            if result:
                results.append(result)
                logger.info(f"IMS妫€娴嬪畬鎴? 寮傚父={result.is_anomaly}, 鍒嗘暟={result.anomaly_score:.3f}")

                # 浠呭湪IMS妫€娴嬪埌寮傚父鏃惰繘琛岃鍒欐娴嬶細鍏堣窇楂樼骇瑙勫垯锛堟椂搴忥級锛屽啀鍥為€€鍗曠偣瑙勫垯
                if result.is_anomaly:
                    try:
                        from rule_detection.service import evaluate_advanced_rules_for_data_point, evaluate_rules_for_data_point
                        adv_results = evaluate_advanced_rules_for_data_point(cmg_data)
                        logger.info(
                            f"楂樼骇瑙勫垯妫€娴嬪畬鎴? 鎬绘暟={len(adv_results)} 瑙﹀彂={sum(1 for r in adv_results if r.get('is_triggered'))}"
                        )
                        # 鍏煎锛氬悓鏃惰繍琛屽崟鐐硅鍒欙紝渚夸簬閫愭杩佺Щ/瀵规瘮
                        base_results = evaluate_rules_for_data_point(cmg_data)
                        logger.info(
                            f"鍩虹瑙勫垯妫€娴嬪畬鎴? 鎬绘暟={len(base_results)} 瑙﹀彂={sum(1 for r in base_results if r['is_triggered'])}"
                        )
                    except Exception as er:
                        logger.error(f"瑙勫垯妫€娴嬪け璐? {er}")

                # 鑻MS寮傚父锛屽皾璇曡繘琛孧SFG铻嶅悎锛堝彲閫夛級
                if result.is_anomaly:
                    try:
                        # 1) 鐢熸垚娴嬬偣璇勫垎 test_scores锛氫紭鍏堜娇鐢ㄧ嫭绔嬫祴鐐硅鍒欙紱鑻ョ己澶卞垯鍥為€€鍒拌鍒欑粨鏋滄槧灏?                        cmg_model = cmg_data.cmg.cmg_model
                        test_scores: Dict[str, float] = {}

                        # 1.1 鐙珛娴嬬偣瑙勫垯璺緞 - 鍙娇鐢ㄦ椿璺僊SFG閰嶇疆鐨勮鍒?                        active_msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).order_by('-updated_at').first()
                        if active_msfg:
                            tprules = list(TestPointRule.objects.filter(msfg_definition=active_msfg, is_online=True))
                        else:
                            tprules = []
                        if tprules:
                            vars_ = {}
                            raw = cmg_data.data or {}
                            for k, v in (raw.items() if isinstance(raw, dict) else []):
                                try:
                                    vars_[k] = float(v)
                                except Exception:
                                    vars_[k] = v

                            # 娉ㄥ叆绐楀彛鍑芥暟: 浠モ€滃抚鈥濅负鍗曚綅璇诲彇璇MG鏈€杩慛甯у巻鍙?                            from data_management.models import PHMData as PHMDataModel
                            from django.conf import settings as dj_settings

                            HISTORY_LIMIT = getattr(dj_settings, 'MSFG_RULE_HISTORY_LIMIT', 100)

                            def _fetch_series(param: str, frames: float) -> list:
                                try:
                                    n = int(float(frames))
                                    n = max(1, min(n, HISTORY_LIMIT))
                                    qs = PHMDataModel.objects.filter(
                                        cmg=cmg_data.cmg,
                                        timestamp__lte=cmg_data.timestamp
                                    ).order_by('-timestamp')[:n]
                                    vals = []
                                    for d in qs:
                                        dv = (d.data or {}).get(param)
                                        try:
                                            vals.append(float(dv))
                                        except Exception:
                                            continue
                                    return list(reversed(vals))
                                except Exception:
                                    return []

                            def mean(param: str, frames: float) -> float:
                                s = _fetch_series(param, frames)
                                return sum(s) / len(s) if s else float('nan')

                            def var(param: str, frames: float) -> float:
                                s = _fetch_series(param, frames)
                                if len(s) < 2:
                                    return float('nan')
                                m = sum(s) / len(s)
                                return sum((x - m) ** 2 for x in s) / (len(s) - 1)

                            def std(param: str, frames: float) -> float:
                                import math as _m
                                v = var(param, frames)
                                return _m.sqrt(v) if v == v else float('nan')

                            def wmin(param: str, frames: float) -> float:
                                s = _fetch_series(param, frames)
                                return min(s) if s else float('nan')

                            def wmax(param: str, frames: float) -> float:
                                s = _fetch_series(param, frames)
                                return max(s) if s else float('nan')

                            def delta(param: str, frames: float) -> float:
                                s = _fetch_series(param, frames)
                                return (s[-1] - s[0]) if len(s) >= 2 else float('nan')

                            def slope(param: str, frames: float) -> float:
                                s = _fetch_series(param, frames)
                                n = len(s)
                                if n < 2:
                                    return float('nan')
                                # 绠€鍗曠嚎鎬у洖褰掓枩鐜囷紙x涓虹储寮曪級
                                xs = list(range(n))
                                x_mean = sum(xs) / n
                                y_mean = sum(s) / n
                                num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, s))
                                den = sum((x - x_mean) ** 2 for x in xs) or float('nan')
                                return num / den if den == den else float('nan')

                            def pct_change(param: str, frames: float) -> float:
                                s = _fetch_series(param, frames)
                                if len(s) < 2:
                                    return float('nan')
                                base = s[0]
                                return (s[-1] - base) / base if base else float('nan')

                            def between(val: float, lo: float, hi: float) -> bool:
                                try:
                                    v = float(val)
                                    return (v >= float(lo)) and (v <= float(hi))
                                except Exception:
                                    return False

                            def adiff(param: str, frames: float) -> float:
                                s = _fetch_series(param, frames)
                                return abs(s[-1] - s[-2]) if len(s) >= 2 else float('nan')

                            def ma_diff(param: str, sub_frames: float) -> float:
                                # 鍙栨渶杩戜袱涓浉閭诲瓙绐楃殑鍧囧€煎樊缁濆鍊硷細|mean(鏈€杩憇ub) - mean(娆¤繎sub)|
                                s1 = _fetch_series(param, sub_frames)
                                s2 = _fetch_series(param, sub_frames * 2.0)
                                if not s1 or len(s2) < 2:
                                    return float('nan')
                                import statistics as _st
                                prev_segment_len = len(s2) - len(s1)
                                if prev_segment_len <= 0:
                                    return float('nan')
                                prev_mean = _st.mean(s2[:prev_segment_len]) if prev_segment_len > 0 else float('nan')
                                curr_mean = _st.mean(s1)
                                try:
                                    return abs(curr_mean - prev_mean)
                                except Exception:
                                    return float('nan')

                            def rollstd(param: str, frames: float) -> float:
                                return std(param, frames)

                            def level(param_current_value: float, median: float, mad: float) -> float:
                                try:
                                    if isinstance(param_current_value, str):
                                        x = float(vars_.get(param_current_value, float('nan')))
                                    else:
                                        x = float(param_current_value)
                                    m = float(median)
                                    md = float(mad) if float(mad) != 0 else 1e-9
                                    return abs(x - m) / md
                                except Exception:
                                    return float('nan')

                            per_test_scores: Dict[str, List[tuple]] = {}
                            _FUNC_NAMES = {
                                'mean','var','std','wmin','wmax','delta','slope','pct_change','between',
                                'adiff','ma_diff','rollstd','level',
                                'abs','round','min','max','sin','cos','tan','asin','acos','atan','log','exp'
                            }
                            for r in tprules:
                                try:
                                    expr = str(r.rule_expression or '').strip()
                                    if not expr:
                                        continue
                                    import ast
                                    ast_obj = ast.parse(expr, mode='eval')
                                    _names: set = set()
                                    class _NameCollector(ast.NodeVisitor):
                                        def visit_Name(self, node):
                                            _names.add(node.id)
                                    _NameCollector().visit(ast_obj)
                                    ref_vars = sorted([n for n in _names if n not in _FUNC_NAMES])
                                    missing_vars = sorted([n for n in ref_vars if n not in vars_])

                                    val = SafeEvaluator(vars_, funcs={
                                        'mean': mean,
                                        'var': var,
                                        'std': std,
                                        'wmin': wmin,
                                        'wmax': wmax,
                                        'delta': delta,
                                        'slope': slope,
                                        'pct_change': pct_change,
                                        'between': between,
                                        'adiff': adiff,
                                        'ma_diff': ma_diff,
                                        'rollstd': rollstd,
                                        'level': level,
                                    }).visit(ast_obj)
                                    score = 1.0 if bool(val) else 0.0
                                    try:
                                        fval = float(val)
                                        if fval >= 0.0 and fval <= 1.0:
                                            score = float(fval)
                                    except Exception:
                                        pass
                                    per_test_scores.setdefault(r.test_name, []).append((score, float(r.weight or 1.0)))
                                    try:
                                        logger.info(
                                            f"TPRule[{r.test_name}/{r.rule_id}] expr='{expr}' refs={ref_vars} missing={missing_vars} val={val} score={score} weight={r.weight}"
                                        )
                                    except Exception:
                                        pass
                                except Exception:
                                    logger.exception(f"TPRule 瑙ｆ瀽/姹傚€煎け璐? test={getattr(r,'test_name',None)} id={getattr(r,'rule_id',None)} expr={getattr(r,'rule_expression',None)}")
                                    continue

                            for tname, arr in per_test_scores.items():
                                num = sum(s * w for s, w in arr)
                                den = sum(w for _, w in arr) or 1.0
                                test_scores[tname] = max(0.0, min(1.0, num / den))

                            # 鑻ョ嫭绔嬫祴鐐硅鍒欏瓨鍦ㄤ絾鏈骇鐢熶换浣曟湁鏁堝垎鏁帮紝鍒欏洖閫€鍒?Rule->TestPoint 鏄犲皠
                            if not test_scores:
                                mappings = list(TestPointRuleMapping.objects.filter(cmg_model=cmg_model, is_active=True).select_related('rule_definition'))
                                if mappings:
                                    from rule_detection.models import RuleDetectionResult as RR
                                    rr_qs = RR.objects.filter(
                                        data_point=cmg_data,
                                        rule_definition__in=[m.rule_definition for m in mappings]
                                    ).select_related('rule_definition')
                                    tmp: Dict[str, List[tuple]] = {}
                                    rule_to_test = {m.rule_definition_id: (m.test_name, float(m.weight or 1.0)) for m in mappings}
                                    for rr in rr_qs:
                                        t = rule_to_test.get(rr.rule_definition_id)
                                        if not t:
                                            continue
                                        tname, w = t
                                        try:
                                            score = float(rr.confidence_score)
                                        except Exception:
                                            score = 1.0 if rr.is_triggered else 0.0
                                        try:
                                            score = max(0.0, min(1.0, float(score)))
                                        except Exception:
                                            score = 0.0
                                        tmp.setdefault(tname, []).append((score, w))
                                    for tname, arr in tmp.items():
                                        num = sum(s * w for s, w in arr)
                                        den = sum(w for _, w in arr) or 1.0
                                        test_scores[tname] = max(0.0, min(1.0, num / den))
                        else:
                            # 1.2 鍥為€€锛氫娇鐢ㄨ鍒欑粨鏋?+ TestPointRuleMapping 鐢熸垚娴嬬偣璇勫垎
                            mappings = list(TestPointRuleMapping.objects.filter(cmg_model=cmg_model, is_active=True).select_related('rule_definition'))
                            if mappings:
                                rr_qs = RuleDetectionResult.objects.filter(
                                    data_point=cmg_data,
                                    rule_definition__in=[m.rule_definition for m in mappings]
                                ).select_related('rule_definition')
                                # 鎸?test_name 鑱氬悎鎵撳垎锛堢敤 mapping.weight 鍋氬姞鏉冿紝榛樿浣跨敤 confidence_score锛涜嫢鏃犲垯 is_triggered->1/0锛?                                tmp: Dict[str, List[tuple]] = {}
                                rule_to_test = {m.rule_definition_id: (m.test_name, float(m.weight or 1.0)) for m in mappings}
                                for rr in rr_qs:
                                    t = rule_to_test.get(rr.rule_definition_id)
                                    if not t:
                                        continue
                                    tname, w = t
                                    try:
                                        score = float(rr.confidence_score)
                                    except Exception:
                                        score = 1.0 if rr.is_triggered else 0.0
                                    # 鎴柇鍒?0..1
                                    try:
                                        score = max(0.0, min(1.0, float(score)))
                                    except Exception:
                                        score = 0.0
                                    tmp.setdefault(tname, []).append((score, w))
                                for tname, arr in tmp.items():
                                    num = sum(s * w for s, w in arr)
                                    den = sum(w for _, w in arr) or 1.0
                                    test_scores[tname] = max(0.0, min(1.0, num / den))
                                if not test_scores:
                                    logger.info("Rule->TestPoint 鏄犲皠瀛樺湪锛屼絾褰撳墠鏁版嵁鐐规棤瑙勫垯缁撴灉锛岃烦杩嘙SFG铻嶅悎")
                                    return results
                            else:
                                logger.info("娌℃湁鍚敤鐨勬祴鐐硅鍒欙紝涓旀棤 Rule->TestPoint 鏄犲皠锛岃烦杩嘙SFG铻嶅悎")
                                return results

                        if not test_scores:
                            logger.info("娴嬬偣璇勫垎涓虹┖锛岃烦杩嘙SFG铻嶅悎")
                            return results

                        # 2) 璋冪敤MSFG铻嶅悎锛堜粠DB閰嶇疆鏋勯€犲浘锛?                        msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).order_by('-updated_at').first()
                        if msfg:
                            try:
                                logger.info(f"MSFG铻嶅悎鍓?test_scores={test_scores} msfg_id={msfg.id}")
                            except Exception:
                                pass
                            nodes = list(msfg.nodes.all())
                            edges_qs = list(msfg.edges.all())
                            test_name_by_id = {n.node_id: n.name for n in nodes if n.node_type == 'test'}
                            fault_name_by_id = {n.node_id: n.name for n in nodes if n.node_type == 'fault'}
                            edges = [(e.source_node.node_id, e.target_node.node_id) for e in edges_qs]
                            # 浣跨敤澧炲己鐨凪SFG鍒嗘瀽
                            from msfg_analysis.algorithms.msfg.fusion import enhanced_msfg_analysis
                            
                            analysis_result = enhanced_msfg_analysis(
                                test_scores=test_scores,
                                edges=edges,
                                test_name_by_id=test_name_by_id,
                                fault_name_by_id=fault_name_by_id,
                                nodes=nodes,
                                msfg_definition=msfg,
                                include_component_analysis=True
                            )

                            # 5) 鎸佷箙鍖栧寮虹殑铻嶅悎缁撴灉
                            try:
                                fault_scores = analysis_result['fault_results']
                                sys_summary = analysis_result['system_results']
                                component_analysis = analysis_result['component_results']
                                
                                overall_health = float(sys_summary.get('overall_health', 1.0))
                                detected_faults = sys_summary.get('critical_faults', [])
                                critical_components = [comp for comp, data in component_analysis.items() 
                                                     if data.get('health_score', 1.0) < 0.7]
                                
                                MSFGAnalysisResult.objects.create(
                                    data_point=cmg_data,
                                    msfg_definition=msfg,
                                    test_results=test_scores,
                                    fault_results=fault_scores,
                                    system_results=sys_summary,
                                    component_results=component_analysis,
                                    overall_health_score=overall_health,
                                    detected_faults=detected_faults,
                                    critical_components=critical_components,
                                    analysis_details={
                                        "source": "realtime_testpoint_rules_enhanced",
                                        "analysis_metadata": analysis_result['analysis_metadata']
                                    }
                                )
                            except Exception as save_ex:
                                logger.error(f"淇濆瓨瀹炴椂MSFG缁撴灉澶辫触: {save_ex}")
                            logger.info(f"澧炲己MSFG铻嶅悎瀹屾垚 overall={sys_summary.get('overall_health')}, 閮ㄤ欢鏁?{len(component_analysis)}")
                        else:
                            logger.info("娌℃湁婵€娲荤殑MSFG瀹氫箟锛岃烦杩囪瀺鍚?)
                    except Exception as em:
                        logger.error(f"MSFG铻嶅悎澶辫触: {em}")
            else:
                logger.warning(f"IMS妫€娴嬭繑鍥炵┖缁撴灉")
        except Exception as e:
            logger.error(f"IMS妯″瀷 {ims_model.id} 妫€娴嬪け璐? {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        logger.error(f"杩愯IMS妫€娴嬪け璐? {e}")
        import traceback
        traceback.print_exc()
    return results


def get_anomaly_data_with_ims(cmg_id: str, start_time=None, end_time=None, limit=1000, anomaly_only=False) -> List[Dict[str, Any]]:
    """鑾峰彇鍖呭惈IMS妫€娴嬬粨鏋滅殑鏁版嵁锛堝彲閫夋嫨浠呭紓甯告垨鍏ㄩ儴锛?""
    try:
        cmg = PHM.objects.get(cmg_id=cmg_id)
        
        # 鏋勫缓鏌ヨ
        queryset = PHMData.objects.filter(cmg=cmg)
        
        # 鏀硅繘鏃堕棿鎴冲尮閰嶉€昏緫
        if start_time:
            # 瀵逛簬寮€濮嬫椂闂达紝浣跨敤澶т簬绛変簬锛屼絾鑰冭檻鍒版绉掑鐞嗭紝鍙兘闇€瑕佺◢寰斁瀹芥潯浠?            queryset = queryset.filter(timestamp__gte=start_time)
        if end_time:
            # 瀵逛簬缁撴潫鏃堕棿锛屼娇鐢ㄥ皬浜庣瓑浜?            queryset = queryset.filter(timestamp__lte=end_time)
        
        # 鍙幏鍙栨湁IMS妫€娴嬬粨鏋滅殑鏁版嵁
        queryset = queryset.filter(ims_result__isnull=False)
        
        # 濡傛灉鍙寮傚父鏁版嵁锛屾坊鍔犺繃婊ゆ潯浠?        if anomaly_only:
            queryset = queryset.filter(ims_result__is_anomaly=True)
        
        queryset = queryset.select_related('ims_result', 'ims_result__ims_model')
        queryset = queryset.order_by('-timestamp')[:limit]
        
        results = []
        for data_point in queryset:
            ims_result = data_point.ims_result
            results.append({
                'timestamp': data_point.timestamp.isoformat(),
                'data': data_point.data,
                'ims_detection': {
                    'model_name': ims_result.ims_model.name,
                    'is_anomaly': ims_result.is_anomaly,
                    'anomaly_score': ims_result.anomaly_score,
                    'parameter_scores': ims_result.parameter_scores,
                    'detection_details': ims_result.detection_details
                }
            })
        
        return results
        
    except Exception as e:
        logger.error(f"鑾峰彇IMS寮傚父鏁版嵁澶辫触: {e}")
        return []

