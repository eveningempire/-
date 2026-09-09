#!/usr/bin/env python
"""
璇︾粏璋冭瘯閮ㄤ欢鎻愬彇鍜屾槧灏勬祦绋?
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, PHMModel, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.component_integration import extract_components_from_msfg, ensure_msfg_component_mappings

def debug_component_flow():
    print("馃攳 璇︾粏璋冭瘯閮ㄤ欢鎻愬彇鍜屾槧灏勬祦绋?)
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
        
        # 1. 妫€鏌ユ暟鎹簱涓殑鑺傜偣
        print(f"\n馃攳 1. 妫€鏌ユ暟鎹簱涓殑鑺傜偣")
        print("=" * 40)
        
        all_nodes = MSFGNode.objects.filter(msfg_definition=msfg_definition)
        print(f"馃搳 鎬昏妭鐐规暟: {all_nodes.count()}")
        
        node_types = {}
        for node in all_nodes:
            node_type = node.node_type
            if node_type not in node_types:
                node_types[node_type] = []
            node_types[node_type].append(node)
        
        for node_type, nodes in node_types.items():
            print(f"  {node_type}: {len(nodes)} 涓?)
            for node in nodes[:3]:  # 鍙樉绀哄墠3涓?
                print(f"    - ID: {node.id}, name: '{node.name}', node_id: {node.node_id}")
            if len(nodes) > 3:
                print(f"    ... 杩樻湁 {len(nodes) - 3} 涓?)
        
        # 2. 妫€鏌omponent鑺傜偣鐨勫悕绉?
        print(f"\n馃攳 2. 妫€鏌omponent鑺傜偣鐨勫悕绉?)
        print("=" * 40)
        
        component_nodes = node_types.get('component', [])
        print(f"馃敡 component鑺傜偣鏁伴噺: {len(component_nodes)}")
        
        for i, node in enumerate(component_nodes):
            print(f"  component {i+1}: ID={node.id}, name='{node.name}', node_id={node.node_id}")
            
            # 妫€鏌ュ師濮婮SON涓殑tableName
            if msfg_definition.raw_graph_data:
                for system_data in msfg_definition.raw_graph_data:
                    if 'data' in system_data and 'nodes' in system_data['data']:
                        for raw_node in system_data['data']['nodes']:
                            if raw_node.get('id') == node.node_id:
                                table_name = (raw_node.get('properties') or {}).get('tableName', 'N/A')
                                print(f"    鍘熷tableName: '{table_name}'")
                                break
        
        # 3. 娴嬭瘯閮ㄤ欢鎻愬彇鍑芥暟
        print(f"\n馃攳 3. 娴嬭瘯閮ㄤ欢鎻愬彇鍑芥暟")
        print("=" * 40)
        
        components = extract_components_from_msfg(msfg_definition)
        print(f"馃敡 鎻愬彇鐨勯儴浠? {len(components)} 涓?)
        for comp in components:
            print(f"  - {comp}")
        
        # 4. 妫€鏌SFG瀹氫箟鐨勫瓧娈?
        print(f"\n馃攳 4. 妫€鏌SFG瀹氫箟鐨勫瓧娈?)
        print("=" * 40)
        
        print(f"馃搳 test_names: {len(msfg_definition.test_names or [])} 涓?)
        if msfg_definition.test_names:
            for test in msfg_definition.test_names[:5]:
                print(f"  - {test}")
        
        print(f"馃搳 component_names: {len(msfg_definition.component_names or [])} 涓?)
        if msfg_definition.component_names:
            for comp in msfg_definition.component_names:
                print(f"  - {comp}")
        
        print(f"馃搳 fault_names: {len(msfg_definition.fault_names or [])} 涓?)
        if msfg_definition.fault_names:
            for fault in msfg_definition.fault_names[:5]:
                print(f"  - {fault}")
        
        # 5. 妫€鏌ョ幇鏈夋槧灏?
        print(f"\n馃攳 5. 妫€鏌ョ幇鏈夋槧灏?)
        print("=" * 40)
        
        existing_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
        print(f"馃椇 鐜版湁鏄犲皠鏁伴噺: {existing_mappings.count()}")
        
        for mapping in existing_mappings[:5]:
            print(f"  - {mapping.test_point_name} -> {mapping.component_name}")
        
        # 6. 娴嬭瘯鏄犲皠鐢熸垚
        print(f"\n馃攳 6. 娴嬭瘯鏄犲皠鐢熸垚")
        print("=" * 40)
        
        print("馃攧 璋冪敤 ensure_msfg_component_mappings...")
        ensure_msfg_component_mappings(msfg_definition)
        
        # 妫€鏌ユ槧灏勫悗鐨勭粨鏋?
        updated_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
        print(f"馃椇 鏄犲皠鍚庢暟閲? {updated_mappings.count()}")
        
        for mapping in updated_mappings[:5]:
            print(f"  - {mapping.test_point_name} -> {mapping.component_name}")
        
        # 7. 鍐嶆娴嬭瘯閮ㄤ欢鎻愬彇
        print(f"\n馃攳 7. 鍐嶆娴嬭瘯閮ㄤ欢鎻愬彇")
        print("=" * 40)
        
        components_after = extract_components_from_msfg(msfg_definition)
        print(f"馃敡 鏄犲皠鍚庢彁鍙栫殑閮ㄤ欢: {len(components_after)} 涓?)
        for comp in components_after:
            print(f"  - {comp}")
        
        print("\n" + "=" * 60)
        print("鉁?璋冭瘯瀹屾垚")
        
    except Exception as e:
        print(f"鉂?璋冭瘯杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬭缁嗚皟璇曢儴浠舵祦绋?..")
    debug_component_flow()

