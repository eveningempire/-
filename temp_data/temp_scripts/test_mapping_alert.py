#!/usr/bin/env python
"""
娴嬭瘯缂哄け鏄犲皠鎻愮ず鍔熻兘
楠岃瘉鍓嶇鐣岄潰鏄惁鑳芥纭樉绀虹己澶辩殑鏄犲皠鍏崇郴
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel, TestPointComponentMapping, FaultComponentMapping

def test_mapping_alert():
    print("馃攳 娴嬭瘯缂哄け鏄犲皠鎻愮ず鍔熻兘")
    print("=" * 60)
    
    try:
        # 鑾峰彇鏈€鏂扮殑MSFG瀹氫箟
        cmg_model = PHMModel.objects.filter(is_active=True).first()
        if not cmg_model:
            print("鉂?娌℃湁鎵惧埌婵€娲荤殑PHM妯″瀷")
            return
            
        msfg_definition = MSFGDefinition.objects.filter(cmg_model=cmg_model).order_by('-created_at').first()
        if not msfg_definition:
            print("鉂?娌℃湁鎵惧埌MSFG瀹氫箟")
            return
            
        print(f"馃搵 鍒嗘瀽MSFG: {msfg_definition}")
        
        # 鑾峰彇褰撳墠鏄犲皠
        test_component_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
        fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg_definition)
        
        test_names = msfg_definition.test_names or []
        component_names = msfg_definition.component_names or []
        fault_names = msfg_definition.fault_names or []
        
        mapped_tests = set(test_component_mappings.values_list('test_point_name', flat=True))
        mapped_faults = set(fault_component_mappings.values_list('fault_name', flat=True))
        
        unmapped_tests = set(test_names) - mapped_tests
        unmapped_faults = set(fault_names) - mapped_faults
        
        print(f"\n馃搳 鏄犲皠鐘舵€佸垎鏋?")
        print(f"  鎬绘祴璇曠偣鏁伴噺: {len(test_names)}")
        print(f"  宸叉槧灏勬祴璇曠偣: {len(mapped_tests)}")
        print(f"  鏈槧灏勬祴璇曠偣: {len(unmapped_tests)}")
        print(f"  鎬绘晠闅滄暟閲? {len(fault_names)}")
        print(f"  宸叉槧灏勬晠闅? {len(mapped_faults)}")
        print(f"  鏈槧灏勬晠闅? {len(unmapped_faults)}")
        print(f"  鍙敤閮ㄤ欢: {len(component_names)}")
        
        if unmapped_tests:
            print(f"\n鈿狅笍  缂哄け鐨勬祴璇曠偣-閮ㄤ欢鏄犲皠 ({len(unmapped_tests)}涓?:")
            for i, test in enumerate(list(unmapped_tests)[:10], 1):
                print(f"  {i}. {test}")
            if len(unmapped_tests) > 10:
                print(f"  ... 杩樻湁 {len(unmapped_tests) - 10} 涓?)
        
        if unmapped_faults:
            print(f"\n鈿?缂哄け鐨勬晠闅?閮ㄤ欢鏄犲皠 ({len(unmapped_faults)}涓?:")
            for i, fault in enumerate(list(unmapped_faults)[:10], 1):
                print(f"  {i}. {fault}")
            if len(unmapped_faults) > 10:
                print(f"  ... 杩樻湁 {len(unmapped_faults) - 10} 涓?)
        
        if not unmapped_tests and not unmapped_faults:
            print(f"\n鉁?鎵€鏈夋槧灏勫叧绯诲畬鏁达紒")
            print(f"  鏁呴殰璇婃柇鎺ㄧ悊灏嗗叿鏈夊畬鏁寸殑鏄犲皠鏀寔")
        else:
            print(f"\n馃毃 鍙戠幇缂哄け鐨勬槧灏勫叧绯伙紒")
            print(f"  杩欎簺缂哄け鐨勬槧灏勫皢涓ラ噸褰卞搷鏁呴殰璇婃柇鎺ㄧ悊鐨勫噯纭€?)
            print(f"  寤鸿绔嬪嵆琛ュ叏杩欎簺鏄犲皠鍏崇郴")
        
        # 璁＄畻鏄犲皠瑕嗙洊鐜?
        test_coverage = len(mapped_tests) / len(test_names) * 100 if test_names else 0
        fault_coverage = len(mapped_faults) / len(fault_names) * 100 if fault_names else 0
        
        print(f"\n馃搱 鏄犲皠瑕嗙洊鐜?")
        print(f"  娴嬭瘯鐐规槧灏勮鐩栫巼: {test_coverage:.1f}%")
        print(f"  鏁呴殰鏄犲皠瑕嗙洊鐜? {fault_coverage:.1f}%")
        
        if test_coverage < 80 or fault_coverage < 80:
            print(f"\n鈿狅笍  鏄犲皠瑕嗙洊鐜囦笉瓒筹紒")
            print(f"  寤鸿琛ュ叏鏄犲皠鍏崇郴浠ユ彁楂樻晠闅滆瘖鏂殑鍑嗙‘鎬?)
        else:
            print(f"\n鉁?鏄犲皠瑕嗙洊鐜囪壇濂斤紒")
        
        print(f"\n鉁?娴嬭瘯瀹屾垚")
        
    except Exception as e:
        print(f"鉂?娴嬭瘯杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫祴璇曠己澶辨槧灏勬彁绀哄姛鑳?..")
    test_mapping_alert()

