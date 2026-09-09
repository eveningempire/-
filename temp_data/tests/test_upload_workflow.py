#!/usr/bin/env python
"""
娴嬭瘯鏂囦欢涓婁紶鍜屾娴嬪伐浣滄祦
"""

import os
import sys
import django
import csv
from datetime import datetime
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, PHMModel, ImportSession
from data_management.batch_processing import batch_processor


def create_test_csv_file():
    """鍒涘缓娴嬭瘯CSV鏂囦欢"""
    test_file = Path("test_data.csv")
    
    # 鐢熸垚娴嬭瘯鏁版嵁
    headers = ["timestamp", "param1", "param2", "param3", "param4"]
    data = []
    
    for i in range(100):
        timestamp = f"2024-01-01 10:{i//10:02d}:{i%10:02d}"
        param1 = 10.0 + i * 0.1
        param2 = 20.0 + i * 0.2
        param3 = 15.0 + i * 0.15
        param4 = 5.0 + i * 0.05
        data.append([timestamp, param1, param2, param3, param4])
    
    with open(test_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)
    
    print(f"鍒涘缓娴嬭瘯鏂囦欢: {test_file.absolute()}")
    return test_file


def test_batch_processing():
    """娴嬭瘯鎵归噺澶勭悊鍔熻兘"""
    print("寮€濮嬫祴璇曟枃浠朵笂浼犲拰妫€娴嬪伐浣滄祦...")
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    test_file = create_test_csv_file()
    
    try:
        # 鑾峰彇鎴栧垱寤烘祴璇旵MG
        cmg_model, created = PHMModel.objects.get_or_create(
            model_name="TEST_MODEL",
            defaults={
                'description': "娴嬭瘯鐢–MG妯″瀷",
                'is_active': True
            }
        )
        if created:
            print(f"鍒涘缓PHM妯″瀷: {cmg_model.model_name}")
        
        cmg, created = PHM.objects.get_or_create(
            cmg_id="TEST_PHM_001",
            defaults={
                'name': "娴嬭瘯PHM",
                'cmg_model': cmg_model,
                'enabled': True
            }
        )
        if created:
            print(f"鍒涘缓PHM: {cmg.cmg_id}")
        
        # 鍒涘缓瀵煎叆浼氳瘽
        with open(test_file, 'rb') as f:
            session = ImportSession.objects.create(
                cmg=cmg,
                method=ImportSession.Method.FILE,
                protocol_description="娴嬭瘯瀵煎叆浼氳瘽"
            )
            
            # 妯℃嫙鏂囦欢涓婁紶
            session.file.save(
                f"test_upload_{session.id}.csv",
                f,
                save=True
            )
        
        print(f"鍒涘缓瀵煎叆浼氳瘽: {session.id}")
        print(f"鏂囦欢璺緞: {session.file.path}")
        
        # 寮€濮嬪紓姝ュ鐞?
        print("寮€濮嬪紓姝ュ鐞?..")
        batch_processor.process_import_session_async(session.id)
        
        # 绛夊緟澶勭悊瀹屾垚锛堢畝鍗曡疆璇級
        import time
        max_wait = 60  # 鏈€澶氱瓑寰?0绉?
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            session.refresh_from_db()
            status = session.processing_status
            progress = session.processing_progress
            
            print(f"澶勭悊鐘舵€? {status}, 杩涘害: {progress:.1f}%")
            
            if status in [ImportSession.ProcessingStatus.COMPLETED, ImportSession.ProcessingStatus.FAILED]:
                break
            
            time.sleep(2)
        
        # 鏄剧ず鏈€缁堢粨鏋?
        session.refresh_from_db()
        print(f"\n=== 澶勭悊瀹屾垚 ===")
        print(f"鏈€缁堢姸鎬? {session.processing_status}")
        print(f"鎬昏褰曟暟: {session.total_records}")
        print(f"澶勭悊璁板綍鏁? {session.processed_records}")
        print(f"澶辫触璁板綍鏁? {session.failed_records}")
        print(f"杩涘害: {session.processing_progress:.1f}%")
        
        if session.error_message:
            print(f"閿欒淇℃伅: {session.error_message}")
        
        if session.detection_summary:
            print(f"妫€娴嬫憳瑕? {session.detection_summary}")
        
        # 娓呯悊娴嬭瘯鏂囦欢
        test_file.unlink(missing_ok=True)
        print(f"娓呯悊娴嬭瘯鏂囦欢: {test_file}")
        
        return session.processing_status == ImportSession.ProcessingStatus.COMPLETED
        
    except Exception as e:
        print(f"娴嬭瘯杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 娓呯悊娴嬭瘯鏂囦欢
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    success = test_batch_processing()
    print(f"\n娴嬭瘯缁撴灉: {'鎴愬姛' if success else '澶辫触'}")
    sys.exit(0 if success else 1)

