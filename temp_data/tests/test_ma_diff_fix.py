#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ma_diff函数解析修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rule_detection.algorithms.rule.enhanced_rule_parser import EnhancedRuleParser
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def test_ma_diff_parsing():
    """测试ma_diff函数解析"""
    
    # 定义参数列表
    parameters = ["高速电机电流", "低速电机电流", "温度", "压力", "转速"]
    
    # 创建解析器
    parser = EnhancedRuleParser(parameters)
    
    # 测试规则 - 使用您日志中的实际表达式
    test_rule = 'ma_diff("高速电机电流", 60) > 0.000207828 + 3*0.000138547'
    
    print(f"测试规则: {test_rule}")
    print("-" * 50)
    
    # 解析规则
    result = parser.parse(test_rule)
    
    # 输出结果
    print(f"解析结果: {result.expression}")
    print(f"相关参数: {list(result.related_parameters)}")
    print(f"窗口需求: {result.window_requirements}")
    print(f"错误数: {result.error_count}")
    print(f"警告数: {result.warning_count}")
    
    if result.log_messages:
        print("\n日志消息:")
        for msg in result.log_messages:
            print(f"  {msg['type'].upper()}: {msg['message']}")
    
    # 验证结果
    if result.error_count == 0 and result.warning_count == 0:
        print("\n✅ 测试通过: ma_diff函数解析成功，无错误和警告")
    else:
        print(f"\n❌ 测试失败: 有 {result.error_count} 个错误和 {result.warning_count} 个警告")
    
    return result

def test_multiple_ma_diff_rules():
    """测试多个包含ma_diff的规则"""
    
    parameters = ["高速电机电流", "低速电机电流", "温度", "压力", "转速"]
    parser = EnhancedRuleParser(parameters)
    
    test_rules = [
        'ma_diff("高速电机电流", 60) > 0.000207828 + 3*0.000138547',
        'ma_diff("低速电机电流", 30) > 0.001',
        'mean("温度") > 80 and ma_diff("转速", 20) > 0.5',
        'ma_diff("压力", 10) > 5 or std("振动") > 2'
    ]
    
    print("测试多个ma_diff规则:")
    print("=" * 60)
    
    for i, rule in enumerate(test_rules, 1):
        print(f"\n规则 {i}: {rule}")
        result = parser.parse(rule)
        
        print(f"  解析结果: {result.expression}")
        print(f"  相关参数: {list(result.related_parameters)}")
        print(f"  错误数: {result.error_count}, 警告数: {result.warning_count}")
        
        if result.warning_count > 0:
            print("  ⚠️  有警告:")
            for msg in result.log_messages:
                if msg['type'] == 'warning':
                    print(f"    - {msg['message']}")

if __name__ == "__main__":
    print("开始测试ma_diff函数解析修复...")
    print("=" * 60)
    
    # 测试单个规则
    test_ma_diff_parsing()
    
    print("\n" + "=" * 60)
    
    # 测试多个规则
    test_multiple_ma_diff_rules()
    
    print("\n测试完成!")
