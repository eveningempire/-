from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional
import time
import random
from django.db import transaction, DatabaseError, OperationalError

from data_management.models import PHMData, PHMModel, PHM
from .models import RuleDefinition, FaultDefinition, RuleDetectionResult
from .algorithms.rule.rule_detector import compile_rules, evaluate_rules_on_point
from .algorithms.rule.rule_detector import AdvancedRuleDetector  # 楂樼骇瑙勫垯妫€娴嬪櫒
from .algorithms.rule.advanced_rule_parser import RuleCompiler as AdvancedRuleCompiler  # 楂樼骇瑙勫垯缂栬瘧鍣?from .algorithms.rule.enhanced_rule_detector import EnhancedRuleDetector  # 澧炲己鐗堣鍒欐娴嬪櫒
from .models import ComponentDefinition
from .algorithms.rule.advanced_function_base import (
    calculate_component_health_score,
    aggregate_system_health_score,
)


_compiled_cache: Dict[int, Any] = {}
# 楂樼骇瑙勫垯锛氭ā鍨嬬骇缂栬瘧缂撳瓨銆丆MG绾ф娴嬪櫒涓庡巻鍙插洖濉爣璁?_advanced_compiled_by_model: Dict[int, Dict[str, Any]] = {}
_advanced_detector_by_cmg: Dict[int, AdvancedRuleDetector] = {}
_advanced_warmup_done_for_cmg: Dict[int, bool] = {}


def _get_compiled_rules_for_model(cmg_model: PHMModel) -> Any:
    model_id = cmg_model.id
    if model_id in _compiled_cache:
        return _compiled_cache[model_id]

    # 鏀堕泦鍙傛暟鍚嶏紝杩囨护鎺夋暟鍊煎舰寮忕殑鍙傛暟鍚?    last = (
        PHMData.objects.filter(cmg__cmg_model=cmg_model)
        .order_by("-timestamp")
        .first()
    )
    
    # 鏀堕泦鍙傛暟鍚嶏紝杩囨护鎺夋暟鍊煎舰寮忕殑鍙傛暟鍚?    parameter_names = []
    if last and isinstance(last.data, dict):
        for param_name in last.data.keys():
            # 杩囨护鎺夋暟鍊煎舰寮忕殑鍙傛暟鍚?            if isinstance(param_name, str):
                try:
                    float(param_name)  # 灏濊瘯杞崲涓烘暟鍊?                    # 濡傛灉鎴愬姛杞崲锛岃鏄庢槸鏁板€硷紝璺宠繃
                    continue
                except (ValueError, TypeError):
                    # 濡傛灉杞崲澶辫触锛岃鏄庢槸鏈夋晥鐨勫弬鏁板悕
                    parameter_names.append(param_name)
            elif isinstance(param_name, (int, float)):
                # 鏁板€肩被鍨嬬殑閿紝璺宠繃
                continue
            else:
                # 鍏朵粬绫诲瀷锛岃浆鎹负瀛楃涓?                parameter_names.append(str(param_name))

    # 瑙勫垯琛?    entries: List[Dict[str, Any]] = []
    for rule in RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True).select_related("fault_definition"):
        entries.append(
            {
                "showId": rule.rule_id,
                "ruleExpress": rule.rule_expression,
                "faultName": rule.fault_definition.fault_name,
                "faultLevel": rule.fault_definition.fault_level,
                "component": rule.fault_definition.component,
            }
        )

    compiled = compile_rules(entries, parameter_names)
    _compiled_cache[model_id] = compiled
    return compiled


def clear_rule_cache() -> None:
    _compiled_cache.clear()
    _advanced_compiled_by_model.clear()
    _advanced_detector_by_cmg.clear()
    _advanced_warmup_done_for_cmg.clear()


