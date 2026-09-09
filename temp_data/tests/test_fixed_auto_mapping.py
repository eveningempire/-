#!/usr/bin/env python
"""
娴嬭瘯淇鍚庣殑鑷姩鏄犲皠
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.auto_mapping import auto_extract_msfg_mappings, update_msfg_mappings_from_structure

def test_fixed_auto_mapping():
    """娴嬭瘯淇鍚庣殑鑷姩鏄犲皠"""
    print("=== 娴嬭瘯淇鍚庣殑鑷姩鏄犲皠 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    
    # 2. 鏄剧ずMSFG.component_names
    component_names = active_msfg.component_names or []
    print(f"馃搵 MSFG.component_names: {component_names}")
    print(f"   閮ㄤ欢鏁伴噺: {len(component_names)}")
    
    # 3. 娴嬭瘯鑷姩鏄犲皠鎻愬彇
    print(f"\n馃敡 娴嬭瘯鑷姩鏄犲皠鎻愬彇:")
    
    try:
        mappings = auto_extract_msfg_mappings(active_msfg)
        
        print(f"   鑷姩鏄犲皠缁撴灉: {len(mappings)} 涓祴璇曠偣")
        
        # 缁熻浣跨敤鐨勯儴浠?
        used_components = set()
        for test_name, component_mappings in mappings.items():
            for component_name, _ in component_mappings:
                used_components.add(component_name)
        
        print(f"   鑷姩鏄犲皠浣跨敤鐨勯儴浠? {list(used_components)}")
        print(f"   浣跨敤鐨勯儴浠舵暟閲? {len(used_components)}")
        
        if mappings:
            print(f"   鏄犲皠绀轰緥:")
            for i, (test_name, component_mappings) in enumerate(mappings.items()):
                if i >= 5:  # 鍙樉绀哄墠5涓?
                    break
                print(f"     {test_name} -> {component_mappings}")
        
    except Exception as e:
        print(f"   鉂?鑷姩鏄犲皠鎻愬彇澶辫触: {e}")
        return False
    
    # 4. 娴嬭瘯鑷姩鏇存柊鏄犲皠
    print(f"\n馃攧 娴嬭瘯鑷姩鏇存柊鏄犲皠:")
    
    try:
        success = update_msfg_mappings_from_structure(active_msfg)
        
        if success:
            print(f"   鉁?鑷姩鏇存柊鏄犲皠鎴愬姛")
            
            # 妫€鏌ユ洿鏂板悗鐨勬槧灏?
            updated_mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
            print(f"   鏇存柊鍚庢槧灏勬暟閲? {updated_mappings.count()}")
            
            # 缁熻浣跨敤鐨勯儴浠?
            mapped_components = set(
                updated_mappings.values_list('component_name', flat=True)
            )
            print(f"   鏄犲皠涓娇鐢ㄧ殑閮ㄤ欢: {list(mapped_components)}")
            print(f"   浣跨敤鐨勯儴浠舵暟閲? {len(mapped_components)}")
            
            # 妫€鏌ヨ鐩栫巼
            coverage = len(mapped_components) / len(component_names) * 100
            print(f"   閮ㄤ欢瑕嗙洊鐜? {coverage:.1f}%")
            
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
    
    # 6. 缁熻鏄犲皠鍒嗗竷
    print(f"\n馃搳 鏄犲皠鍒嗗竷缁熻:")
    
    # 缁熻姣忎釜閮ㄤ欢鐨勬槧灏勬暟閲?
    component_mapping_counts = {}
    for mapping in TestPointComponentMapping.objects.filter(msfg_definition=active_msfg):
        component = mapping.component_name
        if component not in component_mapping_counts:
            component_mapping_counts[component] = 0
        component_mapping_counts[component] += 1
    
    print(f"   鍚勯儴浠舵槧灏勬暟閲?")
    for component, count in sorted(component_mapping_counts.items()):
        print(f"     {component}: {count} 涓槧灏?)
    
    return True

if __name__ == "__main__":
    test_fixed_auto_mapping()

