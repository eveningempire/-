#!/usr/bin/env python
"""
璋冭瘯MSFG鏁版嵁缁撴瀯
"""

import os
import sys
import django
import json

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping

def debug_msfg_data():
    """璋冭瘯MSFG鏁版嵁缁撴瀯"""
    print("=== 璋冭瘯MSFG鏁版嵁缁撴瀯 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    print(f"   ID: {active_msfg.id}")
    print(f"   鍒涘缓鏃堕棿: {active_msfg.created_at}")
    print(f"   鏇存柊鏃堕棿: {active_msfg.updated_at}")
    
    # 2. 妫€鏌ュ師濮嬪浘鏁版嵁
    print(f"\n馃攳 妫€鏌ュ師濮嬪浘鏁版嵁:")
    raw_data = active_msfg.raw_graph_data
    
    if raw_data is None:
        print("   鉂?raw_graph_data 涓?None")
    elif raw_data == {}:
        print("   鉂?raw_graph_data 涓虹┖瀛楀吀")
    else:
        print(f"   鉁?raw_graph_data 绫诲瀷: {type(raw_data)}")
        print(f"   raw_graph_data 閿? {list(raw_data.keys()) if isinstance(raw_data, dict) else '涓嶆槸瀛楀吀'}")
        
        # 灏濊瘯瑙ｆ瀽JSON
        if isinstance(raw_data, str):
            try:
                parsed_data = json.loads(raw_data)
                print(f"   JSON瑙ｆ瀽鎴愬姛锛岀被鍨? {type(parsed_data)}")
                raw_data = parsed_data
            except json.JSONDecodeError as e:
                print(f"   鉂?JSON瑙ｆ瀽澶辫触: {e}")
        
        # 妫€鏌ユ暟鎹粨鏋?
        if isinstance(raw_data, dict):
            nodes = raw_data.get('nodes', [])
            edges = raw_data.get('edges', [])
            
            print(f"   nodes 绫诲瀷: {type(nodes)}")
            print(f"   edges 绫诲瀷: {type(edges)}")
            
            if isinstance(nodes, list):
                print(f"   nodes 闀垮害: {len(nodes)}")
                if nodes:
                    print(f"   绗竴涓妭鐐? {nodes[0]}")
            else:
                print(f"   nodes 涓嶆槸鍒楄〃: {nodes}")
            
            if isinstance(edges, list):
                print(f"   edges 闀垮害: {len(edges)}")
                if edges:
                    print(f"   绗竴鏉¤竟: {edges[0]}")
            else:
                print(f"   edges 涓嶆槸鍒楄〃: {edges}")
    
    # 3. 妫€鏌ュ叾浠栫浉鍏冲瓧娈?
    print(f"\n馃搳 妫€鏌ュ叾浠栧瓧娈?")
    print(f"   test_names: {active_msfg.test_names}")
    print(f"   fault_names: {active_msfg.fault_names}")
    print(f"   component_names: {active_msfg.component_names}")
    
    # 4. 妫€鏌ユ暟鎹簱涓殑鑺傜偣鍜岃竟
    print(f"\n馃梽锔?妫€鏌ユ暟鎹簱涓殑鑺傜偣鍜岃竟:")
    from msfg_analysis.models import MSFGNode, MSFGEdge
    
    nodes_in_db = MSFGNode.objects.filter(msfg_definition=active_msfg)
    edges_in_db = MSFGEdge.objects.filter(msfg_definition=active_msfg)
    
    print(f"   鏁版嵁搴撲腑鐨勮妭鐐规暟閲? {nodes_in_db.count()}")
    print(f"   鏁版嵁搴撲腑鐨勮竟鏁伴噺: {edges_in_db.count()}")
    
    if nodes_in_db.exists():
        print(f"   鑺傜偣绀轰緥:")
        for i, node in enumerate(nodes_in_db[:3]):
            print(f"     {i+1}. ID: {node.id}, 鍚嶇О: {node.name}, 绫诲瀷: {node.node_type}")
    
         if edges_in_db.exists():
         print(f"   杈圭ず渚?")
         for i, edge in enumerate(edges_in_db[:3]):
             print(f"     {i+1}. 婧? {edge.source_node.name if edge.source_node else 'None'}, "
                   f"鐩爣: {edge.target_node.name if edge.target_node else 'None'}, "
                   f"鏉冮噸: {getattr(edge, 'weight', 'N/A')}")
    
    # 5. 妫€鏌ユ槧灏勫叧绯?
    print(f"\n馃敆 妫€鏌ユ槧灏勫叧绯?")
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    print(f"   鏄犲皠鏁伴噺: {mappings.count()}")
    
    if mappings.exists():
        print(f"   鏄犲皠绀轰緥:")
        for i, mapping in enumerate(mappings[:5]):
            print(f"     {i+1}. {mapping.test_point_name} -> {mapping.component_name}")
    
    # 6. 灏濊瘯閲嶅缓鍘熷鍥炬暟鎹?
    print(f"\n馃敡 灏濊瘯閲嶅缓鍘熷鍥炬暟鎹?")
    
    if nodes_in_db.exists() and edges_in_db.exists():
        print(f"   浠庢暟鎹簱閲嶅缓鍥炬暟鎹?..")
        
        # 閲嶅缓鑺傜偣
        rebuilt_nodes = []
        for node in nodes_in_db:
            node_data = {
                'id': str(node.id),
                'name': node.name,
                'type': node.node_type,
                'text': {'value': node.name}
            }
            rebuilt_nodes.append(node_data)
        
        # 閲嶅缓杈?
        rebuilt_edges = []
        for edge in edges_in_db:
            edge_data = {
                'source': str(edge.source_node.id) if edge.source_node else '',
                'target': str(edge.target_node.id) if edge.target_node else '',
                'weight': edge.weight
            }
            rebuilt_edges.append(edge_data)
        
        rebuilt_data = {
            'nodes': rebuilt_nodes,
            'edges': rebuilt_edges
        }
        
        print(f"   閲嶅缓鐨勮妭鐐规暟閲? {len(rebuilt_nodes)}")
        print(f"   閲嶅缓鐨勮竟鏁伴噺: {len(rebuilt_edges)}")
        
        if rebuilt_nodes:
            print(f"   閲嶅缓鐨勮妭鐐圭ず渚? {rebuilt_nodes[0]}")
        if rebuilt_edges:
            print(f"   閲嶅缓鐨勮竟绀轰緥: {rebuilt_edges[0]}")
        
        # 7. 娴嬭瘯鑷姩鏄犲皠
        print(f"\n馃И 娴嬭瘯閲嶅缓鏁版嵁鐨勮嚜鍔ㄦ槧灏?")
        try:
            from msfg_analysis.algorithms.msfg.auto_mapping import MSFGAutoMapping
            
            extractor = MSFGAutoMapping(rebuilt_data)
            mappings = extractor.extract_test_component_mappings()
            
            print(f"   鑷姩鏄犲皠缁撴灉: {len(mappings)} 涓祴璇曠偣")
            if mappings:
                for test_name, component_mappings in list(mappings.items())[:3]:
                    print(f"     {test_name} -> {component_mappings[:2]}")
            
        except Exception as e:
            print(f"   鉂?鑷姩鏄犲皠娴嬭瘯澶辫触: {e}")
    
    return True

if __name__ == "__main__":
    debug_msfg_data()

