#!/usr/bin/env python
"""
鍒嗘瀽椤甸潰涓嬫柟"绯荤粺鎻愬彇鐨勯儴浠?鍜岄〉闈笂鏂?閮ㄤ欢"涓嬫媺妗嗕腑鐨勯儴浠朵笉涓€鑷撮棶棰?
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping

def analyze_component_inconsistency():
    """鍒嗘瀽閮ㄤ欢涓嶄竴鑷撮棶棰?""
    print("=== 閮ㄤ欢涓嶄竴鑷撮棶棰樺垎鏋?===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    
    # 2. 鍒嗘瀽椤甸潰涓嬫柟"绯荤粺鎻愬彇鐨勯儴浠?锛堟潵鑷狹SFG.component_names锛?
    print(f"\n馃搵 椤甸潰涓嬫柟'绯荤粺鎻愬彇鐨勯儴浠?锛堟潵鑷狹SFG.component_names锛?")
    component_names = active_msfg.component_names or []
    print(f"   閮ㄤ欢鏁伴噺: {len(component_names)}")
    for i, component in enumerate(component_names, 1):
        print(f"   {i}. {component}")
    
    # 3. 鍒嗘瀽椤甸潰涓婃柟"閮ㄤ欢"涓嬫媺妗嗕腑鐨勯儴浠讹紙鏉ヨ嚜TestPointComponentMapping锛?
    print(f"\n馃敡 椤甸潰涓婃柟'閮ㄤ欢'涓嬫媺妗嗕腑鐨勯儴浠讹紙鏉ヨ嚜TestPointComponentMapping锛?")
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    mapped_components = set()
    for mapping in mappings:
        mapped_components.add(mapping.component_name)
    
    mapped_components_list = sorted(list(mapped_components))
    print(f"   閮ㄤ欢鏁伴噺: {len(mapped_components_list)}")
    for i, component in enumerate(mapped_components_list, 1):
        print(f"   {i}. {component}")
    
    # 4. 姣旇緝涓や釜鏉ユ簮鐨勯儴浠?
    print(f"\n馃攳 姣旇緝鍒嗘瀽:")
    component_names_set = set(component_names)
    mapped_components_set = set(mapped_components_list)
    
    print(f"   MSFG.component_names涓殑閮ㄤ欢: {component_names}")
    print(f"   TestPointComponentMapping涓殑閮ㄤ欢: {mapped_components_list}")
    
    # 妫€鏌ュ樊寮?
    if component_names_set == mapped_components_set:
        print(f"   鉁?涓や釜鏉ユ簮鐨勯儴浠跺畬鍏ㄤ竴鑷?)
    else:
        print(f"   鉂?涓や釜鏉ユ簮鐨勯儴浠朵笉涓€鑷达紒")
        
        # 鍙湪component_names涓?
        only_in_component_names = component_names_set - mapped_components_set
        if only_in_component_names:
            print(f"   鍙湪MSFG.component_names涓? {list(only_in_component_names)}")
        
        # 鍙湪TestPointComponentMapping涓?
        only_in_mappings = mapped_components_set - component_names_set
        if only_in_mappings:
            print(f"   鍙湪TestPointComponentMapping涓? {list(only_in_mappings)}")
    
    # 5. 鍒嗘瀽闂鏍规簮
    print(f"\n鉂?闂鏍规簮鍒嗘瀽:")
    
    # 闂1: 鏁版嵁鏉ユ簮涓嶅悓
    print(f"   闂1: 鏁版嵁鏉ユ簮涓嶅悓")
    print(f"      - 椤甸潰涓嬫柟: 鏉ヨ嚜MSFG.component_names瀛楁")
    print(f"      - 椤甸潰涓婃柟: 鏉ヨ嚜TestPointComponentMapping琛?)
    print(f"      - 杩欎袱涓暟鎹簮搴旇淇濇寔涓€鑷达紝浣嗗綋鍓嶄笉鍚屾")
    
    # 闂2: 鏇存柊鏃舵満涓嶅悓
    print(f"   闂2: 鏇存柊鏃舵満涓嶅悓")
    print(f"      - MSFG.component_names: 鍦∕SFG缂栬緫鍣ㄤ繚瀛樻椂鏇存柊")
    print(f"      - TestPointComponentMapping: 鍦ㄧ敤鎴风紪杈戞槧灏勬椂鏇存柊")
    print(f"      - 缂哄皯鍚屾鏈哄埗")
    
    # 闂3: 鏁版嵁鍒涘缓閫昏緫涓嶅悓
    print(f"   闂3: 鏁版嵁鍒涘缓閫昏緫涓嶅悓")
    print(f"      - MSFG.component_names: 浠嶮SFG缁撴瀯涓彁鍙?)
    print(f"      - TestPointComponentMapping: 鍙兘鏉ヨ嚜鎵嬪姩杈撳叆鎴栧叾浠栨潵婧?)
    
    # 6. 鍒嗘瀽姝ｇ‘鐨勬暟鎹祦
    print(f"\n鉁?姝ｇ‘鐨勬暟鎹祦搴旇鏄?")
    print(f"   1. MSFG缂栬緫鍣ㄤ繚瀛樻椂锛屼粠MSFG缁撴瀯涓彁鍙栭儴浠?)
    print(f"   2. 鏇存柊MSFG.component_names瀛楁")
    print(f"   3. 閮ㄤ欢鏄犲皠鐣岄潰鍔犺浇鏃讹紝浣跨敤MSFG.component_names浣滀负涓嬫媺妗嗛€夐」")
    print(f"   4. 鐢ㄦ埛閫夋嫨閮ㄤ欢鍒涘缓鏄犲皠鏃讹紝楠岃瘉閮ㄤ欢鍚嶇О鏄惁鍦∕SFG.component_names涓?)
    
    # 7. 妫€鏌ュ綋鍓嶅疄鐜?
    print(f"\n馃敡 褰撳墠瀹炵幇妫€鏌?")
    
    # 妫€鏌SFG.component_names鏄惁姝ｇ‘鎻愬彇
    print(f"   1. MSFG.component_names鎻愬彇閫昏緫:")
    print(f"      - 褰撳墠鏂规硶: 浠嶴ystemData涓彁鍙杗ame瀛楁")
    print(f"      - 闂: SystemData涓嶆槸閮ㄤ欢鑺傜偣锛岃€屾槸绯荤粺淇℃伅")
    print(f"      - 搴旇: 浠巒odes涓彁鍙杢ype='system'鐨勮妭鐐?)
    
    # 妫€鏌estPointComponentMapping鐨勫垱寤洪€昏緫
    print(f"   2. TestPointComponentMapping鍒涘缓閫昏緫:")
    print(f"      - 褰撳墠: 鍙兘鏉ヨ嚜鎵嬪姩杈撳叆鎴栭粯璁ゅ€?)
    print(f"      - 搴旇: 浠嶮SFG.component_names涓€夋嫨")
    
    # 8. 寤鸿淇鏂规
    print(f"\n馃挕 淇鏂规:")
    print(f"   鏂规1: 淇MSFG.component_names鐨勬彁鍙栭€昏緫")
    print(f"      - 淇敼_extract_component_names鏂规硶")
    print(f"      - 浠巒odes涓彁鍙杢ype='system'鐨勮妭鐐?)
    
    print(f"   鏂规2: 缁熶竴閮ㄤ欢鏉ユ簮")
    print(f"      - 閮ㄤ欢鏄犲皠鐣岄潰浣跨敤MSFG.component_names浣滀负鏁版嵁婧?)
    print(f"      - 鍒涘缓鏄犲皠鏃堕獙璇侀儴浠跺悕绉?)
    
    print(f"   鏂规3: 寤虹珛鍚屾鏈哄埗")
    print(f"      - MSFG淇濆瓨鏃惰嚜鍔ㄦ洿鏂扮浉鍏虫槧灏?)
    print(f"      - 寤虹珛鏁版嵁涓€鑷存€ф鏌?)
    
    # 9. 鍏蜂綋淇姝ラ
    print(f"\n馃敡 鍏蜂綋淇姝ラ:")
    print(f"   姝ラ1: 淇_extract_component_names鏂规硶")
    print(f"   姝ラ2: 淇敼閮ㄤ欢鏄犲皠鐣岄潰锛屼娇鐢∕SFG.component_names")
    print(f"   姝ラ3: 娣诲姞鏁版嵁楠岃瘉锛岀‘淇濇槧灏勪腑鐨勯儴浠跺湪MSFG.component_names涓?)
    print(f"   姝ラ4: 寤虹珛鏁版嵁鍚屾鏈哄埗")
    
    return True

if __name__ == "__main__":
    analyze_component_inconsistency()

