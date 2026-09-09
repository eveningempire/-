"""
规则检测增强评分机制
专门为规则检测模块提供0-1连续分数评分功能
保持与MSFG模块的独立性
"""

import re
import math
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

class RuleScoringEnhancer:
    """规则检测评分增强器"""
    
    def __init__(self):
        """初始化评分增强器"""
        self.scoring_methods = {
            'boolean': self._score_boolean_result,
            'comparison': self._score_comparison_result,
            'level_function': self._score_level_function,
            'statistical': self._score_statistical_result,
            'threshold': self._score_threshold_result,
            'range': self._score_range_result,
        }
    
    def convert_to_continuous_score(self, value: Any, expression: str, data: Dict[str, Any]) -> float:
        """
        将规则检测结果转换为0-1连续分数
        
        Args:
            value: 规则表达式计算结果
            expression: 规则表达式字符串
            data: 当前数据点
            
        Returns:
            float: 0-1之间的连续分数
        """
        try:
            # 1. 确定评分方法
            scoring_method = self._determine_scoring_method(expression, value)
            
            # 2. 应用相应的评分方法
            if scoring_method in self.scoring_methods:
                score = self.scoring_methods[scoring_method](value, expression, data)
            else:
                # 默认方法
                score = self._score_boolean_result(value, expression, data)
            
            # 3. 确保分数在有效范围内
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"评分转换失败: {e}")
            return 0.0
    
    def _determine_scoring_method(self, expression: str, value: Any) -> str:
        """确定适用的评分方法"""
        expression_lower = expression.lower()
        
        # 检查level函数
        if 'level(' in expression_lower:
            return 'level_function'
        
        # 检查统计函数
        stat_functions = ['mean(', 'std(', 'var(', 'mad(', 'rms(', 'slope(']
        if any(func in expression_lower for func in stat_functions):
            return 'statistical'
        
        # 检查范围比较
        if 'between(' in expression_lower or 'in_range(' in expression_lower:
            return 'range'
        
        # 检查阈值比较
        if self._has_threshold_comparison(expression):
            return 'threshold'
        
        # 检查一般比较操作
        if self._has_comparison_operators(expression):
            return 'comparison'
        
        # 默认布尔评分
        return 'boolean'
    
    def _score_boolean_result(self, value: Any, expression: str, data: Dict[str, Any]) -> float:
        """布尔结果的评分方法"""
        if isinstance(value, bool):
            if value:
                # 对于True结果，尝试从表达式中提取更多信息
                return self._extract_probability_from_boolean_expression(expression, data)
            else:
                return 0.0
        else:
            # 非布尔值，尝试转换为布尔
            return 1.0 if bool(value) else 0.0
    
    def _score_comparison_result(self, value: Any, expression: str, data: Dict[str, Any]) -> float:
        """比较操作的评分方法"""
        if isinstance(value, bool):
            if not value:
                return 0.0
            
            # 提取比较信息
            comparison_info = self._extract_comparison_info(expression, data)
            if comparison_info:
                return self._calculate_comparison_score(comparison_info)
        
        return 1.0 if bool(value) else 0.0
    
    def _score_level_function(self, value: Any, expression: str, data: Dict[str, Any]) -> float:
        """level函数的评分方法"""
        # 提取level函数参数
        level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', expression)
        
        if level_matches:
            scores = []
            for param_name, median_str, mad_str in level_matches:
                if param_name in data:
                    try:
                        x = float(data[param_name])
                        median = float(median_str)
                        mad = float(mad_str)
                        
                        if mad > 0:
                            level_value = abs(x - median) / mad
                            # 将level值转换为概率分数
                            score = self._level_to_probability(level_value)
                            scores.append(score)
                    except (ValueError, TypeError):
                        continue
            
            if scores:
                return max(scores)  # 取最大值作为最终分数
        
        # 回退到布尔评分
        return self._score_boolean_result(value, expression, data)
    
    def _score_statistical_result(self, value: Any, expression: str, data: Dict[str, Any]) -> float:
        """统计函数的评分方法"""
        if isinstance(value, (int, float)):
            # 使用sigmoid函数将统计结果转换为概率
            return self._sigmoid_normalize(value)
        
        return self._score_boolean_result(value, expression, data)
    
    def _score_threshold_result(self, value: Any, expression: str, data: Dict[str, Any]) -> float:
        """阈值比较的评分方法"""
        threshold_info = self._extract_threshold_info(expression, data)
        if threshold_info:
            return self._calculate_threshold_score(threshold_info)
        
        return self._score_boolean_result(value, expression, data)
    
    def _score_range_result(self, value: Any, expression: str, data: Dict[str, Any]) -> float:
        """范围检查的评分方法"""
        range_info = self._extract_range_info(expression, data)
        if range_info:
            return self._calculate_range_score(range_info)
        
        return self._score_boolean_result(value, expression, data)
    
    def _extract_probability_from_boolean_expression(self, expression: str, data: Dict[str, Any]) -> float:
        """从布尔表达式中提取概率信息"""
        # 检查是否有数值比较
        comparison_matches = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*([><=!]+)\s*([0-9.]+)', expression)
        
        if comparison_matches:
            scores = []
            for param_name, operator, threshold_str in comparison_matches:
                if param_name in data:
                    try:
                        param_value = float(data[param_name])
                        threshold = float(threshold_str)
                        score = self._calculate_comparison_probability(param_value, operator, threshold)
                        scores.append(score)
                    except (ValueError, TypeError):
                        continue
            
            if scores:
                return max(scores)  # 取最大值
        
        # 默认返回中等置信度
        return 0.7
    
    def _calculate_comparison_probability(self, value: float, operator: str, threshold: float) -> float:
        """计算比较操作的概率分数"""
        if operator == '>':
            if value > threshold:
                # 计算超出阈值的程度
                excess = (value - threshold) / max(abs(threshold), 1e-6)
                return min(1.0, 0.5 + 0.5 * self._sigmoid_normalize(excess))
            else:
                return 0.0
        elif operator == '<':
            if value < threshold:
                # 计算低于阈值的程度
                deficit = (threshold - value) / max(abs(threshold), 1e-6)
                return min(1.0, 0.5 + 0.5 * self._sigmoid_normalize(deficit))
            else:
                return 0.0
        elif operator == '>=':
            if value >= threshold:
                excess = (value - threshold) / max(abs(threshold), 1e-6)
                return min(1.0, 0.5 + 0.5 * self._sigmoid_normalize(excess))
            else:
                return 0.0
        elif operator == '<=':
            if value <= threshold:
                deficit = (threshold - value) / max(abs(threshold), 1e-6)
                return min(1.0, 0.5 + 0.5 * self._sigmoid_normalize(deficit))
            else:
                return 0.0
        elif operator == '==':
            # 相等比较，计算接近程度
            diff = abs(value - threshold) / max(abs(threshold), 1e-6)
            return max(0.0, 1.0 - diff)
        elif operator == '!=':
            # 不等比较
            diff = abs(value - threshold) / max(abs(threshold), 1e-6)
            return min(1.0, diff)
        else:
            return 0.5
    
    def _level_to_probability(self, level_value: float) -> float:
        """将level值转换为概率分数"""
        # level值越大，异常概率越高
        if level_value <= 1.0:
            return 0.1  # 低概率
        elif level_value <= 2.0:
            return 0.3  # 中低概率
        elif level_value <= 3.0:
            return 0.5  # 中等概率
        elif level_value <= 5.0:
            return 0.8  # 高概率
        else:
            return 0.95  # 很高概率
    
    def _sigmoid_normalize(self, value: float) -> float:
        """使用sigmoid函数将数值标准化到0-1"""
        if value <= 0:
            return 0.0
        elif value >= 10:
            return 1.0
        else:
            return 1.0 / (1.0 + math.exp(-value))
    
    def _has_threshold_comparison(self, expression: str) -> bool:
        """检查是否包含阈值比较"""
        threshold_patterns = [
            r'[a-zA-Z_][a-zA-Z0-9_]*\s*[><=!]+\s*[0-9.]+',
            r'[0-9.]+\s*[><=!]+\s*[a-zA-Z_][a-zA-Z0-9_]*'
        ]
        return any(re.search(pattern, expression) for pattern in threshold_patterns)
    
    def _has_comparison_operators(self, expression: str) -> bool:
        """检查是否包含比较操作符"""
        operators = ['>', '<', '>=', '<=', '==', '!=']
        return any(op in expression for op in operators)
    
    def _extract_comparison_info(self, expression: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取比较操作信息"""
        comparison_matches = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*([><=!]+)\s*([0-9.]+)', expression)
        
        if comparison_matches:
            for param_name, operator, threshold_str in comparison_matches:
                if param_name in data:
                    try:
                        return {
                            'param_name': param_name,
                            'param_value': float(data[param_name]),
                            'operator': operator,
                            'threshold': float(threshold_str)
                        }
                    except (ValueError, TypeError):
                        continue
        
        return None
    
    def _calculate_comparison_score(self, comparison_info: Dict[str, Any]) -> float:
        """计算比较操作分数"""
        value = comparison_info['param_value']
        operator = comparison_info['operator']
        threshold = comparison_info['threshold']
        
        return self._calculate_comparison_probability(value, operator, threshold)
    
    def _extract_threshold_info(self, expression: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取阈值信息"""
        # 这里可以扩展更复杂的阈值提取逻辑
        return self._extract_comparison_info(expression, data)
    
    def _calculate_threshold_score(self, threshold_info: Dict[str, Any]) -> float:
        """计算阈值分数"""
        return self._calculate_comparison_score(threshold_info)
    
    def _extract_range_info(self, expression: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取范围信息"""
        # 这里可以扩展范围检查的逻辑
        return None
    
    def _calculate_range_score(self, range_info: Dict[str, Any]) -> float:
        """计算范围分数"""
        # 这里可以扩展范围评分的逻辑
        return 0.5


def calculate_rule_confidence(expression: str, data: Dict[str, Any], result: Any) -> float:
    """
    计算规则检测结果的置信度
    
    Args:
        expression: 规则表达式
        data: 当前数据
        result: 规则计算结果
        
    Returns:
        float: 置信度分数(0-1)
    """
    confidence = 0.5  # 基础置信度
    
    try:
        # 1. 数据完整性检查
        missing_params = _count_missing_parameters(expression, data)
        if missing_params == 0:
            confidence += 0.2
        elif missing_params <= 2:
            confidence += 0.1
        
        # 2. 表达式复杂度
        complexity = _calculate_expression_complexity(expression)
        if complexity < 3:
            confidence += 0.1
        elif complexity < 5:
            confidence += 0.05
        
        # 3. 结果类型检查
        if isinstance(result, (int, float)):
            confidence += 0.1
        elif isinstance(result, bool):
            confidence += 0.05
        
        # 4. 表达式有效性
        if _is_expression_valid(expression):
            confidence += 0.1
        
    except Exception as e:
        logger.warning(f"置信度计算失败: {e}")
    
    return min(1.0, confidence)


def _count_missing_parameters(expression: str, data: Dict[str, Any]) -> int:
    """统计缺失的参数数量"""
    # 提取表达式中的参数名
    param_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)'
    params = re.findall(param_pattern, expression)
    
    # 过滤掉函数名和常量
    function_names = ['abs', 'min', 'max', 'sqrt', 'log', 'exp', 'sin', 'cos', 'tan']
    missing_count = 0
    
    for param in params:
        if param not in function_names and not param.isdigit() and param not in data:
            missing_count += 1
    
    return missing_count


def _calculate_expression_complexity(expression: str) -> int:
    """计算表达式复杂度"""
    complexity = 0
    
    # 操作符数量
    operators = ['+', '-', '*', '/', '>', '<', '>=', '<=', '==', '!=', 'and', 'or', 'not']
    for op in operators:
        complexity += expression.count(op)
    
    # 函数调用数量
    function_calls = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*\(', expression)
    complexity += len(function_calls)
    
    # 括号深度
    max_depth = 0
    current_depth = 0
    for char in expression:
        if char == '(':
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif char == ')':
            current_depth = max(0, current_depth - 1)
    
    complexity += max_depth
    
    return complexity


def _is_expression_valid(expression: str) -> bool:
    """检查表达式是否有效"""
    try:
        # 基本语法检查
        if not expression or not expression.strip():
            return False
        
        # 括号匹配检查
        if expression.count('(') != expression.count(')'):
            return False
        
        # 基本结构检查
        if len(expression) < 2:
            return False
        
        return True
        
    except Exception:
        return False
