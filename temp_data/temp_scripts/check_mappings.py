#!/usr/bin/env python
"""
妫€鏌ユ槧灏勬暟鎹?
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
from msfg_analysis.models import MSFGDefinition, TestPointFaultMapping, FaultComponentMapping

def check_mappings():
    """妫€鏌ユ槧灏勬暟鎹?""
    print("=== 妫€鏌ユ槧灏勬暟鎹?===")
    
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
    
    # 妫€鏌ユ祴璇曠偣-鏁呴殰鏄犲皠
    test_fault_mappings = TestPointFaultMapping.objects.filter(msfg_definition=msfg)
    print(f"\n馃搳 娴嬭瘯鐐?鏁呴殰鏄犲皠鏁伴噺: {len(test_fault_mappings)}")
    
    # 缁熻鍞竴鐨勬祴璇曠偣鍜屾晠闅?
    unique_tests = set()
    unique_faults = set()
    for mapping in test_fault_mappings:
        unique_tests.add(mapping.test_point_name)
        unique_faults.add(mapping.fault_name)
    
    print(f"鍞竴娴嬭瘯鐐规暟閲? {len(unique_tests)}")
    print(f"鍞竴鏁呴殰鏁伴噺: {len(unique_faults)}")
    
    # 妫€鏌ユ晠闅?閮ㄤ欢鏄犲皠
    fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg)
    print(f"\n馃搳 鏁呴殰-閮ㄤ欢鏄犲皠鏁伴噺: {len(fault_component_mappings)}")
    
    # 缁熻鍞竴鐨勬晠闅滃拰閮ㄤ欢
    mapped_faults = set()
    unique_components = set()
    for mapping in fault_component_mappings:
        mapped_faults.add(mapping.fault_name)
        unique_components.add(mapping.component_name)
    
    print(f"宸叉槧灏勬晠闅滄暟閲? {len(mapped_faults)}")
    print(f"鍞竴閮ㄤ欢鏁伴噺: {len(unique_components)}")
    
    # 妫€鏌ユ槧灏勫畬鏁存€?
    unmapped_faults = unique_faults - mapped_faults
    if unmapped_faults:
        print(f"\n鈿狅笍 鏈槧灏勭殑鏁呴殰 ({len(unmapped_faults)}涓?:")
        for fault in sorted(unmapped_faults):
            print(f"  - {fault}")
    else:
        print(f"\n鉁?鎵€鏈夋晠闅滈兘宸叉槧灏勫埌閮ㄤ欢")
    
    # 鏄剧ず鏄犲皠璇︽儏
    print(f"\n馃搵 鏁呴殰-閮ㄤ欢鏄犲皠璇︽儏:")
    for mapping in fault_component_mappings.order_by('fault_name')[:20]:
        print(f"  {mapping.fault_name} -> {mapping.component_name}")
    
    if len(fault_component_mappings) > 20:
        print(f"  ... 杩樻湁 {len(fault_component_mappings) - 20} 涓槧灏?)
    
    # 妫€鏌SFG鑺傜偣
    print(f"\n馃攳 MSFG鑺傜偣淇℃伅:")
    test_nodes = msfg.nodes.filter(node_type='test')
    fault_nodes = msfg.nodes.filter(node_type='fault')
    print(f"娴嬭瘯鑺傜偣鏁伴噺: {test_nodes.count()}")
    print(f"鏁呴殰鑺傜偣鏁伴噺: {fault_nodes.count()}")
    
    # 妫€鏌ヨ妭鐐逛笌鏄犲皠鐨勪竴鑷存€?
    msfg_test_names = set(node.name for node in test_nodes)
    msfg_fault_names = set(node.name for node in fault_nodes)
    
    unmapped_tests = msfg_test_names - unique_tests
    if unmapped_tests:
        print(f"\n鈿狅笍 MSFG涓湭鏄犲皠鐨勬祴璇曠偣 ({len(unmapped_tests)}涓?:")
        for test in sorted(unmapped_tests):
            print(f"  - {test}")
    
    unmapped_msfg_faults = msfg_fault_names - unique_faults
    if unmapped_msfg_faults:
        print(f"\n鈿狅笍 MSFG涓湭鏄犲皠鐨勬晠闅?({len(unmapped_msfg_faults)}涓?:")
        for fault in sorted(unmapped_msfg_faults):
            print(f"  - {fault}")

if __name__ == "__main__":
    check_mappings()

