"""
规则解析器
从原项目的RuleParse.py简化而来，提供规则表达式解析功能
"""

import re
import json
from typing import List, Dict, Any, Tuple, Optional


class RuleParser:
    """规则解析器类"""
    
    def __init__(self, parameter_names: List[str] = None, fault_names: List[str] = None):
        """
        初始化规则解析器
        
        Args:
            parameter_names: 可用的参数名称列表
            fault_names: 可用的故障名称列表
        """
        self.parameter_names = parameter_names or []
        self.fault_names = fault_names or []
        self.sequences = {}
        self.sequence_order = []
        self.related_parameters = {}
        self.related_faults = set()
        self.log = []
        self.warning_count = 0
        self.error_count = 0
        self.raw_rule = ""
        self.parsed_rule = None
    
    def parse(self, rule_expression: str) -> Optional[Any]:
        """
        解析规则表达式
        
        Args:
            rule_expression: 规则表达式字符串
            
        Returns:
            解析后的规则结构，如果解析失败返回None
        """
        self.raw_rule = rule_expression
        self._reset_state()
        
        # 预处理规则表达式
        processed_rule = self._preprocess_rule(rule_expression)
        
        # 解析规则
        try:
            result = self._parse_expression(processed_rule)
            self.parsed_rule = result
            
            # 验证规则
            if not self._validate_rule(result):
                self.error_count += 1
                self.log.append({
                    "type": "error", 
                    "text": f"规则验证失败: {rule_expression}"
                })
                return None
            
            return result
            
        except Exception as e:
            self.error_count += 1
            self.log.append({
                "type": "error", 
                "text": f"规则解析失败: {str(e)}"
            })
            return None
    
    def _reset_state(self):
        """重置解析器状态"""
        self.sequences = {}
        self.sequence_order = []
        self.related_parameters = {}
        self.related_faults = set()
        self.log = []
        self.warning_count = 0
        self.error_count = 0
    
    def _preprocess_rule(self, rule: str) -> str:
        """预处理规则表达式"""
        # 移除多余空格
        rule = re.sub(r'\s+', ' ', rule.strip())
        
        # 替换常见的逻辑运算符写法
        if "&&" in rule or "||" in rule or "!" in rule:
            self.warning_count += 1
            self.log.append({
                "type": "warn", 
                "text": "请勿使用&&、||、!等逻辑运算符写法，建议使用 and、or、not"
            })
            rule = rule.replace("&&", " and ").replace("||", " or ")
            rule = rule.replace("!=", "~=").replace("!", " not ").replace("~=", "!=")
        
        # 标准化引号
        rule = rule.replace("'", '"').replace('\\"', "'")
        
        return rule
    
    def _parse_expression(self, expression: str) -> Any:
        """解析表达式"""
        # 这里实现简化的表达式解析
        # 实际项目中这部分非常复杂，我们先实现基本功能
        
        # 查找参数引用
        param_pattern = r'\b(' + '|'.join(re.escape(p) for p in self.parameter_names) + r')\b'
        found_params = re.findall(param_pattern, expression)
        for param in found_params:
            self.related_parameters[param] = self.related_parameters.get(param, 0) + 1
        
        # 查找故障引用
        fault_pattern = r'\b(' + '|'.join(re.escape(f) for f in self.fault_names) + r')\b'
        found_faults = re.findall(fault_pattern, expression)
        for fault in found_faults:
            self.related_faults.add(fault)
        
        # 返回简化的解析结果
        return {
            "type": "rule_expression",
            "expression": expression,
            "related_parameters": list(self.related_parameters.keys()),
            "related_faults": list(self.related_faults)
        }
    
    def _validate_rule(self, parsed_rule: Any) -> bool:
        """验证解析后的规则"""
        if not parsed_rule:
            return False
        
        # 检查是否有相关参数
        if not parsed_rule.get("related_parameters"):
            self.warning_count += 1
            self.log.append({
                "type": "warn", 
                "text": "规则未引用任何参数"
            })
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取解析统计信息"""
        return {
            "warnings": self.warning_count,
            "errors": self.error_count,
            "related_parameters": len(self.related_parameters),
            "related_faults": len(self.related_faults),
            "log": self.log
        }


class RuleCompiler:
    """规则编译器，将规则转换为可执行格式"""
    
    def __init__(self, parameter_names: List[str] = None):
        """
        初始化规则编译器
        
        Args:
            parameter_names: 可用的参数名称列表
        """
        self.parameter_names = parameter_names or []
    
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
        
        for rule_def in rule_definitions:
            if not rule_def.get('is_online', True):
                continue  # 跳过离线规则
            
            parser = RuleParser(self.parameter_names)
            parsed_rule = parser.parse(rule_def.get('rule_expression', ''))
            
            if parsed_rule:
                compiled_rule = {
                    "rule_id": rule_def.get('rule_id', ''),
                    "fault_name": rule_def.get('fault_name', ''),
                    "fault_level": rule_def.get('fault_level', 1),
                    "component": rule_def.get('component', ''),
                    "expression": rule_def.get('rule_expression', ''),
                    "parsed_expression": parsed_rule,
                    "related_parameters": parsed_rule.get('related_parameters', []),
                    "plan_description": rule_def.get('plan_description', ''),
                    "source": rule_def.get('source', 'expert')
                }
                compiled_rules.append(compiled_rule)
                
                # 构建故障名称映射
                fault_name_map[rule_def.get('fault_name', '')] = rule_def.get('fault_name', '')
        
        return {
            "detect_type": "rule",
            "rules": compiled_rules,
            "fault_name_map": fault_name_map,
            "parameter_names": self.parameter_names,
            "compiled_at": "2024-01-01T00:00:00Z"  # 应该使用实际时间
        }


def test_rule_parser():
    """测试规则解析器"""
    parameters = ["温度", "压力", "转速", "电流"]
    faults = ["过热故障", "压力异常", "转速过高"]
    
    parser = RuleParser(parameters, faults)
    
    # 测试简单规则
    rule1 = "温度 > 80 and 压力 < 10"
    result1 = parser.parse(rule1)
    print(f"规则1: {rule1}")
    print(f"解析结果: {result1}")
    print(f"统计信息: {parser.get_statistics()}")
    print()
    
    # 测试复杂规则
    rule2 = "温度 > 85 && 转速 > 1000 || 过热故障"
    result2 = parser.parse(rule2)
    print(f"规则2: {rule2}")
    print(f"解析结果: {result2}")
    print(f"统计信息: {parser.get_statistics()}")


if __name__ == "__main__":
    test_rule_parser()
