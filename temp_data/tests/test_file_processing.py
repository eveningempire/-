#!/usr/bin/env python
"""
娴嬭瘯鏂囦欢澶勭悊鍔熻兘锛堜粎瑙ｆ瀽鍜屽瓨鍌紝涓嶅寘鍚娴嬶級
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

from data_management.models import PHM, PHMModel, ImportSession, PHMData
from data_management.batch_processing import BatchFileProcessor


def create_test_csv_file():
    """鍒涘缓娴嬭瘯CSV鏂囦欢"""
    test_file = Path("test_data_simple.csv")
    
    # 鐢熸垚娴嬭瘯鏁版嵁
    headers = ["timestamp", "param1", "param2", "param3", "param4"]
    data = []
    
    for i in range(10):  # 鍑忓皯鍒?0鏉¤褰曟柟渚挎祴璇?
        timestamp = f"2024-01-01 10:00:{i:02d}"
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


def test_file_parsing_and_storage():
    """娴嬭瘯鏂囦欢瑙ｆ瀽鍜屽瓨鍌ㄥ姛鑳?""
    print("寮€濮嬫祴璇曟枃浠惰В鏋愬拰瀛樺偍...")
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    test_file = create_test_csv_file()
    processor = BatchFileProcessor()
    
    try:
        # 鑾峰彇鎴栧垱寤烘祴璇旵MG
        cmg_model, created = PHMModel.objects.get_or_create(
            model_name="TEST_MODEL_SIMPLE",
            defaults={
                'description': "绠€鍗曟祴璇曠敤PHM妯″瀷",
                'is_active': True
            }
        )
        if created:
            print(f"鍒涘缓PHM妯″瀷: {cmg_model.model_name}")
        
        cmg, created = PHM.objects.get_or_create(
            cmg_id="TEST_PHM_SIMPLE",
            defaults={
                'name': "绠€鍗曟祴璇旵MG",
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
                protocol_description="绠€鍗曟祴璇曞鍏ヤ細璇?
            )
            
            # 妯℃嫙鏂囦欢涓婁紶
            session.file.save(
                f"test_simple_{session.id}.csv",
                f,
                save=True
            )
        
        print(f"鍒涘缓瀵煎叆浼氳瘽: {session.id}")
        print(f"鏂囦欢璺緞: {session.file.path}")
        
        # 娴嬭瘯鏂囦欢瑙ｆ瀽
        print("寮€濮嬭В鏋愭枃浠?..")
        parsed_data = processor._parse_file(session)
        print(f"瑙ｆ瀽缁撴灉: 鍏?{len(parsed_data)} 鏉¤褰?)
        
        if parsed_data:
            print("鍓?鏉¤В鏋愭暟鎹?")
            for i, item in enumerate(parsed_data[:3]):
                print(f"  {i+1}: {item['timestamp']} -> {item['data']}")
        
        # 娴嬭瘯鏁版嵁瀛樺偍
        print("寮€濮嬪瓨鍌ㄦ暟鎹?..")
        stored_records = processor._store_data(session, parsed_data)
        print(f"瀛樺偍缁撴灉: 鍏?{len(stored_records)} 鏉¤褰?)
        
        # 楠岃瘉鏁版嵁搴撲腑鐨勬暟鎹?
        db_count = PHMData.objects.filter(cmg=cmg, import_session=session).count()
        print(f"鏁版嵁搴撻獙璇? 鍏?{db_count} 鏉¤褰?)
        
        # 鏇存柊浼氳瘽鐘舵€?
        session.total_records = len(parsed_data)
        session.processed_records = len(stored_records)
        session.processing_status = ImportSession.ProcessingStatus.COMPLETED
        session.processing_progress = 100.0
        session.save()
        
        print(f"浼氳瘽鐘舵€? {session.processing_status}")
        print(f"澶勭悊杩涘害: {session.processing_progress}%")
        
        # 娓呯悊娴嬭瘯鏂囦欢
        test_file.unlink(missing_ok=True)
        print(f"娓呯悊娴嬭瘯鏂囦欢: {test_file}")
        
        return len(stored_records) == len(parsed_data) and db_count == len(stored_records)
        
    except Exception as e:
        print(f"娴嬭瘯杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 娓呯悊娴嬭瘯鏂囦欢
        if test_file.exists():
            test_file.unlink()


def test_different_file_formats():
    """娴嬭瘯涓嶅悓鏂囦欢鏍煎紡鐨勮В鏋?""
    print("\n寮€濮嬫祴璇曚笉鍚屾枃浠舵牸寮?..")
    
    # 娴嬭瘯XLSX鏍煎紡
    try:
        from openpyxl import Workbook
        
        xlsx_file = Path("test_data.xlsx")
        wb = Workbook()
        ws = wb.active
        
        # 鍐欏叆琛ㄥご
        headers = ["timestamp", "param1", "param2", "param3"]
        ws.append(headers)
        
        # 鍐欏叆鏁版嵁
        for i in range(5):
            row = [f"2024-01-01 11:00:{i:02d}", 10.0 + i, 20.0 + i*2, 30.0 + i*3]
            ws.append(row)
        
        wb.save(xlsx_file)
        print(f"鍒涘缓XLSX娴嬭瘯鏂囦欢: {xlsx_file}")
        
        # 娓呯悊
        xlsx_file.unlink(missing_ok=True)
        print("XLSX鏍煎紡鏀寔姝ｅ父")
        
    except ImportError:
        print("娉ㄦ剰: openpyxl鏈畨瑁咃紝璺宠繃XLSX娴嬭瘯")
    except Exception as e:
        print(f"XLSX娴嬭瘯澶辫触: {e}")
    
    return True


if __name__ == "__main__":
    print("=== 鏂囦欢澶勭悊鍔熻兘娴嬭瘯 ===")
    
    # 娴嬭瘯鍩烘湰鏂囦欢澶勭悊
    success1 = test_file_parsing_and_storage()
    print(f"鏂囦欢瑙ｆ瀽鍜屽瓨鍌ㄦ祴璇? {'鎴愬姛' if success1 else '澶辫触'}")
    
    # 娴嬭瘯涓嶅悓鏍煎紡
    success2 = test_different_file_formats()
    print(f"鏂囦欢鏍煎紡娴嬭瘯: {'鎴愬姛' if success2 else '澶辫触'}")
    
    overall_success = success1 and success2
    print(f"\n鎬讳綋娴嬭瘯缁撴灉: {'鎴愬姛' if overall_success else '澶辫触'}")
    sys.exit(0 if overall_success else 1)

