#!/usr/bin/env python
"""
鍒嗘瀽500NM鐨勯儴浠舵彁鍙栭€昏緫
鐢ㄤ簬鐞嗚В姝ｇ‘鐨勯儴浠舵彁鍙栨柟寮?
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition, MSFGNode, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.component_integration import extract_components_from_msfg

def analyze_500nm_components():
    """璇︾粏鍒嗘瀽500NM鐨勯儴浠舵彁鍙栭€昏緫"""
    print("馃攳 璇︾粏鍒嗘瀽500NM鐨勯儴浠舵彁鍙栭€昏緫")
    print("=" * 80)
    
    try:
        # 1. 鏌ユ壘500NM鐨凜MG妯″瀷
        cmg_model = PHMModel.objects.get(model_name="500NM")
        print(f"鉁?鎵惧埌PHM妯″瀷: {cmg_model.model_name} (ID: {cmg_model.id})")
        
        # 2. 鏌ユ壘娲昏穬鐨凪SFG閰嶇疆
        active_msfg = MSFGDefinition.objects.filter(
            cmg_model=cmg_model,
            is_active=True
        ).order_by('-updated_at').first()
        
        if not active_msfg:
            print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG閰嶇疆")
            return
        
        print(f"鉁?鎵惧埌娲昏穬MSFG: {active_msfg.name} (ID: {active_msfg.id})")
        print(f"   鍒涘缓鏃堕棿: {active_msfg.created_at}")
        print(f"   鏇存柊鏃堕棿: {active_msfg.updated_at}")
        
        # 3. 璇︾粏鍒嗘瀽MSFG鐨刢omponent_names瀛楁
        print(f"\n馃搵 MSFG.component_names瀛楁璇︾粏鍒嗘瀽:")
        if active_msfg.component_names:
            print(f"   鉁?鏈夐儴浠跺垪琛? {active_msfg.component_names}")
            print(f"   閮ㄤ欢鏁伴噺: {len(active_msfg.component_names)}")
            for i, comp in enumerate(active_msfg.component_names, 1):
                print(f"     {i}. {comp}")
        else:
            print("   鉂?component_names瀛楁涓虹┖")
        
        # 4. 璇︾粏鍒嗘瀽MSFGNode琛ㄤ腑鐨勬墍鏈夎妭鐐?
        print(f"\n馃敡 MSFGNode琛ㄤ腑鐨勬墍鏈夎妭鐐硅缁嗗垎鏋?")
        all_nodes = MSFGNode.objects.filter(msfg_definition=active_msfg)
        print(f"   鎬昏妭鐐规暟閲? {all_nodes.count()}")
        
        # 鎸夌被鍨嬪垎缁?
        nodes_by_type = {}
        for node in all_nodes:
            node_type = node.node_type
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
            nodes_by_type[node_type].append(node)
        
        for node_type, nodes in nodes_by_type.items():
            print(f"\n   馃搳 {node_type} 绫诲瀷鑺傜偣 ({len(nodes)} 涓?:")
            for node in nodes:
                print(f"      - ID: {node.node_id}, 鍚嶇О: '{node.name}', 绫诲瀷: {node.node_type}")
                if node.properties:
                    print(f"        灞炴€? {node.properties}")
        
        # 5. 鐗瑰埆鍏虫敞绯荤粺鑺傜偣
        print(f"\n馃敡 绯荤粺鑺傜偣璇︾粏鍒嗘瀽:")
        system_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='system'
        )
        
        print(f"   绯荤粺鑺傜偣鎬绘暟: {system_nodes.count()}")
        for node in system_nodes:
            print(f"      - ID: {node.node_id}")
            print(f"        鍚嶇О: '{node.name}'")
            print(f"        浣嶇疆: ({node.position_x}, {node.position_y})")
            print(f"        灞炴€? {node.properties}")
            print(f"        鏄惁琚帓闄? {'鏄? if node.name in ['root', 'system', ''] else '鍚?}")
        
        # 6. 鍒嗘瀽娴嬭瘯鐐?閮ㄤ欢鏄犲皠
        print(f"\n馃敆 娴嬭瘯鐐?閮ㄤ欢鏄犲皠璇︾粏鍒嗘瀽:")
        mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
        if mappings.exists():
            print(f"   鏄犲皠鎬绘暟: {mappings.count()}")
            for mapping in mappings:
                print(f"      - 娴嬭瘯鐐? '{mapping.test_point_name}'")
                print(f"        閮ㄤ欢: '{mapping.component_name}'")
                print(f"        鏄犲皠绫诲瀷: {mapping.mapping_type}")
                print(f"        鏉冮噸: {mapping.weight}")
                print(f"        閮ㄤ欢绫诲瀷: {mapping.component_type}")
                print(f"        閲嶈搴? {mapping.importance_weight}")
                print(f"        鏄惁鍏抽敭: {mapping.is_critical}")
                print(f"        鎻忚堪: {mapping.description}")
        else:
            print("   鉂?娌℃湁鎵惧埌娴嬭瘯鐐?閮ㄤ欢鏄犲皠")
        
        # 7. 浣跨敤extract_components_from_msfg鍑芥暟鎻愬彇閮ㄤ欢
        print(f"\n馃攳 extract_components_from_msfg鍑芥暟鎻愬彇缁撴灉:")
        try:
            extracted_components = extract_components_from_msfg(active_msfg)
            if extracted_components:
                print(f"   鉁?鎻愬彇鍒?{len(extracted_components)} 涓儴浠?")
                for i, comp in enumerate(extracted_components, 1):
                    print(f"     {i}. {comp}")
            else:
                print("   鉂?娌℃湁鎻愬彇鍒颁换浣曢儴浠?)
        except Exception as e:
            print(f"   鉂?鎻愬彇閮ㄤ欢鏃跺嚭閿? {e}")
        
        # 8. 鍒嗘瀽鍘熷鍥炬暟鎹?
        print(f"\n馃搳 鍘熷鍥炬暟鎹垎鏋?")
        if active_msfg.raw_graph_data:
            print(f"   鉁?鏈夊師濮嬪浘鏁版嵁")
            # 鍒嗘瀽鍘熷鍥炬暟鎹腑鐨勮妭鐐?
            raw_data = active_msfg.raw_graph_data
            if isinstance(raw_data, dict) and 'nodes' in raw_data:
                raw_nodes = raw_data['nodes']
                print(f"   鍘熷鑺傜偣鏁伴噺: {len(raw_nodes)}")
                
                # 鍒嗘瀽绯荤粺鑺傜偣
                system_nodes_raw = [n for n in raw_nodes if 'system' in str(n.get('type', '')).lower()]
                print(f"   鍘熷绯荤粺鑺傜偣鏁伴噺: {len(system_nodes_raw)}")
                
                for node in system_nodes_raw:
                    node_type = node.get('type', '')
                    node_name = (
                        (node.get('text') or {}).get('value') or 
                        node.get('name') or 
                        (node.get('properties') or {}).get('tableName') or 
                        node.get('id')
                    )
                    print(f"      - 绫诲瀷: {node_type}, 鍚嶇О: '{node_name}'")
        else:
            print("   鉂?娌℃湁鍘熷鍥炬暟鎹?)
        
        # 9. 鎬荤粨500NM鐨勬垚鍔熺粡楠?
        print(f"\n馃挕 500NM鎴愬姛缁忛獙鎬荤粨:")
        print(f"   1. component_names瀛楁: {'鏈夋暟鎹? if active_msfg.component_names else '鏃犳暟鎹?}")
        print(f"   2. 绯荤粺鑺傜偣鏁伴噺: {len([n for n in system_nodes if n.name not in ['root', 'system', '']])}")
        print(f"   3. 娴嬭瘯鐐?閮ㄤ欢鏄犲皠鏁伴噺: {mappings.count()}")
        print(f"   4. extract_components_from_msfg缁撴灉: {len(extracted_components) if extracted_components else 0} 涓儴浠?)
        
    except PHMModel.DoesNotExist:
        print("鉂?鎵句笉鍒?00NM鐨凜MG妯″瀷")
    except Exception as e:
        print(f"鉂?鍒嗘瀽杩囩▼涓嚭閿? {e}")

def main():
    """涓诲嚱鏁?""
    analyze_500nm_components()

if __name__ == "__main__":
    main()

