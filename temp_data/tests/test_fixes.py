#!/usr/bin/env python
"""
娴嬭瘯淇鏁堟灉鐨勮剼鏈?
楠岃瘉鏂囦欢缂栫爜妫€娴嬨€佹牸寮忔敮鎸併€佺粺璁′慨澶嶇瓑
"""

import os
import sys
import django
from pathlib import Path

# 璁剧疆Django鐜
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, ImportSession
from data_management.batch_processing import BatchFileProcessor
import logging

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_encoding_detection():
    """娴嬭瘯缂栫爜妫€娴嬪姛鑳?""
    print("=== 娴嬭瘯缂栫爜妫€娴嬪姛鑳?===")
    
    try:
        from data_management.batch_processing import BatchFileProcessor
        processor = BatchFileProcessor()
        
        # 娴嬭瘯缂栫爜妫€娴嬪嚱鏁?
        def detect_encoding(file_path: str) -> str:
            try:
                import chardet
                with open(file_path, 'rb') as f:
                    raw_data = f.read(10000)
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']
                    confidence = result['confidence']
                    print(f"妫€娴嬪埌缂栫爜: {encoding} (缃俊搴? {confidence:.2f})")
                    return encoding
            except ImportError:
                print("chardet鏈畨瑁?)
                return 'utf-8'
            except Exception as e:
                print(f"缂栫爜妫€娴嬪け璐? {e}")
                return 'utf-8'
        
        # 娴嬭瘯涓€涓ず渚嬫枃浠?
        test_file = "test_encoding.csv"
        with open(test_file, 'w', encoding='gbk') as f:
            f.write("鏃堕棿,鍙傛暟1,鍙傛暟2\n")
            f.write("2025-08-17 10:00:00,1.0,2.0\n")
        
        encoding = detect_encoding(test_file)
        print(f"鏂囦欢 {test_file} 鐨勭紪鐮? {encoding}")
        
        # 娓呯悊娴嬭瘯鏂囦欢
        os.remove(test_file)
        
    except Exception as e:
        print(f"缂栫爜妫€娴嬫祴璇曞け璐? {e}")

def test_format_support():
    """娴嬭瘯鏍煎紡鏀寔"""
    print("\n=== 娴嬭瘯鏍煎紡鏀寔 ===")
    
    supported_formats = ['.csv', '.xlsx', '.xls', '.xlsm', '.json', '.ndjson']
    print(f"鏀寔鐨勬牸寮? {supported_formats}")
    
    # 妫€鏌ヤ緷璧?
    try:
        import chardet
        print("鉁?chardet 宸插畨瑁?)
    except ImportError:
        print("鉂?chardet 鏈畨瑁?)
    
    try:
        from openpyxl import load_workbook
        print("鉁?openpyxl 宸插畨瑁?)
    except ImportError:
        print("鉂?openpyxl 鏈畨瑁?)

def test_statistics_fix():
    """娴嬭瘯缁熻淇"""
    print("\n=== 娴嬭瘯缁熻淇 ===")
    
    # 妫€鏌ユ渶杩戠殑瀵煎叆浼氳瘽
    try:
        sessions = ImportSession.objects.all().order_by('-timestamp')[:5]
        print(f"鏈€杩戠殑瀵煎叆浼氳瘽鏁伴噺: {len(sessions)}")
        
        for session in sessions:
            print(f"\n浼氳瘽 {session.id}:")
            print(f"  鐘舵€? {session.processing_status}")
            print(f"  鎬昏褰曟暟: {session.total_records}")
            print(f"  宸插鐞嗚褰曟暟: {session.processed_records}")
            
            if session.detection_summary:
                summary = session.detection_summary
                print(f"  妫€娴嬫憳瑕?")
                print(f"    IMS妫€娴? {summary.get('ims_evaluations', 0)}")
                print(f"    寮傚父鏁伴噺: {summary.get('ims_anomalies', 0)}")
                print(f"    瑙勫垯璇勪及: {summary.get('rule_evaluations', 0)}")
                print(f"    瑙勫垯瑙﹀彂: {summary.get('rule_triggers', 0)}")
                print(f"    MSFG璇勪及: {summary.get('msfg_evaluations', 0)}")
                
    except Exception as e:
        print(f"缁熻娴嬭瘯澶辫触: {e}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("寮€濮嬫祴璇曚慨澶嶆晥鏋?..")
    
    test_encoding_detection()
    test_format_support()
    test_statistics_fix()
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")
    print("璇锋鏌ヤ互涓婅緭鍑猴紝纭淇鏄惁鏈夋晥")

if __name__ == "__main__":
    main()

