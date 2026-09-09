#!/usr/bin/env python
"""
妫€鏌ユ暟鎹簱涓妭鐐圭殑瀹為檯绫诲瀷
"""

import os
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge
from msfg_analysis.algorithms.msfg.component_integration import get_active_msfg_for_cmg_model

def check_node_types_in_database():
    """妫€鏌ユ暟鎹簱涓妭鐐圭殑瀹為檯绫诲瀷"""
    print("馃攳 妫€鏌ユ暟鎹簱涓妭鐐圭殑瀹為檯绫诲瀷")
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            print(f"  鉂?娌℃湁婵€娲荤殑MSFG瀹氫箟")
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 鑾峰彇鎵€鏈夎妭鐐?
        all_nodes = MSFGNode.objects.filter(msfg_definition=active_msfg)
        print(f"  馃搳 鎬昏妭鐐规暟: {all_nodes.count()}")
        
        # 鎸夌被鍨嬬粺璁¤妭鐐?
        node_types = {}
        for node in all_nodes:
            node_type = node.node_type
            if node_type not in node_types:
                node_types[node_type] = []
            node_types[node_type].append({
                'id': node.id,
                'name': node.name,
                'node_id': node.node_id
            })
        
        print(f"  馃彈锔? 鏁版嵁搴撲腑鐨勮妭鐐圭被鍨嬪垎甯?")
        for node_type, nodes in node_types.items():
            print(f"    {node_type}: {len(nodes)} 涓?)
            for node in nodes[:3]:  # 鏄剧ず鍓?涓?
                print(f"      - ID: {node['id']}, node_id: {node['node_id']}, name: '{node['name']}'")
            if len(nodes) > 3:
                print(f"      ... 杩樻湁 {len(nodes) - 3} 涓?)

def check_json_import_logic():
    """妫€鏌SON瀵煎叆閫昏緫"""
    print("\n馃搫 妫€鏌SON瀵煎叆閫昏緫")
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 妫€鏌ュ師濮婮SON鏁版嵁
        raw_data = active_msfg.raw_graph_data
        if raw_data and 'nodes' in raw_data:
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

def check_type_mapping():
    """妫€鏌ョ被鍨嬫槧灏勫叧绯?""
    print("\n馃攧 妫€鏌ョ被鍨嬫槧灏勫叧绯?)
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 鑾峰彇鍘熷JSON鏁版嵁
        raw_data = active_msfg.raw_graph_data
        if not raw_data or 'nodes' not in raw_data:
            continue
        
        # 鑾峰彇鏁版嵁搴撲腑鐨勮妭鐐?
        db_nodes = MSFGNode.objects.filter(msfg_definition=active_msfg)
        
        # 鍒涘缓鏄犲皠鍏崇郴
        json_to_db_mapping = {}
        for json_node in raw_data['nodes']:
            json_id = json_node.get('id')
            json_type = json_node.get('type', 'unknown')
            
            # 鏌ユ壘瀵瑰簲鐨勬暟鎹簱鑺傜偣
            db_node = db_nodes.filter(node_id=json_id).first()
            if db_node:
                json_to_db_mapping[json_id] = {
                    'json_type': json_type,
                    'db_type': db_node.node_type,
                    'json_name': json_node.get('name', ''),
                    'db_name': db_node.name,
                    'match': json_type == db_node.node_type
                }
        
        print(f"  馃搳 绫诲瀷鏄犲皠妫€鏌?")
        for node_id, mapping in json_to_db_mapping.items():
            status = "鉁? if mapping['match'] else "鉂?
            print(f"    {status} {node_id}: JSON({mapping['json_type']}) -> DB({mapping['db_type']})")
            if not mapping['match']:
                print(f"      JSON name: '{mapping['json_name']}', DB name: '{mapping['db_name']}'")

def main():
    """涓诲嚱鏁?""
    print("馃殌 寮€濮嬫鏌SFG鑺傜偣绫诲瀷")
    
    # 1. 妫€鏌ユ暟鎹簱涓殑鑺傜偣绫诲瀷
    check_node_types_in_database()
    
    # 2. 妫€鏌SON瀵煎叆閫昏緫
    check_json_import_logic()
    
    # 3. 妫€鏌ョ被鍨嬫槧灏勫叧绯?
    check_type_mapping()
    
    print("\n" + "=" * 60)
    print("鉁?妫€鏌ュ畬鎴?)
    print("=" * 60)

if __name__ == "__main__":
    main()

