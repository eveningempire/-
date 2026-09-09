#!/usr/bin/env python
"""
涓虹敤鎴锋彁渚涘叿浣撶殑鏄犲皠琛ュ叏寤鸿
鍩轰簬MSFG缁撴瀯鍜屽伐绋嬬煡璇嗘彁渚涙櫤鑳藉缓璁?
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel, TestPointComponentMapping, FaultComponentMapping
from collections import defaultdict

def suggest_mapping_completion():
    print("馃挕 涓虹敤鎴锋彁渚涙槧灏勮ˉ鍏ㄥ缓璁?)
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
        
        print(f"\n馃搳 褰撳墠鐘舵€?")
        print(f"  鏈槧灏勬祴鐐? {len(unmapped_tests)} 涓?)
        print(f"  鏈槧灏勬晠闅? {len(unmapped_faults)} 涓?)
        print(f"  鍙敤閮ㄤ欢: {len(component_names)} 涓?)
        
        # 鍩轰簬宸ョ▼鐭ヨ瘑鐨勬槧灏勫缓璁?
        print(f"\n馃敡 娴嬬偣-閮ㄤ欢鏄犲皠寤鸿:")
        
        # 杞€熺浉鍏虫祴鐐?
        speed_tests = [t for t in unmapped_tests if '杞€? in t]
        if speed_tests:
            print(f"  馃搱 杞€熸祴鐐瑰缓璁?")
            for test in speed_tests:
                if '楂橀€? in test:
                    print(f"    {test} 鈫?杞瓙鎺у埗鍣?(楂橀€熻浆閫熸帶鍒?")
                elif '浣庨€? in test:
                    print(f"    {test} 鈫?妗嗘灦鎺у埗鍣?(浣庨€熻浆閫熸帶鍒?")
        
        # 杞存俯鐩稿叧娴嬬偣
        temp_tests = [t for t in unmapped_tests if '杞存俯' in t or '娓╁害' in t]
        if temp_tests:
            print(f"  馃尅锔?杞存俯娴嬬偣寤鸿:")
            for test in temp_tests:
                if '鍥虹揣绔? in test:
                    print(f"    {test} 鈫?杞瓙杞存壙 (鍥虹揣绔酱鎵挎俯搴?")
                elif '婊戝姩绔? in test:
                    print(f"    {test} 鈫?杞瓙杞存壙 (婊戝姩绔酱鎵挎俯搴?")
        
        # 寮€鍏充俊鍙锋祴鐐?
        switch_tests = [t for t in unmapped_tests if '寮€鍏? in t]
        if switch_tests:
            print(f"  馃攲 寮€鍏充俊鍙锋祴鐐瑰缓璁?")
            for test in switch_tests:
                if '100V' in test:
                    print(f"    {test} 鈫?鐢垫簮鏉?(100V寮€鍏虫帶鍒?")
        
        # 鍏朵粬娴嬬偣
        other_tests = [t for t in unmapped_tests if t not in speed_tests + temp_tests + switch_tests]
        if other_tests:
            print(f"  馃攳 鍏朵粬娴嬬偣寤鸿:")
            for test in other_tests:
                if 'SPI' in test or '鏃嬪彉' in test:
                    print(f"    {test} 鈫?鏃嬪彉SPI (鏃嬪彉淇″彿澶勭悊)")
                elif '1553' in test:
                    print(f"    {test} 鈫?1553B鎺ュ彛 (閫氫俊鎺ュ彛)")
                else:
                    print(f"    {test} 鈫?闇€瑕佹牴鎹叿浣撳姛鑳界‘瀹?)
        
        # 鏁呴殰-閮ㄤ欢鏄犲皠寤鸿
        print(f"\n馃敡 鏁呴殰-閮ㄤ欢鏄犲皠寤鸿:")
        
        # 鐢垫簮鐩稿叧鏁呴殰
        power_faults = [f for f in unmapped_faults if any(keyword in f for keyword in ['鐢垫簮', '鐢靛帇', 'V', '鍔犵數', '鏂數'])]
        if power_faults:
            print(f"  鈿?鐢垫簮鐩稿叧鏁呴殰寤鸿:")
            for fault in power_faults:
                if '100V' in fault:
                    print(f"    {fault} 鈫?鐢垫簮鏉?(100V鐢垫簮绯荤粺)")
                elif '12V' in fault or '5V' in fault:
                    print(f"    {fault} 鈫?鐢垫簮鏉?(浣庡帇鐢垫簮绯荤粺)")
                else:
                    print(f"    {fault} 鈫?鐢垫簮鏉?(鐢垫簮绯荤粺)")
        
        # 鐢垫満鐩稿叧鏁呴殰
        motor_faults = [f for f in unmapped_faults if any(keyword in f for keyword in ['鐢垫満', '椹卞姩', 'PWM', '缁曠粍'])]
        if motor_faults:
            print(f"  馃殌 鐢垫満鐩稿叧鏁呴殰寤鸿:")
            for fault in motor_faults:
                if '妗嗘灦' in fault:
                    print(f"    {fault} 鈫?妗嗘灦鎺у埗鍣?(妗嗘灦鐢垫満鎺у埗)")
                elif '杞瓙' in fault:
                    print(f"    {fault} 鈫?杞瓙鎺у埗鍣?(杞瓙鐢垫満鎺у埗)")
                else:
                    print(f"    {fault} 鈫?杞瓙椹卞姩鐢垫満 (鐢垫満鏈綋)")
        
        # 杞存壙鐩稿叧鏁呴殰
        bearing_faults = [f for f in unmapped_faults if any(keyword in f for keyword in ['杞存壙', '杞存俯', '娓╁害'])]
        if bearing_faults:
            print(f"  馃攧 杞存壙鐩稿叧鏁呴殰寤鸿:")
            for fault in bearing_faults:
                print(f"    {fault} 鈫?杞瓙杞存壙 (杞存壙绯荤粺)")
        
        # 閫氫俊鐩稿叧鏁呴殰
        comm_faults = [f for f in unmapped_faults if any(keyword in f for keyword in ['閫氫俊', '1553', 'SPI', '瑙ｈ皟'])]
        if comm_faults:
            print(f"  馃摗 閫氫俊鐩稿叧鏁呴殰寤鸿:")
            for fault in comm_faults:
                if '1553' in fault:
                    print(f"    {fault} 鈫?1553B鎺ュ彛 (1553閫氫俊)")
                elif 'SPI' in fault or '鏃嬪彉' in fault:
                    print(f"    {fault} 鈫?鏃嬪彉SPI (鏃嬪彉淇″彿)")
                elif '瑙ｈ皟' in fault:
                    print(f"    {fault} 鈫?鏃嬪彉瑙ｈ皟鏈虹 (淇″彿瑙ｈ皟)")
        
        # 閲囨牱鐩稿叧鏁呴殰
        sampling_faults = [f for f in unmapped_faults if any(keyword in f for keyword in ['閲囨牱', '閲囬泦', '鐢垫祦', '鐢靛帇'])]
        if sampling_faults:
            print(f"  馃搳 閲囨牱鐩稿叧鏁呴殰寤鸿:")
            for fault in sampling_faults:
                if '鐢垫祦' in fault:
                    if '妗嗘灦' in fault:
                        print(f"    {fault} 鈫?妗嗘灦鐢垫祦閲囨牱 (妗嗘灦鐢垫祦)")
                    else:
                        print(f"    {fault} 鈫?杞瓙鐢垫祦閲囨牱 (杞瓙鐢垫祦)")
                elif '鐢靛帇' in fault:
                    print(f"    {fault} 鈫?妗嗘灦鐢垫祦閲囨牱 (鐢靛帇閲囨牱)")
                else:
                    print(f"    {fault} 鈫?闇€瑕佹牴鎹叿浣撳姛鑳界‘瀹?)
        
        # 鍏朵粬鏁呴殰
        other_faults = [f for f in unmapped_faults if f not in power_faults + motor_faults + bearing_faults + comm_faults + sampling_faults]
        if other_faults:
            print(f"  馃攳 鍏朵粬鏁呴殰寤鸿:")
            for fault in other_faults[:10]:  # 鍙樉绀哄墠10涓?
                print(f"    {fault} 鈫?闇€瑕佹牴鎹叿浣撳姛鑳界‘瀹?)
            if len(other_faults) > 10:
                print(f"    ... 杩樻湁 {len(other_faults) - 10} 涓晠闅滈渶瑕佹墜鍔ㄧ‘瀹?)
        
        # 浼樺厛绾у缓璁?
        print(f"\n馃幆 琛ュ叏浼樺厛绾у缓璁?")
        print(f"  1. 楂樹紭鍏堢骇 - 杞€熸祴鐐规槧灏?(褰卞搷杞€熸帶鍒?")
        print(f"  2. 楂樹紭鍏堢骇 - 杞存俯娴嬬偣鏄犲皠 (褰卞搷瀹夊叏鐩戞祴)")
        print(f"  3. 涓紭鍏堢骇 - 鐢垫簮鏁呴殰鏄犲皠 (褰卞搷绯荤粺渚涚數)")
        print(f"  4. 涓紭鍏堢骇 - 鐢垫満鏁呴殰鏄犲皠 (褰卞搷椹卞姩鎺у埗)")
        print(f"  5. 浣庝紭鍏堢骇 - 鍏朵粬鏁呴殰鏄犲皠 (瀹屽杽璇婃柇瑕嗙洊)")
        
        # 蹇€熻ˉ鍏ㄥ缓璁?
        print(f"\n鈿?蹇€熻ˉ鍏ㄥ缓璁?")
        print(f"  1. 浣跨敤鍓嶇鏄犲皠缂栬緫鍣ㄦ壒閲忔坊鍔犲缓璁殑鏄犲皠")
        print(f"  2. 閲嶇偣鍏虫敞楂樹紭鍏堢骇鏄犲皠")
        print(f"  3. 鏍规嵁瀹為檯宸ョ▼缁忛獙璋冩暣鏄犲皠鍏崇郴")
        print(f"  4. 娴嬭瘯鏄犲皠鍚庣殑鎺ㄧ悊鏁堟灉")
        
        print(f"\n鉁?鏄犲皠琛ュ叏寤鸿鐢熸垚瀹屾垚")
        
    except Exception as e:
        print(f"鉂?鐢熸垚寤鸿杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬬敓鎴愭槧灏勮ˉ鍏ㄥ缓璁?..")
    suggest_mapping_completion()

