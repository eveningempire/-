#!/usr/bin/env python
"""
妫€鏌ュ鐞嗗悗鏁版嵁涓殑鑺傜偣绫诲瀷
"""

import os
import django
import json

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition
from msfg_analysis.algorithms.msfg.component_integration import get_active_msfg_for_cmg_model

def check_processed_nodes():
    """妫€鏌ュ鐞嗗悗鏁版嵁涓殑鑺傜偣绫诲瀷"""
    print("馃攳 妫€鏌ュ鐞嗗悗鏁版嵁涓殑鑺傜偣绫诲瀷")
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            print(f"  鉂?娌℃湁婵€娲荤殑MSFG瀹氫箟")
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 妫€鏌ュ鐞嗗悗鐨凧SON鏁版嵁
        processed_data = active_msfg.processed_graph_data
        if not processed_data or not isinstance(processed_data, list):
            print(f"  鉂?processed_data涓嶆槸鍒楄〃鎴栦负绌?)
            continue
        
        print(f"  馃搳 processed_data闀垮害: {len(processed_data)}")
        
        # 閬嶅巻鎵€鏈夌郴缁熸暟鎹?
        all_nodes = []
        all_edges = []
        
        for i, system_data in enumerate(processed_data):
            print(f"  馃搳 绯荤粺 {i+1}: {system_data.get('name', 'Unknown')}")
            
            if 'data' in system_data and isinstance(system_data['data'], dict):
                data = system_data['data']
                
                # 鏀堕泦鑺傜偣
                if 'nodes' in data and isinstance(data['nodes'], list):
                    nodes = data['nodes']
                    print(f"    馃搳 鑺傜偣鏁? {len(nodes)}")
                    all_nodes.extend(nodes)
                    
                    # 缁熻鑺傜偣绫诲瀷
                    node_types = {}
                    for node in nodes:
                        node_type = node.get('type', 'unknown')
                        if node_type not in node_types:
                            node_types[node_type] = []
                        node_types[node_type].append({
                            'id': node.get('id'),
                            'name': node.get('name', ''),
                            'text': node.get('text', {}).get('value', '') if node.get('text') else ''
                        })
                    
                    print(f"    馃彈锔? 鑺傜偣绫诲瀷鍒嗗竷:")
                    for node_type, nodes_list in node_types.items():
                        print(f"      {node_type}: {len(nodes_list)} 涓?)
                        for node in nodes_list[:2]:  # 鏄剧ず鍓?涓?
                            print(f"        - id: {node['id']}, name: '{node['name']}', text: '{node['text']}'")
                        if len(nodes_list) > 2:
                            print(f"        ... 杩樻湁 {len(nodes_list) - 2} 涓?)
                
                # 鏀堕泦杈?
                if 'edges' in data and isinstance(data['edges'], list):
                    edges = data['edges']
                    print(f"    馃搳 杈规暟: {len(edges)}")
                    all_edges.extend(edges)
            else:
                print(f"    鉂?娌℃湁data瀛楁鎴杁ata涓嶆槸瀛楀吀")
        
        # 姹囨€绘墍鏈夎妭鐐?
        print(f"\n馃搳 姹囨€绘墍鏈夎妭鐐?")
        print(f"  馃搳 鎬昏妭鐐规暟: {len(all_nodes)}")
        print(f"  馃搳 鎬昏竟鏁? {len(all_edges)}")
        
        # 缁熻鎵€鏈夎妭鐐圭殑绫诲瀷
        all_node_types = {}
        for node in all_nodes:
            node_type = node.get('type', 'unknown')
            if node_type not in all_node_types:
                all_node_types[node_type] = []
            all_node_types[node_type].append({
                'id': node.get('id'),
                'name': node.get('name', ''),
                'text': node.get('text', {}).get('value', '') if node.get('text') else ''
            })
        
        print(f"  馃彈锔? 鎵€鏈夎妭鐐圭被鍨嬪垎甯?")
        for node_type, nodes_list in all_node_types.items():
            print(f"    {node_type}: {len(nodes_list)} 涓?)
            for node in nodes_list[:3]:  # 鏄剧ず鍓?涓?
                print(f"      - id: {node['id']}, name: '{node['name']}', text: '{node['text']}'")
            if len(nodes_list) > 3:
                print(f"      ... 杩樻湁 {len(nodes_list) - 3} 涓?)

def check_specific_node_types():
    """妫€鏌ョ壒瀹氱殑鑺傜偣绫诲瀷"""
    print("\n馃攳 妫€鏌ョ壒瀹氱殑鑺傜偣绫诲瀷")
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        processed_data = active_msfg.processed_graph_data
        if not processed_data or not isinstance(processed_data, list):
            continue
        
        # 鏀堕泦鎵€鏈夎妭鐐?
        all_nodes = []
        for system_data in processed_data:
            if 'data' in system_data and isinstance(system_data['data'], dict):
                data = system_data['data']
                if 'nodes' in data and isinstance(data['nodes'], list):
                    all_nodes.extend(data['nodes'])
        
        # 鏌ユ壘subsystem-node鍜宖ault-node
        subsystem_nodes = []
        fault_nodes = []
        
        for node in all_nodes:
            node_type = node.get('type', '')
            if 'subsystem' in node_type.lower():
                subsystem_nodes.append(node)
            elif 'fault' in node_type.lower():
                fault_nodes.append(node)
        
        print(f"  馃敡 subsystem鐩稿叧鑺傜偣: {len(subsystem_nodes)} 涓?)
        for node in subsystem_nodes:
            print(f"    - type: '{node.get('type')}', id: {node.get('id')}, name: '{node.get('name')}'")
        
        print(f"  馃敡 fault鐩稿叧鑺傜偣: {len(fault_nodes)} 涓?)
        for node in fault_nodes:
            print(f"    - type: '{node.get('type')}', id: {node.get('id')}, name: '{node.get('name')}'")

if __name__ == "__main__":
    check_processed_nodes()
    check_specific_node_types()

