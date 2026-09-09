#!/usr/bin/env python3
"""
测试系统配置功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_management.config import get_config, set_config, get_all_config, update_config

def test_config():
    print("=== 系统配置测试 ===")
    
    # 测试获取配置
    print("\n1. 获取当前配置:")
    config = get_all_config()
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # 测试获取单个配置
    print("\n2. 获取单个配置:")
    threshold = get_config('streaming_threshold')
    batch_size = get_config('batch_size')
    print(f"  streaming_threshold: {threshold}")
    print(f"  batch_size: {batch_size}")
    
    # 测试更新配置
    print("\n3. 更新配置:")
    update_config({
        'streaming_threshold': 2000,
        'batch_size': 800
    })
    print("  配置已更新")
    
    # 验证更新
    print("\n4. 验证更新后的配置:")
    config = get_all_config()
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # 测试重置
    print("\n5. 重置为默认配置:")
    from data_management.config import system_config
    system_config.reset_to_default()
    
    print("\n6. 验证重置后的配置:")
    config = get_all_config()
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_config()
