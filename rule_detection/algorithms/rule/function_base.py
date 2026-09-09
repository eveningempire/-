"""
规则检测核心函数库
从原项目的FuncBase.py迁移而来，提供规则表达式计算的基础函数
"""

import math
from typing import Dict, List, Any, Tuple, Optional, Union

_globalParas = "{{GlobalParas}}"
_eps = 1e-10
_alias = {
    "and": "_and", 
    "or": "_or", 
    "xor": "_xor", 
    "not": "_not", 
    ">=": "_ge", 
    "<=": "_le", 
    ">": "_gt", 
    "<": "_lt", 
    "==": "_eq", 
    "!=": "_neq", 
    "+": "_plus", 
    "-": "_minus", 
    "*": "_mul", 
    "/": "_div", 
    "//": "_intdiv", 
    "%": "_mod", 
    "**": "_pow", 
    "&": "_bitand", 
    "|": "_bitor", 
    "^": "_bitxor", 
    "~": "_bitnot", 
    "[]": "_allcond", 
    "<>": "_anycond", 
    "{}": "_partialcond", 
    "int": "_int", 
    "log": "_log", 
    "exp": "_exp", 
    "abs": "_abs", 
    "sin": "_sin",
    "cos": "_cos",
    "tan": "_tan",
    "asin": "_asin",
    "acos": "_acos",
    "atan": "_atan",
    "atan2": "_atan2"
}


def _prod(args: List[float]) -> float:
    """计算参数列表的乘积"""
    try:
        res = 1
        for arg in args:
            res *= arg
        return res
    except Exception:
        return float('nan')


def _mean(value_: List[float]) -> float:
    """计算平均值"""
    if value_:
        return sum(value_) / len(value_)
    else:
        return float("nan")


def score_ge(res1: float, res2: float) -> float:
    """计算大于等于比较的模糊得分"""
    if math.isnan(res1) or math.isnan(res2):
        return 0
    elif res1 >= 0 and res2 >= 0:
        return min(1, (res1 + _eps) / (res2 + _eps) / 2)
    elif res1 <= 0 and res2 <= 0:
        return min(1, (-res2 + _eps) / (-res1 + _eps) / 2)
    else:
        return float(res1 >= res2)


def _getTimeByTime(value_: List[float], time_: List[float], actualTime: float, 
                   deltaTime: float, trigTime: Optional[float] = None) -> float:
    """根据时间获取对应的时间戳"""
    if not time_:
        return float('nan')
    splitTime = actualTime - deltaTime
    idStart = 0
    idEnd = len(time_) - 1
    startTime = time_[idStart]
    endTime = time_[idEnd]
    
    if trigTime is not None and (splitTime < trigTime or endTime < trigTime):
        return float('nan')
    if startTime > splitTime:
        return float("nan")
    elif endTime <= splitTime:
        return time_[-1]
    
    while idStart + 5 < idEnd:
        idPredict = idStart + max(1, round((endTime - splitTime) / (endTime - startTime) * (idEnd - idStart)))
        if time_[idPredict] > splitTime:
            idEnd = idPredict
            endTime = time_[idEnd]
        else:
            idStart = idPredict
            startTime = time_[idStart]
    
    for idTime in reversed(range(idStart, idEnd)):
        if time_[idTime] <= splitTime:
            break
    
    if trigTime is None or time_[idTime] >= trigTime:
        return time_[idTime]
    else:
        return float('nan')


def _getValueByTime(value_: List[float], time_: List[float], actualTime: float, 
                    deltaTime: float, trigTime: Optional[float] = None) -> float:
    """根据时间获取对应的值"""
    if not time_:
        return float('nan')
    splitTime = actualTime - deltaTime
    idStart = 0
    idEnd = len(time_) - 1
    startTime = time_[idStart]
    endTime = time_[idEnd]
    
    if trigTime is not None and (splitTime < trigTime or endTime < trigTime):
        return float('nan')
    if startTime > splitTime:
        return float("nan")
    elif endTime <= splitTime:
        return value_[-1]
    
    while idStart + 5 < idEnd:
        idPredict = idStart + max(1, round((endTime - splitTime) / (endTime - startTime) * (idEnd - idStart)))
        if time_[idPredict] > splitTime:
            idEnd = idPredict
            endTime = time_[idEnd]
        else:
            idStart = idPredict
            startTime = time_[idStart]
    
    for idTime in reversed(range(idStart, idEnd)):
        if time_[idTime] <= splitTime:
            break
    
    if trigTime is None or time_[idTime] >= trigTime:
        return value_[idTime]
    else:
        return float('nan')


