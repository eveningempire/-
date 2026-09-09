"""
高级规则函数基础库
基于旧平台功能，为CMG健康管理提供完整的规则检测函数支持

主要功能：
1. 时域统计函数（Max、Min、Mean）
2. 趋势分析函数（Increase、Decrease）
3. 时序条件函数（[]、<>、{}）
4. 触发器和前置条件函数
5. 参数访问和时间处理函数
6. 模糊逻辑置信度计算
"""

import math
import logging
from typing import Dict, List, Any, Tuple, Optional, Union
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# 全局常量
EPS = 1e-10  # 数值精度
GLOBAL_PARAS = "{{GlobalParas}}"  # 全局参数标识

# 函数别名映射
FUNCTION_ALIASES = {
    "and": "_and", "or": "_or", "xor": "_xor", "not": "_not",
    ">=": "_ge", "<=": "_le", ">": "_gt", "<": "_lt", 
    "==": "_eq", "!=": "_neq",
    "+": "_plus", "-": "_minus", "*": "_mul", "/": "_div", 
    "//": "_intdiv", "%": "_mod", "**": "_pow",
    "&": "_bitand", "|": "_bitor", "^": "_bitxor", "~": "_bitnot",
    "[]": "_allcond", "<>": "_anycond", "{}": "_partialcond",
    "int": "_int", "log": "_log", "exp": "_exp", "abs": "_abs",
    "sin": "_sin", "cos": "_cos", "tan": "_tan",
    "asin": "_asin", "acos": "_acos", "atan": "_atan", "atan2": "_atan2"
}


def score_ge(res1: float, res2: float) -> float:
    """计算大于等于运算的模糊置信度分数"""
    if math.isnan(res1) or math.isnan(res2):
        return 0.0
    elif res1 >= 0 and res2 >= 0:
        return min(1.0, (res1 + EPS) / (res2 + EPS) / 2)
    elif res1 <= 0 and res2 <= 0:
        return min(1.0, (-res2 + EPS) / (-res1 + EPS) / 2)
    else:
        return float(res1 >= res2)


def get_value_by_time(values: List[float], times: List[float], actual_time: float, 
                      delta_time: float, trigger_time: Optional[float] = None) -> float:
    """根据时间获取历史值"""
    if not times:
        return float('nan')
    
    split_time = actual_time - delta_time
    id_start = 0
    id_end = len(times) - 1
    start_time = times[id_start]
    end_time = times[id_end]
    
    # 检查触发时间约束
    if trigger_time is not None and (split_time < trigger_time or end_time < trigger_time):
        return float('nan')
    
    if start_time > split_time:
        return float('nan')
    elif end_time <= split_time:
        return values[-1]
    
    # 二分查找
    while id_start + 5 < id_end:
        id_predict = id_start + max(1, round((end_time - split_time) / (end_time - start_time) * (id_end - id_start)))
        if times[id_predict] > split_time:
            id_end = id_predict
            end_time = times[id_end]
        else:
            id_start = id_predict
            start_time = times[id_start]
    
    # 找到最接近的时间点
    for id_time in reversed(range(id_start, id_end)):
        if times[id_time] <= split_time:
            break
    
    if trigger_time is None or times[id_time] >= trigger_time:
        return values[id_time]
    else:
        return float('nan')


def get_range_by_time(values: List[float], times: List[float], actual_time: float, 
                      delta_time: float, trigger_time: Optional[float] = None) -> List[float]:
    """根据时间获取历史值范围"""
    if not times:
        return []
    
    split_time = actual_time - delta_time if trigger_time is None else max(actual_time - delta_time, trigger_time)
    id_start = 0
    id_end = len(times) - 1
    start_time = times[id_start]
    end_time = times[id_end]
    
    if split_time > end_time:
        return []
    if start_time >= split_time:
        return values[:]
    
    # 二分查找起始位置
    while id_start + 5 < id_end:
        id_predict = id_start + max(1, round((end_time - split_time) / (end_time - start_time) * (id_end - id_start)))
        if times[id_predict] > split_time:
            id_end = id_predict
            end_time = times[id_end]
        else:
            id_start = id_predict
            start_time = times[id_start]
    
    for id_time in range(id_start, id_end):
        if times[id_time] >= split_time:
            break
        id_time += 1
    
    return values[id_time:]


