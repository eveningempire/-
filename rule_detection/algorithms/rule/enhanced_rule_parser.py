"""
增强版规则解析器
支持高级统计函数和区间检测功能
"""

import re
import math
import json
import logging
from typing import Dict, List, Any, Set, Tuple, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EnhancedParseResult:
    """增强解析结果数据类"""
    expression: str
    related_parameters: Set[str] = field(default_factory=set)
    related_faults: Set[str] = field(default_factory=set)
    seq_order: List[Tuple[str, str]] = field(default_factory=list)
    sequences: Dict[str, Dict[str, Tuple[Any, Any]]] = field(default_factory=dict)
    error_count: int = 0
    warning_count: int = 0
    log_messages: List[Dict[str, str]] = field(default_factory=list)
    # 新增：区间检测需求
    window_requirements: Dict[str, Dict[str, int]] = field(default_factory=dict)


class EnhancedRuleParser:
    """增强版规则解析器 - 支持高级统计函数和区间检测"""
    
    def __init__(self, parameter_names: List[str], fault_names: List[str] = None):
        """
        初始化增强解析器
        
        Args:
            parameter_names: 可用的参数名称列表
            fault_names: 可用的故障名称列表
        """
        self.parameter_names = set(parameter_names)
        self.fault_names = set(fault_names or [])
        
        # 解析状态
        self.reset_parse_state()
        
        # 基础函数模式定义
        self.basic_function_patterns = {
            'Para': r'Para\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            'Time': r'Time\s*\(\s*([^,]*)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            'Max': r'Max\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            'Min': r'Min\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            'Mean': r'Mean\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            'Increase': r'Increase\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            'Decrease': r'Decrease\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            'PreCond': r'PreCond\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            'Trigger': r'Trigger\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            'Fault': r'Fault\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
        }
        
        # 新增：高级统计函数模式
        self.advanced_function_patterns = {
            # 基础统计函数（单参数）
            'mean': r'mean\s*\(\s*"([^"]+)"\s*\)',
            'std': r'std\s*\(\s*"([^"]+)"\s*\)',
            'var': r'var\s*\(\s*"([^"]+)"\s*\)',
            'mad': r'mad\s*\(\s*"([^"]+)"\s*\)',
            'rms': r'rms\s*\(\s*"([^"]+)"\s*\)',
            'max': r'max\s*\(\s*"([^"]+)"\s*\)',
            'min': r'min\s*\(\s*"([^"]+)"\s*\)',
            'range': r'range\s*\(\s*"([^"]+)"\s*\)',
            
            # 带窗口参数的函数 - 修复正则表达式，支持不带引号的参数名
            'slope': r'slope\s*\(\s*([^,]+)\s*,\s*(\d+)\s*\)',
            'diffmean': r'diffmean\s*\(\s*([^,]+)\s*,\s*(\d+)\s*\)',
            'diffstd': r'diffstd\s*\(\s*([^,]+)\s*,\s*(\d+)\s*\)',
            'ma': r'ma\s*\(\s*([^,]+)\s*,\s*(\d+)\s*\)',
            'ma_diff': r'ma_diff\s*\(\s*([^,]+)\s*,\s*(\d+)\s*\)',
            'autocorr': r'autocorr\s*\(\s*([^,]+)\s*,\s*(\d+)\s*\)',
            'rollstd': r'rollstd\s*\(\s*([^,]+)\s*,\s*(\d+)\s*\)',
            
            # level函数 - 支持带引号和不带引号的参数名
            'level': r'level\s*\(\s*"([^"]+)"\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
        }
        
        # 时序条件模式
        self.temporal_patterns = {
            '[]': r'\[([^\]]+)\]\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            '<>': r'<([^>]+)>\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            '{}': r'\{([^}]+)\}\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)'
        }
    
    def reset_parse_state(self):
        """重置解析状态"""
        self.related_parameters = set()
        self.related_faults = set()
        self.seq_order = []
        self.sequences = {}
        self.error_count = 0
        self.warning_count = 0
        self.log_messages = []
        self.window_requirements = {}
    
    def parse(self, rule_expression: str) -> EnhancedParseResult:
        """
        解析规则表达式
        
        Args:
            rule_expression: 规则表达式字符串
            
        Returns:
            增强解析结果
        """
        self.reset_parse_state()
        
        try:
            # 预处理表达式
            processed_expr = self._preprocess_expression(rule_expression)
            
            # 解析基础函数调用
            processed_expr = self._parse_basic_functions(processed_expr)
            
            # 解析高级统计函数调用
            processed_expr = self._parse_advanced_functions(processed_expr)
            
            # 解析时序条件
            processed_expr = self._parse_temporal_conditions(processed_expr)
            
            # 验证解析结果
            self._validate_parse_result(processed_expr)
            
            return EnhancedParseResult(
                expression=processed_expr,
                related_parameters=self.related_parameters,
                related_faults=self.related_faults,
                seq_order=self.seq_order,
                sequences=self.sequences,
                error_count=self.error_count,
                warning_count=self.warning_count,
                log_messages=self.log_messages,
                window_requirements=self.window_requirements
            )
            
        except Exception as e:
            self._add_error(f"解析失败: {str(e)}")
            return EnhancedParseResult(
                expression=rule_expression,
                error_count=self.error_count,
                warning_count=self.warning_count,
                log_messages=self.log_messages,
                window_requirements=self.window_requirements
            )
    
    def _preprocess_expression(self, expression: str) -> str:
        """预处理表达式"""
        # 移除多余空格
        expression = re.sub(r'\s+', ' ', expression.strip())
        
        # 替换中文运算符
        replacements = {
            '并且': ' and ',
            '或者': ' or ',
            '非': ' not ',
            '大于': ' > ',
            '小于': ' < ',
            '等于': ' == ',
            '不等于': ' != ',
            '大于等于': ' >= ',
            '小于等于': ' <= '
        }
        
        for chinese, english in replacements.items():
            expression = expression.replace(chinese, english)
        
        return expression
    
    def _parse_basic_functions(self, expression: str) -> str:
        """解析基础函数调用"""
        for func_name, pattern in self.basic_function_patterns.items():
            expression = self._parse_function_type(expression, func_name, pattern, is_advanced=False)
        return expression
    
    def _parse_advanced_functions(self, expression: str) -> str:
        """解析高级统计函数调用"""
        for func_name, pattern in self.advanced_function_patterns.items():
            expression = self._parse_function_type(expression, func_name, pattern, is_advanced=True)
        return expression
    
    def _parse_function_type(self, expression: str, func_name: str, pattern: str, is_advanced: bool = False) -> str:
        """解析特定类型的函数"""
        matches = list(re.finditer(pattern, expression))
        
        for match in reversed(matches):  # 从后往前替换，避免位置偏移
            try:
                if is_advanced:
                    result = self._parse_advanced_function(func_name, match)
                else:
                    result = self._parse_basic_function(func_name, match)
                
                if result:
                    expression = expression[:match.start()] + result + expression[match.end():]
                    
            except Exception as e:
                self._add_error(f"解析函数 {func_name} 时出错: {str(e)}")
                continue
        
        return expression
    
    def _parse_basic_function(self, func_name: str, match: re.Match) -> str:
        """解析基础函数"""
        if func_name in ['Para', 'Time']:
            return self._parse_parameter_function(func_name, match)
        elif func_name in ['Max', 'Min', 'Mean']:
            return self._parse_statistical_function(func_name, match)
        elif func_name in ['Increase', 'Decrease']:
            return self._parse_trend_function(func_name, match)
        elif func_name in ['PreCond', 'Trigger']:
            return self._parse_condition_function(func_name, match)
        elif func_name == 'Fault':
            return self._parse_fault_function(func_name, match)
        
        return match.group(0)
    
    def _parse_advanced_function(self, func_name: str, match: re.Match) -> str:
        """解析高级统计函数"""
        try:
            if func_name in ['mean', 'std', 'var', 'mad', 'rms', 'max', 'min', 'range']:
                # 单参数函数
                param_name = match.group(1).strip().strip('"\'')
                return self._parse_single_param_stat_function(func_name, param_name)
            
            elif func_name in ['slope', 'diffmean', 'diffstd', 'ma', 'ma_diff', 'autocorr', 'rollstd']:
                # 双参数函数（参数名 + 窗口大小）
                param_name = match.group(1).strip().strip('"\'')
                window_size = match.group(2).strip()
                return self._parse_window_stat_function(func_name, param_name, window_size)
            
            elif func_name == 'level':
                # level函数（参数名 + 两个数值参数）
                param_name = match.group(1).strip().strip('"\'')
                median_value = match.group(2).strip()
                mad_value = match.group(3).strip()
                logger.debug(f"解析level函数: param_name={param_name}, median={median_value}, mad={mad_value}")
                return self._parse_level_function(func_name, param_name, median_value, mad_value)
            
        except Exception as e:
            self._add_error(f"解析高级函数 {func_name} 时出错: {str(e)}")
        
        return match.group(0)
    
    def _parse_single_param_stat_function(self, func_name: str, param_name: str) -> str:
        """解析单参数统计函数"""
        # 清理参数名（移除可能的引号）
        param_name = param_name.strip().strip('"\'')
        
        # 验证参数名
        if param_name and param_name not in self.parameter_names:
            self._add_warning(f"未知参数: {param_name}")
        
        if param_name:
            self.related_parameters.add(param_name)
            # 为单参数函数设置默认窗口大小
            self._add_window_requirement(param_name, func_name, 10)  # 默认10帧
        
        # 返回函数调用格式，与检测器期望的格式匹配
        return f'{func_name}("{param_name}")'
    
    def _parse_window_stat_function(self, func_name: str, param_name: str, window_size: str) -> str:
        """解析带窗口的统计函数"""
        # 清理参数名（移除可能的引号）
        param_name = param_name.strip().strip('"\'')
        
        # 验证参数名
        if param_name and param_name not in self.parameter_names:
            self._add_warning(f"未知参数: {param_name}")
        
        if param_name:
            self.related_parameters.add(param_name)
        
        # 解析窗口大小
        try:
            window = int(float(window_size))
            self._add_window_requirement(param_name, func_name, window)
        except ValueError:
            self._add_error(f"无效的窗口大小: {window_size}")
            return f'{func_name}("{param_name}", 10)'  # 使用默认值
        
        # 返回函数调用格式，与检测器期望的格式匹配
        return f'{func_name}("{param_name}", {window})'
    
    def _add_window_requirement(self, param_name: str, func_name: str, window_size: int):
        """添加窗口需求"""
        if param_name not in self.window_requirements:
            self.window_requirements[param_name] = {}
        
        # 记录每个函数对参数的最大窗口需求
        if func_name not in self.window_requirements[param_name]:
            self.window_requirements[param_name][func_name] = window_size
        else:
            self.window_requirements[param_name][func_name] = max(
                self.window_requirements[param_name][func_name], 
                window_size
            )
    
    def _parse_level_function(self, func_name: str, param_name: str, median_value: str, mad_value: str) -> str:
        """解析level函数"""
        # 清理参数名（移除可能的引号）
        param_name = param_name.strip().strip('"\'')
        
        # 验证参数名
        if param_name and param_name not in self.parameter_names:
            self._add_warning(f"未知参数: {param_name}")
        
        if param_name:
            self.related_parameters.add(param_name)
        
        # 解析数值参数
        try:
            median = float(median_value)
            mad = float(mad_value)
        except ValueError:
            self._add_error(f"无效的数值参数: median={median_value}, mad={mad_value}")
            return f'{func_name}("{param_name}", {median_value}, {mad_value})'
        
        # 返回函数调用格式，与检测器期望的格式匹配
        return f'{func_name}("{param_name}", {median}, {mad})'
    
    def _parse_parameter_function(self, func_name: str, match: re.Match) -> str:
        """解析参数函数 (Para/Time)"""
        param_name = match.group(1).strip().strip('"\'')
        delta_value = match.group(2).strip()
        is_time_mode = match.group(3).strip()
        
        # 验证参数名
        if param_name and param_name not in self.parameter_names:
            self._add_warning(f"未知参数: {param_name}")
        
        if param_name:
            self.related_parameters.add(param_name)
        
        # 解析时间/帧模式
        try:
            is_time = int(float(is_time_mode))
            delta = float(delta_value)
        except ValueError:
            self._add_error(f"无效的{func_name}函数参数")
            return match.group(0)
        
        # 记录参数需求
        if param_name:
            param_info = (int(delta) if not is_time else 0, delta if is_time else 0)
            if param_name not in self.sequences.get('Time', {}):
                self.sequences.setdefault('Time', {})[param_name] = (None, [param_info])
            else:
                self.sequences['Time'][param_name][1].append(param_info)
        
        return f'["{func_name}", "{param_name}", {delta}, {is_time}]'
    
    def _parse_statistical_function(self, func_name: str, match: re.Match) -> str:
        """解析统计函数 (Max/Min/Mean)"""
        sub_expr = match.group(1).strip()
        delta_value = match.group(2).strip()
        is_time_mode = match.group(3).strip()
        
        try:
            delta = float(delta_value)
            is_time = int(float(is_time_mode))
        except ValueError:
            self._add_error(f"无效的{func_name}函数参数")
            return match.group(0)
        
        # 递归解析子表达式
        parsed_sub_expr = self._parse_advanced_functions(sub_expr)
        
        # 生成唯一标识符
        func_id = f"{func_name}||{sub_expr}"
        
        # 记录序列信息
        self.sequences.setdefault(func_name, {})[func_id] = (
            [parsed_sub_expr], 
            [(int(delta) if not is_time else 0, delta if is_time else 0)]
        )
        
        if (func_name, func_id) not in self.seq_order:
            self.seq_order.append((func_name, func_id))
        
        return f'["{func_name}", "{func_id}", {delta}, {is_time}]'
    
    def _parse_trend_function(self, func_name: str, match: re.Match) -> str:
        """解析趋势函数 (Increase/Decrease)"""
        sub_expr = match.group(1).strip()
        delta_value = match.group(2).strip()
        is_time_mode = match.group(3).strip()
        
        try:
            delta = float(delta_value)
            is_time = int(float(is_time_mode))
        except ValueError:
            self._add_error(f"无效的{func_name}函数参数")
            return match.group(0)
        
        # 递归解析子表达式
        parsed_sub_expr = self._parse_advanced_functions(sub_expr)
        
        # 生成唯一标识符
        func_id = f"{func_name}||{sub_expr}"
        
        # 记录序列信息
        self.sequences.setdefault(func_name, {})[func_id] = (
            [parsed_sub_expr],
            [(int(delta) if not is_time else 0, delta if is_time else 0)]
        )
        
        if (func_name, func_id) not in self.seq_order:
            self.seq_order.append((func_name, func_id))
        
        return f'["{func_name}", "{func_id}", {delta}, {is_time}]'
    
    def _parse_condition_function(self, func_name: str, match: re.Match) -> str:
        """解析条件函数 (PreCond/Trigger)"""
        if func_name == 'PreCond':
            cond_expr = match.group(1).strip()
            delay_value = match.group(2).strip()
            main_expr = match.group(3).strip()
            
            try:
                delay = float(delay_value)
            except ValueError:
                self._add_error(f"无效的{func_name}延时参数")
                return match.group(0)
            
            # 解析条件表达式和主表达式
            parsed_cond = self._parse_advanced_functions(cond_expr)
            parsed_main = self._parse_advanced_functions(main_expr)
            
            func_id = f"{func_name}||{cond_expr}"
            self.sequences.setdefault(func_name, {})[func_id] = ([parsed_cond], None)
            
            if (func_name, func_id) not in self.seq_order:
                self.seq_order.append((func_name, func_id))
            
            return f'["{func_name}", "{func_id}", {delay}, {parsed_main}]'
        
        elif func_name == 'Trigger':
            trigger_expr = match.group(1).strip()
            delay_value = match.group(2).strip()
            cancel_expr = match.group(3).strip()
            
            try:
                delay = float(delay_value)
            except ValueError:
                self._add_error(f"无效的{func_name}延时参数")
                return match.group(0)
            
            # 解析触发和取消表达式
            parsed_trigger = self._parse_advanced_functions(trigger_expr)
            parsed_cancel = self._parse_advanced_functions(cancel_expr)
            
            func_id = f"{func_name}||{trigger_expr}||{cancel_expr}"
            self.sequences.setdefault(func_name, {})[func_id] = (
                [parsed_trigger, parsed_cancel], 
                [delay]
            )
            
            if (func_name, func_id) not in self.seq_order:
                self.seq_order.append((func_name, func_id))
            
            return f'["{func_name}", "{func_id}", {delay}]'
        
        return match.group(0)
    
    def _parse_fault_function(self, func_name: str, match: re.Match) -> str:
        """解析故障函数"""
        fault_name = match.group(1).strip().strip('"\'')
        fault_level = match.group(2).strip()
        
        # 验证故障名
        if fault_name and self.fault_names and fault_name not in self.fault_names:
            self._add_warning(f"未知故障: {fault_name}")
        
        if fault_name:
            self.related_faults.add(fault_name)
        
        try:
            level = int(float(fault_level))
        except ValueError:
            self._add_error(f"无效的故障等级: {fault_level}")
            return match.group(0)
        
        return f'["{func_name}", "{fault_name}", {level}]'
    
    def _parse_temporal_conditions(self, expression: str) -> str:
        """解析时序条件"""
        for operator, pattern in self.temporal_patterns.items():
            expression = self._parse_temporal_operator(expression, operator, pattern)
        
        return expression
    
    def _parse_temporal_operator(self, expression: str, operator: str, pattern: str) -> str:
        """解析特定时序操作符"""
        matches = list(re.finditer(pattern, expression))
        
        for match in reversed(matches):
            try:
                if operator == '{}':  # 部分条件
                    cond_expr = match.group(1).strip()
                    window_size = match.group(2).strip()
                    threshold = match.group(3).strip()
                    
                    try:
                        m = int(float(window_size))
                        n = int(float(threshold))
                    except ValueError:
                        self._add_error("无效的{}条件参数")
                        continue
                    
                    parsed_cond = self._parse_advanced_functions(cond_expr)
                    func_id = f"{{}}||{cond_expr}"
                    
                    self.sequences.setdefault('{}', {})[func_id] = ([parsed_cond], [m])
                    
                    if ('{}', func_id) not in self.seq_order:
                        self.seq_order.append(('{}', func_id))
                    
                    result = f'["{operator}", "{func_id}", {m}, {n}]'
                
                else:  # [] 或 <> 条件
                    cond_expr = match.group(1).strip()
                    duration = match.group(2).strip()
                    
                    try:
                        t = float(duration)
                    except ValueError:
                        self._add_error(f"无效的{operator}条件持续时间")
                        continue
                    
                    parsed_cond = self._parse_advanced_functions(cond_expr)
                    func_id = f"{operator}||{cond_expr}"
                    
                    self.sequences.setdefault(operator, {})[func_id] = ([parsed_cond], None)
                    
                    if (operator, func_id) not in self.seq_order:
                        self.seq_order.append((operator, func_id))
                    
                    result = f'["{operator}", "{func_id}", {t}]'
                
                expression = expression[:match.start()] + result + expression[match.end():]
                
            except Exception as e:
                self._add_error(f"解析{operator}条件时出错: {str(e)}")
                continue
        
        return expression
    
    def _validate_parse_result(self, expression: str):
        """验证解析结果"""
        # 检查是否有未解析的函数调用
        remaining_functions = re.findall(r'[A-Za-z_]\w*\s*\(', expression)
        
        # 定义所有已知的函数白名单
        known_functions = {
            # 基础逻辑和数学函数
            'and', 'or', 'not', 'abs', 'min', 'max', 'sin', 'cos', 'tan', 'log', 'exp',
            # 高级统计函数
            'mean', 'std', 'var', 'mad', 'rms', 'range', 'slope', 'diffmean', 'diffstd', 
            'ma', 'ma_diff', 'autocorr', 'rollstd', 'level',
            # 基础函数
            'Para', 'Time', 'Max', 'Min', 'Mean', 'Increase', 'Decrease', 'PreCond', 'Trigger', 'Fault'
        }
        
        for func in remaining_functions:
            func_name = func.rstrip('(').strip()
            if func_name not in known_functions:
                self._add_warning(f"可能未正确解析的函数: {func_name}")
        
        # 检查括号匹配
        if expression.count('(') != expression.count(')'):
            self._add_error("括号不匹配")
        
        if expression.count('[') != expression.count(']'):
            self._add_error("方括号不匹配")
    
    def _add_error(self, message: str):
        """添加错误消息"""
        self.error_count += 1
        self.log_messages.append({"type": "error", "message": message})
        logger.error(f"规则解析错误: {message}")
    
    def _add_warning(self, message: str):
        """添加警告消息"""
        self.warning_count += 1
        self.log_messages.append({"type": "warning", "message": message})
        logger.warning(f"规则解析警告: {message}")
    
    def get_parameter_requirements(self) -> Dict[str, Dict[str, int]]:
        """获取参数需求信息"""
        requirements = {}
        
        for param_name in self.related_parameters:
            requirements[param_name] = {
                "max_frame_history": 0,
                "max_time_history": 0.0
            }
        
        # 从序列信息中提取需求
        for func_type, func_dict in self.sequences.items():
            for func_id, (expressions, counts) in func_dict.items():
                if counts:
                    for frame_count, time_count in counts:
                        if frame_count > 0:
                            # 需要找到对应的参数名
                            for param_name in self.related_parameters:
                                if param_name in func_id:
                                    requirements[param_name]["max_frame_history"] = max(
                                        requirements[param_name]["max_frame_history"],
                                        frame_count
                                    )
                        if time_count > 0:
                            for param_name in self.related_parameters:
                                if param_name in func_id:
                                    requirements[param_name]["max_time_history"] = max(
                                        requirements[param_name]["max_time_history"],
                                        time_count
                                    )
        
        # 从窗口需求中提取需求
        for param_name, func_requirements in self.window_requirements.items():
            if param_name not in requirements:
                requirements[param_name] = {
                    "max_frame_history": 0,
                    "max_time_history": 0.0
                }
            
            max_window = max(func_requirements.values()) if func_requirements else 0
            requirements[param_name]["max_frame_history"] = max(
                requirements[param_name]["max_frame_history"],
                max_window
            )
        
        return requirements


def test_enhanced_parser():
    """测试增强版解析器"""
    parameters = ["温度", "压力", "转速", "电流", "电压", "振动"]
    faults = ["过热故障", "压力异常", "转速过高"]
    
    parser = EnhancedRuleParser(parameters, faults)
    
    # 测试高级统计函数
    test_rules = [
        'mean("温度") > 80',
        'std("压力") > 10',
        'var("转速") > 100',
        'slope("温度", 20) > 0.5',
        'ma("压力", 10) > 100',
        'autocorr("振动", 5) > 0.8',
        'mean("温度") > 80 and std("压力") < 5',
        'slope("转速", 15) > 0.1 or ma_diff("电流", 8) > 2'
    ]
    
    for i, rule in enumerate(test_rules, 1):
        print(f"\n测试 {i}: {rule}")
        result = parser.parse(rule)
        print(f"解析结果: {result.expression}")
        print(f"相关参数: {list(result.related_parameters)}")
        print(f"窗口需求: {result.window_requirements}")
        print(f"错误数: {result.error_count}, 警告数: {result.warning_count}")


if __name__ == "__main__":
    test_enhanced_parser()
