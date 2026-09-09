#!/usr/bin/env python
"""
妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠鐨勬暟鎹拰閫昏緫
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.component_integration import extract_components_from_msfg

def check_component_mappings():
    """妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠"""
    print("=== 妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    print(f"   PHM妯″瀷: {active_msfg.cmg_model.model_name}")
    
    # 2. 妫€鏌SFG瀹氫箟涓殑閮ㄤ欢
    print(f"\n2. MSFG瀹氫箟涓殑閮ㄤ欢:")
    if active_msfg.component_names:
        for i, component in enumerate(active_msfg.component_names, 1):
            print(f"   {i}. {component}")
    else:
        print("   鈿狅笍 娌℃湁瀹氫箟閮ㄤ欢")
    
    # 3. 妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠
    print(f"\n3. 娴嬭瘯鐐?閮ㄤ欢鏄犲皠:")
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    print(f"   鏄犲皠鏁伴噺: {mappings.count()}")
    
    if mappings.count() == 0:
        print("   鈿狅笍 娌℃湁鎵惧埌娴嬭瘯鐐?閮ㄤ欢鏄犲皠")
        print("   杩欒В閲婁簡涓轰粈涔堥儴浠跺仴搴峰垎鏁伴兘鏄?.0")
    else:
        for mapping in mappings:
            print(f"   娴嬭瘯鐐? {mapping.test_point_name} -> 閮ㄤ欢: {mapping.component_name}")
            print(f"     鏉冮噸: {mapping.importance_weight}, 鍏抽敭: {mapping.is_critical}")
    
    # 4. 妫€鏌ユ祴璇曠偣鍒楄〃
    print(f"\n4. MSFG瀹氫箟涓殑娴嬭瘯鐐?")
    if active_msfg.test_names:
        for i, test_name in enumerate(active_msfg.test_names, 1):
            print(f"   {i}. {test_name}")
    else:
        print("   鈿狅笍 娌℃湁瀹氫箟娴嬭瘯鐐?)
    
    # 5. 灏濊瘯鎻愬彇閮ㄤ欢
    print(f"\n5. 浠嶮SFG鎻愬彇鐨勯儴浠?")
    extracted_components = extract_components_from_msfg(active_msfg)
    print(f"   鎻愬彇鍒?{len(extracted_components)} 涓儴浠?")
    for i, component in enumerate(extracted_components, 1):
        print(f"   {i}. {component}")
    
    # 6. 鍒嗘瀽闂
    print(f"\n6. 闂鍒嗘瀽:")
    if mappings.count() == 0:
        print("   鉂?涓昏闂: 娌℃湁娴嬭瘯鐐?閮ㄤ欢鏄犲皠")
        print("   馃挕 瑙ｅ喅鏂规: 闇€瑕佸垱寤烘祴璇曠偣-閮ㄤ欢鏄犲皠")
        
        # 妫€鏌ユ槸鍚︽湁娴嬭瘯鐐瑰拰閮ㄤ欢
        if active_msfg.test_names and extracted_components:
            print(f"   鉁?鏈?{len(active_msfg.test_names)} 涓祴璇曠偣")
            print(f"   鉁?鏈?{len(extracted_components)} 涓儴浠?)
            print("   馃挕 寤鸿: 涓烘瘡涓祴璇曠偣鍒涘缓鍒扮浉搴旈儴浠剁殑鏄犲皠")
        else:
            print("   鉂?缂哄皯娴嬭瘯鐐规垨閮ㄤ欢瀹氫箟")
    else:
        print("   鉁?鏈夋祴璇曠偣-閮ㄤ欢鏄犲皠")
        print("   馃攳 闇€瑕佹鏌ユ槧灏勬槸鍚︽纭尮閰嶆祴璇曠偣鍚嶇О")
    
    return True

if __name__ == '__main__':
    check_component_mappings()

