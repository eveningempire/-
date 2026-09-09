"""
瑙勫垯妫€娴嬪櫒鍙繍琛屽疄鐜?

鎻愪緵灏嗚鍒欏畾涔夌紪璇戜负鍙墽琛屽璞★紝骞跺鍗曠偣鏁版嵁鎵ц瑙勫垯璇勪及銆?

琛ㄨ揪寮忚瘎浼颁娇鐢ㄥ彈闄怉ST瑙ｉ噴鍣紝鏀寔甯歌甯冨皵/姣旇緝/绠楁湳杩愮畻鍙婂皯閲忔暟瀛﹀嚱鏁般€?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import ast
import math

from .rule_parser import RuleParser


ALLOWED_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "exp": math.exp,
}


class SafeEvaluator(ast.NodeVisitor):
    """鏋佺畝瀹夊叏琛ㄨ揪寮忔眰鍊煎櫒锛屼粎鍏佽瀹夊叏鑺傜偣銆傛敮鎸佹敞鍏ヨ嚜瀹氫箟鍑芥暟銆?""

    def __init__(self, variables: Dict[str, Any], funcs: Optional[Dict[str, Any]] = None) -> None:
        self.vars = variables
        self.funcs = dict(ALLOWED_FUNCS)
        if funcs:
            # 瑕嗙洊鎴栨墿灞曞厑璁稿嚱鏁?
            self.funcs.update(funcs)

    def visit(self, node):  # type: ignore[override]
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            # 鍙橀噺鍚嶄粠鎻愪緵鐨剉ars鑾峰彇锛岀己澶辫繑鍥瀗an
            return self.vars.get(node.id, float("nan"))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):
            val = self.visit(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +val
            if isinstance(node.op, ast.USub):
                return -val
            return not val
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)):
            left = self.visit(node.left)
            right = self.visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Mod):
                return left % right
            return left ** right
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            vals = [self.visit(v) for v in node.values]
            return all(vals) if isinstance(node.op, ast.And) else any(vals)
        if isinstance(node, ast.Compare):
            left = self.visit(node.left)
            result = True
            for op, comp in zip(node.ops, node.comparators):
                right = self.visit(comp)
                if isinstance(op, ast.Eq):
                    ok = left == right
                elif isinstance(op, ast.NotEq):
                    ok = left != right
                elif isinstance(op, ast.Gt):
                    ok = left > right
                elif isinstance(op, ast.GtE):
                    ok = left >= right
                elif isinstance(op, ast.Lt):
                    ok = left < right
                elif isinstance(op, ast.LtE):
                    ok = left <= right
                else:
                    raise ValueError("Unsupported comparator")
                if not ok:
                    result = False
                    break
                left = right
            return result
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only direct function calls are allowed")
            fname = node.func.id
            fn = self.funcs.get(fname)
            if fn is None:
                raise ValueError(f"Function not allowed: {fname}")
            args = [self.visit(a) for a in node.args]
            return fn(*args)
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def _build_vars_from_point(data_point: Dict[str, Any]) -> Dict[str, Any]:
    # 灏嗘暟鎹瓧鍏哥殑閿洿鎺ヤ綔涓哄彉閲忓悕锛涢潪鏁板€煎皾璇曡浆鎹负float
    vars_: Dict[str, Any] = {}
    for k, v in data_point.items():
        try:
            vars_[k] = float(v)
        except Exception:
            vars_[k] = v
    return vars_


@dataclass
class CompiledRule:
    rule_id: str
    fault_name: str
    fault_level: int
    component: str
    expression: str
    ast_obj: ast.AST
    related_parameters: List[str]


