#!/usr/bin/env python
"""
鍒嗘瀽MSFG璁＄畻閫昏緫锛屾鏌ヤ粠娴嬬偣鍒嗘暟鍒版晠闅滃垎鏁板啀鍒伴儴浠跺垎鏁扮殑鎺ㄥ杩囩▼
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
from msfg_analysis.algorithms.msfg.component_integration import extract_components_from_msfg
import numpy as np

def analyze_msfg_logic():
    """鍒嗘瀽MSFG璁＄畻閫昏緫"""
    print("=== MSFG璁＄畻閫昏緫鍒嗘瀽 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    print(f"   PHM妯″瀷: {active_msfg.cmg_model.model_name}")
    
    # 2. 鍒嗘瀽MSFG缁撴瀯
    print(f"\n馃搳 MSFG缁撴瀯鍒嗘瀽:")
    
    # 鑾峰彇鎵€鏈夎妭鐐?
    test_nodes = MSFGNode.objects.filter(
        msfg_definition=active_msfg,
        node_type='test'
    ).order_by('name')
    
    fault_nodes = MSFGNode.objects.filter(
        msfg_definition=active_msfg,
        node_type='fault'
    ).order_by('name')
    
    system_nodes = MSFGNode.objects.filter(
        msfg_definition=active_msfg,
        node_type='system'
    ).exclude(name__in=['root', 'system', '']).order_by('name')
    
    edges = MSFGEdge.objects.filter(msfg_definition=active_msfg)
    
    print(f"   娴嬭瘯鐐规暟閲? {test_nodes.count()}")
    print(f"   鏁呴殰鐐规暟閲? {fault_nodes.count()}")
    print(f"   绯荤粺鑺傜偣鏁伴噺: {system_nodes.count()}")
    print(f"   杈规暟閲? {edges.count()}")
    
    # 3. 鏄剧ず娴嬭瘯鐐?
    print(f"\n馃攳 娴嬭瘯鐐瑰垪琛?")
    for i, node in enumerate(test_nodes, 1):
        print(f"   {i}. {node.name}")
    
    # 4. 鏄剧ず鏁呴殰鐐?
    print(f"\n鈿狅笍 鏁呴殰鐐瑰垪琛?")
    for i, node in enumerate(fault_nodes, 1):
        print(f"   {i}. {node.name}")
    
    # 5. 鏄剧ず绯荤粺鑺傜偣锛堥儴浠讹級
    print(f"\n馃敡 绯荤粺鑺傜偣锛堥儴浠讹級鍒楄〃:")
    for i, node in enumerate(system_nodes, 1):
        print(f"   {i}. {node.name}")
    
    # 6. 鍒嗘瀽杈圭殑杩炴帴鍏崇郴
    print(f"\n馃敆 杈圭殑杩炴帴鍏崇郴:")
    test_to_fault_edges = []
    for edge in edges:
        if edge.source_node.node_type == 'test' and edge.target_node.node_type == 'fault':
            test_to_fault_edges.append(edge)
            print(f"   娴嬭瘯鐐? {edge.source_node.name} -> 鏁呴殰鐐? {edge.target_node.name}")
    
    print(f"   娴嬭瘯鐐瑰埌鏁呴殰鐐圭殑杈规暟閲? {len(test_to_fault_edges)}")
    
    # 7. 鍒嗘瀽閮ㄤ欢鎻愬彇閫昏緫
    print(f"\n馃敡 閮ㄤ欢鎻愬彇閫昏緫鍒嗘瀽:")
    
    # 浠嶮SFG缁撴瀯涓彁鍙栫殑閮ㄤ欢
    extracted_components = extract_components_from_msfg(active_msfg)
    print(f"   浠嶮SFG缁撴瀯鎻愬彇鐨勯儴浠? {extracted_components}")
    
    # 娴嬭瘯鐐?閮ㄤ欢鏄犲皠
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    mapped_components = set()
    for mapping in mappings:
        mapped_components.add(mapping.component_name)
    
    print(f"   鏄犲皠涓殑閮ㄤ欢: {list(mapped_components)}")
    
    # 8. 妫€鏌ヨ绠楅€昏緫闂
    print(f"\n鉂?娼滃湪闂鍒嗘瀽:")
    
    # 闂1: 娴嬭瘯鐐瑰埌鏁呴殰鐐圭殑鏄犲皠鏄惁瀹屾暣
    mapped_test_points = set()
    for edge in test_to_fault_edges:
        mapped_test_points.add(edge.source_node.name)
    
    all_test_points = set(test_nodes.values_list('name', flat=True))
    unmapped_tests = all_test_points - mapped_test_points
    
    if unmapped_tests:
        print(f"   鈿狅笍 闂1: 鏈夋祴璇曠偣娌℃湁杩炴帴鍒版晠闅滅偣: {unmapped_tests}")
    else:
        print(f"   鉁?鎵€鏈夋祴璇曠偣閮借繛鎺ュ埌鏁呴殰鐐?)
    
    # 闂2: 鏁呴殰鐐瑰埌閮ㄤ欢鐨勬槧灏勬槸鍚﹀畬鏁?
    if not mappings.exists():
        print(f"   鈿狅笍 闂2: 娌℃湁娴嬭瘯鐐?閮ㄤ欢鏄犲皠锛屾棤娉曡绠楅儴浠跺仴搴峰害")
    else:
        print(f"   鉁?瀛樺湪娴嬭瘯鐐?閮ㄤ欢鏄犲皠")
    
    # 闂3: 閮ㄤ欢鏉ユ簮涓嶄竴鑷?
    if set(extracted_components) != mapped_components:
        print(f"   鈿狅笍 闂3: 閮ㄤ欢鏉ユ簮涓嶄竴鑷?)
        print(f"      浠嶮SFG缁撴瀯鎻愬彇: {extracted_components}")
        print(f"      浠庢槧灏勪腑鑾峰彇: {list(mapped_components)}")
    
    # 9. 妯℃嫙璁＄畻杩囩▼
    print(f"\n馃М 妯℃嫙璁＄畻杩囩▼:")
    
    if test_nodes.exists() and fault_nodes.exists() and test_to_fault_edges:
        # 鍒涘缓妯℃嫙娴嬭瘯鍒嗘暟
        test_scores = {}
        for test_node in test_nodes:
            test_scores[test_node.name] = [0.5]  # 妯℃嫙涓瓑鍒嗘暟
        
        # 鏋勫缓鏁呴殰鍒伴儴浠剁殑鏄犲皠
        component_mappings = {}
        for mapping in mappings:
            component_name = mapping.component_name
            if component_name not in component_mappings:
                component_mappings[component_name] = []
            # 杩欓噷闇€瑕佸皢娴嬭瘯鐐规槧灏勫埌鏁呴殰鐐癸紝鐒跺悗鏁呴殰鐐规槧灏勫埌閮ㄤ欢
            # 杩欐槸涓€涓叧閿棶棰橈細缂哄皯娴嬭瘯鐐?>鏁呴殰鐐?>閮ㄤ欢鐨勫畬鏁存槧灏勯摼
        
        print(f"   娴嬭瘯鍒嗘暟: {test_scores}")
        print(f"   閮ㄤ欢鏄犲皠: {component_mappings}")
        
        if component_mappings:
            print(f"   鉁?鍙互杩涜閮ㄤ欢鍋ュ悍搴﹁绠?)
        else:
            print(f"   鉂?缂哄皯閮ㄤ欢鏄犲皠锛屾棤娉曡绠楅儴浠跺仴搴峰害")
    else:
        print(f"   鉂?MSFG缁撴瀯涓嶅畬鏁达紝鏃犳硶杩涜妯℃嫙璁＄畻")
    
    # 10. 寤鸿瑙ｅ喅鏂规
    print(f"\n馃挕 寤鸿瑙ｅ喅鏂规:")
    print(f"   1. 纭繚鎵€鏈夋祴璇曠偣閮借繛鎺ュ埌鏁呴殰鐐?)
    print(f"   2. 寤虹珛瀹屾暣鐨勬祴璇曠偣->鏁呴殰鐐?>閮ㄤ欢鏄犲皠閾?)
    print(f"   3. 缁熶竴閮ㄤ欢鏉ユ簮锛岄伩鍏嶄笉涓€鑷?)
    print(f"   4. 妫€鏌SFG缂栬緫鍣ㄧ殑淇濆瓨閫昏緫锛岀‘淇漜omponent_names姝ｇ‘鏇存柊")
    
    return True

if __name__ == "__main__":
    analyze_msfg_logic()

