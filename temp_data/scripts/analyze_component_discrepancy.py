#!/usr/bin/env python
"""
鍒嗘瀽MSFG閮ㄤ欢瀵瑰簲绠＄悊鐣岄潰涓儴浠朵笉涓€鑷寸殑闂
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.component_integration import extract_components_from_msfg

def analyze_component_discrepancy():
    """鍒嗘瀽閮ㄤ欢涓嶄竴鑷撮棶棰?""
    print("=== MSFG閮ㄤ欢瀵瑰簲绠＄悊鐣岄潰鍒嗘瀽 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    print(f"   PHM妯″瀷: {active_msfg.cmg_model.model_name}")
    
    # 2. 鍒嗘瀽"绯荤粺鎻愬彇鐨勯儴浠?锛堥〉闈笅鏂规樉绀猴級
    print(f"\n馃搵 椤甸潰涓嬫柟'绯荤粺鎻愬彇鐨勯儴浠?锛堟潵鑷狹SFG.component_names锛?")
    if active_msfg.component_names:
        for i, component in enumerate(active_msfg.component_names, 1):
            print(f"   {i}. {component}")
    else:
        print("   鈿狅笍 娌℃湁瀹氫箟閮ㄤ欢")
    
    # 3. 鍒嗘瀽"缂栬緫娴嬬偣-閮ㄤ欢瀵瑰簲鍏崇郴"涓殑閮ㄤ欢锛堥〉闈笂鏂规樉绀猴級
    print(f"\n馃敡 椤甸潰涓婃柟'缂栬緫娴嬬偣-閮ㄤ欢瀵瑰簲鍏崇郴'涓殑閮ㄤ欢锛堟潵鑷猅estPointComponentMapping锛?")
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    print(f"   鏄犲皠鏁伴噺: {mappings.count()}")
    
    if mappings.count() == 0:
        print("   鈿狅笍 娌℃湁鎵惧埌娴嬭瘯鐐?閮ㄤ欢鏄犲皠")
    else:
        # 鏀堕泦鏄犲皠涓殑閮ㄤ欢
        mapped_components = set()
        for mapping in mappings:
            mapped_components.add(mapping.component_name)
            print(f"   娴嬭瘯鐐? {mapping.test_point_name} -> 閮ㄤ欢: {mapping.component_name}")
        
        print(f"\n   鏄犲皠涓殑閮ㄤ欢鍒楄〃:")
        for i, component in enumerate(sorted(mapped_components), 1):
            print(f"   {i}. {component}")
    
    # 4. 鍒嗘瀽浠嶮SFG缁撴瀯涓彁鍙栫殑閮ㄤ欢
    print(f"\n馃攳 浠嶮SFG缁撴瀯涓彁鍙栫殑閮ㄤ欢锛坋xtract_components_from_msfg鍑芥暟锛?")
    extracted_components = extract_components_from_msfg(active_msfg)
    for i, component in enumerate(extracted_components, 1):
        print(f"   {i}. {component}")
    
    # 5. 闂鍒嗘瀽
    print(f"\n鉂?闂鍒嗘瀽:")
    
    # 姣旇緝涓変釜鏉ユ簮鐨勯儴浠?
    component_names_set = set(active_msfg.component_names or [])
    mapped_components_set = set()
    for mapping in mappings:
        mapped_components_set.add(mapping.component_name)
    extracted_components_set = set(extracted_components)
    
    print(f"   MSFG.component_names 涓殑閮ㄤ欢鏁伴噺: {len(component_names_set)}")
    print(f"   TestPointComponentMapping 涓殑閮ㄤ欢鏁伴噺: {len(mapped_components_set)}")
    print(f"   extract_components_from_msfg 鎻愬彇鐨勯儴浠舵暟閲? {len(extracted_components_set)}")
    
    # 妫€鏌ュ樊寮?
    if component_names_set != mapped_components_set:
        print(f"   鈿狅笍 MSFG.component_names 涓?TestPointComponentMapping 涓殑閮ㄤ欢涓嶄竴鑷?")
        print(f"   鍙湪 component_names 涓? {component_names_set - mapped_components_set}")
        print(f"   鍙湪鏄犲皠涓? {mapped_components_set - component_names_set}")
    
    if component_names_set != extracted_components_set:
        print(f"   鈿狅笍 MSFG.component_names 涓?extract_components_from_msfg 鎻愬彇鐨勯儴浠朵笉涓€鑷?")
        print(f"   鍙湪 component_names 涓? {component_names_set - extracted_components_set}")
        print(f"   鍙湪鎻愬彇涓? {extracted_components_set - component_names_set}")
    
    # 6. 寤鸿瑙ｅ喅鏂规
    print(f"\n馃挕 寤鸿瑙ｅ喅鏂规:")
    print(f"   1. 椤甸潰涓嬫柟鏄剧ず鐨?绯荤粺鎻愬彇鐨勯儴浠?鏉ヨ嚜 MSFG.component_names 瀛楁")
    print(f"   2. 椤甸潰涓婃柟缂栬緫鐨?娴嬬偣-閮ㄤ欢瀵瑰簲鍏崇郴'鏉ヨ嚜 TestPointComponentMapping 琛?)
    print(f"   3. 杩欎袱涓暟鎹簮搴旇淇濇寔涓€鑷达紝浣嗗綋鍓嶅瓨鍦ㄥ樊寮?)
    print(f"   4. 寤鸿:")
    print(f"      - 妫€鏌?MSFG 缂栬緫鍣ㄤ繚瀛樻椂鏄惁姝ｇ‘鏇存柊浜?component_names")
    print(f"      - 妫€鏌?TestPointComponentMapping 鐨勫垱寤洪€昏緫")
    print(f"      - 鑰冭檻浣跨敤 extract_components_from_msfg 鍑芥暟缁熶竴閮ㄤ欢鏉ユ簮")
    
    return True

if __name__ == "__main__":
    analyze_component_discrepancy()