def _getRangeByTime(value_: List[float], time_: List[float], actualTime: float, 
                    deltaTime: float, trigTime: Optional[float] = None) -> List[float]:
    """根据时间获取时间范围内的值列表"""
    if not time_:
        return []
    splitTime = actualTime - deltaTime if trigTime is None else max(actualTime - deltaTime, trigTime)
    idStart = 0
    idEnd = len(time_) - 1
    startTime = time_[idStart]
    endTime = time_[idEnd]
    
    if splitTime > endTime:
        return []
    if startTime >= splitTime:
        return value_[:]
    
    while idStart + 5 < idEnd:
        idPredict = idStart + max(1, round((endTime - splitTime) / (endTime - startTime) * (idEnd - idStart)))
        if time_[idPredict] > splitTime:
            idEnd = idPredict
            endTime = time_[idEnd]
        else:
            idStart = idPredict
            startTime = time_[idStart]
    
    for idTime in range(idStart, idEnd):
        if time_[idTime] >= splitTime:
            break
        idTime += 1
    return value_[idTime:]


def _getTimeByFrame(value_: List[float], time_: List[float], deltaFrame: int, 
                    trigTime: Optional[float] = None) -> float:
    """根据帧数获取对应的时间戳"""
    if len(value_) < deltaFrame + 1:
        return float("nan")
    elif trigTime is None or time_[-deltaFrame - 1] >= trigTime:
        return time_[-deltaFrame - 1]
    else:
        return float("nan")


def _getValueByFrame(value_: List[float], time_: List[float], deltaFrame: int, 
                     trigTime: Optional[float] = None) -> float:
    """根据帧数获取对应的值"""
    if len(value_) < deltaFrame + 1:
        return float("nan")
    elif trigTime is None or time_[-deltaFrame - 1] >= trigTime:
        return value_[-deltaFrame - 1]
    else:
        return float("nan")


def _getRangeByFrame(value_: List[float], time_: List[float], deltaFrame: int, 
                     trigTime: Optional[float] = None) -> List[float]:
    """根据帧数获取帧范围内的值列表"""
    if trigTime is None:
        return value_[-deltaFrame - 1:]
    for frame_, timeForFrame in enumerate(time_[-deltaFrame - 1:]):
        if timeForFrame >= trigTime:
            break
        frame_ += 1
    return value_[-deltaFrame - 1:][frame_:]


