#!/usr/bin/env python
"""
妫€鏌omponent鑺傜偣鐨勫師濮嬫暟鎹紝瀵绘壘鍚嶇О淇℃伅
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, PHMModel

def check_component_names():
    print("馃攳 妫€鏌omponent鑺傜偣鐨勫師濮嬫暟鎹?)
    print("=" * 60)
    
    # 鑾峰彇鏈€鏂扮殑MSFG瀹氫箟
    try:
        cmg_model = PHMModel.objects.filter(is_active=True).first()
        if not cmg_model:
            print("鉂?娌℃湁鎵惧埌婵€娲荤殑PHM妯″瀷")
            return
            
        msfg_definition = MSFGDefinition.objects.filter(cmg_model=cmg_model).order_by('-created_at').first()
        if not msfg_definition:
            print("鉂?娌℃湁鎵惧埌MSFG瀹氫箟")
            return
            
        print(f"馃搵 妫€鏌MG妯″瀷: {cmg_model}")
        print(f"  鉁?MSFG: {msfg_definition}")
        
        # 鑾峰彇鎵€鏈塩omponent鑺傜偣
        component_nodes = MSFGNode.objects.filter(
            msfg_definition=msfg_definition,
            node_type='component'
        )
        
        print(f"馃敡 component鑺傜偣鏁伴噺: {component_nodes.count()}")
        
        # 妫€鏌ユ瘡涓猚omponent鑺傜偣鐨勮缁嗕俊鎭?
        for i, node in enumerate(component_nodes[:5]):  # 鍙樉绀哄墠5涓?
            print(f"\n馃敡 component鑺傜偣 {i+1}:")
            print(f"  - ID: {node.id}")
            print(f"  - node_id: {node.node_id}")
            print(f"  - name: '{node.name}'")
            print(f"  - position_x: {node.position_x}")
            print(f"  - position_y: {node.position_y}")
            
            # 妫€鏌ュ師濮婮SON鏁版嵁
            if msfg_definition.raw_graph_data:
                print(f"  馃攳 鍦ㄥ師濮婮SON涓煡鎵捐妭鐐?{node.node_id}...")
                
                # 鍦ㄥ師濮嬫暟鎹腑鏌ユ壘杩欎釜鑺傜偣
                found_in_raw = False
                for system_data in msfg_definition.raw_graph_data:
                    if 'data' in system_data and 'nodes' in system_data['data']:
                        for raw_node in system_data['data']['nodes']:
                            if raw_node.get('id') == node.node_id:
                                print(f"  鉁?鍦ㄥ師濮婮SON涓壘鍒拌妭鐐?")
                                print(f"    - type: {raw_node.get('type', 'N/A')}")
                                print(f"    - text: '{raw_node.get('text', 'N/A')}'")
                                print(f"    - name: '{raw_node.get('name', 'N/A')}'")
                                print(f"    - properties: {raw_node.get('properties', {})}")
                                found_in_raw = True
                                break
                        if found_in_raw:
                            break
                
                if not found_in_raw:
                    print(f"  鉂?鍦ㄥ師濮婮SON涓湭鎵惧埌鑺傜偣 {node.node_id}")
        
        # 妫€鏌rocessed_graph_data
        if msfg_definition.processed_graph_data:
            print(f"\n馃攳 妫€鏌rocessed_graph_data涓殑component鑺傜偣...")
            for system_data in msfg_definition.processed_graph_data:
                if 'data' in system_data and 'nodes' in system_data['data']:
                    for proc_node in system_data['data']['nodes']:
                        if proc_node.get('type') == 'subsystem-node':
                            print(f"  馃敡 subsystem-node: {proc_node.get('text', 'N/A')} (id: {proc_node.get('id', 'N/A')})")
        
        print("\n" + "=" * 60)
        print("鉁?妫€鏌ュ畬鎴?)
        
    except Exception as e:
        print(f"鉂?妫€鏌ヨ繃绋嬩腑鍑洪敊: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫鏌omponent鑺傜偣鍘熷鏁版嵁...")
    check_component_names()