def get_value_by_frame(values: List[float], times: List[float], delta_frame: int, 
                       trigger_time: Optional[float] = None) -> float:
    """根据帧数获取历史值"""
    if len(values) < delta_frame + 1:
        return float('nan')
    elif trigger_time is None or times[-delta_frame - 1] >= trigger_time:
        return values[-delta_frame - 1]
    else:
        return float('nan')


def get_range_by_frame(values: List[float], times: List[float], delta_frame: int, 
                       trigger_time: Optional[float] = None) -> List[float]:
    """根据帧数获取历史值范围"""
    if trigger_time is None:
        return values[-delta_frame - 1:]
    
    for frame, time_for_frame in enumerate(times[-delta_frame - 1:]):
        if time_for_frame >= trigger_time:
            break
        frame += 1
    
    return values[-delta_frame - 1:][frame:]


class AdvancedRuleFunctions:
    """高级规则函数库"""
    
    @staticmethod
    def _and(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """逻辑与运算"""
        result = True
        score = 1.0
        
        for arg in args:
            try:
                res, sco = get_result(data, arg, trigger_time=trigger_time)
            except Exception:
                if result:
                    return None, 0.0
                continue
            
            if arg[0] == "Trigger" and res:
                trigger_time = data["Trigger"][f"{arg[0]}||{arg[2]}"]["trigTime"] + arg[1]
                continue
            elif arg[0] == "Trigger" and not res:
                return False, 0.0
            
            if res is None:
                if result:
                    result = None
                score = min(score, sco)
            elif not res:
                result = False
                score = min(score, sco)
        
        return result, score
    
    @staticmethod
    def _or(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """逻辑或运算"""
        result = False
        score = 0.0
        
        for arg in args:
            try:
                res, sco = get_result(data, arg, trigger_time=trigger_time)
            except Exception:
                result = None
                continue
            
            if res:
                return True, 1.0
            elif res is None:
                result = None
            
            score = max(score, sco)
        
        return result, score
    
    @staticmethod
    def _not(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """逻辑非运算"""
        try:
            res, sco = get_result(data, args[0], trigger_time=trigger_time)
        except Exception:
            return None, 0.0
        
        if res is None:
            return None, 1.0 - max(sco, EPS)
        elif res:
            return False, 1.0 - max(sco, EPS)
        else:
            return True, 1.0
    
    @staticmethod
    def _ge(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """大于等于比较"""
        try:
            res1, _ = get_result(data, args[0], trigger_time=trigger_time)
            res2, _ = get_result(data, args[1], trigger_time=trigger_time)
        except Exception:
            return None, 0.0
        
        if math.isnan(res1) or math.isnan(res2):
            return None, 0.0
        else:
            return res1 >= res2, score_ge(res1, res2)
    
    @staticmethod
    def _gt(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """大于比较"""
        try:
            res1, _ = get_result(data, args[0], trigger_time=trigger_time)
            res2, _ = get_result(data, args[1], trigger_time=trigger_time)
        except Exception:
            return None, 0.0
        
        if math.isnan(res1) or math.isnan(res2):
            return None, 0.0
        
        score = score_ge(res1, res2)
        if (res1 * res2) >= 0:
            if abs(res1 - res2) >= EPS:
                return res1 > res2, score * (1 - (min(abs(res1), abs(res2)) + EPS) / (2 * max(abs(res1), abs(res2)) + EPS))
            else:
                return res1 > res2, score * (abs(res1 - res2) / EPS / 2)
        else:
            return res1 > res2, score
    
    @staticmethod
    def Para(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[float, float]:
        """参数访问函数"""
        try:
            param_data = data["Para"][args[0]]
            if args[2]:  # 时间模式
                return get_value_by_time(
                    param_data["value"], param_data["time"],
                    data["actualTime"], args[1], trigger_time=trigger_time
                ), 0.0
            else:  # 帧模式
                return get_value_by_frame(
                    param_data["value"], param_data["time"],
                    args[1], trigger_time=trigger_time
                ), 0.0
        except Exception as e:
            logger.error(f"参数访问错误: {e}")
            return float('nan'), 0.0
    
    @staticmethod
    def Max(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[float, float]:
        """最大值函数"""
        try:
            param_data = data["MMM"][args[0]]
            if args[2]:  # 时间模式
                values = get_range_by_time(
                    param_data["value"], param_data["time"],
                    data["actualTime"], args[1], trigger_time=trigger_time
                )
            else:  # 帧模式
                values = get_range_by_frame(
                    param_data["value"], param_data["time"],
                    args[1], trigger_time=trigger_time
                )
            
            return max(values) if values else float('nan'), 0.0
        except Exception:
            return float('nan'), 0.0
    
    @staticmethod
    def Min(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[float, float]:
        """最小值函数"""
        try:
            param_data = data["MMM"][args[0]]
            if args[2]:  # 时间模式
                values = get_range_by_time(
                    param_data["value"], param_data["time"],
                    data["actualTime"], args[1], trigger_time=trigger_time
                )
            else:  # 帧模式
                values = get_range_by_frame(
                    param_data["value"], param_data["time"],
                    args[1], trigger_time=trigger_time
                )
            
            return min(values) if values else float('nan'), 0.0
        except Exception:
            return float('nan'), 0.0
    
    @staticmethod
    def Mean(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[float, float]:
        """均值函数"""
        try:
            param_data = data["MMM"][args[0]]
            if args[2]:  # 时间模式
                values = get_range_by_time(
                    param_data["value"], param_data["time"],
                    data["actualTime"], args[1], trigger_time=trigger_time
                )
            else:  # 帧模式
                values = get_range_by_frame(
                    param_data["value"], param_data["time"],
                    args[1], trigger_time=trigger_time
                )
            
            return sum(values) / len(values) if values else float('nan'), 0.0
        except Exception:
            return float('nan'), 0.0
    
    @staticmethod
    def Increase(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """递增趋势检测"""
        try:
            crease_data = data["Crease"][args[0]]
            if args[2]:  # 时间模式
                split_time = data["actualTime"] - args[1] if trigger_time is None else max(data["actualTime"] - args[1], trigger_time)
                
                if len(crease_data["time"]) < 2 or crease_data["time"][-2] <= split_time:
                    return None, 0.0
                elif crease_data["lastDecTime"] is None:
                    return True, 1.0
                elif crease_data["lastDecTime"] <= split_time:
                    return True, min(1.0, (data["actualTime"] - crease_data["lastDecTime"]) / args[1] / 2)
                else:
                    return False, (data["actualTime"] - crease_data["lastDecTime"]) / args[1] / 2
            else:  # 帧模式
                values = crease_data["value"][-args[1] + 1:]
                all_count = len(values)
                
                if all_count > 1:
                    scores = [score_ge(d_next, d_pre) for d_pre, d_next in zip(values[:-1], values[1:])]
                    true_count = sum([s >= 0.5 for s in scores])
                    return true_count >= all_count - 1, min(scores) if scores else 0.0
                else:
                    return None, 0.0
        except Exception:
            return None, 0.0
    
    @staticmethod
    def Decrease(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """递减趋势检测"""
        try:
            crease_data = data["Crease"][args[0]]
            if args[2]:  # 时间模式
                split_time = data["actualTime"] - args[1] if trigger_time is None else max(data["actualTime"] - args[1], trigger_time)
                
                if len(crease_data["time"]) < 2 or crease_data["time"][-2] <= split_time:
                    return None, 0.0
                elif crease_data["lastIncTime"] is None:
                    return True, 1.0
                elif crease_data["lastIncTime"] <= split_time:
                    return True, min(1.0, (data["actualTime"] - crease_data["lastIncTime"]) / args[1] / 2)
                else:
                    return False, (data["actualTime"] - crease_data["lastIncTime"]) / args[1] / 2
            else:  # 帧模式
                values = crease_data["value"][-args[1] + 1:]
                all_count = len(values)
                
                if all_count > 1:
                    scores = [score_ge(d_pre, d_next) for d_pre, d_next in zip(values[:-1], values[1:])]
                    true_count = sum([s >= 0.5 for s in scores])
                    return true_count >= all_count - 1, min(scores) if scores else 0.0
                else:
                    return None, 0.0
        except Exception:
            return None, 0.0
    
    @staticmethod
    def _allcond(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """持续条件检测 []"""
        try:
            all_cond_name, t = args
            last_false_time = data["[]"][all_cond_name]["lastFalseTime"]
            last_time = data["[]"][all_cond_name]["lastTime"]
            
            if (trigger_time is not None and last_time < trigger_time) or data["actualTime"] - last_time > t:
                return None, 0.0
            elif last_false_time is None or data["actualTime"] - last_false_time > t:
                return True, min((data["actualTime"] - last_false_time) / t / 2, 1.0)
            else:
                return False, (data["actualTime"] - last_false_time) / t / 2
        except Exception:
            return None, 0.0
    
    @staticmethod
    def _anycond(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """任意条件检测 <>"""
        try:
            any_cond_name, t = args
            last_true_time = data["<>"][any_cond_name]["lastTrueTime"]
            last_time = data["<>"][any_cond_name]["lastTime"]
            
            if (trigger_time is not None and last_time < trigger_time) or data["actualTime"] - last_time > t:
                return None, 0.0
            elif data["actualTime"] - last_true_time < t:
                return True, min((data["actualTime"] - last_true_time) / t / 2, 1.0)
            else:
                return False, t / (data["actualTime"] - last_true_time) / 2
        except Exception:
            return None, 0.0
    
    @staticmethod
    def _partialcond(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """部分条件检测 {}"""
        try:
            partial_cond_name, m, n = args
            values = data["{}"][partial_cond_name]["value"][-m:]
            scores = data["{}"][partial_cond_name]["score"][-m:]
            times = data["{}"][partial_cond_name]["time"][-m:]
            start_id = 0
            
            if trigger_time is not None:
                for t in times:
                    if t < trigger_time:
                        start_id += 1
                    else:
                        break
            
            values = values[start_id:]
            scores = scores[start_id:]
            
            if len(values) < n:
                return False, 0.0
            else:
                true_count = sum(values)
                if true_count >= n:
                    return True, sorted(scores)[-min(m, len(scores))]
                else:
                    return False, sorted(scores)[-min(m, len(scores))] if scores else 0.0
        except Exception:
            return None, 0.0
    
    @staticmethod
    def PreCond(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """前置条件函数"""
        try:
            if ((trigger_time is None or data["PreCond"][args[0]]["validedTime"] > trigger_time) and
                data["actualTime"] > data["PreCond"][args[0]]["validedTime"] + args[1]):
                res, sco = get_result(data, args[2])
                return res, sco / 2 + 0.25
            else:
                return False, 0.25 * (data["actualTime"] - data["PreCond"][args[0]]["validedTime"]) / args[1]
        except Exception:
            return None, 0.0
    
    @staticmethod
    def Trigger(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """触发器函数"""
        try:
            trig_time = data["Trigger"][f"{args[0]}||{args[2]}"]["trigTime"]
            if trig_time == -1:
                return False, 0.0
            elif trigger_time is None or trigger_time < trig_time:
                if trig_time + args[1] <= data["actualTime"]:
                    return True, min(1.0, (data["actualTime"] - trig_time) / args[1] / 2)
                else:
                    return False, (data["actualTime"] - trig_time) / args[1] / 2
            else:
                return None, 0.0
        except Exception:
            return None, 0.0
    
    @staticmethod
    def Fault(data: Dict[str, Any], args: List[Any], trigger_time: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """故障状态函数"""
        try:
            fault_info = data["Fault"][f"{args[0]},{args[1]}"]
            if trigger_time is None or trigger_time < fault_info["time"]:
                return fault_info["state"], fault_info["score"]
            else:
                return None, 0.0
        except Exception:
            return None, 0.0


def get_result(data: Dict[str, Any], args: Any, trigger_time: Optional[float] = None) -> Tuple[Any, float]:
    """
    规则结果计算入口函数
    
    Args:
        data: 检测数据字典
        args: 参数列表或常量值
        trigger_time: 触发时间
        
    Returns:
        (结果值, 置信度分数)
    """
    if isinstance(args, list):
        func_name = FUNCTION_ALIASES.get(args[0]) or args[0]
        func = getattr(AdvancedRuleFunctions, func_name, None)
        if func:
            return func(data, args[1:], trigger_time=trigger_time)
        else:
            logger.error(f"未知函数: {args[0]}")
            return None, 0.0
    else:
        # 常量值
        return args, 1.0 if args is True else 0.0


def calculate_component_health_score(component_name: str, rule_results: List[Dict[str, Any]], 
                                   parameter_weights: Optional[Dict[str, float]] = None) -> float:
    """
    计算部件健康度分数 - 基于异常程度的连续健康分数
    
    Args:
        component_name: 部件名称
        rule_results: 规则检测结果列表
        parameter_weights: 参数权重字典
        
    Returns:
        部件健康度分数 (0-1)，1表示完全健康，0表示完全不健康
    """
    import math
    
    if not rule_results:
        return 1.0  # 无检测结果时认为健康
    
    # 筛选相关的规则结果
    component_results = [r for r in rule_results if r.get('component') == component_name]
    
    if not component_results:
        return 1.0  # 无相关结果时认为健康
    
    # 计算加权健康度分数
    total_weight = 0.0
    weighted_health = 0.0
    
    for result in component_results:
        # 获取置信度分数
        confidence = result.get('confidence_score', 0.0)
        fault_level = result.get('fault_level', 1)
        
        # 计算异常程度：结合置信度和故障等级
        # 置信度越高，异常程度越严重
        # 故障等级越高，异常程度越严重
        anomaly_intensity = confidence * min(fault_level / 5.0, 1.0)
        
        # 使用指数衰减函数计算健康度
        # 异常程度越高，健康度越低
        # 异常程度为0时，健康度为1
        # 异常程度为1时，健康度接近0.1（保留最小值）
        decay_factor = 2.5  # 可调整的衰减因子，控制健康度下降的速度
        health_score = math.exp(-anomaly_intensity * decay_factor)
        
        # 确保健康度在合理范围内 [0.1, 1.0]
        health_score = max(0.1, min(1.0, health_score))
        
        # 获取参数权重
        related_params = result.get('related_parameters', [])
        param_weight = 1.0
        if parameter_weights:
            param_weight = sum(parameter_weights.get(param, 1.0) for param in related_params) / max(len(related_params), 1)
        
        weighted_health += health_score * param_weight
        total_weight += param_weight
    
    if total_weight > 0:
        return weighted_health / total_weight
    else:
        return 1.0


def aggregate_system_health_score(component_scores: Dict[str, float], 
                                component_weights: Optional[Dict[str, float]] = None) -> float:
    """
    聚合系统级健康度分数
    
    Args:
        component_scores: 各部件健康度分数字典
        component_weights: 部件权重字典
        
    Returns:
        系统健康度分数 (0-1)
    """
    if not component_scores:
        return 1.0
    
    total_weight = 0.0
    weighted_health = 0.0
    
    for component, score in component_scores.items():
        weight = component_weights.get(component, 1.0) if component_weights else 1.0
        weighted_health += score * weight
        total_weight += weight
    
    return weighted_health / total_weight if total_weight > 0 else 1.0


def test_health_score_calculation():
    """
    测试健康分数计算逻辑
    """
    import math
    
    # 测试数据
    test_cases = [
        # (置信度, 故障等级, 期望健康度范围)
        (0.0, 1, (0.95, 1.0)),      # 无异常，应该接近1
        (0.1, 1, (0.8, 0.9)),       # 轻微异常
        (0.3, 1, (0.5, 0.7)),       # 中等异常
        (0.5, 1, (0.3, 0.5)),       # 较重异常
        (0.7, 1, (0.15, 0.3)),      # 严重异常
        (0.9, 1, (0.1, 0.2)),       # 非常严重异常
        (1.0, 1, (0.08, 0.15)),     # 最严重异常
        (0.5, 3, (0.2, 0.4)),       # 高故障等级
        (0.5, 5, (0.1, 0.3)),       # 最高故障等级
    ]
    
    print("健康分数计算测试:")
    print("置信度 | 故障等级 | 异常强度 | 健康分数")
    print("-" * 40)
    
    for confidence, fault_level, expected_range in test_cases:
        anomaly_intensity = confidence * min(fault_level / 5.0, 1.0)
        decay_factor = 2.5
        health_score = math.exp(-anomaly_intensity * decay_factor)
        health_score = max(0.1, min(1.0, health_score))
        
        print(f"{confidence:6.1f} | {fault_level:8d} | {anomaly_intensity:8.3f} | {health_score:8.3f}")
        
        # 验证结果是否在期望范围内
        if expected_range[0] <= health_score <= expected_range[1]:
            print("  ✓ 通过")
        else:
            print(f"  ✗ 失败 (期望: {expected_range[0]:.3f}-{expected_range[1]:.3f})")
    
    print("\n健康分数特性:")
    print("- 置信度越高，健康度越低")
    print("- 故障等级越高，健康度越低")
    print("- 提供0.1-1.0之间的连续值")
    print("- 避免了二值化问题")


if __name__ == "__main__":
    test_health_score_calculation()
