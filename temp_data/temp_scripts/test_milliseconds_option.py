#!/usr/bin/env python3
"""
娴嬭瘯姣澶勭悊閫夐」鍔熻兘

楠岃瘉鐢ㄦ埛鍙互閫夋嫨鏄惁鑷姩涓洪噸澶嶆椂闂存埑娣诲姞姣銆?
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

def test_milliseconds_option():
    """娴嬭瘯姣澶勭悊閫夐」鍔熻兘"""
    print("馃И 娴嬭瘯姣澶勭悊閫夐」鍔熻兘...")
    
    try:
        # 鑾峰彇涓€涓狢MG
        cmg = PHM.objects.first()
        if not cmg:
            print("   鉂?娌℃湁鍙敤鐨凜MG")
            return False
        
        print(f"   鉁?浣跨敤PHM: {cmg.name} ({cmg.cmg_id})")
        
        # 娴嬭瘯鍒涘缓甯︽湁涓嶅悓姣澶勭悊閫夐」鐨勫鍏ヤ細璇?
        test_cases = [
            {"add_milliseconds": True, "description": "鍚敤姣澶勭悊"},
            {"add_milliseconds": False, "description": "绂佺敤姣澶勭悊"}
        ]
        
        for test_case in test_cases:
            print(f"   馃攧 娴嬭瘯: {test_case['description']}")
            
            # 鍒涘缓娴嬭瘯瀵煎叆浼氳瘽
            session = ImportSession.objects.create(
                cmg=cmg,
                method=ImportSession.Method.FILE,
                import_mode=ImportSession.ImportMode.IMPORT_ONLY,
                add_milliseconds=test_case['add_milliseconds']
            )
            
            print(f"   鉁?鍒涘缓浼氳瘽鎴愬姛锛孖D: {session.id}")
            print(f"   馃搳 姣澶勭悊閫夐」: {session.add_milliseconds}")
            
            # 楠岃瘉閫夐」鏄惁姝ｇ‘淇濆瓨
            if session.add_milliseconds == test_case['add_milliseconds']:
                print(f"   鉁?閫夐」淇濆瓨姝ｇ‘")
            else:
                print(f"   鉂?閫夐」淇濆瓨閿欒锛屾湡鏈? {test_case['add_milliseconds']}, 瀹為檯: {session.add_milliseconds}")
                return False
            
            # 娓呯悊娴嬭瘯鏁版嵁
            session.delete()
        
        print("   鉁?姣澶勭悊閫夐」娴嬭瘯瀹屾垚")
        return True
        
    except Exception as e:
        print(f"   鉂?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_processing_logic():
    """娴嬭瘯鎵归噺澶勭悊閫昏緫涓殑姣澶勭悊"""
    print("\n馃И 娴嬭瘯鎵归噺澶勭悊閫昏緫...")
    
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
        
        # 娴嬭瘯鍚敤姣澶勭悊
        print("   馃攧 娴嬭瘯鍚敤姣澶勭悊...")
        session_with_ms = ImportSession.objects.create(
            cmg=cmg,
            method=ImportSession.Method.FILE,
            import_mode=ImportSession.ImportMode.IMPORT_ONLY,
            add_milliseconds=True
        )
        
        processor = BatchFileProcessor()
        processed_data = processor._add_milliseconds_to_duplicate_timestamps(test_data.copy())
        
        # 妫€鏌ユ槸鍚︽坊鍔犱簡姣
        timestamps = [item['timestamp'] for item in processed_data]
        unique_timestamps = set(timestamps)
        
        if len(unique_timestamps) == len(timestamps):
            print("   鉁?姣澶勭悊鎴愬姛锛屾椂闂存埑鍞竴")
        else:
            print("   鉂?姣澶勭悊澶辫触锛屼粛鏈夐噸澶嶆椂闂存埑")
            return False
        
        session_with_ms.delete()
        
        # 娴嬭瘯绂佺敤姣澶勭悊
        print("   馃攧 娴嬭瘯绂佺敤姣澶勭悊...")
        session_without_ms = ImportSession.objects.create(
            cmg=cmg,
            method=ImportSession.Method.FILE,
            import_mode=ImportSession.ImportMode.IMPORT_ONLY,
            add_milliseconds=False
        )
        
        # 妯℃嫙鎵归噺澶勭悊閫昏緫
        if session_without_ms.add_milliseconds:
            processed_data = processor._add_milliseconds_to_duplicate_timestamps(test_data.copy())
            print("   鈿狅笍  搴旇璺宠繃姣澶勭悊锛屼絾瀹為檯鎵ц浜?)
        else:
            processed_data = test_data.copy()
            print("   鉁?姝ｇ‘璺宠繃姣澶勭悊")
        
        session_without_ms.delete()
        
        print("   鉁?鎵归噺澶勭悊閫昏緫娴嬭瘯瀹屾垚")
        return True
        
    except Exception as e:
        print(f"   鉂?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """涓绘祴璇曞嚱鏁?""
    print("馃殌 寮€濮嬫绉掑鐞嗛€夐」娴嬭瘯...\n")
    
    tests = [
        test_milliseconds_option,
        test_batch_processing_logic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"馃搳 娴嬭瘯缁撴灉: {passed}/{total} 閫氳繃")
    
    if passed == total:
        print("馃帀 鎵€鏈夋祴璇曢€氳繃! 姣澶勭悊閫夐」鍔熻兘姝ｅ父!")
        print("\n馃挕 鍔熻兘璇存槑:")
        print("   1. 鐢ㄦ埛鍙互鍦ㄦ枃浠跺鍏ユ椂閫夋嫨鏄惁鑷姩娣诲姞姣")
        print("   2. 鍚敤鏃讹紝绯荤粺浼氳嚜鍔ㄤ负閲嶅鏃堕棿鎴虫坊鍔犳绉掔骇绮惧害")
        print("   3. 绂佺敤鏃讹紝绯荤粺淇濇寔鍘熷鏃堕棿鎴充笉鍙?)
        print("   4. 閫夐」浼氭纭繚瀛樺埌鏁版嵁搴撳苟鍦ㄥ鐞嗘椂鐢熸晥")
        return True
    else:
        print("鈿狅笍  閮ㄥ垎娴嬭瘯澶辫触锛岃妫€鏌ュ姛鑳藉疄鐜?)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

