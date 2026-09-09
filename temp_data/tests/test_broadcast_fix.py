#!/usr/bin/env python
"""
娴嬭瘯_broadcast_progress璋冪敤淇
"""

import os
import sys
import django
from pathlib import Path

# 璁剧疆Django鐜
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.batch_processing import BatchFileProcessor

def test_broadcast_progress_call():
    """娴嬭瘯_broadcast_progress璋冪敤"""
    print("=== 娴嬭瘯_broadcast_progress璋冪敤淇 ===")
    
    processor = BatchFileProcessor()
    
    # 妯℃嫙鍙傛暟
    session_id = 123
    processed_count = 500
    total_records = 1600
    
    # 璁＄畻杩涘害
    progress = (processed_count / total_records) * 100
    
    print(f"浼氳瘽ID: {session_id}")
    print(f"宸插鐞? {processed_count}")
    print(f"鎬绘暟: {total_records}")
    print(f"杩涘害: {progress:.2f}%")
    
    try:
        # 娴嬭瘯璋冪敤
        processor._broadcast_progress(session_id, progress, processed_count, total_records)
        print("鉁?_broadcast_progress璋冪敤鎴愬姛")
    except Exception as e:
        print(f"鉂?_broadcast_progress璋冪敤澶辫触: {e}")
    
    print("\n淇鎬荤粨:")
    print("1. 鉁?鍙傛暟椤哄簭: session_id, progress, processed, total")
    print("2. 鉁?杩涘害璁＄畻: (processed / total) * 100")
    print("3. 鉁?绫诲瀷鍖归厤: int, float, int, int")

if __name__ == "__main__":
    test_broadcast_progress_call()

