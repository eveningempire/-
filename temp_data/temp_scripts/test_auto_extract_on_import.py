#!/usr/bin/env python
"""
娴嬭瘯MSFG瀵煎叆鏃剁殑鑷姩鏄犲皠鎻愬彇鍔熻兘
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel, TestPointComponentMapping, FaultComponentMapping

def test_auto_extract_on_import():
    print("馃攳 娴嬭瘯MSFG瀵煎叆鏃剁殑鑷姩鏄犲皠鎻愬彇鍔熻兘")
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
            
        print(f"馃搵 妫€鏌SFG: {msfg_definition}")
        print(f"  馃搮 鍒涘缓鏃堕棿: {msfg_definition.created_at}")
        
        # 妫€鏌ユ槧灏勫叧绯?
        print(f"\n馃搳 褰撳墠鏄犲皠鍏崇郴:")
        
        # 1. 娴嬬偣-閮ㄤ欢鏄犲皠
        test_component_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
        print(f"  娴嬬偣-閮ㄤ欢鏄犲皠: {test_component_mappings.count()} 涓?)
        if test_component_mappings.exists():
            print(f"    绀轰緥:")
            for mapping in test_component_mappings[:5]:
                print(f"      {mapping.test_point_name} -> {mapping.component_name} (鏉冮噸: {mapping.weight})")
            if test_component_mappings.count() > 5:
                print(f"      ... 杩樻湁 {test_component_mappings.count() - 5} 涓?)
        
        # 2. 鏁呴殰-閮ㄤ欢鏄犲皠
        fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg_definition)
        print(f"  鏁呴殰-閮ㄤ欢鏄犲皠: {fault_component_mappings.count()} 涓?)
        if fault_component_mappings.exists():
            print(f"    绀轰緥:")
            for mapping in fault_component_mappings[:5]:
                print(f"      {mapping.fault_name} -> {mapping.component_name} (鏉冮噸: {mapping.weight})")
            if fault_component_mappings.count() > 5:
                print(f"      ... 杩樻湁 {fault_component_mappings.count() - 5} 涓?)
        
        # 3. 妫€鏌SFG瀹氫箟涓殑瀛楁
        print(f"\n馃搵 MSFG瀹氫箟瀛楁:")
        print(f"  娴嬭瘯鐐规暟閲? {len(msfg_definition.test_names or [])}")
        print(f"  鏁呴殰鏁伴噺: {len(msfg_definition.fault_names or [])}")
        print(f"  閮ㄤ欢鏁伴噺: {len(msfg_definition.component_names or [])}")
        
        if msfg_definition.component_names:
            print(f"  閮ㄤ欢鍒楄〃: {msfg_definition.component_names}")
        
        # 4. 缁熻鏄犲皠瑕嗙洊鐜?
        print(f"\n馃搱 鏄犲皠瑕嗙洊鐜囧垎鏋?")
        
        # 娴嬬偣瑕嗙洊鐜?
        test_names = msfg_definition.test_names or []
        mapped_tests = set(test_component_mappings.values_list('test_point_name', flat=True))
        test_coverage = len(mapped_tests) / len(test_names) * 100 if test_names else 0
        print(f"  娴嬬偣瑕嗙洊鐜? {test_coverage:.1f}% ({len(mapped_tests)}/{len(test_names)})")
        
        # 鏁呴殰瑕嗙洊鐜?
        fault_names = msfg_definition.fault_names or []
        mapped_faults = set(fault_component_mappings.values_list('fault_name', flat=True))
        fault_coverage = len(mapped_faults) / len(fault_names) * 100 if fault_names else 0
        print(f"  鏁呴殰瑕嗙洊鐜? {fault_coverage:.1f}% ({len(mapped_faults)}/{len(fault_names)})")
        
        # 閮ㄤ欢瑕嗙洊鐜?
        component_names = msfg_definition.component_names or []
        mapped_components = set(test_component_mappings.values_list('component_name', flat=True))
        component_coverage = len(mapped_components) / len(component_names) * 100 if component_names else 0
        print(f"  閮ㄤ欢瑕嗙洊鐜? {component_coverage:.1f}% ({len(mapped_components)}/{len(component_names)})")
        
        # 5. 妫€鏌ユ湭鏄犲皠鐨勯」鐩?
        print(f"\n鈿狅笍 鏈槧灏勯」鐩?")
        
        unmapped_tests = set(test_names) - mapped_tests
        if unmapped_tests:
            print(f"  鏈槧灏勭殑娴嬭瘯鐐? {list(unmapped_tests)}")
        else:
            print(f"  鉁?鎵€鏈夋祴璇曠偣閮藉凡鏄犲皠")
        
        unmapped_faults = set(fault_names) - mapped_faults
        if unmapped_faults:
            print(f"  鏈槧灏勭殑鏁呴殰: {list(unmapped_faults)}")
        else:
            print(f"  鉁?鎵€鏈夋晠闅滈兘宸叉槧灏?)
        
        unmapped_components = set(component_names) - mapped_components
        if unmapped_components:
            print(f"  鏈槧灏勭殑閮ㄤ欢: {list(unmapped_components)}")
        else:
            print(f"  鉁?鎵€鏈夐儴浠堕兘宸叉槧灏?)
        
        print(f"\n鉁?鑷姩鏄犲皠鎻愬彇鍔熻兘妫€鏌ュ畬鎴?)
        
        # 6. 寤鸿
        print(f"\n馃挕 寤鸿:")
        if test_coverage < 100:
            print(f"  1. 娴嬬偣瑕嗙洊鐜囦笉瓒筹紝寤鸿鎵嬪姩琛ュ厖娴嬬偣-閮ㄤ欢鏄犲皠")
        if fault_coverage < 100:
            print(f"  2. 鏁呴殰瑕嗙洊鐜囦笉瓒筹紝寤鸿鎵嬪姩琛ュ厖鏁呴殰-閮ㄤ欢鏄犲皠")
        if component_coverage < 100:
            print(f"  3. 閮ㄤ欢瑕嗙洊鐜囦笉瓒筹紝寤鸿妫€鏌SFG鍥剧粨鏋?)
        
        print(f"  4. 鍙互閫氳繃鍓嶇鐣岄潰杩涗竴姝ヨ皟鏁存槧灏勬潈閲嶅拰鍏崇郴")
        
    except Exception as e:
        print(f"鉂?妫€鏌ヨ繃绋嬩腑鍑洪敊: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫祴璇曡嚜鍔ㄦ槧灏勬彁鍙栧姛鑳?..")
    test_auto_extract_on_import()



