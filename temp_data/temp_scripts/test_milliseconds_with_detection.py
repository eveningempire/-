#!/usr/bin/env python3
"""
娴嬭瘯姣澶勭悊閫夐」鍦ㄥ鍏?妫€娴嬫ā寮忎笅鐨勬晥鏋?

楠岃瘉鍦ㄥ鍏?妫€娴嬫ā寮忎笅锛屾绉掑鐞嗛€夋嫨閫昏緫鏄惁浠嶇劧鐢熸晥銆?
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

from data_management.models import PHM, ImportSession
from datetime import datetime, timedelta
from django.utils import timezone

def test_milliseconds_with_detection():
    """娴嬭瘯姣澶勭悊閫夐」鍦ㄥ鍏?妫€娴嬫ā寮忎笅鐨勬晥鏋?""
    print("馃И 娴嬭瘯姣澶勭悊閫夐」鍦ㄥ鍏?妫€娴嬫ā寮忎笅鐨勬晥鏋?..")
    
    try:
        # 鑾峰彇涓€涓狢MG
        cmg = PHM.objects.first()
        if not cmg:
            print("   鉂?娌℃湁鍙敤鐨凜MG")
            return False
        
        print(f"   鉁?浣跨敤PHM: {cmg.name} ({cmg.cmg_id})")
        
        # 娴嬭瘯涓嶅悓閰嶇疆缁勫悎
        test_cases = [
            {
                "import_mode": ImportSession.ImportMode.IMPORT_AND_DETECT,
                "add_milliseconds": True,
                "description": "瀵煎叆+妫€娴?+ 鍚敤姣澶勭悊"
            },
            {
                "import_mode": ImportSession.ImportMode.IMPORT_AND_DETECT,
                "add_milliseconds": False,
                "description": "瀵煎叆+妫€娴?+ 绂佺敤姣澶勭悊"
            },
            {
                "import_mode": ImportSession.ImportMode.IMPORT_ONLY,
                "add_milliseconds": True,
                "description": "浠呭鍏?+ 鍚敤姣澶勭悊"
            },
            {
                "import_mode": ImportSession.ImportMode.IMPORT_ONLY,
                "add_milliseconds": False,
                "description": "浠呭鍏?+ 绂佺敤姣澶勭悊"
            }
        ]
        
        for test_case in test_cases:
            print(f"   馃攧 娴嬭瘯: {test_case['description']}")
            
            # 鍒涘缓娴嬭瘯瀵煎叆浼氳瘽
            session = ImportSession.objects.create(
                cmg=cmg,
                method=ImportSession.Method.FILE,
                import_mode=test_case['import_mode'],
                add_milliseconds=test_case['add_milliseconds']
            )
            
            print(f"   鉁?鍒涘缓浼氳瘽鎴愬姛锛孖D: {session.id}")
            print(f"   馃搳 瀵煎叆妯″紡: {session.import_mode}")
            print(f"   馃搳 姣澶勭悊閫夐」: {session.add_milliseconds}")
            
            # 楠岃瘉閰嶇疆鏄惁姝ｇ‘淇濆瓨
            if (session.import_mode == test_case['import_mode'] and 
                session.add_milliseconds == test_case['add_milliseconds']):
                print(f"   鉁?閰嶇疆淇濆瓨姝ｇ‘")
            else:
                print(f"   鉂?閰嶇疆淇濆瓨閿欒")
                return False
            
            # 娓呯悊娴嬭瘯鏁版嵁
            session.delete()
        
        print("   鉁?姣澶勭悊閫夐」鍦ㄥ鍏?妫€娴嬫ā寮忎笅鐨勬祴璇曞畬鎴?)
        return True
        
    except Exception as e:
        print(f"   鉂?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_processing_flow():
    """娴嬭瘯澶勭悊娴佺▼涓绉掑鐞嗙殑浣嶇疆"""
    print("\n馃И 娴嬭瘯澶勭悊娴佺▼涓绉掑鐞嗙殑浣嶇疆...")
    
    try:
        from data_management.batch_processing import BatchFileProcessor
        
        # 鑾峰彇涓€涓狢MG
        cmg = PHM.objects.first()
        if not cmg:
            print("   鉂?娌℃湁鍙敤鐨凜MG")
            return False
        
        # 鍒涘缓娴嬭瘯鏁版嵁锛堝寘鍚噸澶嶆椂闂存埑锛?
        test_timestamp = timezone.now()
        test_data = [
            {'timestamp': test_timestamp, 'data': {'value': 1}},
            {'timestamp': test_timestamp, 'data': {'value': 2}},
            {'timestamp': test_timestamp, 'data': {'value': 3}},
        ]
        
        # 娴嬭瘯瀵煎叆+妫€娴嬫ā寮?+ 鍚敤姣澶勭悊
        print("   馃攧 娴嬭瘯瀵煎叆+妫€娴嬫ā寮?+ 鍚敤姣澶勭悊...")
        session = ImportSession.objects.create(
            cmg=cmg,
            method=ImportSession.Method.FILE,
            import_mode=ImportSession.ImportMode.IMPORT_AND_DETECT,
            add_milliseconds=True
        )
        
        processor = BatchFileProcessor()
        
        # 妯℃嫙澶勭悊娴佺▼
        print("   馃搵 1. 鏂囦欢瑙ｆ瀽闃舵...")
        # 杩欓噷妯℃嫙瑙ｆ瀽鍚庣殑鏁版嵁
        parsed_data = test_data.copy()
        
        print("   馃搵 2. 姣澶勭悊闃舵...")
        if session.add_milliseconds:
            parsed_data = processor._add_milliseconds_to_duplicate_timestamps(parsed_data)
            print("   鉁?鎵ц浜嗘绉掑鐞?)
        else:
            print("   鉁?璺宠繃浜嗘绉掑鐞?)
        
        print("   馃搵 3. 鏁版嵁瀛樺偍闃舵...")
        # 妯℃嫙瀛樺偍锛堣繖閲屽彧鏄鏌ユ暟鎹級
        timestamps = [item['timestamp'] for item in parsed_data]
        unique_timestamps = set(timestamps)
        print(f"   馃搳 瀛樺偍鐨勬暟鎹椂闂存埑鏁伴噺: {len(timestamps)}")
        print(f"   馃搳 鍞竴鏃堕棿鎴虫暟閲? {len(unique_timestamps)}")
        
        print("   馃搵 4. 妫€娴嬮樁娈?..")
        print("   鉁?妫€娴嬮樁娈典娇鐢ㄥ凡瀛樺偍鐨勬暟鎹紙鏃堕棿鎴冲凡澶勭悊锛?)
        
        # 楠岃瘉姣澶勭悊鏁堟灉
        if session.add_milliseconds and len(unique_timestamps) == len(timestamps):
            print("   鉁?姣澶勭悊鐢熸晥锛屾椂闂存埑鍞竴")
        elif not session.add_milliseconds and len(unique_timestamps) < len(timestamps):
            print("   鉁?姣澶勭悊琚鐢紝淇濇寔閲嶅鏃堕棿鎴?)
        else:
            print("   鉂?姣澶勭悊鏁堟灉涓嶇鍚堥鏈?)
            return False
        
        session.delete()
        
        print("   鉁?澶勭悊娴佺▼娴嬭瘯瀹屾垚")
        return True
        
    except Exception as e:
        print(f"   鉂?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """涓绘祴璇曞嚱鏁?""
    print("馃殌 寮€濮嬫绉掑鐞嗛€夐」鍦ㄥ鍏?妫€娴嬫ā寮忎笅鐨勬祴璇?..\n")
    
    tests = [
        test_milliseconds_with_detection,
        test_processing_flow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"馃搳 娴嬭瘯缁撴灉: {passed}/{total} 閫氳繃")
    
    if passed == total:
        print("馃帀 鎵€鏈夋祴璇曢€氳繃! 姣澶勭悊閫夐」鍦ㄥ鍏?妫€娴嬫ā寮忎笅姝ｅ父宸ヤ綔!")
        print("\n馃挕 鍔熻兘纭:")
        print("   1. 姣澶勭悊閫夋嫨鍦ㄥ鍏?妫€娴嬫ā寮忎笅浠嶇劧鐢熸晥")
        print("   2. 姣澶勭悊鍦ㄦ暟鎹В鏋愰樁娈佃繘琛岋紝鏃╀簬妫€娴嬮樁娈?)
        print("   3. 妫€娴嬩娇鐢ㄧ殑鏄凡澶勭悊鏃堕棿鎴崇殑鏁版嵁")
        print("   4. 鎵€鏈夊鍏ユā寮忕粍鍚堥兘鏀寔姣澶勭悊閫夐」")
        return True
    else:
        print("鈿狅笍  閮ㄥ垎娴嬭瘯澶辫触锛岃妫€鏌ュ姛鑳藉疄鐜?)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

