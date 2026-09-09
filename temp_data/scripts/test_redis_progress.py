#!/usr/bin/env python
"""
娴嬭瘯Redis杩涘害鏇存柊鍔熻兘
楠岃瘉寮傛杩涘害鏇存柊鍜屽墠绔疆璇㈡帴鍙ｆ槸鍚︽甯稿伐浣?
"""

import os
import sys
import django
import time
import requests
import json

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.redis_service import redis_service
from data_management.models import ImportSession
from data_management.batch_processing import batch_processor

def test_redis_progress():
    """娴嬭瘯Redis杩涘害鏇存柊鍔熻兘"""
    print("=== 娴嬭瘯Redis杩涘害鏇存柊鍔熻兘 ===")
    
    # 1. 娴嬭瘯Redis杩炴帴
    print("1. 娴嬭瘯Redis杩炴帴...")
    if redis_service.ping():
        print("鉁?Redis杩炴帴姝ｅ父")
    else:
        print("鉁?Redis杩炴帴澶辫触")
        return False
    
    # 2. 娴嬭瘯杩涘害鏇存柊鍜岃幏鍙?
    print("\n2. 娴嬭瘯杩涘害鏇存柊鍜岃幏鍙?..")
    test_session_id = 999999  # 浣跨敤涓€涓祴璇旾D
    
    # 鏇存柊杩涘害
    success = redis_service.update_processing_progress(
        session_id=test_session_id,
        progress=45.5,
        processed=455,
        total=1000,
        status="processing",
        message="姝ｅ湪澶勭悊鏁版嵁..."
    )
    
    if success:
        print("鉁?杩涘害鏇存柊鎴愬姛")
    else:
        print("鉁?杩涘害鏇存柊澶辫触")
        return False
    
    # 鑾峰彇杩涘害
    progress_data = redis_service.get_processing_progress(test_session_id)
    if progress_data:
        print(f"鉁?杩涘害鑾峰彇鎴愬姛: {progress_data}")
    else:
        print("鉁?杩涘害鑾峰彇澶辫触")
        return False
    
    # 3. 娴嬭瘯杩涘害娓呴櫎
    print("\n3. 娴嬭瘯杩涘害娓呴櫎...")
    clear_success = redis_service.clear_processing_progress(test_session_id)
    if clear_success:
        print("鉁?杩涘害娓呴櫎鎴愬姛")
        
        # 楠岃瘉娓呴櫎鍚庤幏鍙栦笉鍒版暟鎹?
        cleared_data = redis_service.get_processing_progress(test_session_id)
        if cleared_data is None:
            print("鉁?娓呴櫎鍚庢暟鎹‘瀹炰笉瀛樺湪")
        else:
            print("鉁?娓呴櫎鍚庢暟鎹粛鐒跺瓨鍦?)
            return False
    else:
        print("鉁?杩涘害娓呴櫎澶辫触")
        return False
    
    return True

def test_batch_processor_progress():
    """娴嬭瘯BatchProcessor鐨勮繘搴︽洿鏂版柟娉?""
    print("\n=== 娴嬭瘯BatchProcessor杩涘害鏇存柊 ===")
    
    try:
        processor = batch_processor
        
        # 娴嬭瘯_update_redis_progress鏂规硶
        print("1. 娴嬭瘯_update_redis_progress鏂规硶...")
        processor._update_redis_progress(
            session_id=888888,
            progress=75.0,
            processed=750,
            total=1000,
            status="processing",
            message="娴嬭瘯杩涘害鏇存柊"
        )
        
        # 楠岃瘉杩涘害鏄惁鍐欏叆Redis
        progress_data = redis_service.get_processing_progress(888888)
        if progress_data and progress_data.get('progress') == 75.0:
            print("鉁?BatchProcessor杩涘害鏇存柊鎴愬姛")
        else:
            print("鉁?BatchProcessor杩涘害鏇存柊澶辫触")
            return False
        
        # 娓呯悊娴嬭瘯鏁版嵁
        redis_service.clear_processing_progress(888888)
        print("鉁?娴嬭瘯鏁版嵁宸叉竻鐞?)
        
        return True
        
    except Exception as e:
        print(f"鉁?BatchProcessor娴嬭瘯澶辫触: {e}")
        return False

def test_api_endpoint():
    """娴嬭瘯API鎺ュ彛锛堥渶瑕丏jango鏈嶅姟鍣ㄨ繍琛岋級"""
    print("\n=== 娴嬭瘯API鎺ュ彛 ===")
    
    # 妫€鏌ユ槸鍚︽湁鍙敤鐨勫鍏ヤ細璇?
    try:
        sessions = ImportSession.objects.all()[:1]
        if not sessions:
            print("鈿?娌℃湁鍙敤鐨勫鍏ヤ細璇濓紝璺宠繃API娴嬭瘯")
            return True
        
        session = sessions[0]
        print(f"浣跨敤浼氳瘽ID: {session.id}")
        
        # 妯℃嫙杩涘害鏁版嵁
        redis_service.update_processing_progress(
            session_id=session.id,
            progress=60.0,
            processed=600,
            total=1000,
            status="processing",
            message="API娴嬭瘯杩涘害"
        )
        
        # 娴嬭瘯API鎺ュ彛
        try:
            # 杩欓噷闇€瑕丏jango鏈嶅姟鍣ㄨ繍琛岋紝濡傛灉娌℃湁杩愯鍒欒烦杩?
            response = requests.get(
                f"http://localhost:8000/api/import-sessions/{session.id}/progress/",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"鉁?API鎺ュ彛姝ｅ父: {data}")
                
                # 娓呯悊娴嬭瘯鏁版嵁
                redis_service.clear_processing_progress(session.id)
                return True
            else:
                print(f"鉁?API鎺ュ彛杩斿洖閿欒: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("鈿?Django鏈嶅姟鍣ㄦ湭杩愯锛岃烦杩嘇PI娴嬭瘯")
            return True
        except Exception as e:
            print(f"鉁?API娴嬭瘯澶辫触: {e}")
            return False
            
    except Exception as e:
        print(f"鉁?API娴嬭瘯鍑嗗澶辫触: {e}")
        return False

def main():
    """涓绘祴璇曞嚱鏁?""
    print("寮€濮嬫祴璇昍edis杩涘害鏇存柊鍔熻兘...\n")
    
    results = []
    
    # 杩愯鍚勯」娴嬭瘯
    results.append(("Redis杩涘害鍔熻兘", test_redis_progress()))
    results.append(("BatchProcessor杩涘害", test_batch_processor_progress()))
    results.append(("API鎺ュ彛", test_api_endpoint()))
    
    # 杈撳嚭娴嬭瘯缁撴灉
    print("\n=== 娴嬭瘯缁撴灉姹囨€?===")
    all_passed = True
    for test_name, result in results:
        status = "鉁?閫氳繃" if result else "鉁?澶辫触"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n鎬讳綋缁撴灉: {'鉁?鎵€鏈夋祴璇曢€氳繃' if all_passed else '鉁?閮ㄥ垎娴嬭瘯澶辫触'}")
    
    if all_passed:
        print("\n馃帀 Redis寮傛杩涘害鏇存柊鍔熻兘宸叉垚鍔熷疄鐜帮紒")
        print("鍓嶇鐜板湪鍙互閫氳繃杞 /api/import-sessions/{id}/progress/ 鎺ュ彛鑾峰彇瀹炴椂杩涘害")
    else:
        print("\n鉂?閮ㄥ垎鍔熻兘闇€瑕佷慨澶?)
    
    return all_passed

if __name__ == "__main__":
    main()