def evaluate_rules_for_data_point(cmg_data: PHMData) -> List[Dict[str, Any]]:
    """瀵瑰崟鐐规暟鎹墽琛岃鍒欒瘎浼板苟鍏ュ簱锛岃繑鍥炲唴瀛樼粨鏋滃垪琛ㄣ€?
    杩斿洖缁撴灉椤瑰瓧娈碉細
      - rule_id, fault_name, fault_level, component, is_triggered, score, related_parameters
    """
    import logging
    logger = logging.getLogger(__name__)
    
    cmg_model = cmg_data.cmg.cmg_model
    
    # 妫€鏌ユ槸鍚︽湁浣跨敤楂樼骇缁熻鍑芥暟鐨勮鍒欙紙澶у皬鍐欎笉鏁忔劅锛岃ˉ鍏呯己澶卞嚱鏁板悕锛?    has_advanced_rules = False
    advanced_markers = [
        'mean(', 'std(', 'var(', 'mad(', 'rms(', 'slope(', 'diffmean(', 'diffstd(',
        'ma(', 'ma_diff(', 'autocorr(', 'level(', 'rollstd('
    ]
    for rule in RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True):
        expr_l = str(rule.rule_expression or '').lower()
        if any(marker in expr_l for marker in advanced_markers):
            has_advanced_rules = True
            break
    
    if has_advanced_rules:
        logger.info("妫€娴嬪埌楂樼骇缁熻鍑芥暟瑙勫垯锛屼娇鐢ㄥ寮虹増瑙勫垯妫€娴嬪櫒")
        return evaluate_rules_with_enhanced_detector(cmg_data)
    else:
        logger.info("浣跨敤浼犵粺瑙勫垯妫€娴嬪櫒")
        return evaluate_rules_with_traditional_detector(cmg_data)


def evaluate_rules_with_traditional_detector(cmg_data: PHMData) -> List[Dict[str, Any]]:
    """浣跨敤浼犵粺瑙勫垯妫€娴嬪櫒杩涜璇勪及"""
    cmg_model = cmg_data.cmg.cmg_model
    compiled = _get_compiled_rules_for_model(cmg_model)
    raw_results = evaluate_rules_on_point(cmg_data.data, compiled)

    # 璁＄畻鏈抚涓嬪悇閮ㄤ欢鐨勫仴搴峰害鍒嗘暟锛?-1锛夛紝浣滀负褰掍竴鍖栭儴浠跺垎鏁?    try:
        # 瑙勮寖鍖栧瓧娈碉細灏?raw_results 鐨?'score' 鏄犲皠涓哄仴搴疯绠楁墍闇€鐨?'confidence_score'
        normalized_results: List[Dict[str, Any]] = []
        for r in raw_results:
            comp_name = str(r.get("component") or "").strip()
            if not comp_name:
                continue
            normalized_results.append(
                {
                    "component": comp_name,
                    "is_triggered": bool(r.get("is_triggered", False)),
                    "confidence_score": float(r.get("score") or 0.0),
                    "fault_level": int(r.get("fault_level") or 1),
                    "related_parameters": list(r.get("related_parameters") or []),
                }
            )

        components_in_results = {it["component"] for it in normalized_results}
        component_health_scores: Dict[str, float] = {}
        for comp_name in components_in_results:
            component_health_scores[comp_name] = calculate_component_health_score(
                comp_name, normalized_results, parameter_weights=None
            )
    except Exception:
        component_health_scores = {}

    # 鏁呴殰鍚?-> FaultDefinition
    fault_map = {f.fault_name: f for f in FaultDefinition.objects.filter(cmg_model=cmg_model)}

    # 鍥哄畾椤哄簭锛屽噺灏戝苟鍙戦攣鍐茬獊
    ordered_results = sorted(
        raw_results,
        key=lambda x: (str(x.get("fault_name") or ""), str(x.get("rule_id") or "")),
    )

    # 灏忕矑搴﹀師瀛愬潡 + 1213 姝婚攣閲嶈瘯
    for r in ordered_results:
        fault_def = fault_map.get(r["fault_name"])
        if not fault_def:
            continue
        rule_def = (
            RuleDefinition.objects.filter(cmg_model=cmg_model, rule_id=r["rule_id"]).first()
        )

        max_retries = 3
        attempt = 0
        while True:
            try:
                with transaction.atomic():
                    details = dict(r)
                    # 闄勫姞閮ㄤ欢鍋ュ悍搴﹀垎鏁帮紝渚夸簬鍓嶇鐩存帴浣跨敤
                    try:
                        comp_name = str(r.get("component") or "").strip()
                        if comp_name:
                            details["component_health_score"] = float(component_health_scores.get(comp_name, 1.0))
                    except Exception:
                        pass

                    RuleDetectionResult.objects.create(
                        data_point=cmg_data,
                        rule_definition=rule_def,
                        fault_definition=fault_def,
                        is_triggered=bool(r["is_triggered"]),
                        confidence_score=float(r["score"]),
                        detection_details=details,
                    )
                break
            except (OperationalError, DatabaseError) as e:
                msg = str(e)
                if "1213" in msg or "Deadlock found" in msg:
                    attempt += 1
                    if attempt > max_retries:
                        break
                    time.sleep((0.01 * (2 ** (attempt - 1))) + random.uniform(0, 0.03))
                    continue
                else:
                    raise

    return raw_results


