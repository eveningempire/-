#!/usr/bin/env python
"""
璇︾粏妫€鏌ubsystem-node鐨凧SON缁撴瀯锛屽鎵惧悕绉颁俊鎭?
"""
import os
import sys
import django
import json

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel

def check_subsystem_structure():
    print("馃攳 璇︾粏妫€鏌ubsystem-node鐨凧SON缁撴瀯")
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
        
        # 妫€鏌aw_graph_data涓殑subsystem-node
        if msfg_definition.raw_graph_data:
            print(f"\n馃攳 妫€鏌aw_graph_data涓殑subsystem-node...")
            subsystem_count = 0
            
            for system_idx, system_data in enumerate(msfg_definition.raw_graph_data):
                if 'data' in system_data and 'nodes' in system_data['data']:
                    print(f"\n馃搳 绯荤粺 {system_idx + 1}: {system_data.get('name', 'Unknown')}")
                    
                    for node_idx, node in enumerate(system_data['data']['nodes']):
                        if node.get('type') == 'subsystem-node':
                            subsystem_count += 1
                            print(f"\n馃敡 subsystem-node {subsystem_count}:")
                            print(f"  - id: {node.get('id')}")
                            print(f"  - type: {node.get('type')}")
                            print(f"  - text: {node.get('text')}")
                            print(f"  - name: {node.get('name')}")
                            print(f"  - properties: {json.dumps(node.get('properties', {}), indent=4, ensure_ascii=False)}")
                            
                            # 璇︾粏妫€鏌ext瀛楁
                            text_data = node.get('text')
                            if text_data:
                                print(f"  - text瀛楁绫诲瀷: {type(text_data)}")
                                if isinstance(text_data, dict):
                                    for key, value in text_data.items():
                                        print(f"    - text.{key}: {value}")
                                else:
                                    print(f"    - text鍊? {text_data}")
                            
                            # 妫€鏌ュ叾浠栧彲鑳界殑瀛楁
                            for field in ['label', 'title', 'description', 'displayName']:
                                if field in node:
                                    print(f"  - {field}: {node[field]}")
                            
                            # 鍙樉绀哄墠3涓猻ubsystem-node
                            if subsystem_count >= 3:
                                break
                    
                    if subsystem_count >= 3:
                        break
        
        # 妫€鏌rocessed_graph_data涓殑subsystem-node
        if msfg_definition.processed_graph_data:
            print(f"\n馃攳 妫€鏌rocessed_graph_data涓殑subsystem-node...")
            for system_idx, system_data in enumerate(msfg_definition.processed_graph_data):
                if 'data' in system_data and 'nodes' in system_data['data']:
                    print(f"\n馃搳 澶勭悊鍚庣郴缁?{system_idx + 1}: {system_data.get('name', 'Unknown')}")
                    
                    for node in system_data['data']['nodes']:
                        if node.get('type') == 'subsystem-node':
                            print(f"  馃敡 subsystem-node: {node}")
                            break
        
        print("\n" + "=" * 60)
        print("鉁?妫€鏌ュ畬鎴?)
        
    except Exception as e:
        print(f"鉂?妫€鏌ヨ繃绋嬩腑鍑洪敊: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬭缁嗘鏌ubsystem-node缁撴瀯...")
    check_subsystem_structure()

