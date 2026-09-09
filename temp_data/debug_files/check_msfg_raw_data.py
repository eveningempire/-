#!/usr/bin/env python
"""
妫€鏌SFG鍘熷鏁版嵁锛屽垎鏋愬浘缁撴瀯闂
"""
import os
import sys
import django
import json

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel

def check_msfg_raw_data():
    print("馃攳 妫€鏌SFG鍘熷鏁版嵁")
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
        
        # 妫€鏌ュ師濮嬪浘鏁版嵁
        raw_data = msfg_definition.raw_graph_data
        processed_data = msfg_definition.processed_graph_data
        
        print(f"\n馃搳 鍘熷鍥炬暟鎹粨鏋?")
        if isinstance(raw_data, dict):
            print(f"  绫诲瀷: dict")
            print(f"  閿? {list(raw_data.keys())}")
            
            # 妫€鏌ystemData
            if 'SystemData' in raw_data:
                system_data = raw_data['SystemData']
                print(f"  SystemData: {len(system_data)} 涓郴缁?)
                
                for i, system in enumerate(system_data):
                    print(f"\n  绯荤粺 {i+1}:")
                    if isinstance(system, dict):
                        system_id = system.get('system_id', 'unknown')
                        print(f"    ID: {system_id}")
                        
                        data = system.get('data', {})
                        if isinstance(data, dict):
                            nodes = data.get('nodes', [])
                            edges = data.get('edges', [])
                            
                            print(f"    鑺傜偣鏁? {len(nodes)}")
                            print(f"    杈规暟: {len(edges)}")
                            
                            # 鍒嗘瀽鑺傜偣绫诲瀷
                            node_types = {}
                            for node in nodes:
                                if isinstance(node, dict):
                                    node_type = str(node.get('type', '')).lower()
                                    if node_type not in node_types:
                                        node_types[node_type] = 0
                                    node_types[node_type] += 1
                            
                            print(f"    鑺傜偣绫诲瀷鍒嗗竷:")
                            for node_type, count in node_types.items():
                                print(f"      {node_type}: {count} 涓?)
                            
                            # 鍒嗘瀽杈圭殑杩炴帴妯″紡
                            if edges:
                                print(f"    杈硅繛鎺ユā寮?")
                                edge_patterns = {}
                                for edge in edges:
                                    if isinstance(edge, dict):
                                        source_id = edge.get('sourceNodeId') or edge.get('source', '')
                                        target_id = edge.get('targetNodeId') or edge.get('target', '')
                                        
                                        # 鎵惧埌婧愯妭鐐瑰拰鐩爣鑺傜偣鐨勭被鍨?
                                        source_type = 'unknown'
                                        target_type = 'unknown'
                                        
                                        for node in nodes:
                                            if isinstance(node, dict) and str(node.get('id', '')) == str(source_id):
                                                source_type = str(node.get('type', '')).lower()
                                            if isinstance(node, dict) and str(node.get('id', '')) == str(target_id):
                                                target_type = str(node.get('type', '')).lower()
                                        
                                        pattern = f"{source_type} -> {target_type}"
                                        if pattern not in edge_patterns:
                                            edge_patterns[pattern] = []
                                        edge_patterns[pattern].append((source_id, target_id))
                                
                                for pattern, edge_list in edge_patterns.items():
                                    print(f"      {pattern}: {len(edge_list)} 鏉?)
                                    for source_id, target_id in edge_list[:3]:
                                        print(f"        {source_id} -> {target_id}")
                                    if len(edge_list) > 3:
                                        print(f"        ... 杩樻湁 {len(edge_list) - 3} 鏉?)
        else:
            print(f"  绫诲瀷: {type(raw_data)}")
            print(f"  鍐呭: {str(raw_data)[:200]}...")
        
        print(f"\n馃搳 澶勭悊鍚庡浘鏁版嵁缁撴瀯:")
        if isinstance(processed_data, dict):
            print(f"  绫诲瀷: dict")
            print(f"  閿? {list(processed_data.keys())}")
            
            if 'nodes' in processed_data and 'edges' in processed_data:
                nodes = processed_data['nodes']
                edges = processed_data['edges']
                
                print(f"  鑺傜偣鏁? {len(nodes)}")
                print(f"  杈规暟: {len(edges)}")
                
                # 鍒嗘瀽鑺傜偣绫诲瀷
                node_types = {}
                for node in nodes:
                    if isinstance(node, dict):
                        node_type = str(node.get('type', '')).lower()
                        if node_type not in node_types:
                            node_types[node_type] = 0
                        node_types[node_type] += 1
                
                print(f"  鑺傜偣绫诲瀷鍒嗗竷:")
                for node_type, count in node_types.items():
                    print(f"    {node_type}: {count} 涓?)
                
                # 鍒嗘瀽杈圭殑杩炴帴妯″紡
                if edges:
                    print(f"  杈硅繛鎺ユā寮?")
                    edge_patterns = {}
                    for edge in edges:
                        if isinstance(edge, dict):
                            source_id = edge.get('sourceNodeId') or edge.get('source', '')
                            target_id = edge.get('targetNodeId') or edge.get('target', '')
                            
                            # 鎵惧埌婧愯妭鐐瑰拰鐩爣鑺傜偣鐨勭被鍨?
                            source_type = 'unknown'
                            target_type = 'unknown'
                            
                            for node in nodes:
                                if isinstance(node, dict) and str(node.get('id', '')) == str(source_id):
                                    source_type = str(node.get('type', '')).lower()
                                if isinstance(node, dict) and str(node.get('id', '')) == str(target_id):
                                    target_type = str(node.get('type', '')).lower()
                            
                            pattern = f"{source_type} -> {target_type}"
                            if pattern not in edge_patterns:
                                edge_patterns[pattern] = []
                            edge_patterns[pattern].append((source_id, target_id))
                    
                    for pattern, edge_list in edge_patterns.items():
                        print(f"    {pattern}: {len(edge_list)} 鏉?)
                        for source_id, target_id in edge_list[:3]:
                            print(f"      {source_id} -> {target_id}")
                        if len(edge_list) > 3:
                            print(f"      ... 杩樻湁 {len(edge_list) - 3} 鏉?)
        else:
            print(f"  绫诲瀷: {type(processed_data)}")
            print(f"  鍐呭: {str(processed_data)[:200]}...")
        
        print("\n" + "=" * 60)
        print("鉁?鍘熷鏁版嵁鍒嗘瀽瀹屾垚")
        
    except Exception as e:
        print(f"鉂?鍒嗘瀽杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫鏌ュ師濮嬫暟鎹?..")
    check_msfg_raw_data()



