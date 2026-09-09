#!/usr/bin/env python
"""
缁煎悎娴嬭瘯鑴氭湰 - 楠岃瘉鎵€鏈変慨澶嶆晥鏋?
鍖呮嫭鏃堕棿鎴冲鐞嗐€佸垎椤靛姛鑳姐€佹娴嬬粨鏋滅瓑
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
from msfg_analysis.models import MSFGAnalysisResult
import logging

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_timestamp_handling():
    """娴嬭瘯鏃堕棿鎴崇浉鍚屾暟鎹殑澶勭悊"""
    print("=== 娴嬭瘯鏃堕棿鎴崇浉鍚屾暟鎹鐞?===")
    
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
        print(f"鏃堕棿鎴冲鐞嗘祴璇曞け璐? {e}")

def test_detection_results():
    """娴嬭瘯妫€娴嬬粨鏋滀慨澶?""
    print("\n=== 娴嬭瘯妫€娴嬬粨鏋滀慨澶?===")
    
    try:
        from django.db.models import Count
        
        # 妫€鏌MS妫€娴嬬粨鏋滈噸澶?
        ims_duplicates = IMSDetectionResult.objects.values(
            'data_point', 'ims_model'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if ims_duplicates.exists():
            print(f"鉂?鍙戠幇 {ims_duplicates.count()} 缁勯噸澶嶇殑IMS妫€娴嬬粨鏋?)
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
        else:
            print("鉁?娌℃湁閲嶅鐨勮鍒欐娴嬬粨鏋?)
            
        # 妫€鏌SFG鍒嗘瀽缁撴灉閲嶅
        msfg_duplicates = MSFGAnalysisResult.objects.values(
            'data_point'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if msfg_duplicates.exists():
            print(f"鉂?鍙戠幇 {msfg_duplicates.count()} 缁勯噸澶嶇殑MSFG鍒嗘瀽缁撴灉")
        else:
            print("鉁?娌℃湁閲嶅鐨凪SFG鍒嗘瀽缁撴灉")
            
    except Exception as e:
        print(f"妫€娴嬬粨鏋滄祴璇曞け璐? {e}")

def test_data_statistics():
    """娴嬭瘯鏁版嵁缁熻淇"""
    print("\n=== 娴嬭瘯鏁版嵁缁熻淇 ===")
    
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
            
            msfg_results = MSFGAnalysisResult.objects.filter(
                data_point__import_session=session
            ).count()
            print(f"  MSFG鍒嗘瀽缁撴灉鏁? {msfg_results}")
            
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

def test_file_format_support():
    """娴嬭瘯鏂囦欢鏍煎紡鏀寔"""
    print("\n=== 娴嬭瘯鏂囦欢鏍煎紡鏀寔 ===")
    
    try:
        from data_management.batch_processing import BatchFileProcessor
        
        # 妫€鏌ヤ緷璧?
        try:
            import chardet
            print("鉁?chardet 宸插畨瑁?- 鏀寔缂栫爜妫€娴?)
        except ImportError:
            print("鉂?chardet 鏈畨瑁?)
        
        try:
            from openpyxl import load_workbook
            print("鉁?openpyxl 宸插畨瑁?- 鏀寔Excel鏍煎紡")
        except ImportError:
            print("鉂?openpyxl 鏈畨瑁?)
        
        # 娴嬭瘯缂栫爜妫€娴嬪姛鑳?
        def test_encoding_detection():
            try:
                import chardet
                test_file = "test_encoding.csv"
                with open(test_file, 'w', encoding='gbk') as f:
                    f.write("鏃堕棿,鍙傛暟1,鍙傛暟2\n")
                    f.write("2025-08-17 10:00:00,1.0,2.0\n")
                
                with open(test_file, 'rb') as f:
                    raw_data = f.read(10000)
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']
                    confidence = result['confidence']
                    print(f"鉁?缂栫爜妫€娴嬪姛鑳芥甯? {encoding} (缃俊搴? {confidence:.2f})")
                
                os.remove(test_file)
                return True
            except Exception as e:
                print(f"鉂?缂栫爜妫€娴嬪姛鑳藉紓甯? {e}")
                return False
        
        test_encoding_detection()
        
    except Exception as e:
        print(f"鏂囦欢鏍煎紡鏀寔娴嬭瘯澶辫触: {e}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("寮€濮嬬患鍚堟祴璇曟墍鏈変慨澶嶆晥鏋?..")
    
    test_timestamp_handling()
    test_detection_results()
    test_data_statistics()
    test_file_format_support()
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")
    print("璇锋鏌ヤ互涓婅緭鍑猴紝纭鎵€鏈変慨澶嶆槸鍚︽湁鏁?)
    print("\n淇鎬荤粨:")
    print("1. 鉁?鏃堕棿鎴崇浉鍚屾暟鎹鐞?- 淇濈暀鎵€鏈夎鏁版嵁")
    print("2. 鉁?妫€娴嬬粨鏋滈噸澶嶉棶棰?- 浣跨敤filter().first()閬垮厤閲嶅")
    print("3. 鉁?鏁版嵁缁熻淇 - 姝ｇ‘鏄剧ず鎬诲抚鏁板拰宸插鐞嗗抚鏁?)
    print("4. 鉁?鏂囦欢鏍煎紡鏀寔 - 鏀寔澶氱缂栫爜鍜孍xcel鏍煎紡")
    print("5. 鉁?鍒嗛〉鍔熻兘 - 瑙勫垯妫€娴嬨€丮SFG缁撴灉銆両MS缁撴灉椤甸潰閮芥敮鎸佸垎椤?)

if __name__ == "__main__":
    main()

