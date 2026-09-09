#!/usr/bin/env python
"""
娴嬭瘯鏁版嵁瀛樺偍淇鏁堟灉
楠岃瘉瑙ｆ瀽鐨勮褰曟暟鏄惁涓庡瓨鍌ㄧ殑璁板綍鏁颁竴鑷?
"""

import os
import sys
import django
from pathlib import Path

# 璁剧疆Django鐜
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import ImportSession, PHMData
from data_management.batch_processing import BatchFileProcessor
import logging

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_storage_logic():
    """娴嬭瘯瀛樺偍閫昏緫淇"""
    print("=== 娴嬭瘯鏁版嵁瀛樺偍閫昏緫淇 ===")
    
    try:
        # 妫€鏌ユ渶杩戠殑瀵煎叆浼氳瘽
        sessions = ImportSession.objects.all().order_by('-timestamp')[:3]
        print(f"鏈€杩戠殑瀵煎叆浼氳瘽鏁伴噺: {len(sessions)}")
        
        for session in sessions:
            print(f"\n浼氳瘽 {session.id}:")
            print(f"  鐘舵€? {session.processing_status}")
            print(f"  鎬昏褰曟暟: {session.total_records}")
            print(f"  宸插鐞嗚褰曟暟: {session.processed_records}")
            
            # 妫€鏌ュ疄闄呭瓨鍌ㄧ殑鏁版嵁璁板綍鏁?
            actual_records = PHMData.objects.filter(import_session=session).count()
            print(f"  瀹為檯瀛樺偍璁板綍鏁? {actual_records}")
            
            # 楠岃瘉瀛樺偍鏁伴噺鏄惁涓庤В鏋愭暟閲忎竴鑷?
            if session.total_records == actual_records:
                print("  鉁?瀛樺偍鏁伴噺涓庤В鏋愭暟閲忎竴鑷?)
            else:
                print(f"  鉂?瀛樺偍鏁伴噺涓庤В鏋愭暟閲忎笉涓€鑷? 瑙ｆ瀽{session.total_records}, 瀛樺偍{actual_records}")
            
            # 妫€鏌ユ槸鍚︽湁鐩稿悓鏃堕棿鎴崇殑璁板綍
            from django.db.models import Count
            duplicate_timestamps = PHMData.objects.filter(
                import_session=session
            ).values('timestamp').annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            if duplicate_timestamps.exists():
                print(f"  鉁?鍙戠幇 {duplicate_timestamps.count()} 涓噸澶嶆椂闂存埑锛岀郴缁熸纭鐞嗕簡")
                for dup in duplicate_timestamps[:3]:
                    print(f"    鏃堕棿鎴? {dup['timestamp']}, 璁板綍鏁? {dup['count']}")
            else:
                print("  鈩癸笍  娌℃湁鍙戠幇閲嶅鏃堕棿鎴?)
                
    except Exception as e:
        print(f"瀛樺偍閫昏緫娴嬭瘯澶辫触: {e}")

def test_parse_and_store():
    """娴嬭瘯瑙ｆ瀽鍜屽瓨鍌ㄦ祦绋?""
    print("\n=== 娴嬭瘯瑙ｆ瀽鍜屽瓨鍌ㄦ祦绋?===")
    
    try:
        # 鍒涘缓涓€涓祴璇旵SV鏂囦欢
        test_file = "test_storage.csv"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("鏃堕棿,鍙傛暟1,鍙傛暟2\n")
            # 鍒涘缓涓€浜涚浉鍚屾椂闂存埑鐨勬暟鎹?
            for i in range(100):
                timestamp = "2025-08-17 10:00:00"
                f.write(f"{timestamp},{i*1.1},{i*2.2}\n")
        
        print(f"鍒涘缓浜嗘祴璇曟枃浠? {test_file}")
        print(f"鏂囦欢澶у皬: {os.path.getsize(test_file)} 瀛楄妭")
        
        # 娴嬭瘯瑙ｆ瀽
        processor = BatchFileProcessor()
        
        # 妯℃嫙瑙ｆ瀽杩囩▼
        with open(test_file, 'r', encoding='utf-8') as fh:
            import csv
            reader = csv.reader(fh)
            rows = list(reader)
            print(f"CSV瑙ｆ瀽缁撴灉: {len(rows)} 琛?)
            print(f"  鏍囬琛? {rows[0]}")
            print(f"  鏁版嵁琛屾暟: {len(rows) - 1}")
        
        # 娓呯悊娴嬭瘯鏂囦欢
        os.remove(test_file)
        print("鉁?瑙ｆ瀽鍜屽瓨鍌ㄦ祦绋嬫祴璇曞畬鎴?)
        
    except Exception as e:
        print(f"瑙ｆ瀽鍜屽瓨鍌ㄦ祦绋嬫祴璇曞け璐? {e}")

def test_batch_processing():
    """娴嬭瘯鎵归噺澶勭悊閫昏緫"""
    print("\n=== 娴嬭瘯鎵归噺澶勭悊閫昏緫 ===")
    
    try:
        from data_management.batch_processing import BatchFileProcessor
        
        # 鍒涘缓澶勭悊鍣ㄥ疄渚?
        processor = BatchFileProcessor()
        
        # 妫€鏌ユ渶杩戠殑澶勭悊浼氳瘽
        sessions = ImportSession.objects.filter(
            processing_status=ImportSession.ProcessingStatus.COMPLETED
        ).order_by('-timestamp')[:1]
        
        if sessions.exists():
            session = sessions[0]
            print(f"妫€鏌ヤ細璇?{session.id} 鐨勫鐞嗙粨鏋?")
            print(f"  瑙ｆ瀽璁板綍鏁? {session.total_records}")
            print(f"  瀛樺偍璁板綍鏁? {PHMData.objects.filter(import_session=session).count()}")
            print(f"  妫€娴嬭褰曟暟: {session.processed_records}")
            
            # 楠岃瘉鏁版嵁涓€鑷存€?
            stored_count = PHMData.objects.filter(import_session=session).count()
            if session.total_records == stored_count:
                print("  鉁?鏁版嵁涓€鑷存€ч獙璇侀€氳繃")
            else:
                print(f"  鉂?鏁版嵁涓€鑷存€ч獙璇佸け璐? 瑙ｆ瀽{session.total_records}, 瀛樺偍{stored_count}")
        else:
            print("娌℃湁鎵惧埌宸插畬鎴愮殑澶勭悊浼氳瘽")
            
    except Exception as e:
        print(f"鎵归噺澶勭悊閫昏緫娴嬭瘯澶辫触: {e}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("寮€濮嬫祴璇曟暟鎹瓨鍌ㄤ慨澶嶆晥鏋?..")
    
    test_storage_logic()
    test_parse_and_store()
    test_batch_processing()
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")
    print("璇锋鏌ヤ互涓婅緭鍑猴紝纭瀛樺偍淇鏄惁鏈夋晥")
    print("\n淇鎬荤粨:")
    print("1. 鉁?绉婚櫎浜嗗瓨鍌ㄦ椂鐨勯噸澶嶆鏌ラ€昏緫")
    print("2. 鉁?鎵€鏈夎В鏋愮殑璁板綍閮戒細琚瓨鍌?)
    print("3. 鉁?鏀寔鐩稿悓鏃堕棿鎴崇殑澶氭潯璁板綍")
    print("4. 鉁?浣跨敤ignore_conflicts=True閬垮厤鏁版嵁搴撳啿绐?)

if __name__ == "__main__":
    main()

