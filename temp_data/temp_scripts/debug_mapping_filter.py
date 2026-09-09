#!/usr/bin/env python
"""
璋冭瘯鏄犲皠杩囨护闂
"""

import os
import sys
import django
from pathlib import Path

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM
from msfg_analysis.models import MSFGDefinition, TestPointFaultMapping

def debug_mapping_filter():
    """璋冭瘯鏄犲皠杩囨护闂"""
    print("=== 璋冭瘯鏄犲皠杩囨护闂 ===")
    
    # 鑾峰彇绗竴涓狢MG妯″瀷
    cmg = PHM.objects.first()
    if not cmg:
        print("鉂?娌℃湁鎵惧埌PHM妯″瀷")
        return
    
    print(f"PHM妯″瀷: {cmg.cmg_model}")
    
    # 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    msfg = MSFGDefinition.objects.filter(
        cmg_model=cmg.cmg_model, 
        is_active=True
    ).order_by('-updated_at').first()
    
    if not msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return
    
    print(f"娲昏穬MSFG: {msfg.name}")
    
    # 鑾峰彇鎵€鏈夋祴璇曠偣-鏁呴殰鏄犲皠
    user_mappings = TestPointFaultMapping.objects.filter(msfg_definition=msfg)
    print(f"\n馃搳 鎬绘槧灏勬暟閲? {len(user_mappings)}")
    
    # 鑾峰彇MSFG涓殑鑺傜偣
    test_nodes = msfg.nodes.filter(node_type='test')
    fault_nodes = msfg.nodes.filter(node_type='fault')
    
    msfg_test_names = set(node.name for node in test_nodes)
    msfg_fault_names = set(node.name for node in fault_nodes)
    
    print(f"MSFG娴嬭瘯鑺傜偣鏁伴噺: {len(msfg_test_names)}")
    print(f"MSFG鏁呴殰鑺傜偣鏁伴噺: {len(msfg_fault_names)}")
    
    # 鍒嗘瀽姣忎釜鏄犲皠
    valid_mappings = 0
    invalid_mappings = []
    
    for mapping in user_mappings:
        test_in_msfg = mapping.test_point_name in msfg_test_names
        fault_in_msfg = mapping.fault_name in msfg_fault_names
        
        if test_in_msfg and fault_in_msfg:
            valid_mappings += 1
        else:
            invalid_mappings.append({
                'test_point': mapping.test_point_name,
                'fault_name': mapping.fault_name,
                'test_in_msfg': test_in_msfg,
                'fault_in_msfg': fault_in_msfg
            })
    
    print(f"\n鉁?鏈夋晥鏄犲皠: {valid_mappings}")
    print(f"鉂?鏃犳晥鏄犲皠: {len(invalid_mappings)}")
    
    # 鍒嗘瀽鏃犳晥鏄犲皠鐨勫師鍥?
    test_not_in_msfg = set()
    fault_not_in_msfg = set()
    
    for invalid in invalid_mappings:
        if not invalid['test_in_msfg']:
            test_not_in_msfg.add(invalid['test_point'])
        if not invalid['fault_in_msfg']:
            fault_not_in_msfg.add(invalid['fault_name'])
    
    print(f"\n馃攳 鍒嗘瀽鏃犳晥鏄犲皠鍘熷洜:")
    print(f"娴嬭瘯鐐逛笉鍦∕SFG涓? {len(test_not_in_msfg)} 涓?)
    print(f"鏁呴殰涓嶅湪MSFG涓? {len(fault_not_in_msfg)} 涓?)
    
    if test_not_in_msfg:
        print(f"\n馃搵 涓嶅湪MSFG涓殑娴嬭瘯鐐?")
        for test in sorted(test_not_in_msfg):
            print(f"  - {test}")
    
    if fault_not_in_msfg:
        print(f"\n馃搵 涓嶅湪MSFG涓殑鏁呴殰:")
        for fault in sorted(fault_not_in_msfg):
            print(f"  - {fault}")
    
    # 鏄剧ずMSFG涓殑娴嬭瘯鐐瑰拰鏁呴殰
    print(f"\n馃搵 MSFG涓殑娴嬭瘯鐐?")
    for test in sorted(msfg_test_names):
        print(f"  - {test}")
    
    print(f"\n馃搵 MSFG涓殑鏁呴殰:")
    for fault in sorted(msfg_fault_names):
        print(f"  - {fault}")
    
    # 妫€鏌ユ槧灏勪腑鐨勬祴璇曠偣鍜屾晠闅?
    mapping_test_names = set(mapping.test_point_name for mapping in user_mappings)
    mapping_fault_names = set(mapping.fault_name for mapping in user_mappings)
    
    print(f"\n馃搳 鏄犲皠缁熻:")
    print(f"鏄犲皠涓殑娴嬭瘯鐐规暟閲? {len(mapping_test_names)}")
    print(f"鏄犲皠涓殑鏁呴殰鏁伴噺: {len(mapping_fault_names)}")
    
    # 鏄剧ず鏄犲皠涓殑娴嬭瘯鐐瑰拰鏁呴殰
    print(f"\n馃搵 鏄犲皠涓殑娴嬭瘯鐐?")
    for test in sorted(mapping_test_names):
        in_msfg = "鉁? if test in msfg_test_names else "鉂?
        print(f"  {in_msfg} {test}")
    
    print(f"\n馃搵 鏄犲皠涓殑鏁呴殰:")
    for fault in sorted(mapping_fault_names):
        in_msfg = "鉁? if fault in msfg_fault_names else "鉂?
        print(f"  {in_msfg} {fault}")

if __name__ == "__main__":
    debug_mapping_filter()

