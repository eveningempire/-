#!/usr/bin/env python3
"""
测试时间戳解析修复
"""

import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifetime_prediction.rul_predict.predict import Predictor

def test_timestamp_parsing():
    """测试时间戳解析功能"""
    
    # 测试数据
    test_timestamps = [
        "2024-04-24T15:46:29.001000+00:00",  # 原始错误格式
        "2024-04-24T15:46:29Z",              # Z格式
        "2024-04-24T15:46:29+00:00",         # 标准格式
        "2024-04-24 15:46:29",               # 空格格式
    ]
    
    print("测试时间戳解析...")
    
    for ts in test_timestamps:
        try:
            # 使用修复后的解析函数
            def parse_timestamp(ts_str):
                if isinstance(ts_str, str):
                    if ts_str.endswith('+00:00'):
                        return pd.to_datetime(ts_str)
                    elif ts_str.endswith('Z'):
                        return pd.to_datetime(ts_str.replace('Z', '+00:00'))
                    else:
                        return pd.to_datetime(ts_str)
                return pd.to_datetime(ts_str)
            
            parsed = parse_timestamp(ts)
            print(f"✓ {ts} -> {parsed}")
            
        except Exception as e:
            print(f"✗ {ts} -> 错误: {e}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_timestamp_parsing()

