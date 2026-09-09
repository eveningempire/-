#!/usr/bin/env python
"""
妫€鏌omponent鑺傜偣鐨勭湡瀹瀟ableName
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, PHMModel

def check_real_component_names():
    print("馃攳 妫€鏌omponent鑺傜偣鐨勭湡瀹瀟ableName")
    print("=" * 60)
    
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
        for i, node in enumerate(component_nodes):
            print(f"\n馃敡 component鑺傜偣 {i+1}:")
            print(f"  - ID: {node.id}")
            print(f"  - node_id: {node.node_id}")
            print(f"  - 鏁版嵁搴搉ame: '{node.name}'")
            
            # 妫€鏌ュ師濮婮SON涓殑tableName
            if msfg_definition.raw_graph_data:
                for system_data in msfg_definition.raw_graph_data:
                    if 'data' in system_data and 'nodes' in system_data['data']:
                        for raw_node in system_data['data']['nodes']:
                            if raw_node.get('id') == node.node_id:
                                table_name = (raw_node.get('properties') or {}).get('tableName', 'N/A')
                                print(f"  - 鍘熷tableName: '{table_name}'")
                                
                                # 妫€鏌ュ叾浠栧彲鑳界殑瀛楁
                                props = raw_node.get('properties', {})
                                print(f"  - properties: {props}")
                                break
        
        print("\n" + "=" * 60)
        print("鉁?妫€鏌ュ畬鎴?)
        
    except Exception as e:
        print(f"鉂?妫€鏌ヨ繃绋嬩腑鍑洪敊: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫鏌ョ湡瀹為儴浠跺悕绉?..")
    check_real_component_names()

