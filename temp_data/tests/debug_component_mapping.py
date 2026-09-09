#!/usr/bin/env python
"""
璋冭瘯缁勪欢鏄犲皠闂
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping, MSFGNode
from data_management.models import PHMModel

def debug_component_mapping():
    print("=" * 60)
    print("璋冭瘯缁勪欢鏄犲皠闂")
    print("=" * 60)
    
    # 鑾峰彇MSFG
    try:
        cmg_model = PHMModel.objects.get(id=3)
        msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
        print(f"MSFG: {msfg.name}")
    except Exception as e:
        print(f"鑾峰彇MSFG澶辫触: {e}")
        return
    
    # 1. 妫€鏌SFG瀹氫箟鐨勭粍浠跺悕绉?
    print(f"\n1. MSFG瀹氫箟鐨勭粍浠跺悕绉?")
    component_names = msfg.component_names or []
    print(f"   鏁伴噺: {len(component_names)}")
    for i, comp in enumerate(component_names, 1):
        print(f"   {i}. {comp}")
    
    # 2. 妫€鏌estPointComponentMapping
    print(f"\n2. TestPointComponentMapping鏁版嵁:")
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg)
    print(f"   鏁伴噺: {mappings.count()}")
    
    if mappings.exists():
        # 缁熻缁勪欢鍒嗗竷
        component_counts = {}
        for mapping in mappings:
            comp_name = mapping.component_name
            if comp_name not in component_counts:
                component_counts[comp_name] = 0
            component_counts[comp_name] += 1
        
        print(f"   鏄犲皠涓殑缁勪欢鍒嗗竷:")
        for comp, count in component_counts.items():
            print(f"     - {comp}: {count} 涓槧灏?)
        
        # 鏄剧ず鍓嶅嚑涓槧灏勭ず渚?
        print(f"\n   鏄犲皠绀轰緥:")
        for i, mapping in enumerate(mappings[:5], 1):
            print(f"     {i}. {mapping.test_point_name} -> {mapping.component_name} (鏉冮噸: {mapping.weight})")
    else:
        print("   娌℃湁鎵惧埌TestPointComponentMapping鏁版嵁")
    
    # 3. 妫€鏌ユ晠闅滆妭鐐?
    print(f"\n3. MSFG鏁呴殰鑺傜偣:")
    fault_nodes = MSFGNode.objects.filter(msfg_definition=msfg, node_type='fault')
    print(f"   鏁伴噺: {fault_nodes.count()}")
    
    fault_names = [node.name for node in fault_nodes]
    for i, fault in enumerate(fault_names[:10], 1):
        print(f"   {i}. {fault}")
    if len(fault_names) > 10:
        print(f"   ... 杩樻湁 {len(fault_names) - 10} 涓晠闅?)
    
    # 4. 妫€鏌ユ祴璇曡妭鐐?
    print(f"\n4. MSFG娴嬭瘯鑺傜偣:")
    test_nodes = MSFGNode.objects.filter(msfg_definition=msfg, node_type='test')
    print(f"   鏁伴噺: {test_nodes.count()}")
    
    test_names = [node.name for node in test_nodes]
    for i, test in enumerate(test_names[:10], 1):
        print(f"   {i}. {test}")
    if len(test_names) > 10:
        print(f"   ... 杩樻湁 {len(test_names) - 10} 涓祴鐐?)
    
    # 5. 娴嬭瘯缁勪欢鏄犲皠鏈嶅姟
    print(f"\n5. 娴嬭瘯缁勪欢鏄犲皠鏈嶅姟:")
    try:
        from msfg_analysis.services.component_mapping import build_msfg_component_mappings
        component_mappings = build_msfg_component_mappings(msfg)
        
        print(f"   鏈嶅姟杩斿洖鐨勭粍浠舵暟閲? {len(component_mappings)}")
        for comp_name, fault_list in component_mappings.items():
            print(f"     - {comp_name}: {len(fault_list)} 涓晠闅?)
            if fault_list:
                print(f"       鏁呴殰绀轰緥: {fault_list[:3]}{'...' if len(fault_list) > 3 else ''}")
    
    except Exception as e:
        print(f"   缁勪欢鏄犲皠鏈嶅姟澶辫触: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. 鍒嗘瀽闂
    print(f"\n6. 闂鍒嗘瀽:")
    if not component_names:
        print("   鈿狅笍  MSFG娌℃湁瀹氫箟component_names")
    
    if not mappings.exists():
        print("   鈿狅笍  娌℃湁TestPointComponentMapping鏁版嵁")
    
    if component_names and mappings.exists():
        # 妫€鏌ヤ竴鑷存€?
        mapping_components = set(mapping.component_name for mapping in mappings)
        defined_components = set(component_names)
        
        missing_in_mappings = defined_components - mapping_components
        extra_in_mappings = mapping_components - defined_components
        
        if missing_in_mappings:
            print(f"   鈿狅笍  MSFG瀹氫箟涓湁浣嗘槧灏勪腑缂哄け鐨勭粍浠? {missing_in_mappings}")
        
        if extra_in_mappings:
            print(f"   鈿狅笍  鏄犲皠涓湁浣哅SFG瀹氫箟涓己澶辩殑缁勪欢: {extra_in_mappings}")
        
        if not missing_in_mappings and not extra_in_mappings:
            print("   鉁?MSFG瀹氫箟鍜屾槧灏勬暟鎹竴鑷?)

if __name__ == "__main__":
    debug_component_mapping()

