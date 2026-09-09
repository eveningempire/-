#!/usr/bin/env python
"""
娓呯悊閿欒鐨勬槧灏勫叧绯伙紝鎭㈠姝ｇ‘鐨勫浘缁撴瀯
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel, MSFGNode, MSFGEdge
from django.db import transaction

def cleanup_wrong_mappings():
    print("馃Ч 娓呯悊閿欒鐨勬槧灏勫叧绯?)
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
        
        print(f"\n馃搳 褰撳墠鐘舵€?")
        print(f"  鑺傜偣鏁? {nodes.count()}")
        print(f"  杈规暟: {edges.count()}")
        
        # 鍒嗘瀽褰撳墠杈圭殑鏂瑰悜
        edge_directions = {}
        for edge in edges:
            source_type = edge.source_node.node_type if edge.source_node else 'unknown'
            target_type = edge.target_node.node_type if edge.target_node else 'unknown'
            pattern = f"{source_type} -> {target_type}"
            
            if pattern not in edge_directions:
                edge_directions[pattern] = []
            edge_directions[pattern].append(edge)
        
        print(f"\n馃敆 褰撳墠杈规柟鍚?")
        for pattern, edge_list in edge_directions.items():
            print(f"  {pattern}: {len(edge_list)} 鏉?)
        
        # 妫€鏌ユ槸鍚︽湁鎴戝垱寤虹殑閿欒鏄犲皠
        has_wrong_mappings = False
        for pattern in edge_directions.keys():
            if 'test -> component' in pattern and len(edge_directions[pattern]) > 50:
                has_wrong_mappings = True
                break
        
        if not has_wrong_mappings:
            print(f"\n鉁?娌℃湁鍙戠幇閿欒鐨勬槧灏勶紝鏃犻渶娓呯悊")
            return
        
        print(f"\n馃Ч 鍙戠幇閿欒鐨勬槧灏勶紝寮€濮嬫竻鐞?..")
        
        with transaction.atomic():
            # 鍒犻櫎鎵€鏈夌幇鏈夌殑杈?
            edges.delete()
            print(f"  馃棏锔?鍒犻櫎浜嗘墍鏈?{edges.count()} 鏉¤竟")
            
            # 鎭㈠鍘熷鐨勮竟鏂瑰悜锛堝熀浜庡師濮嬫暟鎹級
            print(f"\n馃搵 鎭㈠鍘熷杈规柟鍚?..")
            
            # 浠庡師濮嬫暟鎹腑鎭㈠姝ｇ‘鐨勮竟
            raw_data = msfg_definition.raw_graph_data
            if isinstance(raw_data, dict) and 'SystemData' in raw_data:
                system_data = raw_data['SystemData']
                
                new_edges = []
                edge_count = 0
                
                for system in system_data:
                    if isinstance(system, dict):
                        data = system.get('data', {})
                        nodes_data = data.get('nodes', [])
                        edges_data = data.get('edges', [])
                        
                        # 鏋勫缓鑺傜偣ID鍒版暟鎹簱鑺傜偣鐨勬槧灏?
                        node_id_map = {}
                        for node in nodes:
                            node_id_map[node.node_id] = node
                        
                        # 鎭㈠鍘熷杈?
                        for edge_data in edges_data:
                            if isinstance(edge_data, dict):
                                source_id = str(edge_data.get('sourceNodeId') or edge_data.get('source') or '')
                                target_id = str(edge_data.get('targetNodeId') or edge_data.get('target') or '')
                                
                                if source_id in node_id_map and target_id in node_id_map:
                                    source_node = node_id_map[source_id]
                                    target_node = node_id_map[target_id]
                                    
                                    edge = MSFGEdge(
                                        msfg_definition=msfg_definition,
                                        edge_id=f"edge_{edge_count}",
                                        source_node=source_node,
                                        target_node=target_node,
                                        edge_type=str(edge_data.get('type') or 'polyline'),
                                        properties=edge_data.get('properties') or {}
                                    )
                                    new_edges.append(edge)
                                    edge_count += 1
                
                # 鎵归噺鍒涘缓杈?
                if new_edges:
                    MSFGEdge.objects.bulk_create(new_edges)
                    print(f"  鉁?鎭㈠浜?{len(new_edges)} 鏉″師濮嬭竟")
                else:
                    print(f"  鈿狅笍 娌℃湁鎭㈠浠讳綍杈?)
            
            # 楠岃瘉娓呯悊缁撴灉
            new_edges = MSFGEdge.objects.filter(msfg_definition=msfg_definition)
            print(f"\n馃搳 娓呯悊鍚庣粺璁?")
            print(f"  杈规暟: {new_edges.count()}")
            
            # 鍒嗘瀽鏂扮殑杈规柟鍚?
            new_edge_directions = {}
            for edge in new_edges:
                source_type = edge.source_node.node_type if edge.source_node else 'unknown'
                target_type = edge.target_node.node_type if edge.target_node else 'unknown'
                pattern = f"{source_type} -> {target_type}"
                
                if pattern not in new_edge_directions:
                    new_edge_directions[pattern] = []
                new_edge_directions[pattern].append(edge)
            
            print(f"\n馃敆 娓呯悊鍚庤竟鏂瑰悜:")
            for pattern, edge_list in new_edge_directions.items():
                print(f"  {pattern}: {len(edge_list)} 鏉?)
        
        print(f"\n鉁?娓呯悊瀹屾垚")
        print(f"\n馃挕 寤鸿:")
        print(f"  1. 鐜板湪鍙互閫氳繃鍓嶇鐣岄潰鎵嬪姩缂栬緫鏄犲皠鍏崇郴")
        print(f"  2. 璺緞锛氭祴鐐硅鍒?-> 閮ㄤ欢瀵瑰簲鍏崇郴")
        print(f"  3. 鏍规嵁瀹為檯鐨勭郴缁熺煡璇嗗拰娴嬭瘯鐐瑰姛鑳芥潵璁剧疆姝ｇ‘鐨勬槧灏?)
        
    except Exception as e:
        print(f"鉂?娓呯悊杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫竻鐞嗛敊璇槧灏?..")
    cleanup_wrong_mappings()



