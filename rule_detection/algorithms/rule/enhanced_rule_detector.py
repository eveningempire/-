"""
增强版规则检测器
支持高级统计函数和区间数据缓存
"""

import math
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from collections import deque
from dataclasses import dataclass, field

from .enhanced_rule_parser import EnhancedRuleParser, EnhancedParseResult

logger = logging.getLogger(__name__)


@dataclass
class DataPoint:
    """数据点"""
    value: float
    timestamp: float
    frame_index: int


@dataclass
class WindowBuffer:
    """窗口缓冲区"""
    param_name: str
    max_window_size: int
    data_points: deque = field(default_factory=deque)
    
    def add_data_point(self, value: float, timestamp: float, frame_index: int):
        """添加数据点"""
        data_point = DataPoint(value, timestamp, frame_index)
        self.data_points.append(data_point)
        
        # 保持窗口大小
        while len(self.data_points) > self.max_window_size:
            self.data_points.popleft()
    
    def get_values(self, window_size: Optional[int] = None) -> List[float]:
        """获取指定窗口大小的数值列表"""
        if window_size is None:
            window_size = len(self.data_points)
        
        if window_size > len(self.data_points):
            return []
        
        return [dp.value for dp in list(self.data_points)[-window_size:]]
    
    def get_timestamps(self, window_size: Optional[int] = None) -> List[float]:
        """获取指定窗口大小的时间戳列表"""
        if window_size is None:
            window_size = len(self.data_points)
        
        if window_size > len(self.data_points):
            return []
        
        return [dp.timestamp for dp in list(self.data_points)[-window_size:]]
    
    def get_frame_indices(self, window_size: Optional[int] = None) -> List[int]:
        """获取指定窗口大小的帧索引列表"""
        if window_size is None:
            window_size = len(self.data_points)
        
        if window_size > len(self.data_points):
            return []
        
        return [dp.frame_index for dp in list(self.data_points)[-window_size:]]


