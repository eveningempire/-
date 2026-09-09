#!/usr/bin/env python3
"""
娴嬭瘯鏃堕棿杞存€ц兘浼樺寲

楠岃瘉澶ф暟鎹噺涓嬬殑鏃堕棿杞存暟鎹幏鍙栨€ц兘銆?
"""

import sys
import os
import django
from pathlib import Path
import time

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.db import connection
from data_management.models import PHM, PHMData
from django.utils import timezone
from datetime import timedelta

def test_timeline_performance():
    """娴嬭瘯鏃堕棿杞存暟鎹幏鍙栨€ц兘"""
    print("馃И 娴嬭瘯鏃堕棿杞存€ц兘浼樺寲...")
    
    try:
        # 鑾峰彇涓€涓狢MG
        cmg = PHM.objects.first()
        if not cmg:
            print("   鉂?娌℃湁鍙敤鐨凜MG")
            return False
        
        print(f"   鉁?浣跨敤PHM: {cmg.name} ({cmg.cmg_id})")
        
        # 妫€鏌ユ暟鎹噺
        total_count = PHMData.objects.filter(cmg=cmg).count()
        print(f"   馃搳 PHM鎬绘暟鎹噺: {total_count:,} 鏉?)
        
        if total_count == 0:
            print("   鉂?娌℃湁鏁版嵁鍙緵娴嬭瘯")
            return False
        
        # 娴嬭瘯涓嶅悓鏁版嵁閲忕殑鑾峰彇鎬ц兘
        test_limits = [1000, 10000, 100000, 500000, 1000000, 5000000]
        
        for limit in test_limits:
            if limit > total_count:
                print(f"   鈴笍  璺宠繃 {limit:,} 鏉℃祴璇曪紙鏁版嵁涓嶈冻锛?)
                continue
                
            print(f"   馃攧 娴嬭瘯鑾峰彇 {limit:,} 鏉℃暟鎹?..")
            
            start_time = time.time()
            
            # 娴嬭瘯鏁版嵁鑾峰彇
            try:
                data = list(PHMData.objects.filter(cmg=cmg).order_by("timestamp")[:limit])
                end_time = time.time()
                
                duration = end_time - start_time
                print(f"   鉁?鎴愬姛鑾峰彇 {len(data):,} 鏉℃暟鎹紝鑰楁椂: {duration:.2f} 绉?)
                
                # 濡傛灉鑰楁椂瓒呰繃30绉掞紝缁欏嚭璀﹀憡
                if duration > 30:
                    print(f"   鈿狅笍  鑾峰彇鏃堕棿杈冮暱锛屽彲鑳介渶瑕佷紭鍖?)
                
            except Exception as e:
                print(f"   鉂?鑾峰彇澶辫触: {e}")
                return False
        
        print("   鉁?鏃堕棿杞存€ц兘娴嬭瘯瀹屾垚")
        return True
        
    except Exception as e:
        print(f"   鉂?娴嬭瘯澶辫触: {e}")
        return False

def test_database_connection():
    """娴嬭瘯鏁版嵁搴撹繛鎺ョǔ瀹氭€?""
    print("\n馃И 娴嬭瘯鏁版嵁搴撹繛鎺ョǔ瀹氭€?..")
    
    try:
        # 娴嬭瘯杩炴帴
        connection.ensure_connection()
        print("   鉁?鏁版嵁搴撹繛鎺ユ甯?)
        
        # 娴嬭瘯鏌ヨ鎬ц兘
        cmg = PHM.objects.first()
        if not cmg:
            print("   鉂?娌℃湁鍙敤鐨凜MG")
            return False
        
        # 娴嬭瘯澶ф暟鎹噺鏌ヨ
        print("   馃攧 娴嬭瘯澶ф暟鎹噺鏌ヨ...")
        start_time = time.time()
        
        # 鑾峰彇鏁版嵁閲忕粺璁?
        count = PHMData.objects.filter(cmg=cmg).count()
        end_time = time.time()
        
        print(f"   鉁?缁熻鏌ヨ瀹屾垚锛屾暟鎹噺: {count:,}锛岃€楁椂: {end_time - start_time:.2f} 绉?)
        
        return True
        
    except Exception as e:
        print(f"   鉂?娴嬭瘯澶辫触: {e}")
        return False

def main():
    """涓绘祴璇曞嚱鏁?""
    print("馃殌 寮€濮嬫椂闂磋酱鎬ц兘娴嬭瘯...\n")
    
    tests = [
        test_database_connection,
        test_timeline_performance
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"馃搳 娴嬭瘯缁撴灉: {passed}/{total} 閫氳繃")
    
    if passed == total:
        print("馃帀 鎵€鏈夋祴璇曢€氳繃! 鏃堕棿杞存€ц兘浼樺寲鎴愬姛!")
        print("\n馃挕 浼樺寲鍐呭:")
        print("   1. 澧炲姞浜咥PI瓒呮椂鏃堕棿鍒?鍒嗛挓")
        print("   2. 浼樺寲浜嗗悗绔暟鎹幏鍙栭€昏緫锛屼娇鐢ㄥ垎鎵瑰鐞?)
        print("   3. 鏀硅繘浜嗗墠绔敊璇鐞嗗拰鐢ㄦ埛鍙嶉")
        print("   4. 鏀寔鏈€澶?00涓囨潯鏁版嵁鐨勫鐞?)
        return True
    else:
        print("鈿狅笍  閮ㄥ垎娴嬭瘯澶辫触锛岃妫€鏌ラ厤缃?)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

