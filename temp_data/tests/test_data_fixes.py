#!/usr/bin/env python
"""
娴嬭瘯鏁版嵁缁熻鍜屾娴嬬粨鏋滀慨澶嶇殑鑴氭湰
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
from health_management.models import IMSDetectionResult
from rule_detection.models import RuleDetectionResult
import logging

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_statistics():
    """娴嬭瘯鏁版嵁缁熻淇"""
    print("=== 娴嬭瘯鏁版嵁缁熻淇 ===")
    
    try:
        # 妫€鏌ユ渶杩戠殑瀵煎叆浼氳瘽
        sessions = ImportSession.objects.all().order_by('-timestamp')[:5]
        print(f"鏈€杩戠殑瀵煎叆浼氳瘽鏁伴噺: {len(sessions)}")
        
        for session in sessions:
            print(f"\n浼氳瘽 {session.id}:")
            print(f"  鐘舵€? {session.processing_status}")
            print(f"  鎬昏褰曟暟: {session.total_records}")
            print(f"  宸插鐞嗚褰曟暟: {session.processed_records}")
            
            # 妫€鏌ュ疄闄呭瓨鍌ㄧ殑鏁版嵁璁板綍鏁?
            actual_records = PHMData.objects.filter(import_session=session).count()
            print(f"  瀹為檯瀛樺偍璁板綍鏁? {actual_records}")
            
            # 妫€鏌ユ娴嬬粨鏋滄暟閲?
            ims_results = IMSDetectionResult.objects.filter(
                data_point__import_session=session
            ).count()
            print(f"  IMS妫€娴嬬粨鏋滄暟: {ims_results}")
            
            rule_results = RuleDetectionResult.objects.filter(
                data_point__import_session=session
            ).count()
            print(f"  瑙勫垯妫€娴嬬粨鏋滄暟: {rule_results}")
            
            # 楠岃瘉缁熻鏄惁姝ｇ‘
            if session.total_records == actual_records:
                print("  鉁?鎬昏褰曟暟缁熻姝ｇ‘")
            else:
                print(f"  鉂?鎬昏褰曟暟缁熻閿欒: 鏈熸湜{actual_records}, 瀹為檯{session.total_records}")
            
            if session.processed_records == actual_records:
                print("  鉁?宸插鐞嗚褰曟暟缁熻姝ｇ‘")
            else:
                print(f"  鉂?宸插鐞嗚褰曟暟缁熻閿欒: 鏈熸湜{actual_records}, 瀹為檯{session.processed_records}")
                
    except Exception as e:
        print(f"鏁版嵁缁熻娴嬭瘯澶辫触: {e}")

def test_detection_results():
    """娴嬭瘯妫€娴嬬粨鏋滀慨澶?""
    print("\n=== 娴嬭瘯妫€娴嬬粨鏋滀慨澶?===")
    
    try:
        # 妫€鏌ユ槸鍚︽湁閲嶅鐨勬娴嬬粨鏋?
        from django.db.models import Count
        
        # 妫€鏌MS妫€娴嬬粨鏋滈噸澶?
        ims_duplicates = IMSDetectionResult.objects.values(
            'data_point', 'ims_model'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if ims_duplicates.exists():
            print(f"鉂?鍙戠幇 {ims_duplicates.count()} 缁勯噸澶嶇殑IMS妫€娴嬬粨鏋?)
            for dup in ims_duplicates[:3]:  # 鍙樉绀哄墠3涓?
                print(f"  鏁版嵁鐐笽D: {dup['data_point']}, 妯″瀷ID: {dup['ims_model']}, 鏁伴噺: {dup['count']}")
        else:
            print("鉁?娌℃湁閲嶅鐨処MS妫€娴嬬粨鏋?)
        
        # 妫€鏌ヨ鍒欐娴嬬粨鏋滈噸澶?
        rule_duplicates = RuleDetectionResult.objects.values(
            'data_point', 'rule_definition', 'fault_definition'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if rule_duplicates.exists():
            print(f"鉂?鍙戠幇 {rule_duplicates.count()} 缁勯噸澶嶇殑瑙勫垯妫€娴嬬粨鏋?)
            for dup in rule_duplicates[:3]:  # 鍙樉绀哄墠3涓?
                print(f"  鏁版嵁鐐笽D: {dup['data_point']}, 瑙勫垯ID: {dup['rule_definition']}, 鏁呴殰ID: {dup['fault_definition']}, 鏁伴噺: {dup['count']}")
        else:
            print("鉁?娌℃湁閲嶅鐨勮鍒欐娴嬬粨鏋?)
            
    except Exception as e:
        print(f"妫€娴嬬粨鏋滄祴璇曞け璐? {e}")

def test_file_parsing():
    """娴嬭瘯鏂囦欢瑙ｆ瀽"""
    print("\n=== 娴嬭瘯鏂囦欢瑙ｆ瀽 ===")
    
    try:
        from data_management.batch_processing import BatchFileProcessor
        
        # 鍒涘缓涓€涓祴璇旵SV鏂囦欢
        test_file = "test_16k.csv"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("鏃堕棿,鍙傛暟1,鍙傛暟2\n")
            for i in range(16000):  # 16k琛屾暟鎹?
                f.write(f"2025-08-17 10:00:{i:02d},{i*1.1},{i*2.2}\n")
        
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
        print("鉁?鏂囦欢瑙ｆ瀽娴嬭瘯瀹屾垚")
        
    except Exception as e:
        print(f"鏂囦欢瑙ｆ瀽娴嬭瘯澶辫触: {e}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("寮€濮嬫祴璇曟暟鎹粺璁″拰妫€娴嬬粨鏋滀慨澶?..")
    
    test_data_statistics()
    test_detection_results()
    test_file_parsing()
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")
    print("璇锋鏌ヤ互涓婅緭鍑猴紝纭淇鏄惁鏈夋晥")

if __name__ == "__main__":
    main()