def evaluate_rules_with_enhanced_detector(cmg_data: PHMData) -> List[Dict[str, Any]]:
    """浣跨敤澧炲己鐗堣鍒欐娴嬪櫒杩涜璇勪及"""
    import logging
    logger = logging.getLogger(__name__)
    
    cmg_model = cmg_data.cmg.cmg_model
    cmg = cmg_data.cmg
    
    try:
        # 鍒涘缓澧炲己鐗堣鍒欓厤缃?        rule_config = {
            "rules": [],
            "parameter_names": [],
            "fault_name_map": {}
        }
        
        # 鏀堕泦鍙傛暟鍚?        parameter_names = []
        if isinstance(cmg_data.data, dict):
            for param_name in cmg_data.data.keys():
                # 杩囨护鎺夋暟鍊煎舰寮忕殑鍙傛暟鍚?                if isinstance(param_name, str):
                    try:
                        float(param_name)  # 灏濊瘯杞崲涓烘暟鍊?                        # 濡傛灉鎴愬姛杞崲锛岃鏄庢槸鏁板€硷紝璺宠繃
                        continue
                    except (ValueError, TypeError):
                        # 濡傛灉杞崲澶辫触锛岃鏄庢槸鏈夋晥鐨勫弬鏁板悕
                        parameter_names.append(param_name)
                elif isinstance(param_name, (int, float)):
                    # 鏁板€肩被鍨嬬殑閿紝璺宠繃
                    continue
                else:
                    # 鍏朵粬绫诲瀷锛岃浆鎹负瀛楃涓?                    parameter_names.append(str(param_name))
        
        rule_config["parameter_names"] = parameter_names
        
        # 鏋勫缓瑙勫垯閰嶇疆
        for rule_def in RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True).select_related("fault_definition"):
            # 瑙ｆ瀽瑙勫垯琛ㄨ揪寮忥紝鎻愬彇鐩稿叧鍙傛暟
            from .algorithms.rule.enhanced_rule_parser import EnhancedRuleParser
            parser = EnhancedRuleParser(parameter_names)
            parse_result = parser.parse(rule_def.rule_expression)
            
            # 浣跨敤瑙ｆ瀽鍑虹殑鐩稿叧鍙傛暟锛屽鏋滄病鏈夎В鏋愬嚭鍙傛暟鍒欏皾璇曚粠琛ㄨ揪寮忎腑鎻愬彇
            if parse_result and parse_result.related_parameters:
                related_params = list(parse_result.related_parameters)
            else:
                # 濡傛灉瑙ｆ瀽澶辫触锛屽皾璇曚粠琛ㄨ揪寮忎腑鎵嬪姩鎻愬彇鍙傛暟鍚?                import re
                # 鍖归厤鍙傛暟鍚嶆ā寮忥細涓枃鍙傛暟鍚嶆垨鑻辨枃鍙傛暟鍚?                param_pattern = r'([a-zA-Z\u4e00-\u9fff]+(?:\s*[A-Za-z\u4e00-\u9fff]+)*)'
                matches = re.findall(param_pattern, rule_def.rule_expression)
                # 杩囨护鍑烘湁鏁堢殑鍙傛暟鍚嶏紙鎺掗櫎鍑芥暟鍚嶃€佹暟瀛楃瓑锛?                function_names = ['level', 'rollstd', 'ma_diff', 'mean', 'std', 'var', 'mad', 'rms', 'max', 'min', 'range', 'slope', 'diffmean', 'diffstd', 'ma', 'autocorr']
                related_params = []
                for match in matches:
                    if match not in function_names and not match.replace('.', '').replace('-', '').isdigit():
                        # 妫€鏌ユ槸鍚︽槸鏈夋晥鐨勫弬鏁板悕
                        if any(param in match for param in parameter_names):
                            related_params.append(match)
                
                # 濡傛灉杩樻槸娌℃湁鎵惧埌锛屼娇鐢ㄦ墍鏈夊弬鏁?                if not related_params:
                    related_params = parameter_names
            
            # 璁板綍瑙ｆ瀽缁撴灉
            logger.debug(f"瑙勫垯 {rule_def.rule_id} 瑙ｆ瀽缁撴灉:")
            logger.debug(f"  鍘熷琛ㄨ揪寮? {rule_def.rule_expression}")
            logger.debug(f"  瑙ｆ瀽鍚庤〃杈惧紡: {parse_result.expression if parse_result else 'None'}")
            logger.debug(f"  鐩稿叧鍙傛暟: {list(parse_result.related_parameters) if parse_result else []}")
            logger.debug(f"  閿欒鏁? {parse_result.error_count if parse_result else 0}")
            logger.debug(f"  璀﹀憡鏁? {parse_result.warning_count if parse_result else 0}")
            logger.debug(f"  鏈€缁堢浉鍏冲弬鏁? {related_params}")
            
            rule_config["rules"].append({
                "rule_id": rule_def.rule_id,
                "fault_name": rule_def.fault_definition.fault_name,
                "fault_level": rule_def.fault_definition.fault_level,
                "component": rule_def.fault_definition.component,
                "expression": rule_def.rule_expression,
                "related_parameters": related_params,
                "is_online": rule_def.is_online,
                "source": rule_def.source,
                "plan_description": rule_def.plan_description,
                "parse_result": parse_result  # 娣诲姞瑙ｆ瀽缁撴灉
            })
        
        # 鍒涘缓澧炲己鐗堟娴嬪櫒
        detector = EnhancedRuleDetector(rule_config)
        
        logger.debug(f"澧炲己妫€娴嬪櫒鍒涘缓瀹屾垚锛岄厤缃簡 {len(rule_config['rules'])} 鏉¤鍒?)
        logger.debug(f"瑙勫垯閰嶇疆: {[r['rule_id'] for r in rule_config['rules']]}")
        
        # 娣诲姞璇︾粏鐨勮鍒欎俊鎭?        for rule in rule_config['rules']:
            logger.debug(f"瑙勫垯 {rule['rule_id']}: {rule['expression']}")
            logger.debug(f"  鐩稿叧鍙傛暟: {rule['related_parameters']}")
            logger.debug(f"  鏁呴殰鍚嶇О: {rule['fault_name']}")
            logger.debug(f"  鏁呴殰绛夌骇: {rule['fault_level']}")
        
        # 涓烘娴嬪櫒鎻愪緵鍘嗗彶鏁版嵁
        _warmup_enhanced_detector_for_single_point(detector, cmg, parameter_names)
        
        # 鎵ц妫€娴?        data_frame = cmg_data.data if isinstance(cmg_data.data, dict) else {}
        logger.info(f"鎵ц妫€娴嬶紝鏁版嵁甯у寘鍚?{len(data_frame)} 涓弬鏁?)
        logger.debug(f"鏁版嵁甯у弬鏁? {list(data_frame.keys())}")
        
        detection_results = detector.detect(data_frame, cmg_data.timestamp)
        
        # 杞崲涓轰紶缁熸牸寮忓苟淇濆瓨鍒版暟鎹簱
        raw_results = []
        
        # 鑾峰彇鎵€鏈夎鍒欙紝纭繚姣忎釜瑙勫垯閮芥湁妫€娴嬬粨鏋?        all_rules = RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True)
        detected_rule_ids = {result.get('rule_id') for result in detection_results}
        
        # 澶勭悊妫€娴嬪埌鐨勮鍒?        for result in detection_results:
            # 灏?detector 鐨勭疆淇″害瑁佸壀鍒?[0,1]
            raw_score = float(result.get('confidence_score', 0.0))
            clipped_score = max(0.0, min(1.0, raw_score))
            
            raw_result = {
                "rule_id": result.get('rule_id', ''),
                "fault_name": result.get('fault_name', ''),
                "fault_level": result.get('fault_level', 1),
                "component": result.get('component', ''),
                "is_triggered": bool(result.get('is_triggered')),
                "score": clipped_score,
                "related_parameters": result.get('related_parameters', [])
            }
            raw_results.append(raw_result)
            
            # 淇濆瓨鍒版暟鎹簱
            _save_enhanced_rule_result(cmg_data, raw_result)
        
        # 澶勭悊鏈娴嬪埌鐨勮鍒欙紙鍙兘鏄敱浜庡弬鏁扮己澶辩瓑鍘熷洜锛?        for rule in all_rules:
            if rule.rule_id not in detected_rule_ids:
                # 涓烘湭妫€娴嬬殑瑙勫垯鍒涘缓榛樿缁撴灉
                raw_result = {
                    "rule_id": rule.rule_id,
                    "fault_name": rule.fault_definition.fault_name,
                    "fault_level": rule.fault_definition.fault_level,
                    "component": rule.fault_definition.component,
                    "is_triggered": False,
                    "score": 0.0,  # 鏈娴嬬殑瑙勫垯缃俊搴︿负0
                    "related_parameters": [],
                    "detection_note": "瑙勫垯鏈墽琛屾娴?
                }
                raw_results.append(raw_result)
                
                # 淇濆瓨鍒版暟鎹簱
                _save_enhanced_rule_result(cmg_data, raw_result)
        
        return raw_results
        
    except Exception as e:
        logger.error(f"澧炲己瑙勫垯妫€娴嬪け璐? {e}")
        return []


def _warmup_enhanced_detector_for_single_point(detector: EnhancedRuleDetector, cmg: PHM, parameter_names: list) -> None:
    """涓哄崟鐐规娴嬬殑澧炲己鐗堟娴嬪櫒鎻愪緵鍘嗗彶鏁版嵁"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 鑾峰彇鏈€杩戠殑鍘嗗彶鏁版嵁锛堟渶澶?00甯э紝閬垮厤鎬ц兘闂锛?        from data_management.models import PHMData
        recent_data = PHMData.objects.filter(
            cmg=cmg
        ).order_by('-timestamp')[:500]
        
        if not recent_data:
            logger.debug("娌℃湁鍘嗗彶鏁版嵁鐢ㄤ簬澧炲己妫€娴嬪櫒棰勭儹")
            return
        
        # 鎸夋椂闂撮『搴忔帓搴?        recent_data = list(reversed(recent_data))
        
        logger.debug(f"涓哄寮烘娴嬪櫒鎻愪緵 {len(recent_data)} 甯у巻鍙叉暟鎹?)
        
        # 閫愬抚鏇存柊妫€娴嬪櫒
        for i, record in enumerate(recent_data):
            if isinstance(record.data, dict):
                detector.update_data(record.data, record.timestamp, i)
        
        logger.debug("澧炲己妫€娴嬪櫒棰勭儹瀹屾垚")
        
    except Exception as e:
        logger.warning(f"澧炲己妫€娴嬪櫒棰勭儹澶辫触: {e}")


def _save_enhanced_rule_result(cmg_data: PHMData, raw_result: Dict[str, Any]) -> None:
    """淇濆瓨澧炲己鐗堣鍒欐娴嬬粨鏋滃埌鏁版嵁搴?""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        cmg_model = cmg_data.cmg.cmg_model
        
        # 鑾峰彇鏁呴殰瀹氫箟鍜岃鍒欏畾涔?        fault_def = FaultDefinition.objects.filter(
            cmg_model=cmg_model,
            fault_name=raw_result.get('fault_name', '')
        ).first()
        
        rule_def = RuleDefinition.objects.filter(
            cmg_model=cmg_model,
            rule_id=raw_result.get('rule_id', '')
        ).first()
        
        if fault_def and rule_def:
            # 妫€鏌ユ槸鍚﹀凡瀛樺湪缁撴灉
            existing_result = RuleDetectionResult.objects.filter(
                data_point=cmg_data,
                rule_definition=rule_def,
                fault_definition=fault_def
            ).first()
            
            if existing_result:
                # 鏇存柊鐜版湁缁撴灉
                existing_result.is_triggered = bool(raw_result.get('is_triggered', False))
                # 瑁佸壀鍒嗘暟
                s = float(raw_result.get('score', 0.0))
                existing_result.confidence_score = max(0.0, min(1.0, s))
                existing_result.detection_details = raw_result
                existing_result.save()
            else:
                # 鍒涘缓鏂扮粨鏋?                s = float(raw_result.get('score', 0.0))
                RuleDetectionResult.objects.create(
                    data_point=cmg_data,
                    rule_definition=rule_def,
                    fault_definition=fault_def,
                    is_triggered=bool(raw_result.get('is_triggered', False)),
                    confidence_score=max(0.0, min(1.0, s)),
                    detection_details=raw_result
                )
                
    except Exception as e:
        logger.warning(f"淇濆瓨澧炲己瑙勫垯妫€娴嬬粨鏋滃け璐? {e}")


def _get_advanced_compiled_for_model(cmg_model: PHMModel) -> Dict[str, Any]:
    """缂栬瘧鎸囧畾妯″瀷鐨勯珮绾ц鍒欓厤缃紙甯︽椂搴忎緷璧栨弿杩帮級銆?""
    model_id = cmg_model.id
    if model_id in _advanced_compiled_by_model:
        return _advanced_compiled_by_model[model_id]

    # 鏀堕泦鍦ㄧ嚎瑙勫垯
    rule_defs: List[Dict[str, Any]] = []
    for rd in RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True).select_related("fault_definition"):
        rule_defs.append({
            "rule_id": rd.rule_id,
            "rule_expression": rd.rule_expression,
            "fault_name": rd.fault_definition.fault_name,
            "fault_level": rd.fault_definition.fault_level,
            "component": rd.fault_definition.component,
            "is_online": rd.is_online,
            "source": rd.source,
            "plan_description": rd.plan_description,
        })

    # 鍙傛暟鍚嶏細鍩轰簬鏈€杩戜竴鏉℃暟鎹紙涓庝紶缁熻鍒欎竴鑷达級
    last = (
        PHMData.objects.filter(cmg__cmg_model=cmg_model)
        .order_by("-timestamp")
        .first()
    )
    
    # 鏀堕泦鍙傛暟鍚嶏紝杩囨护鎺夋暟鍊煎舰寮忕殑鍙傛暟鍚?    parameter_names = []
    if last and isinstance(last.data, dict):
        for param_name in last.data.keys():
            # 杩囨护鎺夋暟鍊煎舰寮忕殑鍙傛暟鍚?            if isinstance(param_name, str):
                try:
                    float(param_name)  # 灏濊瘯杞崲涓烘暟鍊?                    # 濡傛灉鎴愬姛杞崲锛岃鏄庢槸鏁板€硷紝璺宠繃
                    continue
                except (ValueError, TypeError):
                    # 濡傛灉杞崲澶辫触锛岃鏄庢槸鏈夋晥鐨勫弬鏁板悕
                    parameter_names.append(param_name)
            elif isinstance(param_name, (int, float)):
                # 鏁板€肩被鍨嬬殑閿紝璺宠繃
                continue
            else:
                # 鍏朵粬绫诲瀷锛岃浆鎹负瀛楃涓?                parameter_names.append(str(param_name))

    compiler = AdvancedRuleCompiler(parameter_names, fault_names=[d.get("fault_name", "") for d in rule_defs])
    compiled = compiler.compile_rules(rule_defs)
    _advanced_compiled_by_model[model_id] = compiled
    return compiled


def _backfill_history_for_detector(cmg_model: PHMModel, cmg_id_int: int, detector: AdvancedRuleDetector, *,
                                   required_params: List[str],
                                   max_frames: int, max_seconds: float,
                                   until_timestamp) -> None:
    """鎸夐渶鍥炲～鍘嗗彶锛堜粎鍦ㄩ娆℃垨鏈厖鍒嗘椂锛夈€備粠鏁版嵁搴撳彇鏈€杩戠獥鍙ｆ暟鎹紝椤哄簭鎺ㄥ叆妫€娴嬪櫒銆?""
    try:
        qs = PHMData.objects.filter(cmg__cmg_model=cmg_model)
        if until_timestamp:
            qs = qs.filter(timestamp__lt=until_timestamp)
        # 浠ユ椂闂翠紭鍏堥檺鍒?        if max_seconds and max_seconds > 0:
            from django.utils import timezone
            end = until_timestamp or timezone.now()
            start = end - timezone.timedelta(seconds=float(max_seconds))
            qs = qs.filter(timestamp__gte=start)
        qs = qs.order_by("timestamp")
        if max_frames and max_frames > 0:
            total = qs.count()
            if total > max_frames:
                qs = qs[total - max_frames: total]
        # 椤哄簭鎺ㄥ叆锛堜笉鍏冲績杩斿洖鍊硷紝浠呯敤浜庡～鍏呭巻鍙诧級
        for rec in qs:
            payload = {k: rec.data.get(k) for k in required_params}
            detector.detect(payload, rec.timestamp)
    except Exception:
        # 鍘嗗彶鍥炲～澶辫触涓嶅簲闃绘柇妫€娴?        pass


def evaluate_advanced_rules_for_data_point(cmg_data: PHMData) -> List[Dict[str, Any]]:
    """浣跨敤楂樼骇瑙勫垯妫€娴嬪櫒锛堝惈鏃跺簭鍑芥暟锛夊鍗曠偣杩涜璇勪及锛屼粎褰?IMS 寮傚父瑙﹀彂鏃惰皟鐢ㄣ€?
    瀹炵幇瑕佺偣锛?    - 妯″瀷绾х紪璇戠紦瀛橈細瑙ｆ瀽瑙勫垯锛屾彁鍙栧簭鍒椾緷璧栦笌闇€姹?    - PHM 绾ф娴嬪櫒缂撳瓨锛氱淮鎸佸巻鍙诧紝璺ㄧ偣绱Н
    - 棣栨鎴栧巻鍙蹭笉瓒虫椂锛屽熀浜?DB 鍥炲～鎵€闇€绐楀彛锛堥伩鍏嶅叏閲忕紦瀛橈級
    """
    cmg = cmg_data.cmg
    cmg_model = cmg.cmg_model
    model_id = cmg_model.id
    cmg_id_int = cmg.id

    compiled_cfg = _get_advanced_compiled_for_model(cmg_model)
    rules_cfg: List[Dict[str, Any]] = compiled_cfg.get("rules", [])
    param_reqs: Dict[str, Dict[str, Any]] = {}
    # 姹囨€绘渶澶ч渶姹?    for r in rules_cfg:
        reqs = r.get("parameter_requirements") or {}
        for p, d in reqs.items():
            cur = param_reqs.get(p) or {"max_frame_history": 0, "max_time_history": 0.0}
            cur["max_frame_history"] = max(int(cur["max_frame_history"]), int(d.get("max_frame_history") or 0))
            cur["max_time_history"] = max(float(cur["max_time_history"]), float(d.get("max_time_history") or 0.0))
            param_reqs[p] = cur

    required_params = sorted(set(compiled_cfg.get("parameter_names") or []))

    # 鍙栧緱/鍒涘缓妫€娴嬪櫒
    detector = _advanced_detector_by_cmg.get(cmg_id_int)
    if detector is None:
        detector = AdvancedRuleDetector({
            "rules": rules_cfg,
            "fault_name_map": compiled_cfg.get("fault_name_map", {}),
            "parameter_names": required_params,
        })
        _advanced_detector_by_cmg[cmg_id_int] = detector
        _advanced_warmup_done_for_cmg[cmg_id_int] = False

    # 棣栨鎴栨湭鍏呭垎锛氬洖濉巻鍙?    if not _advanced_warmup_done_for_cmg.get(cmg_id_int, False):
        max_frames = 0
        max_seconds = 0.0
        for d in param_reqs.values():
            max_frames = max(max_frames, int(d.get("max_frame_history") or 0))
            max_seconds = max(max_seconds, float(d.get("max_time_history") or 0.0))
        if max_frames > 0 or max_seconds > 0:
            _backfill_history_for_detector(
                cmg_model, cmg_id_int, detector,
                required_params=required_params,
                max_frames=max_frames,
                max_seconds=max_seconds,
                until_timestamp=cmg_data.timestamp,
            )
        _advanced_warmup_done_for_cmg[cmg_id_int] = True

    # 鏈抚妫€娴?    data_payload = {k: cmg_data.data.get(k) for k in required_params}
    results = detector.detect(data_payload, cmg_data.timestamp)

    # 杩斿洖缁撴灉浣嗕笉绔嬪嵆鍐欏叆鏁版嵁搴擄紙鐢辨壒閲忓鐞嗙粺涓€澶勭悊锛?    return results or []


def _build_parameter_to_component_map(cmg_model: PHMModel) -> Dict[str, str]:
    """鏋勫缓 鍙傛暟鍚?-> 缁勪欢鍚?鐨勬槧灏勮〃銆?""
    mapping: Dict[str, str] = {}
    for comp in ComponentDefinition.objects.filter(cmg_model=cmg_model):
        params = comp.parameters if isinstance(comp.parameters, list) else []
        for p in params:
            if isinstance(p, str) and p:
                mapping[p] = comp.component_name
    return mapping


def _infer_component_from_params(
    related_parameters: List[str], parameter_to_component: Dict[str, str]
) -> Optional[str]:
    """鏍规嵁娑夊強鐨勫弬鏁版帹鏂渶鐩稿叧鐨勭粍浠讹紙澶氭暟琛ㄥ喅锛夈€?""
    if not related_parameters:
        return None
    counter: Dict[str, int] = {}
    for p in related_parameters:
        comp = parameter_to_component.get(p)
        if not comp:
            continue
        counter[comp] = counter.get(comp, 0) + 1
    if not counter:
        return None
    return max(counter.keys(), key=counter.get)


def compute_component_health_for_model(
    cmg_model: PHMModel,
    *,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 1000,
) -> Dict[str, Any]:
    """
    璁＄畻鎸囧畾妯″瀷鐨勫悇缁勪欢鍋ュ悍搴﹀拰绯荤粺鍋ュ悍搴︺€?
    Returns:
      {
        "component_scores": { component: score (0-1), ... },
        "system_health": float,
        "details": { "num_results": int, "window": {"start":...,"end":...}}
      }
    """
    qs = RuleDetectionResult.objects.select_related("fault_definition", "data_point", "data_point__cmg").filter(
        fault_definition__cmg_model=cmg_model
    ).order_by("-created_at")
    if start_time:
        qs = qs.filter(data_point__timestamp__gte=start_time)
    if end_time:
        qs = qs.filter(data_point__timestamp__lte=end_time)
    if limit:
        qs = qs[: int(limit)]

    parameter_to_component = _build_parameter_to_component_map(cmg_model)

    # 缁勮涓?health 璁＄畻鎵€闇€鐨勮鍒欑粨鏋滄潯鐩?    rule_results: List[Dict[str, Any]] = []
    components_set = set(
        ComponentDefinition.objects.filter(cmg_model=cmg_model).values_list("component_name", flat=True)
    )

    for rr in qs:
        # 浼樺厛浣跨敤鏁呴殰瀹氫箟涓婄殑缁勪欢锛涜嫢鏃犲垯鏍规嵁鍙傛暟鎺ㄦ柇
        comp_name: Optional[str] = rr.fault_definition.component or None
        related_params: List[str] = []
        try:
            det = rr.detection_details or {}
            if isinstance(det.get("related_parameters"), list):
                related_params = [str(p) for p in det["related_parameters"]]
        except Exception:
            related_params = []

        if not comp_name:
            comp_name = _infer_component_from_params(related_params, parameter_to_component)

        if comp_name is None:
            # 鑻ヤ粛鏃犳硶纭畾锛岃烦杩囪鍏ュ仴搴凤紙涓嶅奖鍝嶅叾瀹冪粍浠讹級
            continue

        rule_results.append(
            {
                "component": comp_name,
                "is_triggered": bool(rr.is_triggered),
                "confidence_score": float(rr.confidence_score or 0.0),
                "fault_level": int(getattr(rr.fault_definition, "fault_level", 1) or 1),
                "related_parameters": related_params,
            }
        )

    # 璁＄畻姣忎釜缁勪欢鐨勫仴搴峰害
    component_scores: Dict[str, float] = {}
    for comp in components_set:
        component_scores[comp] = calculate_component_health_score(comp, rule_results, parameter_weights=None)

    # 绯荤粺鍋ュ悍涓虹粍浠跺仴搴风殑鍔犳潈骞冲潎锛堝綋鍓嶇瓑鏉冿級
    system_health = aggregate_system_health_score(component_scores, component_weights=None)

    # 绐楀彛淇℃伅
    window_info: Dict[str, Optional[str]] = {"start": start_time, "end": end_time}

    return {
        "component_scores": component_scores,
        "system_health": system_health,
        "details": {"num_results": len(rule_results), "window": window_info},
    }



