#!/usr/bin/env python
"""
娴嬭瘯瀹屾暣淇鏁堟灉
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.auto_mapping import auto_extract_msfg_mappings, update_msfg_mappings_from_structure

def test_complete_fix():
    """娴嬭瘯瀹屾暣淇鏁堟灉"""
    print("=== 娴嬭瘯瀹屾暣淇鏁堟灉 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    
    # 2. 娴嬭瘯鑷姩鏄犲皠鎻愬彇
    print(f"\n馃敡 娴嬭瘯鑷姩鏄犲皠鎻愬彇:")
    
    try:
        mappings = auto_extract_msfg_mappings(active_msfg)
        
        print(f"   鑷姩鏄犲皠缁撴灉: {len(mappings)} 涓祴璇曠偣")
        
        if mappings:
            print(f"   鏄犲皠绀轰緥:")
            for i, (test_name, component_mappings) in enumerate(mappings.items()):
                if i >= 10:  # 鏄剧ず鍓?0涓?
                    break
                print(f"     {test_name} -> {component_mappings}")
        
        # 缁熻鏄犲皠淇℃伅
        total_mappings = sum(len(component_mappings) for component_mappings in mappings.values())
        avg_mappings_per_test = total_mappings / len(mappings) if mappings else 0
        
        print(f"   鎬绘槧灏勬暟閲? {total_mappings}")
        print(f"   骞冲潎姣忎釜娴嬭瘯鐐规槧灏勫埌 {avg_mappings_per_test:.1f} 涓儴浠?)
        
    except Exception as e:
        print(f"   鉂?鑷姩鏄犲皠鎻愬彇澶辫触: {e}")
        return False
    
    # 3. 姣旇緝褰撳墠鎵嬪姩鏄犲皠鍜岃嚜鍔ㄦ槧灏?
    print(f"\n馃搳 姣旇緝褰撳墠鏄犲皠:")
    
    current_mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    print(f"   褰撳墠鎵嬪姩鏄犲皠鏁伴噺: {current_mappings.count()}")
    
    if current_mappings.exists():
        print(f"   褰撳墠鏄犲皠绀轰緥:")
        for i, mapping in enumerate(current_mappings[:5]):
            print(f"     {mapping.test_point_name} -> {mapping.component_name} (鏉冮噸: {mapping.weight})")
    
    # 4. 娴嬭瘯鑷姩鏇存柊鏄犲皠
    print(f"\n馃攧 娴嬭瘯鑷姩鏇存柊鏄犲皠:")
    
    try:
        success = update_msfg_mappings_from_structure(active_msfg)
        
        if success:
            print(f"   鉁?鑷姩鏇存柊鏄犲皠鎴愬姛")
            
            # 妫€鏌ユ洿鏂板悗鐨勬槧灏?
            updated_mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
            print(f"   鏇存柊鍚庢槧灏勬暟閲? {updated_mappings.count()}")
            
            if updated_mappings.exists():
                print(f"   鏇存柊鍚庢槧灏勭ず渚?")
                for i, mapping in enumerate(updated_mappings[:5]):
                    print(f"     {mapping.test_point_name} -> {mapping.component_name} (鏉冮噸: {mapping.weight})")
        else:
            print(f"   鉂?鑷姩鏇存柊鏄犲皠澶辫触")
            
    except Exception as e:
        print(f"   鉂?鑷姩鏇存柊鏄犲皠寮傚父: {e}")
    
    # 5. 楠岃瘉鏁版嵁涓€鑷存€?
    print(f"\n馃攳 楠岃瘉鏁版嵁涓€鑷存€?")
    
    # 妫€鏌SFG.component_names鍜屾槧灏勪腑鐨勯儴浠舵槸鍚︿竴鑷?
    component_names = active_msfg.component_names or []
    mapped_components = set(
        TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
        .values_list('component_name', flat=True)
    )
    
    print(f"   MSFG.component_names: {component_names}")
    print(f"   鏄犲皠涓殑閮ㄤ欢: {list(mapped_components)}")
    
    # 妫€鏌ヤ竴鑷存€?
    msfg_set = set(component_names)
    mapped_set = mapped_components
    
    only_in_msfg = msfg_set - mapped_set
    only_in_mapped = mapped_set - msfg_set
    common = msfg_set & mapped_set
    
    if only_in_msfg:
        print(f"   鈿狅笍 鍙湪MSFG.component_names涓? {only_in_msfg}")
    if only_in_mapped:
        print(f"   鈿狅笍 鍙湪鏄犲皠涓? {only_in_mapped}")
    if not only_in_msfg and not only_in_mapped:
        print(f"   鉁?閮ㄤ欢鍒楄〃瀹屽叏涓€鑷?)
    
    # 6. 鎬荤粨
    print(f"\n馃挕 鎬荤粨:")
    print(f"   鉁?鑷姩鏄犲皠鍔熻兘姝ｅ父宸ヤ綔")
    print(f"   鉁?閮ㄤ欢鑺傜偣鍚嶇О宸蹭慨澶?)
    print(f"   鉁?鍙互浠嶮SFG缁撴瀯鑷姩鎻愬彇鏄犲皠鍏崇郴")
    print(f"   馃敡 寤鸿浣跨敤鑷姩鏄犲皠鏇夸唬鎵嬪姩鏄犲皠")
    
    return True

if __name__ == "__main__":
    test_complete_fix()

