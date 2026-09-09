#!/usr/bin/env python
"""
娴嬭瘯D鐭╅樀淇
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

from data_management.models import PHM, PHMData
from msfg_analysis.models import MSFGDefinition
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

def test_d_matrix_fix():
    """娴嬭瘯D鐭╅樀淇"""
    print("=== 娴嬭瘯D鐭╅樀淇 ===")
    
    # 鑾峰彇鏁版嵁
    cmg = PHM.objects.first()
    data_point = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    
    print(f"PHM: {cmg.cmg_model}")
    print(f"鏁版嵁鐐? {data_point.timestamp}")
    print(f"MSFG: {msfg.name}")
    
    # 鑾峰彇MSFG鑺傜偣
    test_nodes = list(msfg.nodes.filter(node_type='test'))
    fault_nodes = list(msfg.nodes.filter(node_type='fault'))
    edges = list(msfg.edges.all())
    
    print(f"\n馃搳 MSFG缁撴瀯:")
    print(f"娴嬭瘯鑺傜偣: {len(test_nodes)} 涓?)
    print(f"鏁呴殰鑺傜偣: {len(fault_nodes)} 涓?)
    print(f"杈? {len(edges)} 涓?)
    
    # 娴嬭瘯D鐭╅樀鏋勫缓
    fusion = AdvancedMSFGFusion()
    D_matrix, test_name_to_idx, fault_name_to_idx = fusion.build_d_matrix(
        test_nodes, fault_nodes, edges, msfg
    )
    
    print(f"\n馃攳 D鐭╅樀淇℃伅:")
    print(f"褰㈢姸: {D_matrix.shape}")
    print(f"闈為浂鍏冪礌: {D_matrix.nnz}")
    print(f"绋€鐤忓害: {1 - D_matrix.nnz / (D_matrix.shape[0] * D_matrix.shape[1]):.3f}")
    
    # 妫€鏌ユ晠闅滆妭鐐规暟閲?
    print(f"\n馃搵 鏁呴殰鑺傜偣鍒嗘瀽:")
    print(f"鍘熷鏁呴殰鑺傜偣鏁伴噺: {len(fault_nodes)}")
    print(f"鎵╁睍鍚庢晠闅滆妭鐐规暟閲? {len(fault_name_to_idx)}")
    
    # 鏄剧ず鏂板鐨勬晠闅滆妭鐐?
    original_fault_names = set(node.name for node in fault_nodes)
    extended_fault_names = set(fault_name_to_idx.keys())
    new_faults = extended_fault_names - original_fault_names
    
    if new_faults:
        print(f"鏂板鏁呴殰鑺傜偣: {len(new_faults)} 涓?)
        for fault in sorted(new_faults)[:10]:
            print(f"  - {fault}")
        if len(new_faults) > 10:
            print(f"  ... 杩樻湁 {len(new_faults) - 10} 涓?)
    else:
        print("娌℃湁鏂板鏁呴殰鑺傜偣")
    
    # 妫€鏌ユ槧灏勬湁鏁堟€?
    from msfg_analysis.models import TestPointFaultMapping
    user_mappings = TestPointFaultMapping.objects.filter(msfg_definition=msfg)
    
    valid_mappings = 0
    for mapping in user_mappings:
        if (mapping.test_point_name in test_name_to_idx and 
            mapping.fault_name in fault_name_to_idx):
            valid_mappings += 1
    
    print(f"\n馃搳 鏄犲皠鏈夋晥鎬?")
    print(f"鎬绘槧灏勬暟閲? {len(user_mappings)}")
    print(f"鏈夋晥鏄犲皠鏁伴噺: {valid_mappings}")
    print(f"鏃犳晥鏄犲皠鏁伴噺: {len(user_mappings) - valid_mappings}")
    
    if valid_mappings == len(user_mappings):
        print("鉁?鎵€鏈夋槧灏勯兘鏈夋晥锛?)
    else:
        print("鉂?浠嶆湁鏃犳晥鏄犲皠")

if __name__ == "__main__":
    test_d_matrix_fix()

