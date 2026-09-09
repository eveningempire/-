#!/usr/bin/env python
"""
璋冭瘯閮ㄤ欢鑺傜偣鍚嶇О闂
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge

def debug_component_names():
    """璋冭瘯閮ㄤ欢鑺傜偣鍚嶇О闂"""
    print("=== 璋冭瘯閮ㄤ欢鑺傜偣鍚嶇О闂 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    
    # 2. 鍒嗘瀽鎵€鏈夎妭鐐?
    print(f"\n馃攳 鍒嗘瀽鎵€鏈夎妭鐐?")
    nodes_in_db = MSFGNode.objects.filter(msfg_definition=active_msfg)
    
    test_nodes = []
    fault_nodes = []
    component_nodes = []
    other_nodes = []
    
    for node in nodes_in_db:
        node_type = str(node.node_type).lower()
        node_name = node.name
        
        print(f"   鑺傜偣: ID={node.id}, 鍚嶇О='{node_name}', 绫诲瀷='{node_type}'")
        
        if 'test' in node_type or 'sensor' in node_type:
            test_nodes.append((node.id, node_name, node_type))
        elif 'fault' in node_type or 'failure' in node_type:
            fault_nodes.append((node.id, node_name, node_type))
        elif 'system' in node_type and 'root' not in node_type:
            component_nodes.append((node.id, node_name, node_type))
        else:
            other_nodes.append((node.id, node_name, node_type))
    
    # 3. 璇︾粏鍒嗘瀽閮ㄤ欢鑺傜偣
    print(f"\n馃敡 璇︾粏鍒嗘瀽閮ㄤ欢鑺傜偣:")
    print(f"   閮ㄤ欢鑺傜偣鏁伴噺: {len(component_nodes)}")
    
    for i, (node_id, node_name, node_type) in enumerate(component_nodes):
        print(f"   {i+1}. ID: {node_id}, 鍚嶇О: '{node_name}', 绫诲瀷: '{node_type}'")
        print(f"      鍚嶇О闀垮害: {len(node_name)}")
        print(f"      鍚嶇О瀛楄妭: {repr(node_name)}")
        print(f"      鏄惁涓虹┖: {node_name == ''}")
        print(f"      鏄惁鍏ㄧ┖鏍? {node_name.strip() == ''}")
    
    # 4. 妫€鏌SFG.component_names
    print(f"\n馃搳 妫€鏌SFG.component_names:")
    component_names = active_msfg.component_names or []
    print(f"   component_names: {component_names}")
    
    # 5. 姣旇緝鏁版嵁搴撲腑鐨勯儴浠惰妭鐐瑰拰component_names
    print(f"\n馃攳 姣旇緝鏁版嵁搴撻儴浠惰妭鐐瑰拰component_names:")
    
    db_component_names = [name for _, name, _ in component_nodes]
    msfg_component_names = component_names
    
    print(f"   鏁版嵁搴撲腑鐨勯儴浠跺悕绉? {db_component_names}")
    print(f"   MSFG.component_names: {msfg_component_names}")
    
    # 鎵惧嚭宸紓
    db_set = set(db_component_names)
    msfg_set = set(msfg_component_names)
    
    only_in_db = db_set - msfg_set
    only_in_msfg = msfg_set - db_set
    common = db_set & msfg_set
    
    print(f"   鍙湪鏁版嵁搴撲腑: {only_in_db}")
    print(f"   鍙湪MSFG.component_names涓? {only_in_msfg}")
    print(f"   鍏卞悓瀛樺湪: {common}")
    
    # 6. 鍒嗘瀽杈圭殑杩炴帴鍏崇郴
    print(f"\n馃敆 鍒嗘瀽杈圭殑杩炴帴鍏崇郴:")
    edges_in_db = MSFGEdge.objects.filter(msfg_definition=active_msfg)
    
    # 缁熻杩炴帴鍒伴儴浠剁殑杈?
    component_connections = {}
    for edge in edges_in_db:
        if edge.target_node and edge.target_node.node_type.lower() in ['system']:
            target_name = edge.target_node.name
            source_name = edge.source_node.name if edge.source_node else 'Unknown'
            
            if target_name not in component_connections:
                component_connections[target_name] = []
            component_connections[target_name].append(source_name)
    
    print(f"   杩炴帴鍒伴儴浠剁殑杈?")
    for component, sources in component_connections.items():
        print(f"     {component} <- {sources}")
    
    return True

if __name__ == "__main__":
    debug_component_names()

