"""
改进的专家规则评分机制
参考MSFG测点评分的成功修复经验，为专家规则提供连续的0-1评分
"""

import re
import math
import logging
import numpy as np
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ImprovedRuleScoring:
    """改进的规则评分类"""
    
    def __init__(self):
        """初始化评分器"""
        self.default_score = 0.2  # 默认分数
        self._current_data = {}
    
    def calculate_rule_score(self, result: Any, expression: str, data: Dict[str, Any]) -> float:
        """
        计算规则的连续评分
        
        Args:
            result: 规则表达式执行结果
            expression: 规则表达式
            data: 当前数据
            
        Returns:
            float: 0-1之间的连续分数
        """
        try:
            # 设置当前数据供函数使用
            self._current_data = data
            
            # 1. 如果表达式执行失败或结果为None，返回0
            if result is None:
                return 0.0
            
            # 2. 检查是否包含level函数
            if 'level(' in expression:
                return self._score_level_expression(expression, data, result)
            
            # 3. 检查是否包含统计函数
            stat_functions = ['rollstd(', 'ma_diff(', 'mean(', 'std(', 'var(']
            if any(func in expression for func in stat_functions):
                return self._score_statistical_expression(expression, data, result)
            
            # 4. 检查是否是比较表达式
            if self._is_comparison_expression(expression):
                return self._score_comparison_expression(expression, data, result)
            
            # 5. 默认布尔评分
            return self._score_boolean_result(result)
            
        except Exception as e:
            logger.error(f"规则评分计算失败: {e}")
            return 0.0
        finally:
            # 清理当前数据
            self._current_data = {}
    
    def _score_level_expression(self, expression: str, data: Dict[str, Any], result: Any) -> float:
        """
        对包含level函数的表达式进行评分
        参考MSFG中修复后的level函数逻辑
        """
        try:
            # 提取level函数调用
            level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', expression)
            
            if level_matches:
                level_values = []
                
                for param_name, median_str, mad_str in level_matches:
                    if param_name in data:
                        try:
                            x = float(data[param_name])
                            median = float(median_str)
                            mad = float(mad_str)
                            
                            # 🔧 使用MSFG中修复后的level计算逻辑
                            level_result = self._calculate_level_value(x, median, mad)
                            level_values.append(level_result)
                            
                        except (ValueError, TypeError):
                            continue
                
                if level_values:
                    # 将level值转换为概率分数
                    max_level = max(level_values)
                    return self._level_to_probability_score(max_level)
            
            # 如果无法提取level函数，回退到布尔评分
            return self._score_boolean_result(result)
            
        except Exception as e:
            logger.debug(f"Level表达式评分失败: {e}")
            return self._score_boolean_result(result)
    
    def _calculate_level_value(self, x: float, median: float, mad: float) -> float:
        """
        计算level值，使用MSFG中修复后的逻辑
        """
        if abs(mad) < 1e-6:  # MAD接近0，说明历史数据很稳定
            deviation = abs(x - median)
            
            if abs(median) > 0:
                # 对于非零中位数，使用相对偏差
                relative_deviation = deviation / abs(median)
                if relative_deviation < 0.001:  # 相对偏差小于0.1%
                    return 0.0  # 正常状态
                elif relative_deviation < 0.01:  # 相对偏差小于1%
                    return 1.0  # 轻微偏差
                elif relative_deviation < 0.05:  # 相对偏差小于5%
                    return 2.0  # 中等偏差
                else:
                    return 3.5  # 显著偏差，但不过度惩罚
            else:
                # 对于零中位数，使用绝对偏差
                if deviation < 0.01:
                    return 0.0
                elif deviation < 0.1:
                    return 1.0
                elif deviation < 1.0:
                    return 2.0
                else:
                    return 3.5
        else:
            # MAD不为0时，使用标准计算
            return abs(x - median) / abs(mad)
    
    def _level_to_probability_score(self, level_value: float) -> float:
        """
        将level值转换为概率分数，使用MSFG中修复后的映射
        """
        if level_value <= 0.5:
            return 0.0   # 完全正常
        elif level_value <= 1.0:
            return 0.05  # 轻微偏差
        elif level_value <= 1.5:
            return 0.1   # 小幅异常
        elif level_value <= 2.0:
            return 0.2   # 中等异常
        elif level_value <= 2.5:
            return 0.35  # 显著异常
        elif level_value <= 3.0:
            return 0.5   # 严重异常
        elif level_value <= 4.0:
            return 0.7   # 很严重异常
        elif level_value <= 5.0:
            return 0.85  # 极严重异常
        else:
            return 0.95  # 最严重异常，但不是100%
    
    def _score_statistical_expression(self, expression: str, data: Dict[str, Any], result: Any) -> float:
        """对统计函数表达式进行评分"""
        try:
            # 检查表达式是否是比较形式 (stat_func - value) / max(threshold, 1e-9) > 3.0
            comparison_match = re.search(r'\((.*?)\s*-\s*([0-9.]+)\)\s*/\s*max\(([0-9.]+),\s*1e-9\)\s*>\s*([0-9.]+)', expression)
            
            if comparison_match:
                stat_expr = comparison_match.group(1).strip()
                baseline = float(comparison_match.group(2))
                threshold = float(comparison_match.group(3))
                comparison_threshold = float(comparison_match.group(4))
                
                # 计算统计函数的值
                stat_value = self._evaluate_statistical_function(stat_expr, data)
                
                if stat_value is not None:
                    # 计算标准化偏差
                    deviation = abs(stat_value - baseline)
                    normalized_deviation = deviation / max(threshold, 1e-6)
                    
                    # 将偏差转换为概率分数
                    return self._deviation_to_probability_score(normalized_deviation, comparison_threshold)
            
            # 回退到布尔评分
            return self._score_boolean_result(result)
            
        except Exception as e:
            logger.debug(f"统计表达式评分失败: {e}")
            return self._score_boolean_result(result)
    
    def _evaluate_statistical_function(self, stat_expr: str, data: Dict[str, Any]) -> Optional[float]:
        """评估统计函数"""
        try:
            # 简化实现：对于rollstd等函数，返回合理的默认值
            if 'rollstd(' in stat_expr:
                # 提取参数名
                param_match = re.search(r'rollstd\("([^"]+)"', stat_expr)
                if param_match:
                    param_name = param_match.group(1)
                    if param_name in data:
                        x = float(data[param_name])
                        # 假设标准差约为值的0.1%（对于稳定参数）
                        return max(abs(x) * 0.001, 1e-6)
            
            elif 'ma_diff(' in stat_expr:
                # 提取参数名
                param_match = re.search(r'ma_diff\("([^"]+)"', stat_expr)
                if param_match:
                    param_name = param_match.group(1)
                    if param_name in data:
                        x = float(data[param_name])
                        # 假设移动平均差分约为值的0.01%
                        return max(abs(x) * 0.0001, 1e-6)
            
            return None
            
        except Exception:
            return None
    
    def _deviation_to_probability_score(self, normalized_deviation: float, threshold: float) -> float:
        """将标准化偏差转换为概率分数"""
        if normalized_deviation <= threshold * 0.5:
            return 0.0   # 正常
        elif normalized_deviation <= threshold:
            return 0.1   # 轻微异常
        elif normalized_deviation <= threshold * 1.5:
            return 0.3   # 中等异常
        elif normalized_deviation <= threshold * 2:
            return 0.6   # 显著异常
        elif normalized_deviation <= threshold * 3:
            return 0.8   # 严重异常
        else:
            return 0.95  # 极严重异常
    
    def _score_comparison_expression(self, expression: str, data: Dict[str, Any], result: Any) -> float:
        """对比较表达式进行评分"""
        try:
            # 提取比较操作
            comparison_matches = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*([><=!]+)\s*([0-9.]+)', expression)
            
            if comparison_matches:
                scores = []
                for param_name, operator, threshold_str in comparison_matches:
                    if param_name in data:
                        try:
                            param_value = float(data[param_name])
                            threshold = float(threshold_str)
                            score = self._calculate_comparison_score(param_value, operator, threshold)
                            scores.append(score)
                        except (ValueError, TypeError):
                            continue
                
                if scores:
                    return max(scores)  # 取最大值作为最终分数
            
            # 回退到布尔评分
            return self._score_boolean_result(result)
            
        except Exception as e:
            logger.debug(f"比较表达式评分失败: {e}")
            return self._score_boolean_result(result)
    
    def _calculate_comparison_score(self, value: float, operator: str, threshold: float) -> float:
        """计算比较操作的分数"""
        if operator == '>':
            if value > threshold:
                # 计算超出阈值的程度
                excess = (value - threshold) / max(abs(threshold), 1e-6)
                return min(0.95, 0.5 + 0.4 * self._sigmoid_normalize(excess))
            else:
                return 0.0
        elif operator == '<':
            if value < threshold:
                # 计算低于阈值的程度
                deficit = (threshold - value) / max(abs(threshold), 1e-6)
                return min(0.95, 0.5 + 0.4 * self._sigmoid_normalize(deficit))
            else:
                return 0.0
        elif operator == '>=':
            if value >= threshold:
                excess = (value - threshold) / max(abs(threshold), 1e-6)
                return min(0.95, 0.5 + 0.4 * self._sigmoid_normalize(excess))
            else:
                return 0.0
        elif operator == '<=':
            if value <= threshold:
                deficit = (threshold - value) / max(abs(threshold), 1e-6)
                return min(0.95, 0.5 + 0.4 * self._sigmoid_normalize(deficit))
            else:
                return 0.0
        else:
            return 0.5
    
    def _sigmoid_normalize(self, value: float) -> float:
        """使用sigmoid函数将数值标准化到0-1"""
        if value <= 0:
            return 0.0
        elif value >= 5:
            return 1.0
        else:
            return 1.0 / (1.0 + math.exp(-value))
    
    def _is_comparison_expression(self, expression: str) -> bool:
        """检查是否是比较表达式"""
        operators = ['>', '<', '>=', '<=', '==', '!=']
        return any(op in expression for op in operators)
    
    def _score_boolean_result(self, result: Any) -> float:
        """对布尔结果进行评分"""
        if isinstance(result, bool):
            return 0.7 if result else 0.0  # True时返回0.7而不是1.0，避免过度惩罚
        elif isinstance(result, (int, float)):
            if result > 0:
                return min(0.95, 0.5 + 0.4 * self._sigmoid_normalize(result))
            else:
                return 0.0
        else:
            return 0.0
