"""
高级规则解析器
支持复杂的CMG规则表达式解析，包括时域函数、逻辑运算、时序条件等

基于旧平台的RuleParse.py改进，增加了更好的错误处理和类型安全
"""

import re
import math
import json
import logging
from typing import Dict, List, Any, Set, Tuple, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """解析结果数据类"""
    expression: str
    related_parameters: Set[str] = field(default_factory=set)
    related_faults: Set[str] = field(default_factory=set)
    seq_order: List[Tuple[str, str]] = field(default_factory=list)
    sequences: Dict[str, Dict[str, Tuple[Any, Any]]] = field(default_factory=dict)
    error_count: int = 0
    warning_count: int = 0
    log_messages: List[Dict[str, str]] = field(default_factory=list)


class AdvancedRuleParser:
    """高级规则解析器"""
    
    def __init__(self, parameter_names: List[str], fault_names: List[str] = None):
        """
        初始化解析器
        
        Args:
            parameter_names: 可用的参数名称列表
            fault_names: 可用的故障名称列表
        """
        self.parameter_names = set(parameter_names)
        self.fault_names = set(fault_names or [])
        
        # 解析状态
        self.reset_parse_state()
        
        # 函数模式定义
        self.function_patterns = {
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
    
    def parse(self, rule_expression: str) -> ParseResult:
        """
        解析规则表达式
        
        Args:
            rule_expression: 规则表达式字符串
            
        Returns:
            解析结果
        """
        self.reset_parse_state()
        
        try:
            # 预处理表达式
            processed_expr = self._preprocess_expression(rule_expression)
            
            # 解析各种函数调用
            processed_expr = self._parse_functions(processed_expr)
            
            # 解析时序条件
            processed_expr = self._parse_temporal_conditions(processed_expr)
            
            # 验证解析结果
            self._validate_parse_result(processed_expr)
            
            return ParseResult(
                expression=processed_expr,
                related_parameters=self.related_parameters,
                related_faults=self.related_faults,
                seq_order=self.seq_order,
                sequences=self.sequences,
                error_count=self.error_count,
                warning_count=self.warning_count,
                log_messages=self.log_messages
            )
            
        except Exception as e:
            self._add_error(f"解析失败: {str(e)}")
            return ParseResult(
                expression=rule_expression,
                error_count=self.error_count,
                warning_count=self.warning_count,
                log_messages=self.log_messages
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
    
    def _parse_functions(self, expression: str) -> str:
        """解析函数调用"""
        for func_name, pattern in self.function_patterns.items():
            expression = self._parse_function_type(expression, func_name, pattern)
        
        return expression
    
    def _parse_function_type(self, expression: str, func_name: str, pattern: str) -> str:
        """解析特定类型的函数"""
        matches = list(re.finditer(pattern, expression))
        
        for match in reversed(matches):  # 从后往前替换，避免位置偏移
            try:
                if func_name in ['Para', 'Time']:
                    result = self._parse_parameter_function(func_name, match)
                elif func_name in ['Max', 'Min', 'Mean']:
                    result = self._parse_statistical_function(func_name, match)
                elif func_name in ['Increase', 'Decrease']:
                    result = self._parse_trend_function(func_name, match)
                elif func_name in ['PreCond', 'Trigger']:
                    result = self._parse_condition_function(func_name, match)
                elif func_name == 'Fault':
                    result = self._parse_fault_function(func_name, match)
                else:
                    continue
                
                if result:
                    expression = expression[:match.start()] + result + expression[match.end():]
                    
            except Exception as e:
                self._add_error(f"解析函数 {func_name} 时出错: {str(e)}")
                continue
        
        return expression
    
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
        parsed_sub_expr = self._parse_functions(sub_expr)
        
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
        parsed_sub_expr = self._parse_functions(sub_expr)
        
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
            parsed_cond = self._parse_functions(cond_expr)
            parsed_main = self._parse_functions(main_expr)
            
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
            parsed_trigger = self._parse_functions(trigger_expr)
            parsed_cancel = self._parse_functions(cancel_expr)
            
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
                        # 注意：不要在 f-string 中直接使用空的 {}，否则语法错误
                        self._add_error("无效的{}条件参数")
                        continue
                    
                    parsed_cond = self._parse_functions(cond_expr)
                    # 生成形如 "{}||<expr>" 的唯一标识
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
                    
                    parsed_cond = self._parse_functions(cond_expr)
                    # 小心 f-string 中包含文本大括号时的语法问题
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
        for func in remaining_functions:
            func_name = func.rstrip('(').strip()
            if func_name not in ['and', 'or', 'not', 'abs', 'min', 'max', 'sin', 'cos', 'tan', 'log', 'exp']:
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
                    for count_info in counts:
                        if isinstance(count_info, (list, tuple)) and len(count_info) >= 2:
                            frame_req, time_req = count_info[0], count_info[1]
                            
                            # 从表达式中提取相关参数
                            for param_name in self.related_parameters:
                                if param_name in str(expressions):
                                    if param_name not in requirements:
                                        requirements[param_name] = {
                                            "max_frame_history": 0,
                                            "max_time_history": 0.0
                                        }
                                    
                                    requirements[param_name]["max_frame_history"] = max(
                                        requirements[param_name]["max_frame_history"],
                                        int(frame_req) if isinstance(frame_req, (int, float)) else 0
                                    )
                                    
                                    requirements[param_name]["max_time_history"] = max(
                                        requirements[param_name]["max_time_history"],
                                        float(time_req) if isinstance(time_req, (int, float)) else 0.0
                                    )
        
        return requirements
    
    def get_compilation_info(self) -> Dict[str, Any]:
        """获取编译信息"""
        return {
            "related_parameters": list(self.related_parameters),
            "related_faults": list(self.related_faults),
            "sequence_order": self.seq_order,
            "sequences": self.sequences,
            "parameter_requirements": self.get_parameter_requirements(),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "log_messages": self.log_messages
        }


class RuleCompiler:
    """规则编译器"""
    
    def __init__(self, parameter_names: List[str], fault_names: List[str] = None):
        """
        初始化编译器
        
        Args:
            parameter_names: 可用参数名称列表
            fault_names: 可用故障名称列表
        """
        self.parameter_names = parameter_names
        self.fault_names = fault_names or []
        self.parser = AdvancedRuleParser(parameter_names, fault_names)
    
    def compile_rules(self, rule_definitions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        编译规则定义列表
        
        Args:
            rule_definitions: 规则定义列表
            
        Returns:
            编译后的规则配置
        """
        compiled_rules = []
        fault_name_map = {}
        all_parameters = set()
        compilation_logs = []
        
        for i, rule_def in enumerate(rule_definitions):
            try:
                # 提取规则信息
                rule_id = str(rule_def.get('rule_id', f'R{i:03d}'))
                rule_expr = str(rule_def.get('rule_expression', ''))
                fault_name = str(rule_def.get('fault_name', f'Fault_{i}'))
                fault_level = int(rule_def.get('fault_level', 1))
                component = str(rule_def.get('component', ''))
                is_online = bool(rule_def.get('is_online', True))
                
                if not rule_expr.strip():
                    compilation_logs.append({
                        "rule_id": rule_id,
                        "type": "error",
                        "message": "规则表达式为空"
                    })
                    continue
                
                # 解析规则表达式
                parse_result = self.parser.parse(rule_expr)
                
                if parse_result.error_count > 0:
                    compilation_logs.append({
                        "rule_id": rule_id,
                        "type": "error",
                        "message": f"解析失败，错误数: {parse_result.error_count}",
                        "details": parse_result.log_messages
                    })
                    continue
                
                # 构建编译后的规则
                compiled_rule = {
                    "rule_id": rule_id,
                    "expression": parse_result.expression,
                    "fault_name": fault_name,
                    "fault_level": fault_level,
                    "component": component,
                    "is_online": is_online,
                    "related_parameters": list(parse_result.related_parameters),
                    "related_faults": list(parse_result.related_faults),
                    "sequence_order": parse_result.seq_order,
                    "sequences": parse_result.sequences,
                    "parameter_requirements": self.parser.get_parameter_requirements(),
                    "source": rule_def.get('source', 'expert'),
                    "plan_description": rule_def.get('plan_description', '')
                }
                
                compiled_rules.append(compiled_rule)
                fault_name_map[fault_name] = fault_name
                all_parameters.update(parse_result.related_parameters)
                
                if parse_result.warning_count > 0:
                    compilation_logs.append({
                        "rule_id": rule_id,
                        "type": "warning",
                        "message": f"警告数: {parse_result.warning_count}",
                        "details": parse_result.log_messages
                    })
                
            except Exception as e:
                compilation_logs.append({
                    "rule_id": rule_def.get('rule_id', f'R{i:03d}'),
                    "type": "error",
                    "message": f"编译异常: {str(e)}"
                })
                logger.error(f"编译规则 {rule_def.get('rule_id')} 时出错: {e}")
        
        return {
            "rules": compiled_rules,
            "fault_name_map": fault_name_map,
            "parameter_names": list(all_parameters),
            "compilation_logs": compilation_logs,
            "detect_type": "advanced_rule_detection",
            "total_rules": len(compiled_rules),
            "successful_compilations": len(compiled_rules)
        }
