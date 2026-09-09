#!/usr/bin/env python3
"""
娴嬭瘯绯荤粺閰嶇疆鍔熻兘
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

def test_config():
    print("=== 绯荤粺閰嶇疆娴嬭瘯 ===")
    
    try:
        # 娴嬭瘯瀵煎叆
        from data_management.config import get_config, get_all_config, update_config
        print("鉁?閰嶇疆妯″潡瀵煎叆鎴愬姛")
        
        # 娴嬭瘯鑾峰彇閰嶇疆
        config = get_all_config()
        print(f"鉁?褰撳墠閰嶇疆: {config}")
        
        # 娴嬭瘯鑾峰彇鍗曚釜閰嶇疆
        threshold = get_config('streaming_threshold')
        print(f"鉁?streaming_threshold: {threshold}")
        
        # 娴嬭瘯鏇存柊閰嶇疆
        update_config({'streaming_threshold': 2000})
        new_config = get_all_config()
        print(f"鉁?鏇存柊鍚庨厤缃? {new_config}")
        
        # 娴嬭瘯閲嶇疆
        from data_management.config import system_config
        system_config.reset_to_default()
        reset_config = get_all_config()
        print(f"鉁?閲嶇疆鍚庨厤缃? {reset_config}")
        
        print("=== 鎵€鏈夋祴璇曢€氳繃 ===")
        
    except Exception as e:
        print(f"鉁?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config()