def compile_rules(rule_entries: List[Dict[str, Any]], parameter_names: List[str]) -> List[CompiledRule]:
    compiled: List[CompiledRule] = []
    for entry in rule_entries:
        expr = str(entry.get("ruleExpress") or entry.get("rule_expression") or "").strip()
        if not expr:
            continue
        parser = RuleParser(parameter_names=parameter_names)
        parsed = parser.parse(expr)
        if parsed is None:
            continue
        # 瑙ｆ瀽涓篈ST琛ㄨ揪寮?
        try:
            ast_obj = ast.parse(parsed["expression"], mode="eval")
        except Exception:
            # 鑻ユ棤娉曠紪璇戜负Python琛ㄨ揪寮忥紝鍒欒烦杩?
            continue
        compiled.append(
            CompiledRule(
                rule_id=str(entry.get("showId") or entry.get("rule_id") or ""),
                fault_name=str(entry.get("faultName") or entry.get("fault_name") or ""),
                fault_level=int(entry.get("faultLevel") or entry.get("fault_level") or 1),
                component=str(entry.get("component") or ""),
                expression=parsed["expression"],
                ast_obj=ast_obj,
                related_parameters=list(parsed.get("related_parameters", [])),
            )
        )
    return compiled


def evaluate_rules_on_point(data_point: Dict[str, Any], compiled_rules: List[CompiledRule]) -> List[Dict[str, Any]]:
    """瀵瑰崟鐐规暟鎹墽琛岃鍒欒瘎浼帮紝杩斿洖姣忔潯瑙勫垯缁撴灉銆?""
    from .enhanced_scoring import RuleScoringEnhancer, calculate_rule_confidence
    
    results: List[Dict[str, Any]] = []
    vars_ = _build_vars_from_point(data_point)
    
    # 鍒濆鍖栬瘎鍒嗗寮哄櫒
    scoring_enhancer = RuleScoringEnhancer()
    
    for cr in compiled_rules:
        try:
            value = SafeEvaluator(vars_).visit(cr.ast_obj)
            
            # 浣跨敤澧炲己璇勫垎鏈哄埗杞崲涓鸿繛缁垎鏁?
            continuous_score = scoring_enhancer.convert_to_continuous_score(
                value, cr.expression, data_point
            )
            
            # 璁＄畻缃俊搴?
            confidence = calculate_rule_confidence(cr.expression, data_point, value)
            
            # 搴旂敤缃俊搴﹁皟鏁?
            adjusted_score = continuous_score * confidence
            
            # 纭畾瑙﹀彂鐘舵€侊紙鍙厤缃槇鍊硷級
            is_triggered = adjusted_score > 0.5
            
        except Exception:
            is_triggered = False
            adjusted_score = 0.0
            confidence = 0.0
            continuous_score = 0.0
        
        results.append({
            "rule_id": cr.rule_id,
            "fault_name": cr.fault_name,
            "fault_level": cr.fault_level,
            "component": cr.component,
            "is_triggered": is_triggered,
            "score": float(adjusted_score),
            "confidence": float(confidence),
            "raw_score": float(continuous_score),
            "related_parameters": cr.related_parameters,
        })
    return results

"""
瑙勫垯妫€娴嬪櫒 - 澧炲己鐗?
瀹炵幇瑙勫垯妫€娴嬬殑鏍稿績閫昏緫锛屾敮鎸佸鏉傝鍒欒〃杈惧紡鍜屽仴搴峰害璁＄畻
"""

import math
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone

from .advanced_function_base import get_result, calculate_component_health_score, aggregate_system_health_score
from .advanced_rule_parser import AdvancedRuleParser, RuleCompiler

logger = logging.getLogger(__name__)


class AdvancedRuleDetector:
    """楂樼骇瑙勫垯妫€娴嬪櫒绫?- 鏀寔鏃跺簭鍒嗘瀽鍜屽仴搴峰害璁＄畻"""
    
    def __init__(self, rule_config: Dict[str, Any]):
        """
        鍒濆鍖栬鍒欐娴嬪櫒
        
        Args:
            rule_config: 瑙勫垯閰嶇疆锛屽寘鍚紪璇戝悗鐨勮鍒欏畾涔?
        """
        self.rule_config = rule_config
        self.rules = rule_config.get('rules', [])
        self.fault_name_map = rule_config.get('fault_name_map', {})
        self.parameter_names = rule_config.get('parameter_names', [])
        
        # 鍘嗗彶鏁版嵁缂撳瓨
        self.data_history = {
            "Para": {},      # 鍙傛暟鍘嗗彶鏁版嵁
            "MMM": {},       # 缁熻鍑芥暟鍘嗗彶鏁版嵁
            "Crease": {},    # 瓒嬪娍鍒嗘瀽鍘嗗彶鏁版嵁
            "Trigger": {},   # 瑙﹀彂鍣ㄧ姸鎬?
            "Fault": {},     # 鏁呴殰鐘舵€?
            "PreCond": {},   # 鍓嶇疆鏉′欢鐘舵€?
            "[]": {},        # 鎸佺画鏉′欢鐘舵€?
            "<>": {},        # 浠绘剰鏉′欢鐘舵€?
            "{}": {}         # 閮ㄥ垎鏉′欢鐘舵€?
        }
        
        # 鍒濆鍖栨暟鎹粨鏋?
        self._initialize_data_structures()
        
        logger.info(f"楂樼骇瑙勫垯妫€娴嬪櫒鍒濆鍖栧畬鎴愶紝鍔犺浇 {len(self.rules)} 鏉¤鍒?)
    
    def _initialize_data_structures(self):
        """鍒濆鍖栨娴嬫暟鎹粨鏋?""
        for rule in self.rules:
            # 鍒濆鍖栧弬鏁板巻鍙叉暟鎹?
            for param_name in rule.get('related_parameters', []):
                if param_name not in self.data_history["Para"]:
                    self.data_history["Para"][param_name] = {
                        "value": [],
                        "time": [],
                        "frameMax": 0,
                        "timeMax": 0.0
                    }
            
            # 鍒濆鍖栨晠闅滅姸鎬?
            fault_name = rule.get('fault_name', '')
            if fault_name:
                self.data_history["Fault"][fault_name] = {
                    "state": None,
                    "score": 0.0,
                    "time": 0.0
                }
            
            # 鍒濆鍖栧簭鍒楁暟鎹粨鏋?
            sequences = rule.get('sequences', {})
            for func_type, func_dict in sequences.items():
                if func_type not in self.data_history:
                    continue
                
                for func_id, (expressions, counts) in func_dict.items():
                    if func_type == "MMM":
                        self.data_history[func_type][func_id] = {
                            "convertedRule": expressions[0],
                            "frameMax": 0,
                            "timeMax": 0.0,
                            "value": [],
                            "time": []
                        }
                    elif func_type == "Crease":
                        self.data_history[func_type][func_id] = {
                            "convertedRule": expressions[0],
                            "frameMax": 0,
                            "timeMax": 0.0,
                            "value": [],
                            "time": [],
                            "prevalue": None,
                            "lastDecTime": None,
                            "lastIncTime": None
                        }
                    elif func_type == "[]":
                        self.data_history[func_type][func_id] = {
                            "convertedRule": expressions,
                            "lastTime": None,
                            "lastFalseTime": None
                        }
                    elif func_type == "<>":
                        self.data_history[func_type][func_id] = {
                            "convertedRule": expressions,
                            "lastTime": None,
                            "lastTrueTime": None
                        }
                    elif func_type == "{}":
                        self.data_history[func_type][func_id] = {
                            "convertedRule": expressions,
                            "frameMax": counts[0] if counts else 10,
                            "time": [],
                            "value": [],
                            "score": []
                        }
    
    def detect(self, data_frame: Dict[str, Any], timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        瀵规暟鎹抚杩涜瑙勫垯妫€娴?
        
        Args:
            data_frame: 鏁版嵁甯э紝鍖呭惈鍙傛暟鍚嶇О鍒板€肩殑鏄犲皠
            timestamp: 鏁版嵁鏃堕棿鎴?
            
        Returns:
            妫€娴嬬粨鏋滃垪琛紝姣忎釜缁撴灉鍖呭惈鏁呴殰淇℃伅鍜岀疆淇″害
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # 鏇存柊鍘嗗彶鏁版嵁
        self._update_historical_data(data_frame, timestamp)
        
        results = []
        
        # 鎸夎鍒欎緷璧栭『搴忔墽琛屾娴?
        rule_order = self._determine_rule_execution_order()
        
        for rule in rule_order:
            try:
                # 妫€鏌ヨ鍒欐槸鍚﹀湪绾垮惎鐢?
                if not rule.get('is_online', True):
                    continue
                
                # 妫€鏌ヨ鍒欐槸鍚﹂€傜敤浜庡綋鍓嶆暟鎹?
                if not self._is_rule_applicable(rule, data_frame):
                    continue
                
                # 鎵ц瑙勫垯妫€娴?
                result = self._evaluate_advanced_rule(rule, timestamp)
                
                if result and result.get('is_triggered'):
                    results.append(result)
                    
                    # 鏇存柊鏁呴殰鐘舵€?
                    fault_name = rule.get('fault_name')
                    if fault_name and fault_name in self.data_history["Fault"]:
                        self.data_history["Fault"][fault_name].update({
                            "state": True,
                            "score": result.get('confidence_score', 0.0),
                            "time": timestamp.timestamp()
                        })
                    
            except Exception as e:
                logger.error(f"瑙勫垯 {rule.get('rule_id')} 妫€娴嬪け璐? {e}")
                continue
        
        return results
    
    def _update_historical_data(self, data_frame: Dict[str, Any], timestamp: datetime):
        """鏇存柊鍘嗗彶鏁版嵁"""
        current_time = timestamp.timestamp()
        
        # 鍙洿鏂拌鍒欎腑娑夊強鐨勫弬鏁板巻鍙叉暟鎹?
        for param_name, value in data_frame.items():
            if param_name not in self.data_history["Para"]:
                continue
            
            try:
                numeric_value = float(value)
                self.data_history["Para"][param_name]["value"].append(numeric_value)
                self.data_history["Para"][param_name]["time"].append(current_time)
                
                # 闄愬埗鍘嗗彶鏁版嵁闀垮害锛堜繚鐣欐渶杩慛鐐癸紝榛樿100锛屽彲閰嶇疆锛?
                try:
                    from django.conf import settings as dj_settings
                    HISTORY_LIMIT = int(getattr(dj_settings, 'ADV_RULE_HISTORY_LIMIT', 100))
                except Exception:
                    HISTORY_LIMIT = 100
                if len(self.data_history["Para"][param_name]["value"]) > HISTORY_LIMIT:
                    self.data_history["Para"][param_name]["value"] = self.data_history["Para"][param_name]["value"][-HISTORY_LIMIT:]
                    self.data_history["Para"][param_name]["time"] = self.data_history["Para"][param_name]["time"][-HISTORY_LIMIT:]
                
                # 鍚屾椂鏇存柊MMM鏁版嵁
                for mmm_id in self.data_history["MMM"]:
                    if param_name in mmm_id:
                        try:
                            rule_result, _ = get_result(self.data_history, self.data_history["MMM"][mmm_id]["convertedRule"])
                            if not math.isnan(rule_result):
                                self.data_history["MMM"][mmm_id]["value"].append(rule_result)
                                self.data_history["MMM"][mmm_id]["time"].append(current_time)
                                
                                # 闄愬埗鍘嗗彶鏁版嵁闀垮害
                                if len(self.data_history["MMM"][mmm_id]["value"]) > HISTORY_LIMIT:
                                    self.data_history["MMM"][mmm_id]["value"] = self.data_history["MMM"][mmm_id]["value"][-HISTORY_LIMIT:]
                                    self.data_history["MMM"][mmm_id]["time"] = self.data_history["MMM"][mmm_id]["time"][-HISTORY_LIMIT:]
                        except:
                            pass
                
                # 鏇存柊瓒嬪娍鍒嗘瀽鏁版嵁
                for crease_id in self.data_history["Crease"]:
                    if param_name in crease_id:
                        try:
                            rule_result, _ = get_result(self.data_history, self.data_history["Crease"][crease_id]["convertedRule"])
                            if not math.isnan(rule_result):
                                if self.data_history["Crease"][crease_id]["prevalue"] is not None:
                                    self.data_history["Crease"][crease_id]["value"].append(rule_result)
                                    self.data_history["Crease"][crease_id]["time"].append(current_time)
                                    
                                    # 鏇存柊澧炲噺鏃堕棿
                                    if rule_result > self.data_history["Crease"][crease_id]["prevalue"]:
                                        self.data_history["Crease"][crease_id]["lastIncTime"] = current_time
                                    elif rule_result < self.data_history["Crease"][crease_id]["prevalue"]:
                                        self.data_history["Crease"][crease_id]["lastDecTime"] = current_time
                                
                                self.data_history["Crease"][crease_id]["prevalue"] = rule_result
                                
                                # 闄愬埗鍘嗗彶鏁版嵁闀垮害
                                if len(self.data_history["Crease"][crease_id]["value"]) > HISTORY_LIMIT:
                                    self.data_history["Crease"][crease_id]["value"] = self.data_history["Crease"][crease_id]["value"][-HISTORY_LIMIT:]
                                    self.data_history["Crease"][crease_id]["time"] = self.data_history["Crease"][crease_id]["time"][-HISTORY_LIMIT:]
                        except:
                            pass
            
            except (ValueError, TypeError):
                # 鍙瑙勫垯涓秹鍙婄殑鍙傛暟璁板綍璀﹀憡锛岄伩鍏嶅鏃犲叧鍙傛暟浜х敓澶ч噺璀﹀憡
                logger.debug(f"瑙勫垯鍙傛暟 {param_name} 鐨勫€?{value} 鏃犳硶杞崲涓烘暟鍊?)
                continue
        
        # 鏇存柊鏃跺簭鏉′欢鐘舵€?
        self.data_history["actualTime"] = current_time
    
    def _determine_rule_execution_order(self) -> List[Dict[str, Any]]:
        """纭畾瑙勫垯鎵ц椤哄簭锛岃€冭檻瑙勫垯闂翠緷璧栧叧绯?""
        # 绠€鍖栫増鏈細鎸夋晠闅滅瓑绾ф帓搴忥紝楂樼瓑绾ф晠闅滀紭鍏堟娴?
        return sorted(self.rules, key=lambda rule: rule.get('fault_level', 1), reverse=True)
    
    def _evaluate_advanced_rule(self, rule: Dict[str, Any], timestamp: datetime) -> Optional[Dict[str, Any]]:
        """鎵ц楂樼骇瑙勫垯璇勪及"""
        try:
            rule_expression = rule.get('expression', '')
            if not rule_expression:
                return None
            
            # 鍑嗗妫€娴嬫暟鎹?
            detection_data = dict(self.data_history)
            detection_data["actualTime"] = timestamp.timestamp()
            
            # 鎵ц瑙勫垯璁＄畻
            result, confidence = get_result(detection_data, eval(rule_expression))
            
            # 澶勭悊缁撴灉
            is_triggered = bool(result) if result is not None else False
            confidence_score = float(confidence) if confidence is not None else 0.0
            
            if is_triggered or confidence_score > 0.1:  # 浣庣疆淇″害涔熻褰?
                return {
                    "rule_id": rule.get('rule_id', ''),
                    "fault_name": rule.get('fault_name', ''),
                    "fault_level": rule.get('fault_level', 1),
                    "component": rule.get('component', ''),
                    "is_triggered": is_triggered,
                    "confidence_score": confidence_score,
                    "plan_description": rule.get('plan_description', ''),
                    "source": rule.get('source', 'expert'),
                    "expression": rule_expression,
                    "detection_time": timestamp.timestamp(),
                    "detection_details": {
                        "result": result,
                        "confidence": confidence,
                        "evaluation_timestamp": timestamp.isoformat()
                    },
                    "related_parameters": rule.get('related_parameters', [])
                }
        
        except Exception as e:
            logger.error(f"瑙勫垯 {rule.get('rule_id')} 楂樼骇璇勪及澶辫触: {e}")
        
        return None
    
    def _is_rule_applicable(self, rule: Dict[str, Any], data_frame: Dict[str, Any]) -> bool:
        """妫€鏌ヨ鍒欐槸鍚﹂€傜敤浜庡綋鍓嶆暟鎹?""
        related_params = rule.get('related_parameters', [])
        
        # 妫€鏌ユ墍闇€鍙傛暟鏄惁閮藉瓨鍦?
        for param in related_params:
            if param not in data_frame:
                return False
            
            # 妫€鏌ュ弬鏁板€兼槸鍚︽湁鏁?
            value = data_frame[param]
            if value is None or (isinstance(value, float) and math.isnan(value)):
                return False
        
        return True
    
    def _evaluate_rule(self, rule: Dict[str, Any], detection_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """璇勪及鍗曚釜瑙勫垯"""
        rule_expression = rule.get('expression', '')
        
        try:
            # 杩欓噷搴旇璋冪敤瑙勫垯瑙ｆ瀽鍣ㄦ潵鎵ц瑙勫垯
            # 鐢变簬鍘熷鐨刧etResult鍑芥暟闈炲父澶嶆潅锛屾垜浠疄鐜颁竴涓畝鍖栫増鏈?
            result, confidence = self._simple_rule_evaluation(rule_expression, detection_data)
            
            if result:
                return {
                    "rule_id": rule.get('rule_id', ''),
                    "fault_name": rule.get('fault_name', ''),
                    "fault_level": rule.get('fault_level', 1),
                    "component": rule.get('component', ''),
                    "is_triggered": True,
                    "confidence_score": confidence,
                    "plan_description": rule.get('plan_description', ''),
                    "source": rule.get('source', 'expert'),
                    "expression": rule_expression,
                    "detection_time": detection_data["actualTime"]
                }
        
        except Exception as e:
            logger.error(f"瑙勫垯 {rule.get('rule_id')} 璇勪及澶辫触: {e}")
        
        return None
    
    def _simple_rule_evaluation(self, expression: str, detection_data: Dict[str, Any]) -> Tuple[bool, float]:
        """
        绠€鍖栫殑瑙勫垯璇勪及
        
        杩欐槸涓€涓畝鍖栧疄鐜帮紝瀹為檯椤圭洰涓簲璇ヤ娇鐢ㄥ畬鏁寸殑瑙勫垯瑙ｆ瀽鍣?
        """
        try:
            # 鎻愬彇鍙傛暟鍊?
            param_values = {}
            for param_name, param_data in detection_data["Para"].items():
                if param_data["value"]:
                    param_values[param_name] = param_data["value"][0]
            
            # 绠€鍗曠殑琛ㄨ揪寮忚瘎浼?
            # 杩欓噷鍙鐞嗕竴浜涘熀鏈殑姣旇緝琛ㄨ揪寮?
            if ">" in expression:
                parts = expression.split(">")
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    left_val = param_values.get(left, 0)
                    try:
                        right_val = float(right)
                        result = left_val > right_val
                        # 璁＄畻妯＄硦缃俊搴?
                        confidence = min(1.0, max(0.0, (left_val - right_val) / right_val)) if right_val != 0 else 0.5
                        return result, confidence
                    except ValueError:
                        pass
            
            elif "<" in expression:
                parts = expression.split("<")
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    left_val = param_values.get(left, 0)
                    try:
                        right_val = float(right)
                        result = left_val < right_val
                        confidence = min(1.0, max(0.0, (right_val - left_val) / right_val)) if right_val != 0 else 0.5
                        return result, confidence
                    except ValueError:
                        pass
            
            # 濡傛灉鏃犳硶瑙ｆ瀽锛岃繑鍥為粯璁ゅ€?
            return False, 0.0
            
        except Exception as e:
            logger.error(f"瑙勫垯璇勪及寮傚父: {e}")
            return False, 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """鑾峰彇妫€娴嬪櫒缁熻淇℃伅"""
        return {
            "total_rules": len(self.rules),
            "parameter_count": len(self.parameter_names),
            "fault_types": len(self.fault_name_map),
            "config_type": self.rule_config.get('detect_type', 'unknown')
        }


class RuleDetectionService:
    """瑙勫垯妫€娴嬫湇鍔?""
    
    def __init__(self):
        """鍒濆鍖栬鍒欐娴嬫湇鍔?""
        self.detectors: Dict[int, RuleDetector] = {}  # cmg_model_id -> detector
        self.compilers: Dict[int, RuleCompiler] = {}  # cmg_model_id -> compiler
    
    def load_rules_for_model(self, cmg_model_id: int, rule_definitions: List[Dict[str, Any]], 
                           parameter_names: List[str] = None) -> bool:
        """
        涓篊MG妯″瀷鍔犺浇瑙勫垯
        
        Args:
            cmg_model_id: PHM妯″瀷ID
            rule_definitions: 瑙勫垯瀹氫箟鍒楄〃
            parameter_names: 鍙傛暟鍚嶇О鍒楄〃
            
        Returns:
            鏄惁鍔犺浇鎴愬姛
        """
        try:
            # 鍒涘缓缂栬瘧鍣ㄥ苟缂栬瘧瑙勫垯
            compiler = RuleCompiler(parameter_names or [])
            compiled_config = compiler.compile_rules(rule_definitions)
            
            # 鍒涘缓妫€娴嬪櫒
            detector = RuleDetector(compiled_config)
            
            # 缂撳瓨缂栬瘧鍣ㄥ拰妫€娴嬪櫒
            self.compilers[cmg_model_id] = compiler
            self.detectors[cmg_model_id] = detector
            
            logger.info(f"涓篊MG妯″瀷 {cmg_model_id} 鍔犺浇浜?{len(rule_definitions)} 鏉¤鍒?)
            return True
            
        except Exception as e:
            logger.error(f"涓篊MG妯″瀷 {cmg_model_id} 鍔犺浇瑙勫垯澶辫触: {e}")
            return False
    
    def detect_for_model(self, cmg_model_id: int, data_frame: Dict[str, Any], 
                        timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        涓烘寚瀹欳MG妯″瀷鎵ц瑙勫垯妫€娴?
        
        Args:
            cmg_model_id: PHM妯″瀷ID
            data_frame: 鏁版嵁甯?
            timestamp: 鏃堕棿鎴?
            
        Returns:
            妫€娴嬬粨鏋滃垪琛?
        """
        detector = self.detectors.get(cmg_model_id)
        if not detector:
            logger.warning(f"PHM妯″瀷 {cmg_model_id} 娌℃湁鍔犺浇瑙勫垯妫€娴嬪櫒")
            return []
        
        try:
            return detector.detect(data_frame, timestamp)
        except Exception as e:
            logger.error(f"PHM妯″瀷 {cmg_model_id} 瑙勫垯妫€娴嬪け璐? {e}")
            return []
    
    def reload_rules_for_model(self, cmg_model_id: int, rule_definitions: List[Dict[str, Any]], 
                             parameter_names: List[str] = None) -> bool:
        """閲嶆柊鍔犺浇妯″瀷鐨勮鍒?""
        return self.load_rules_for_model(cmg_model_id, rule_definitions, parameter_names)
    
    def get_model_statistics(self, cmg_model_id: int) -> Optional[Dict[str, Any]]:
        """鑾峰彇妯″瀷鐨勮鍒欑粺璁′俊鎭?""
        detector = self.detectors.get(cmg_model_id)
        if detector:
            return detector.get_statistics()
        return None


# 鍏ㄥ眬瑙勫垯妫€娴嬫湇鍔″疄渚?
rule_detection_service = RuleDetectionService()


def test_rule_detector():
    """娴嬭瘯瑙勫垯妫€娴嬪櫒"""
    # 娴嬭瘯鏁版嵁
    rule_definitions = [
        {
            "rule_id": "R001",
            "rule_expression": "娓╁害 > 80",
            "fault_name": "杩囩儹鏁呴殰",
            "fault_level": 3,
            "component": "鐢垫満",
            "is_online": True,
            "plan_description": "妫€鏌ュ喎鍗寸郴缁?,
            "source": "expert"
        }
    ]
    
    parameter_names = ["娓╁害", "鍘嬪姏", "杞€?]
    
    # 鍒涘缓鏈嶅姟骞跺姞杞借鍒?
    service = RuleDetectionService()
    success = service.load_rules_for_model(1, rule_definitions, parameter_names)
    print(f"瑙勫垯鍔犺浇鎴愬姛: {success}")
    
    # 娴嬭瘯妫€娴?
    test_data = {"娓╁害": 85.5, "鍘嬪姏": 12.3, "杞€?: 1500}
    results = service.detect_for_model(1, test_data)
    
    print(f"妫€娴嬬粨鏋? {results}")
    print(f"缁熻淇℃伅: {service.get_model_statistics(1)}")


if __name__ == "__main__":
    test_rule_detector()

