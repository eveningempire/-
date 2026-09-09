#!/usr/bin/env python3
"""
娴嬭瘯鏁版嵁搴撹繛鎺ヤ慨澶?

楠岃瘉鎵归噺鏁版嵁澶勭悊鏃剁殑鏁版嵁搴撹繛鎺ョǔ瀹氭€с€?
"""

import sys
import os
import django
from pathlib import Path

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.db import connection, transaction
from data_management.models import PHM, PHMData, ImportSession
from datetime import datetime, timedelta
import time
from django.utils import timezone

def test_database_connection():
    """娴嬭瘯鏁版嵁搴撹繛鎺ョǔ瀹氭€?""
    print("馃И 娴嬭瘯鏁版嵁搴撹繛鎺ョǔ瀹氭€?..")
    
    try:
        # 娴嬭瘯鍩烘湰杩炴帴
        connection.ensure_connection()
        print("   鉁?鏁版嵁搴撹繛鎺ユ甯?)
        
        # 娴嬭瘯闀挎椂闂存搷浣?
        print("   馃攧 娴嬭瘯闀挎椂闂存搷浣?..")
        start_time = time.time()
        
        # 妯℃嫙澶ч噺鏁版嵁鎻掑叆
        cmg = PHM.objects.first()
        if not cmg:
            print("   鉂?娌℃湁鍙敤鐨凜MG")
            return False
        
        # 鍒涘缓娴嬭瘯鏁版嵁
        test_data = []
        for i in range(10000):  # 鍒涘缓10000鏉℃祴璇曟暟鎹?
            test_data.append(PHMData(
                cmg=cmg,
                timestamp=timezone.now() + timedelta(seconds=i),
                data={
                    "楂橀€熺數鏈虹數鍘?: 100 + i % 10,
                    "楂橀€熺數鏈虹數娴?: 5 + i % 5,
                    "浣庨€烝鐩哥數娴?: 3 + i % 3,
                    "浣庨€烠鐩哥數娴?: 3 + i % 3
                }
            ))
        
        print(f"   馃搳 鍑嗗鎻掑叆 {len(test_data)} 鏉℃祴璇曟暟鎹?)
        
        # 鍒嗘壒鎻掑叆鏁版嵁
        batch_size = 1000
        for i in range(0, len(test_data), batch_size):
            batch = test_data[i:i + batch_size]
            
            # 妫€鏌ヨ繛鎺?
            try:
                connection.ensure_connection()
            except Exception as e:
                print(f"   鈿狅笍  杩炴帴妫€鏌ュけ璐ワ紝灏濊瘯閲嶈繛: {e}")
                connection.close()
                connection.ensure_connection()
            
            # 鎻掑叆鎵规
            try:
                with transaction.atomic():
                    PHMData.objects.bulk_create(batch, ignore_conflicts=True)
                
                print(f"   鉁?鎴愬姛鎻掑叆鎵规 {i//batch_size + 1}/{(len(test_data) + batch_size - 1)//batch_size}")
                
            except Exception as e:
                print(f"   鉂?鎵规 {i//batch_size + 1} 鎻掑叆澶辫触: {e}")
                if "Server has gone away" in str(e):
                    print("   馃攧 妫€娴嬪埌杩炴帴闂锛屽皾璇曢噸杩?..")
                    try:
                        connection.close()
                        connection.ensure_connection()
                        # 閲嶈瘯
                        with transaction.atomic():
                            PHMData.objects.bulk_create(batch, ignore_conflicts=True)
                        print(f"   鉁?閲嶈瘯鎴愬姛")
                    except Exception as retry_error:
                        print(f"   鉂?閲嶈瘯澶辫触: {retry_error}")
                        return False
                else:
                    return False
        
        end_time = time.time()
        print(f"   鈴憋笍  鎬昏€楁椂: {end_time - start_time:.2f} 绉?)
        
        # 娓呯悊娴嬭瘯鏁版嵁
        print("   馃Ч 娓呯悊娴嬭瘯鏁版嵁...")
        PHMData.objects.filter(cmg=cmg, timestamp__gte=timezone.now() - timedelta(hours=1)).delete()
        
        print("   鉁?鏁版嵁搴撹繛鎺ユ祴璇曞畬鎴?)
        return True
        
    except Exception as e:
        print(f"   鉂?娴嬭瘯澶辫触: {e}")
        return False

def test_batch_processing():
    """娴嬭瘯鎵归噺澶勭悊鍔熻兘"""
    print("\n馃И 娴嬭瘯鎵归噺澶勭悊鍔熻兘...")
    
    try:
        from data_management.batch_processing import batch_processor
        
        # 鑾峰彇涓€涓狢MG
        cmg = PHM.objects.first()
        if not cmg:
            print("   鉂?娌℃湁鍙敤鐨凜MG")
            return False
        
        print(f"   鉁?浣跨敤PHM: {cmg.name} ({cmg.cmg_id})")
        
        # 鍒涘缓娴嬭瘯瀵煎叆浼氳瘽
        session = ImportSession.objects.create(
            cmg=cmg,
            method=ImportSession.Method.FILE,
            import_mode=ImportSession.ImportMode.IMPORT_ONLY
        )
        
        print(f"   鉁?鍒涘缓娴嬭瘯浼氳瘽: {session.id}")
        
        # 妯℃嫙澶ч噺鏁版嵁
        test_data = []
        for i in range(50000):  # 50000鏉℃暟鎹?
            test_data.append({
                'timestamp': timezone.now() + timedelta(seconds=i),
                'data': {
                    "楂橀€熺數鏈虹數鍘?: 100 + i % 10,
                    "楂橀€熺數鏈虹數娴?: 5 + i % 5,
                    "浣庨€烝鐩哥數娴?: 3 + i % 3,
                    "浣庨€烠鐩哥數娴?: 3 + i % 3
                }
            })
        
        print(f"   馃搳 鍑嗗澶勭悊 {len(test_data)} 鏉℃暟鎹?)
        
        # 娴嬭瘯瀛樺偍鍔熻兘
        start_time = time.time()
        stored_records = batch_processor._store_data(session, test_data)
        end_time = time.time()
        
        print(f"   鉁?鎴愬姛瀛樺偍 {len(stored_records)} 鏉¤褰?)
        print(f"   鈴憋笍  瀛樺偍鑰楁椂: {end_time - start_time:.2f} 绉?)
        
        # 娓呯悊娴嬭瘯鏁版嵁
        session.delete()
        PHMData.objects.filter(cmg=cmg, timestamp__gte=timezone.now() - timedelta(hours=1)).delete()
        
        print("   鉁?鎵归噺澶勭悊娴嬭瘯瀹屾垚")
        return True
        
    except Exception as e:
        print(f"   鉂?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """涓绘祴璇曞嚱鏁?""
    print("馃殌 寮€濮嬫暟鎹簱杩炴帴淇娴嬭瘯...\n")
    
    tests = [
        test_database_connection,
        test_batch_processing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"馃搳 娴嬭瘯缁撴灉: {passed}/{total} 閫氳繃")
    
    if passed == total:
        print("馃帀 鎵€鏈夋祴璇曢€氳繃! 鏁版嵁搴撹繛鎺ヤ慨澶嶆垚鍔?")
        print("\n馃挕 淇鍐呭:")
        print("   1. 娣诲姞浜嗘暟鎹簱杩炴帴妫€鏌ュ拰閲嶈繛鏈哄埗")
        print("   2. 瀹炵幇浜嗗垎鎵瑰鐞嗭紝閬垮厤涓€娆℃€у鐞嗗ぇ閲忔暟鎹?)
        print("   3. 澧炲姞浜嗚繛鎺ヨ秴鏃跺拰閲嶈瘯閰嶇疆")
        print("   4. 娣诲姞浜嗚繘搴︽洿鏂板拰閿欒澶勭悊")
        return True
    else:
        print("鈿狅笍  閮ㄥ垎娴嬭瘯澶辫触锛岃妫€鏌ユ暟鎹簱閰嶇疆")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