class FuncBase:
    """规则函数基础类，提供所有规则表达式运算函数"""
    
    @staticmethod
    def _and(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """逻辑与运算"""
        result = True
        score = 1
        for _, arg in enumerate(args):
            try:
                res, sco = getResult(data, arg, trigTime=trigTime)
            except Exception:
                if result:
                    return None, 0
            if arg[0] == "Trigger":
                if res:
                    trigTime = data["Trigger"][f"{arg[0]}||{arg[2]}"]["trigTime"] + arg[1]
                    continue
                else:
                    return False, 0
            if res is None:
                if result:
                    result = None
                score = min(score, sco)
            elif not res:
                result = False
                score = min(score, sco)
        return result, score
    
    @staticmethod
    def _or(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """逻辑或运算"""
        result = False
        score = 0
        for _, arg in enumerate(args):
            try:
                res, sco = getResult(data, arg, trigTime=trigTime)
            except Exception:
                result = None
                continue
            if res:
                return True, 1
            elif res is None:
                result = None
            score = max(score, sco)
        return result, score
    
    @staticmethod
    def _not(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """逻辑非运算"""
        try:
            res, sco = getResult(data, args[0], trigTime=trigTime)
        except Exception:
            return None, 0
        if res is None:
            return None, 1 - max(sco, _eps)
        elif res:
            return False, 1 - max(sco, _eps)
        else:
            return True, 1
    
    @staticmethod
    def _ge(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """大于等于比较"""
        try:
            res1, _ = getResult(data, args[0], trigTime=trigTime)
            res2, _ = getResult(data, args[1], trigTime=trigTime)
        except Exception:
            return None, 0
        if math.isnan(res1) or math.isnan(res2):
            return None, 0
        else:
            return res1 >= res2, score_ge(res1, res2)
    
    @staticmethod
    def _le(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """小于等于比较"""
        try:
            res1, _ = getResult(data, args[0], trigTime=trigTime)
            res2, _ = getResult(data, args[1], trigTime=trigTime)
        except Exception:
            return None, 0
        if math.isnan(res1) or math.isnan(res2):
            return None, 0
        else:
            return res1 <= res2, score_ge(res2, res1)
    
    @staticmethod
    def _gt(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """大于比较"""
        try:
            res1, _ = getResult(data, args[0], trigTime=trigTime)
            res2, _ = getResult(data, args[1], trigTime=trigTime)
        except Exception:
            return None, 0
        if math.isnan(res1) or math.isnan(res2):
            return None, 0
        score = score_ge(res1, res2)
        if (res1 * res2) >= 0:
            if abs(res1 - res2) >= _eps:
                return res1 > res2, score * (1 - (min(abs(res1), abs(res2)) + _eps) / (2 * max(abs(res1), abs(res2)) + _eps))
            else:
                return res1 > res2, score * (abs(res1 - res2) / _eps / 2)
        else:
            return res1 > res2, score
    
    @staticmethod
    def _lt(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """小于比较"""
        try:
            res1, _ = getResult(data, args[0], trigTime=trigTime)
            res2, _ = getResult(data, args[1], trigTime=trigTime)
        except Exception:
            return None, 0
        if math.isnan(res1) or math.isnan(res2):
            return None, 0
        score = score_ge(res2, res1)
        if (res1 * res2) >= 0:
            if abs(res1 - res2) >= _eps:
                return res1 < res2, score * (1 - (min(abs(res1), abs(res2)) + _eps) / (2 * max(abs(res1), abs(res2)) + _eps))
            else:
                return res1 < res2, score * (abs(res1 - res2) / _eps / 2)
        else:
            return res1 < res2, score
    
    @staticmethod
    def _eq(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """等于比较"""
        try:
            res1, _ = getResult(data, args[0], trigTime=trigTime)
            res2, _ = getResult(data, args[1], trigTime=trigTime)
        except Exception:
            return None, 0
        if math.isnan(res1) or math.isnan(res2):
            return None, 0
        elif (res1 * res2) >= 0:
            if abs(res1 - res2) >= _eps:
                return res1 == res2, (min(abs(res1), abs(res2)) + _eps) / (2 * max(abs(res1), abs(res2)) + _eps)
            else:
                return res1 == res2, 1 - abs(res1 - res2) / _eps / 2
        else:
            return False, 1
    
    @staticmethod
    def _neq(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[Optional[bool], float]:
        """不等于比较"""
        try:
            res1, _ = getResult(data, args[0], trigTime=trigTime)
            res2, _ = getResult(data, args[1], trigTime=trigTime)
        except Exception:
            return None, 0
        if math.isnan(res1) or math.isnan(res2):
            return None, 0
        elif (res1 * res2) >= 0:
            if abs(res1 - res2) >= _eps:
                return res1 != res2, 1 - (min(abs(res1), abs(res2)) + _eps) / (2 * max(abs(res1), abs(res2)) + _eps)
            else:
                return res1 != res2, abs(res1 - res2) / _eps / 2
        else:
            return True, 1
    
    # 算术运算函数
    @staticmethod
    def _plus(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """加法运算"""
        try:
            return sum(map(lambda arg: getResult(data, arg, trigTime=trigTime)[0], args)), 0
        except Exception:
            return float('nan'), 0
    
    @staticmethod
    def _minus(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """减法运算"""
        try:
            return getResult(data, args[0])[0] - sum(map(lambda arg: getResult(data, arg, trigTime=trigTime)[0], args[1:])), 0
        except Exception:
            return float('nan'), 0
    
    @staticmethod
    def _mul(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """乘法运算"""
        try:
            return _prod(map(lambda arg: getResult(data, arg, trigTime=trigTime)[0], args)), 0
        except Exception:
            return float('nan'), 0
    
    @staticmethod
    def _div(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """除法运算"""
        try:
            return getResult(data, args[0])[0] / _prod(map(lambda arg: getResult(data, arg, trigTime=trigTime)[0], args[1:])), 0
        except Exception:
            return float('nan'), 0
    
    # 数学函数
    @staticmethod
    def _abs(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """绝对值函数"""
        try:
            res1, _ = getResult(data, args[0], trigTime=trigTime)
            return abs(res1), 0
        except Exception:
            return float('nan'), 0
    
    @staticmethod
    def _sin(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """正弦函数"""
        try:
            res1, _ = getResult(data, args[0], trigTime=trigTime)
            return math.sin(res1), 0
        except Exception:
            return float('nan'), 0
    
    @staticmethod
    def _cos(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """余弦函数"""
        try:
            res1, _ = getResult(data, args[0], trigTime=trigTime)
            return math.cos(res1), 0
        except Exception:
            return float('nan'), 0
    
    # 参数访问函数
    @staticmethod
    def Para(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """获取参数值"""
        try:
            paraData = data["Para"][args[0]]
            if args[2]:  # istime = 1 => Time Mode
                return _getValueByTime(paraData["value"], paraData["time"], 
                                     data["actualTime"], args[1], trigTime=trigTime), 0
            else:  # istime = 0 => Frame Mode
                return _getValueByFrame(paraData["value"], paraData["time"], 
                                      args[1], trigTime=trigTime), 0
        except Exception:
            return float("nan"), 0
    
    @staticmethod
    def Time(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """获取时间戳"""
        try:
            if args[0] == _globalParas:
                return data["actualTime"], 0
            paraData = data["Para"][args[0]]
            if args[2]:  # istime = 1 => Time Mode
                return _getTimeByTime(paraData["value"], paraData["time"], 
                                    data["actualTime"], args[1], trigTime=trigTime), 0
            else:  # istime = 0 => Frame Mode
                return _getTimeByFrame(paraData["value"], paraData["time"], 
                                     args[1], trigTime=trigTime), 0
        except Exception:
            return float("nan"), 0
    
    @staticmethod
    def Max(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """获取最大值"""
        try:
            paraData = data["MMM"][args[0]]
            if args[2]:  # istime = 1 => Time Mode
                return max(_getRangeByTime(paraData["value"], paraData["time"], 
                                         data["actualTime"], args[1], trigTime=trigTime)), 0
            else:  # istime = 0 => Frame Mode
                return max(_getRangeByFrame(paraData["value"], paraData["time"], 
                                          args[1], trigTime=trigTime)), 0
        except Exception:
            return float("nan"), 0
    
    @staticmethod
    def Min(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """获取最小值"""
        try:
            paraData = data["MMM"][args[0]]
            if args[2]:  # istime = 1 => Time Mode
                return min(_getRangeByTime(paraData["value"], paraData["time"], 
                                         data["actualTime"], args[1], trigTime=trigTime)), 0
            else:  # istime = 0 => Frame Mode
                return min(_getRangeByFrame(paraData["value"], paraData["time"], 
                                          args[1], trigTime=trigTime)), 0
        except Exception:
            return float("nan"), 0
    
    @staticmethod
    def Mean(data: Dict[str, Any], args: List[Any], trigTime: Optional[float] = None) -> Tuple[float, float]:
        """获取平均值"""
        try:
            paraData = data["MMM"][args[0]]
            if args[2]:  # istime = 1 => Time Mode
                return _mean(_getRangeByTime(paraData["value"], paraData["time"], 
                                           data["actualTime"], args[1], trigTime=trigTime)), 0
            else:  # istime = 0 => Frame Mode
                return _mean(_getRangeByFrame(paraData["value"], paraData["time"], 
                                            args[1], trigTime=trigTime)), 0
        except Exception:
            return float("nan"), 0


def getResult(data: Dict[str, Any], args: Union[List[Any], Any], 
              trigTime: Optional[float] = None) -> Tuple[Any, float]:
    """获取规则表达式计算结果"""
    if isinstance(args, list):
        funcname_ = _alias.get(args[0]) or args[0]
        func_ = getattr(FuncBase, funcname_)
        return func_(data, args[1:], trigTime=trigTime)
    else:
        return args, 0 if args != True else 1
