#!/usr/bin/env python
"""
娴嬭瘯鑷姩鏄犲皠鍔熻兘
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.auto_mapping import auto_extract_msfg_mappings, MSFGAutoMapping

def test_auto_mapping():
    """娴嬭瘯鑷姩鏄犲皠鍔熻兘"""
    print("=== 娴嬭瘯鑷姩鏄犲皠鍔熻兘 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    
    # 2. 鍒嗘瀽MSFG缁撴瀯
    print(f"\n馃攳 鍒嗘瀽MSFG缁撴瀯:")
    
    # 浠庢暟鎹簱璇诲彇鑺傜偣鍜岃竟
    from msfg_analysis.models import MSFGNode, MSFGEdge
    
    nodes_in_db = MSFGNode.objects.filter(msfg_definition=active_msfg)
    edges_in_db = MSFGEdge.objects.filter(msfg_definition=active_msfg)
    
    print(f"   鏁版嵁搴撲腑鐨勮妭鐐规暟閲? {nodes_in_db.count()}")
    print(f"   鏁版嵁搴撲腑鐨勮竟鏁伴噺: {edges_in_db.count()}")
    
    # 3. 鍒嗙被鑺傜偣
    test_nodes = []
    fault_nodes = []
    component_nodes = []
    other_nodes = []
    
    for node in nodes_in_db:
        node_type = str(node.node_type).lower()
        node_name = node.name
        
        if 'test' in node_type or 'sensor' in node_type:
            test_nodes.append(node_name)
        elif 'fault' in node_type or 'failure' in node_type:
            fault_nodes.append(node_name)
        elif 'system' in node_type and 'root' not in node_type:
            component_nodes.append(node_name)
        else:
            other_nodes.append(node_name)
    
    print(f"   娴嬭瘯鐐硅妭鐐? {len(test_nodes)} 涓?)
    print(f"   鏁呴殰鑺傜偣: {len(fault_nodes)} 涓?)
    print(f"   閮ㄤ欢鑺傜偣: {len(component_nodes)} 涓?)
    print(f"   鍏朵粬鑺傜偣: {len(other_nodes)} 涓?)
    
    if test_nodes:
        print(f"   娴嬭瘯鐐圭ず渚? {test_nodes[:3]}")
    if fault_nodes:
        print(f"   鏁呴殰绀轰緥: {fault_nodes[:3]}")
    if component_nodes:
        print(f"   閮ㄤ欢绀轰緥: {component_nodes[:3]}")
    
    # 4. 娴嬭瘯鑷姩鏄犲皠鎻愬彇
    print(f"\n馃敡 娴嬭瘯鑷姩鏄犲皠鎻愬彇:")
    
    try:
        # 鏋勫缓鍥炬暟鎹粨鏋?
        msfg_data = {
            'nodes': [],
            'edges': []
        }
        
        # 鏋勫缓鑺傜偣鏁版嵁
        for node in nodes_in_db:
            node_data = {
                'id': str(node.id),
                'name': node.name,
                'type': node.node_type,
                'text': {'value': node.name}
            }
            msfg_data['nodes'].append(node_data)
        
        # 鏋勫缓杈规暟鎹?
        for edge in edges_in_db:
            edge_data = {
                'source': str(edge.source_node.id) if edge.source_node else '',
                'target': str(edge.target_node.id) if edge.target_node else '',
                'weight': getattr(edge, 'weight', 1.0)
            }
            msfg_data['edges'].append(edge_data)
        
        # 鍒涘缓鑷姩鏄犲皠鎻愬彇鍣?
        extractor = MSFGAutoMapping(msfg_data)
        
        print(f"   鏋勫缓閭绘帴琛ㄥ畬鎴?")
        print(f"     娴嬭瘯鐐光啋鏁呴殰: {len(extractor.from_test)} 涓?)
        print(f"     鏁呴殰鈫掗儴浠? {len(extractor.from_fault)} 涓?)
        
        # 鎻愬彇鏄犲皠鍏崇郴
        mappings = extractor.extract_test_component_mappings()
        
        print(f"   鎻愬彇鏄犲皠鍏崇郴: {len(mappings)} 涓祴璇曠偣")
        
        if mappings:
            print(f"   鏄犲皠绀轰緥:")
            for i, (test_name, component_mappings) in enumerate(mappings.items()):
                if i >= 3:  # 鍙樉绀哄墠3涓?
                    break
                print(f"     {test_name} -> {component_mappings[:2]}")  # 鍙樉绀哄墠2涓儴浠?
        
        # 鑾峰彇鏄犲皠鐭╅樀
        test_points, components, matrix = extractor.get_mapping_matrix()
        print(f"   鏄犲皠鐭╅樀: {matrix.shape[0]} 涓儴浠?脳 {matrix.shape[1]} 涓祴璇曠偣")
        
        # 褰掍竴鍖?
        normalized_mappings = extractor.normalize_mappings(mappings, method='max')
        print(f"   褰掍竴鍖栧畬鎴?)
        
    except Exception as e:
        print(f"   鉂?鑷姩鏄犲皠鎻愬彇澶辫触: {e}")
        return False
    
    # 5. 姣旇緝褰撳墠鏄犲皠
    print(f"\n馃搳 姣旇緝褰撳墠鏄犲皠:")
    
    current_mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    print(f"   褰撳墠鏄犲皠鏁伴噺: {current_mappings.count()}")
    
    if current_mappings.exists():
        print(f"   褰撳墠鏄犲皠绀轰緥:")
        for i, mapping in enumerate(current_mappings[:3]):
            print(f"     {mapping.test_point_name} -> {mapping.component_name} (鏉冮噸: {mapping.weight})")
    
    # 6. 寤鸿
    print(f"\n馃挕 寤鸿:")
    
    if len(test_nodes) > 0 and len(fault_nodes) > 0 and len(component_nodes) > 0:
        print(f"   鉁?MSFG缁撴瀯瀹屾暣锛屽彲浠ヨ嚜鍔ㄦ彁鍙栨槧灏勫叧绯?)
        print(f"   馃敡 寤鸿浣跨敤鑷姩鏄犲皠鏇夸唬鎵嬪姩鏄犲皠")
    else:
        print(f"   鈿狅笍 MSFG缁撴瀯涓嶅畬鏁?")
        if len(test_nodes) == 0:
            print(f"     - 缂哄皯娴嬭瘯鐐硅妭鐐?)
        if len(fault_nodes) == 0:
            print(f"     - 缂哄皯鏁呴殰鑺傜偣")
        if len(component_nodes) == 0:
            print(f"     - 缂哄皯閮ㄤ欢鑺傜偣")
        print(f"   馃敡 闇€瑕佸畬鍠凪SFG缁撴瀯鎴栦娇鐢ㄦ墜鍔ㄦ槧灏?)
    
    return True

if __name__ == "__main__":
    test_auto_mapping()

