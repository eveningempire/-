#!/usr/bin/env python
"""
璋冭瘯MSFG鍥剧粨鏋勶紝鍒嗘瀽涓轰粈涔堟祴璇曠偣鏃犳硶鍒拌揪閮ㄤ欢
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel, MSFGNode, MSFGEdge

def debug_graph_structure():
    print("馃攳 璋冭瘯MSFG鍥剧粨鏋?)
    print("=" * 60)
    
    try:
        # 鑾峰彇鏈€鏂扮殑MSFG瀹氫箟
        cmg_model = PHMModel.objects.filter(is_active=True).first()
        if not cmg_model:
            print("鉂?娌℃湁鎵惧埌婵€娲荤殑PHM妯″瀷")
            return
            
        msfg_definition = MSFGDefinition.objects.filter(cmg_model=cmg_model).order_by('-created_at').first()
        if not msfg_definition:
            print("鉂?娌℃湁鎵惧埌MSFG瀹氫箟")
            return
            
        print(f"馃搵 妫€鏌SFG: {msfg_definition}")
        
        # 鑾峰彇鎵€鏈夎妭鐐瑰拰杈?
        nodes = MSFGNode.objects.filter(msfg_definition=msfg_definition)
        edges = MSFGEdge.objects.filter(msfg_definition=msfg_definition)
        
        print(f"\n馃搳 鑺傜偣缁熻:")
        node_types = {}
        for node in nodes:
            node_type = node.node_type
            if node_type not in node_types:
                node_types[node_type] = []
            node_types[node_type].append(node)
        
        for node_type, node_list in node_types.items():
            print(f"  {node_type}: {len(node_list)} 涓?)
            for node in node_list[:3]:
                print(f"    - {node.name} (ID: {node.id})")
            if len(node_list) > 3:
                print(f"    ... 杩樻湁 {len(node_list) - 3} 涓?)
        
        print(f"\n馃敆 杈圭粺璁?")
        print(f"  鎬昏竟鏁? {edges.count()}")
        
        # 鍒嗘瀽杈圭殑杩炴帴妯″紡
        edge_patterns = {}
        for edge in edges:
            source_type = edge.source_node.node_type if edge.source_node else 'unknown'
            target_type = edge.target_node.node_type if edge.target_node else 'unknown'
            pattern = f"{source_type} -> {target_type}"
            
            if pattern not in edge_patterns:
                edge_patterns[pattern] = []
            edge_patterns[pattern].append(edge)
        
        print(f"\n馃敆 杈硅繛鎺ユā寮?")
        for pattern, edge_list in edge_patterns.items():
            print(f"  {pattern}: {len(edge_list)} 鏉?)
            for edge in edge_list[:3]:
                source_name = edge.source_node.name if edge.source_node else 'unknown'
                target_name = edge.target_node.name if edge.target_node else 'unknown'
                print(f"    - {source_name} -> {target_name}")
            if len(edge_list) > 3:
                print(f"    ... 杩樻湁 {len(edge_list) - 3} 鏉?)
        
        # 妫€鏌ユ祴璇曠偣鐨勫嚭杈?
        test_nodes = node_types.get('test', [])
        print(f"\n馃幆 娴嬭瘯鐐瑰嚭杈瑰垎鏋?")
        for test_node in test_nodes:
            outgoing_edges = edges.filter(source_node=test_node)
            print(f"  {test_node.name}:")
            if outgoing_edges.exists():
                for edge in outgoing_edges:
                    target_name = edge.target_node.name if edge.target_node else 'unknown'
                    target_type = edge.target_node.node_type if edge.target_node else 'unknown'
                    print(f"    -> {target_name} ({target_type})")
            else:
                print(f"    鈿狅笍 鏃犲嚭杈?)
        
        # 妫€鏌ラ儴浠剁殑鍏ヨ竟
        component_nodes = node_types.get('component', [])
        print(f"\n馃敡 閮ㄤ欢鍏ヨ竟鍒嗘瀽:")
        for component_node in component_nodes:
            incoming_edges = edges.filter(target_node=component_node)
            print(f"  {component_node.name}:")
            if incoming_edges.exists():
                for edge in incoming_edges:
                    source_name = edge.source_node.name if edge.source_node else 'unknown'
                    source_type = edge.source_node.node_type if edge.source_node else 'unknown'
                    print(f"    {source_name} ({source_type}) ->")
            else:
                print(f"    鈿狅笍 鏃犲叆杈?)
        
        # 妫€鏌ユ晠闅滅殑鍏ヨ竟
        fault_nodes = node_types.get('fault', [])
        print(f"\n鈿狅笍 鏁呴殰鍏ヨ竟鍒嗘瀽:")
        for fault_node in fault_nodes:
            incoming_edges = edges.filter(target_node=fault_node)
            print(f"  {fault_node.name}:")
            if incoming_edges.exists():
                for edge in incoming_edges:
                    source_name = edge.source_node.name if edge.source_node else 'unknown'
                    source_type = edge.source_node.node_type if edge.source_node else 'unknown'
                    print(f"    {source_name} ({source_type}) ->")
            else:
                print(f"    鈿狅笍 鏃犲叆杈?)
        
        # 鍒嗘瀽璺緞鍙揪鎬?
        print(f"\n馃攳 璺緞鍙揪鎬у垎鏋?")
        
        # 鏋勫缓閭绘帴琛?
        adjacency = {}
        for edge in edges:
            source_id = edge.source_node.id if edge.source_node else None
            target_id = edge.target_node.id if edge.target_node else None
            
            if source_id and target_id:
                if source_id not in adjacency:
                    adjacency[source_id] = []
                adjacency[source_id].append(target_id)
        
        # 妫€鏌ヤ粠娴嬭瘯鐐瑰埌閮ㄤ欢鐨勮矾寰?
        test_to_component_paths = {}
        for test_node in test_nodes:
            test_to_component_paths[test_node.name] = []
            
            # 浣跨敤BFS鏌ユ壘璺緞
            visited = set()
            queue = [(test_node.id, [test_node.id])]
            
            while queue:
                current_id, path = queue.pop(0)
                
                if current_id in visited:
                    continue
                visited.add(current_id)
                
                # 妫€鏌ュ綋鍓嶈妭鐐规槸鍚︽槸閮ㄤ欢
                current_node = nodes.get(id=current_id)
                if current_node and current_node.node_type == 'component':
                    test_to_component_paths[test_node.name].append(path)
                    continue
                
                # 缁х画鎼滅储
                if current_id in adjacency:
                    for neighbor_id in adjacency[current_id]:
                        if neighbor_id not in visited:
                            queue.append((neighbor_id, path + [neighbor_id]))
        
        print(f"  娴嬭瘯鐐瑰埌閮ㄤ欢鐨勮矾寰?")
        for test_name, paths in test_to_component_paths.items():
            if paths:
                print(f"    {test_name}: {len(paths)} 鏉¤矾寰?)
                for i, path in enumerate(paths[:2]):  # 鍙樉绀哄墠2鏉?
                    path_names = []
                    for node_id in path:
                        node = nodes.get(id=node_id)
                        if node:
                            path_names.append(f"{node.name}({node.node_type})")
                    print(f"      璺緞{i+1}: {' -> '.join(path_names)}")
                if len(paths) > 2:
                    print(f"      ... 杩樻湁 {len(paths) - 2} 鏉¤矾寰?)
            else:
                print(f"    {test_name}: 鈿狅笍 鏃犺矾寰?)
        
        print("\n" + "=" * 60)
        print("鉁?鍥剧粨鏋勫垎鏋愬畬鎴?)
        
    except Exception as e:
        print(f"鉂?鍒嗘瀽杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬭皟璇曞浘缁撴瀯...")
    debug_graph_structure()