class AdvancedStatisticalFunctions:
    """高级统计函数计算器"""
    
    @staticmethod
    def mean(values: List[float]) -> float:
        """计算均值"""
        if not values:
            return float('nan')
        return np.mean(values)
    
    @staticmethod
    def std(values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return float('nan')
        return np.std(values, ddof=1)
    
    @staticmethod
    def var(values: List[float]) -> float:
        """计算方差"""
        if len(values) < 2:
            return float('nan')
        return np.var(values, ddof=1)
    
    @staticmethod
    def mad(values: List[float]) -> float:
        """计算平均绝对偏差"""
        if not values:
            return float('nan')
        median = np.median(values)
        return np.mean(np.abs(np.array(values) - median))
    
    @staticmethod
    def rms(values: List[float]) -> float:
        """计算均方根"""
        if not values:
            return float('nan')
        return np.sqrt(np.mean(np.array(values) ** 2))
    
    @staticmethod
    def max(values: List[float]) -> float:
        """计算最大值"""
        if not values:
            return float('nan')
        return np.max(values)
    
    @staticmethod
    def min(values: List[float]) -> float:
        """计算最小值"""
        if not values:
            return float('nan')
        return np.min(values)
    
    @staticmethod
    def range(values: List[float]) -> float:
        """计算范围（最大值-最小值）"""
        if len(values) < 2:
            return float('nan')
        return np.max(values) - np.min(values)
    
    @staticmethod
    def slope(values: List[float], timestamps: List[float]) -> float:
        """计算线性趋势斜率"""
        if len(values) < 2 or len(timestamps) < 2:
            return float('nan')
        
        # 使用最小二乘法计算斜率
        x = np.array(timestamps)
        y = np.array(values)
        
        # 标准化时间戳（避免数值过大）
        x_normalized = x - x[0]
        
        # 计算斜率
        slope, _ = np.polyfit(x_normalized, y, 1)
        return slope
    
    @staticmethod
    def diffmean(values: List[float]) -> float:
        """计算差分均值"""
        if len(values) < 2:
            return float('nan')
        
        diffs = np.diff(values)
        return np.mean(diffs)
    
    @staticmethod
    def diffstd(values: List[float]) -> float:
        """计算差分标准差"""
        if len(values) < 3:
            return float('nan')
        
        diffs = np.diff(values)
        return np.std(diffs, ddof=1)
    
    @staticmethod
    def ma(values: List[float], window_size: int) -> float:
        """计算移动平均"""
        if len(values) < window_size:
            return float('nan')
        
        return np.mean(values[-window_size:])
    
    @staticmethod
    def ma_diff(values: List[float], window_size: int) -> float:
        """计算移动差分"""
        if len(values) < window_size + 1:
            return float('nan')
        
        recent_values = values[-window_size-1:]
        diffs = np.diff(recent_values)
        return np.mean(diffs)
    
    @staticmethod
    def autocorr(values: List[float], k: int) -> float:
        """计算自相关系数"""
        if len(values) < k + 1:
            return float('nan')
        
        values_array = np.array(values)
        mean_val = np.mean(values_array)
        
        # 计算滞后k的自相关系数
        numerator = 0
        denominator = 0
        
        for i in range(len(values_array) - k):
            numerator += (values_array[i] - mean_val) * (values_array[i + k] - mean_val)
            denominator += (values_array[i] - mean_val) ** 2
        
        if denominator == 0:
            return float('nan')
        
        return numerator / denominator
    
    @staticmethod
    def rollstd(values: List[float], window_size: int) -> float:
        """计算滚动标准差"""
        if len(values) < window_size:
            return float('nan')
        
        recent_values = values[-window_size:]
        return np.std(recent_values, ddof=1)


class EnhancedRuleDetector:
    """增强版规则检测器 - 支持高级统计函数和区间检测"""
    
    def __init__(self, rule_config: Dict[str, Any]):
        """
        初始化增强规则检测器
        
        Args:
            rule_config: 规则配置，包含编译后的规则定义
        """
        self.rule_config = rule_config
        self.rules = rule_config.get('rules', [])
        self.fault_name_map = rule_config.get('fault_name_map', {})
        self.parameter_names = rule_config.get('parameter_names', [])
        
        # 参数窗口缓冲区
        self.parameter_buffers: Dict[str, WindowBuffer] = {}
        
        # 当前数据
        self.current_data: Dict[str, Any] = {}
        
        # 高级统计函数计算器
        self.stats_calculator = AdvancedStatisticalFunctions()
        
        # 历史数据缓存（兼容原有结构）
        self.data_history = {
            "Para": {},      # 参数历史数据
            "MMM": {},       # 统计函数历史数据
            "Crease": {},    # 趋势分析历史数据
            "Trigger": {},   # 触发器状态
            "Fault": {},     # 故障状态
            "PreCond": {},   # 前置条件状态
            "[]": {},        # 持续条件状态
            "<>": {},        # 任意条件状态
            "{}": {}         # 部分条件状态
        }
        
        # 初始化数据结构
        self._initialize_data_structures()
        
        logger.info(f"增强规则检测器初始化完成，加载 {len(self.rules)} 条规则")
    
    def _initialize_data_structures(self):
        """初始化检测数据结构"""
        # 分析所有规则的参数需求
        all_parameters = set()
        window_requirements = {}
        
        for rule in self.rules:
            # 收集相关参数
            related_params = rule.get('related_parameters', [])
            all_parameters.update(related_params)
            
            # 分析窗口需求
            parse_result = rule.get('parse_result')
            if parse_result and hasattr(parse_result, 'window_requirements'):
                for param_name, func_requirements in parse_result.window_requirements.items():
                    if param_name not in window_requirements:
                        window_requirements[param_name] = {}
                    
                    for func_name, window_size in func_requirements.items():
                        if func_name not in window_requirements[param_name]:
                            window_requirements[param_name][func_name] = window_size
                        else:
                            window_requirements[param_name][func_name] = max(
                                window_requirements[param_name][func_name],
                                window_size
                            )
        
        # 初始化参数缓冲区
        for param_name in all_parameters:
            # 确定最大窗口大小
            max_window = 100  # 默认值
            if param_name in window_requirements:
                max_window = max(window_requirements[param_name].values()) if window_requirements[param_name] else 100
                max_window = max(max_window, 100)  # 至少保留100个数据点
            
            self.parameter_buffers[param_name] = WindowBuffer(param_name, max_window)
            
            # 初始化原有数据结构
            if param_name not in self.data_history["Para"]:
                self.data_history["Para"][param_name] = {
                    "value": [],
                    "time": [],
                    "frameMax": 0,
                    "timeMax": 0.0
                }
        
        # 初始化其他数据结构
        for rule in self.rules:
            # 初始化故障状态
            fault_name = rule.get('fault_name', '')
            if fault_name:
                self.data_history["Fault"][fault_name] = {
                    "state": None,
                    "score": 0.0,
                    "time": 0.0
                }
            
            # 初始化序列数据结构
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
    
    def update_data(self, data_frame: Dict[str, Any], timestamp: Optional[datetime] = None, frame_index: Optional[int] = None):
        """
        更新数据
        
        Args:
            data_frame: 数据帧，包含参数名称到值的映射
            timestamp: 数据时间戳
            frame_index: 帧索引
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        if frame_index is None:
            # 如果没有提供帧索引，使用时间戳作为索引
            frame_index = int(timestamp.timestamp() * 1000)
        
        current_time = timestamp.timestamp()
        
        # 更新当前数据
        self.current_data = data_frame.copy()
        
        # 只更新规则中涉及的参数缓冲区
        for param_name, value in data_frame.items():
            # 确保param_name是字符串且不是数值
            if not isinstance(param_name, str):
                continue
            
            # 跳过数值形式的参数名（这些可能是解析错误）
            try:
                float(param_name)
                logger.debug(f"跳过数值形式的参数名: {param_name}")
                continue
            except (ValueError, TypeError):
                pass
            
            if param_name not in self.parameter_buffers:
                continue
            
            try:
                numeric_value = float(value)
                if not math.isnan(numeric_value):
                    # 更新增强缓冲区
                    self.parameter_buffers[param_name].add_data_point(
                        numeric_value, current_time, frame_index
                    )
                    
                    # 同时更新原有数据结构（保持兼容性）
                    self.data_history["Para"][param_name]["value"].append(numeric_value)
                    self.data_history["Para"][param_name]["time"].append(current_time)
                    
                    # 限制历史数据长度
                    try:
                        from django.conf import settings as dj_settings
                        HISTORY_LIMIT = int(getattr(dj_settings, 'ADV_RULE_HISTORY_LIMIT', 100))
                    except Exception:
                        HISTORY_LIMIT = 100
                    
                    if len(self.data_history["Para"][param_name]["value"]) > HISTORY_LIMIT:
                        self.data_history["Para"][param_name]["value"] = self.data_history["Para"][param_name]["value"][-HISTORY_LIMIT:]
                        self.data_history["Para"][param_name]["time"] = self.data_history["Para"][param_name]["time"][-HISTORY_LIMIT:]
            
            except (ValueError, TypeError):
                # 只对规则中涉及的参数记录警告，避免对无关参数产生大量警告
                logger.debug(f"规则参数 {param_name} 的值 {value} 无法转换为数值")
                continue
        
        # 更新时序条件状态
        self.data_history["actualTime"] = current_time
    
    def evaluate_level_function(self, param_name: str, median: float, mad: float) -> float:
        """
        评估level函数
        
        Args:
            param_name: 参数名称
            median: 中位数
            mad: 平均绝对偏差
            
        Returns:
            level函数计算结果
        """
        try:
            # 获取参数当前值
            if param_name not in self.current_data:
                logger.debug(f"参数 {param_name} 在当前数据中不存在")
                return float('nan')
            
            current_value = self.current_data[param_name]
            
            # 转换为数值
            try:
                x = float(current_value)
            except (ValueError, TypeError):
                logger.debug(f"规则参数 {param_name} 的值 {current_value} 无法转换为数值")
                return float('nan')
            
            # 计算level值
            m = float(median)
            md = float(mad) if float(mad) != 0 else 1e-9
            level_value = abs(x - m) / md
            
            return level_value
            
        except Exception as e:
            logger.error(f"计算level函数时出错: {e}")
            return float('nan')
    
    def evaluate_advanced_function(self, func_name: str, param_name: str, window_size: Optional[int] = None) -> float:
        """
        评估高级统计函数
        
        Args:
            func_name: 函数名称
            param_name: 参数名称
            window_size: 窗口大小（可选）
            
        Returns:
            函数计算结果
        """
        logger.debug(f"调用高级函数: {func_name}({param_name}, {window_size})")
        
        if param_name not in self.parameter_buffers:
            logger.debug(f"参数 {param_name} 不在缓冲区中，可用参数: {list(self.parameter_buffers.keys())}")
            return float('nan')
        
        buffer = self.parameter_buffers[param_name]
        values = buffer.get_values(window_size)
        timestamps = buffer.get_timestamps(window_size)
        
        if not values:
            return float('nan')
        
        try:
            if func_name == 'mean':
                return self.stats_calculator.mean(values)
            elif func_name == 'std':
                return self.stats_calculator.std(values)
            elif func_name == 'var':
                return self.stats_calculator.var(values)
            elif func_name == 'mad':
                return self.stats_calculator.mad(values)
            elif func_name == 'rms':
                return self.stats_calculator.rms(values)
            elif func_name == 'max':
                return self.stats_calculator.max(values)
            elif func_name == 'min':
                return self.stats_calculator.min(values)
            elif func_name == 'range':
                return self.stats_calculator.range(values)
            elif func_name == 'slope':
                return self.stats_calculator.slope(values, timestamps)
            elif func_name == 'diffmean':
                return self.stats_calculator.diffmean(values)
            elif func_name == 'diffstd':
                return self.stats_calculator.diffstd(values)
            elif func_name == 'ma':
                if window_size is None:
                    window_size = 10  # 默认窗口大小
                return self.stats_calculator.ma(values, window_size)
            elif func_name == 'ma_diff':
                if window_size is None:
                    window_size = 10  # 默认窗口大小
                return self.stats_calculator.ma_diff(values, window_size)
            elif func_name == 'autocorr':
                if window_size is None:
                    window_size = 1  # 默认滞后1
                return self.stats_calculator.autocorr(values, window_size)
            elif func_name == 'rollstd':
                if window_size is None:
                    window_size = 10  # 默认窗口大小
                return self.stats_calculator.rollstd(values, window_size)
            else:
                logger.warning(f"未知的高级函数: {func_name}")
                return float('nan')
        
        except Exception as e:
            logger.error(f"计算函数 {func_name} 时出错: {e}")
            return float('nan')
    
    def detect(self, data_frame: Dict[str, Any], timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        对数据帧进行规则检测
        
        Args:
            data_frame: 数据帧，包含参数名称到值的映射
            timestamp: 数据时间戳
            
        Returns:
            检测结果列表，每个结果包含故障信息和置信度
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # 更新数据
        self.update_data(data_frame, timestamp)
        
        results = []
        
        # 按规则依赖顺序执行检测
        rule_order = self._determine_rule_execution_order()
        
        logger.debug(f"开始检测 {len(rule_order)} 条规则")
        logger.debug(f"当前数据帧参数: {list(data_frame.keys())}")
        logger.debug(f"当前数据帧值: {data_frame}")
        
        for rule in rule_order:
            try:
                rule_id = rule.get('rule_id', 'unknown')
                logger.debug(f"检测规则: {rule_id}")
                
                # 检查规则是否在线启用
                if not rule.get('is_online', True):
                    logger.debug(f"规则 {rule_id} 未在线启用，跳过")
                    continue
                
                # 检查规则是否适用于当前数据
                if not self._is_rule_applicable(rule, data_frame):
                    logger.debug(f"规则 {rule_id} 不适用于当前数据，跳过")
                    continue
                
                logger.debug(f"规则 {rule_id} 开始评估")
                
                # 执行规则检测（无论是否触发，一律返回结果，避免被误判为“未执行”）
                result = self._evaluate_enhanced_rule(rule, timestamp)

                if result is not None:
                    if result.get('is_triggered'):
                        logger.debug(f"规则 {rule_id} 触发，置信度: {result.get('confidence_score')}")
                        # 更新故障状态
                        fault_name = rule.get('fault_name')
                        if fault_name and fault_name in self.data_history["Fault"]:
                            self.data_history["Fault"][fault_name].update({
                                "state": True,
                                "score": result.get('confidence_score', 0.0),
                                "time": timestamp.timestamp()
                            })
                    else:
                        logger.debug(f"规则 {rule_id} 已评估但未触发，置信度: {result.get('confidence_score')}")

                    results.append(result)
                else:
                    logger.debug(f"规则 {rule_id} 评估无结果（可能表达式为空或计算失败）")
                    
            except Exception as e:
                logger.error(f"规则 {rule.get('rule_id')} 检测失败: {e}")
                continue
        
        return results
    
    def _evaluate_enhanced_rule(self, rule: Dict[str, Any], timestamp: datetime) -> Optional[Dict[str, Any]]:
        """执行增强规则评估"""
        try:
            rule_expression = rule.get('expression', '')
            rule_id = rule.get('rule_id', 'unknown')
            
            if not rule_expression:
                logger.debug(f"规则 {rule_id} 表达式为空")
                return None
            
            logger.debug(f"规则 {rule_id} 表达式: {rule_expression}")
        
            # 解析表达式中的高级函数调用
            parsed_expression = self._parse_advanced_functions_in_expression(rule_expression)
            logger.debug(f"规则 {rule_id} 解析后表达式: {parsed_expression}")
            logger.debug(f"规则 {rule_id} 当前数据: {self.current_data}")
            logger.debug(f"规则 {rule_id} 相关参数: {rule.get('related_parameters', [])}")
            
            # 准备检测数据
            detection_data = dict(self.data_history)
            detection_data["actualTime"] = timestamp.timestamp()
            
            # 执行规则计算
            result = self._evaluate_expression(parsed_expression)
            logger.debug(f"规则 {rule_id} 计算结果: {result}")
            
            # 处理结果 - 改进置信度计算
            is_triggered = bool(result) if result is not None else False
            
            # 计算更连续的置信度分数
            confidence_score = self._calculate_confidence_score(result, rule_expression)
            
            logger.debug(f"规则 {rule_id} 触发状态: {is_triggered}, 置信度: {confidence_score}")
            
            # 无论是否触发都返回结果
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
                    "confidence": confidence_score,
                    "evaluation_timestamp": timestamp.isoformat()
                },
                "related_parameters": rule.get('related_parameters', [])
            }
        
        except Exception as e:
            logger.error(f"规则 {rule.get('rule_id')} 增强评估失败: {e}")
        
        return None
    
    def _parse_advanced_functions_in_expression(self, expression: str) -> str:
        """解析表达式中的高级函数调用"""
        # 解析器已经将高级函数转换为正确的格式
        # 这里不需要额外处理，直接返回表达式
        return expression
    
    def _calculate_confidence_score(self, result: Any, rule_expression: str) -> float:
        """
        计算置信度分数，提供0-1之间的连续值
        
        Args:
            result: 规则计算结果
            rule_expression: 规则表达式
            
        Returns:
            置信度分数 (0.0 - 1.0)
        """
        try:
            # 🔧 使用改进的评分机制，参考MSFG的成功修复经验
            from .improved_scoring import ImprovedRuleScoring
            
            scoring_engine = ImprovedRuleScoring()
            
            # 使用当前数据计算连续分数
            score = scoring_engine.calculate_rule_score(result, rule_expression, self.current_data)
            
            return score
            
        except Exception as e:
            logger.debug(f"置信度计算失败: {e}")
            # 回退到简单的布尔评分
            if result is None:
                return 0.0
            elif isinstance(result, bool):
                return 0.7 if result else 0.0  # 避免过度惩罚
            else:
                return 0.5
    
    def _evaluate_expression(self, expression: str) -> Any:
        """评估表达式"""
        try:
            # 创建安全的评估环境，包含高级统计函数和当前参数值
            safe_globals = {
                'self': self,
                'math': math,
                'np': np,
                'True': True,
                'False': False,
                'None': None,
                # 🔧 修复：使用更健壮的lambda函数定义，支持可变参数
                'mean': lambda param_name, *args: self.evaluate_advanced_function('mean', param_name),
                'std': lambda param_name, *args: self.evaluate_advanced_function('std', param_name),
                'var': lambda param_name, *args: self.evaluate_advanced_function('var', param_name),
                'mad': lambda param_name, *args: self.evaluate_advanced_function('mad', param_name),
                'rms': lambda param_name, *args: self.evaluate_advanced_function('rms', param_name),
                'max': lambda param_name, *args: self.evaluate_advanced_function('max', param_name),
                'min': lambda param_name, *args: self.evaluate_advanced_function('min', param_name),
                'range': lambda param_name, *args: self.evaluate_advanced_function('range', param_name),
                'slope': lambda param_name, window=None, *args: self.evaluate_advanced_function('slope', param_name, window),
                'diffmean': lambda param_name, window=None, *args: self.evaluate_advanced_function('diffmean', param_name, window),
                'diffstd': lambda param_name, window=None, *args: self.evaluate_advanced_function('diffstd', param_name, window),
                'ma': lambda param_name, window=None, *args: self.evaluate_advanced_function('ma', param_name, window),
                'ma_diff': lambda param_name, window=None, *args: self.evaluate_advanced_function('ma_diff', param_name, window),
                'autocorr': lambda param_name, k=1, *args: self.evaluate_advanced_function('autocorr', param_name, k),
                'rollstd': lambda param_name, window=None, *args: self.evaluate_advanced_function('rollstd', param_name, window),
                # 添加level函数支持
                'level': lambda param_name, median=None, mad=None, *args: self.evaluate_level_function(param_name, median or 0, mad or 1),
            }
            
            # 创建局部变量环境，包含参数名到值的映射
            safe_locals = {}
            
            # 添加参数名到值的映射，确保参数名作为字符串被正确处理
            for param_name, value in self.current_data.items():
                if isinstance(param_name, str):
                    safe_locals[param_name] = value
            
            return eval(expression, safe_globals, safe_locals)
        
        except Exception as e:
            logger.error(f"表达式评估失败: {e}")
            return None
    
    def _determine_rule_execution_order(self) -> List[Dict[str, Any]]:
        """确定规则执行顺序，考虑规则间依赖关系"""
        # 简化版本：按故障等级排序，高等级故障优先检测
        return sorted(self.rules, key=lambda rule: rule.get('fault_level', 1), reverse=True)
    
    def _is_rule_applicable(self, rule: Dict[str, Any], data_frame: Dict[str, Any]) -> bool:
        """检查规则是否适用于当前数据"""
        related_params = rule.get('related_parameters', [])

        # 如果没有相关参数，认为规则适用
        if not related_params:
            return True

        expr_text = str(rule.get('expression') or '')
        expr_l = expr_text.lower()
        advanced_markers = ['mean(', 'std(', 'var(', 'mad(', 'rms(', 'slope(', 'diffmean(', 'diffstd(', 'ma(', 'ma_diff(', 'autocorr(', 'rollstd(', 'level(']
        is_advanced_rule = any(m in expr_l for m in advanced_markers)

        # 检查所需参数是否都存在
        for param in related_params:
            has_current = param in data_frame and data_frame[param] is not None

            if not has_current:
                # 高级函数允许依赖历史：若历史缓冲中存在该参数数据，则仍可适用
                has_history = False
                try:
                    buf = self.parameter_buffers.get(param)
                    has_history = bool(buf and len(buf) > 0)
                except Exception:
                    has_history = False

                if is_advanced_rule and has_history:
                    # 允许仅依赖历史数据执行
                    continue

                logger.debug(f"规则 {rule.get('rule_id')} 缺少参数: {param}（且无可用历史），跳过")
                return False

            # 允许 NaN 值，让规则逻辑自行处理
        return True
    
    def get_buffer_info(self) -> Dict[str, Dict[str, Any]]:
        """获取缓冲区信息"""
        info = {}
        for param_name, buffer in self.parameter_buffers.items():
            info[param_name] = {
                "max_window_size": buffer.max_window_size,
                "current_size": len(buffer.data_points),
                "latest_value": buffer.data_points[-1].value if buffer.data_points else None,
                "latest_timestamp": buffer.data_points[-1].timestamp if buffer.data_points else None
            }
        return info


def test_enhanced_detector():
    """测试增强版检测器"""
    # 创建测试规则配置
    rule_config = {
        "rules": [
            {
                "rule_id": "test_rule_1",
                "fault_name": "温度异常",
                "fault_level": 2,
                "component": "发动机",
                "expression": 'mean("温度") > 80',
                "related_parameters": ["温度"],
                "is_online": True
            },
            {
                "rule_id": "test_rule_2",
                "fault_name": "压力波动",
                "fault_level": 1,
                "component": "液压系统",
                "expression": 'std("压力") > 5',
                "related_parameters": ["压力"],
                "is_online": True
            }
        ],
        "parameter_names": ["温度", "压力", "转速"],
        "fault_name_map": {}
    }
    
    # 创建检测器
    detector = EnhancedRuleDetector(rule_config)
    
    # 模拟数据更新
    import time
    current_time = time.time()
    
    for i in range(20):
        # 模拟温度逐渐上升
        temp = 70 + i * 2 + np.random.normal(0, 1)
        pressure = 100 + np.random.normal(0, 3)
        
        data_frame = {
            "温度": temp,
            "压力": pressure,
            "转速": 1500 + np.random.normal(0, 50)
        }
        
        timestamp = datetime.fromtimestamp(current_time + i)
        
        # 更新数据
        detector.update_data(data_frame, timestamp, i)
        
        # 执行检测
        results = detector.detect(data_frame, timestamp)
        
        if results:
            print(f"时间 {timestamp}: 检测到 {len(results)} 个故障")
            for result in results:
                print(f"  - {result['fault_name']}: {result['confidence_score']}")
    
    # 显示缓冲区信息
    print("\n缓冲区信息:")
    buffer_info = detector.get_buffer_info()
    for param, info in buffer_info.items():
        print(f"  {param}: 大小={info['current_size']}, 最新值={info['latest_value']:.2f}")


if __name__ == "__main__":
    test_enhanced_detector()
