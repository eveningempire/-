#!/usr/bin/env python
"""
妫€鏌SFG鐨勫師濮婮SON鏁版嵁
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

def check_raw_json():
    """妫€鏌SFG鐨勫師濮婮SON鏁版嵁"""
    print("馃攳 妫€鏌SFG鐨勫師濮婮SON鏁版嵁")
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            print(f"  鉂?娌℃湁婵€娲荤殑MSFG瀹氫箟")
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 妫€鏌ュ師濮婮SON鏁版嵁
        raw_data = active_msfg.raw_graph_data
        print(f"  馃搳 raw_data绫诲瀷: {type(raw_data)}")
        print(f"  馃搳 raw_data鏄惁涓虹┖: {raw_data is None}")
        
        if raw_data:
            print(f"  馃搳 raw_data閿? {list(raw_data.keys()) if isinstance(raw_data, dict) else '涓嶆槸瀛楀吀'}")
            
            if isinstance(raw_data, dict) and 'nodes' in raw_data:
                nodes = raw_data['nodes']
                print(f"  馃搳 JSON涓殑鑺傜偣鏁? {len(nodes)}")
                
                # 缁熻JSON涓殑鑺傜偣绫诲瀷
                json_node_types = {}
                for node in nodes:
                    node_type = node.get('type', 'unknown')
                    if node_type not in json_node_types:
                        json_node_types[node_type] = []
                    json_node_types[node_type].append({
                        'id': node.get('id'),
                        'name': node.get('name', ''),
                        'text': node.get('text', {}).get('value', '') if node.get('text') else ''
                    })
                
                print(f"  馃彈锔? JSON涓殑鑺傜偣绫诲瀷鍒嗗竷:")
                for node_type, nodes in json_node_types.items():
                    print(f"    {node_type}: {len(nodes)} 涓?)
                    for node in nodes[:3]:  # 鏄剧ず鍓?涓?
                        print(f"      - id: {node['id']}, name: '{node['name']}', text: '{node['text']}'")
                    if len(nodes) > 3:
                        print(f"      ... 杩樻湁 {len(nodes) - 3} 涓?)
            else:
                print(f"  鉂?raw_data涓病鏈塶odes瀛楁")
                # 鏄剧ずraw_data鐨勫墠鍑犱釜閿?
                if isinstance(raw_data, dict):
                    print(f"  馃搳 raw_data鐨勫墠5涓敭: {list(raw_data.keys())[:5]}")
        else:
            print(f"  鉂?raw_data涓虹┖")

def check_processed_json():
    """妫€鏌ュ鐞嗗悗鐨凧SON鏁版嵁"""
    print("\n馃搫 妫€鏌ュ鐞嗗悗鐨凧SON鏁版嵁")
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 妫€鏌ュ鐞嗗悗鐨凧SON鏁版嵁
        processed_data = active_msfg.processed_graph_data
        print(f"  馃搳 processed_data绫诲瀷: {type(processed_data)}")
        print(f"  馃搳 processed_data鏄惁涓虹┖: {processed_data is None}")
        
        if processed_data:
            print(f"  馃搳 processed_data閿? {list(processed_data.keys()) if isinstance(processed_data, dict) else '涓嶆槸瀛楀吀'}")
            
            if isinstance(processed_data, dict) and 'nodes' in processed_data:
                nodes = processed_data['nodes']
                print(f"  馃搳 澶勭悊鍚嶫SON涓殑鑺傜偣鏁? {len(nodes)}")
                
                # 缁熻澶勭悊鍚庣殑鑺傜偣绫诲瀷
                json_node_types = {}
                for node in nodes:
                    node_type = node.get('type', 'unknown')
                    if node_type not in json_node_types:
                        json_node_types[node_type] = []
                    json_node_types[node_type].append({
                        'id': node.get('id'),
                        'name': node.get('name', ''),
                        'text': node.get('text', {}).get('value', '') if node.get('text') else ''
                    })
                
                print(f"  馃彈锔? 澶勭悊鍚嶫SON涓殑鑺傜偣绫诲瀷鍒嗗竷:")
                for node_type, nodes in json_node_types.items():
                    print(f"    {node_type}: {len(nodes)} 涓?)
                    for node in nodes[:3]:  # 鏄剧ず鍓?涓?
                        print(f"      - id: {node['id']}, name: '{node['name']}', text: '{node['text']}'")
                    if len(nodes) > 3:
                        print(f"      ... 杩樻湁 {len(nodes) - 3} 涓?)
            else:
                print(f"  鉂?processed_data涓病鏈塶odes瀛楁")
        else:
            print(f"  鉂?processed_data涓虹┖")

if __name__ == "__main__":
    check_raw_json()
    check_processed_json()

