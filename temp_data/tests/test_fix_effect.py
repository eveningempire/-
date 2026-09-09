#!/usr/bin/env python
"""
娴嬭瘯MSFG缂栬緫鍣ㄤ繚瀛橀€昏緫淇鏁堟灉
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping
from msfg_analysis.views import MSFGEditorView

def test_fix_effect():
    """娴嬭瘯淇鏁堟灉"""
    print("=== 娴嬭瘯MSFG缂栬緫鍣ㄤ繚瀛橀€昏緫淇鏁堟灉 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    
    # 2. 娴嬭瘯鏂扮殑閮ㄤ欢鎻愬彇閫昏緫
    print(f"\n馃攳 娴嬭瘯鏂扮殑閮ㄤ欢鎻愬彇閫昏緫:")
    
    # 鍒涘缓MSFGEditorView瀹炰緥
    editor_view = MSFGEditorView()
    
    # 浣跨敤鏂扮殑_extract_component_names鏂规硶
    raw_data = active_msfg.raw_graph_data
    extracted_components = editor_view._extract_component_names(raw_data)
    
    print(f"   鏂版柟娉曟彁鍙栫殑閮ㄤ欢: {extracted_components}")
    print(f"   褰撳墠MSFG.component_names: {active_msfg.component_names}")
    
    # 3. 姣旇緝缁撴灉
    print(f"\n馃搵 姣旇緝缁撴灉:")
    if extracted_components == active_msfg.component_names:
        print(f"   鉁?鏂版柟娉曟彁鍙栫殑閮ㄤ欢涓庡綋鍓峜omponent_names涓€鑷?)
    else:
        print(f"   鉂?鏂版柟娉曟彁鍙栫殑閮ㄤ欢涓庡綋鍓峜omponent_names涓嶄竴鑷?)
        print(f"   宸紓: {set(extracted_components) ^ set(active_msfg.component_names or [])}")
    
    # 4. 娴嬭瘯API绔偣
    print(f"\n馃寪 娴嬭瘯API绔偣:")
    print(f"   鏂扮殑API绔偣: /api/v1/msfg/testpoint-component-mappings/available-components/")
    print(f"   鍙傛暟: msfg_definition_id={active_msfg.id}")
    
    # 5. 娴嬭瘯鏁版嵁楠岃瘉
    print(f"\n馃敀 娴嬭瘯鏁版嵁楠岃瘉:")
    
    # 妫€鏌ュ綋鍓嶆槧灏勪腑鐨勯儴浠舵槸鍚﹂兘鍦∕SFG.component_names涓?
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    invalid_mappings = []
    
    for mapping in mappings:
        if mapping.component_name not in (active_msfg.component_names or []):
            invalid_mappings.append(mapping)
    
    if invalid_mappings:
        print(f"   鈿狅笍 鍙戠幇 {len(invalid_mappings)} 涓棤鏁堟槧灏?")
        for mapping in invalid_mappings:
            print(f"     - {mapping.test_point_name} -> {mapping.component_name}")
    else:
        print(f"   鉁?鎵€鏈夋槧灏勯兘鏄湁鏁堢殑")
    
    # 6. 寤鸿涓嬩竴姝ユ搷浣?
    print(f"\n馃挕 寤鸿涓嬩竴姝ユ搷浣?")
    print(f"   1. 濡傛灉鏂版柟娉曟彁鍙栫殑閮ㄤ欢涓庡綋鍓嶄笉涓€鑷达紝闇€瑕侀噸鏂颁繚瀛楳SFG")
    print(f"   2. 濡傛灉鏈夋棤鏁堟槧灏勶紝闇€瑕佹竻鐞嗘垨淇")
    print(f"   3. 娴嬭瘯鍓嶇鐣岄潰鏄惁浣跨敤鏂扮殑API绔偣")
    
    return True

if __name__ == "__main__":
    test_fix_effect()

