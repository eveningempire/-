#!/usr/bin/env python
"""
娴嬭瘯MSFG鑺傜偣绫诲瀷淇
"""

import os
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition, MSFGNode
from msfg_analysis.algorithms.msfg.component_integration import get_active_msfg_for_cmg_model, extract_components_from_msfg

def test_msfg_fix():
    """娴嬭瘯MSFG鑺傜偣绫诲瀷淇"""
    print("馃攳 娴嬭瘯MSFG鑺傜偣绫诲瀷淇")
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            print(f"  鉂?娌℃湁婵€娲荤殑MSFG瀹氫箟")
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 妫€鏌ユ暟鎹簱涓殑鑺傜偣绫诲瀷
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
        
        # 娴嬭瘯閮ㄤ欢鎻愬彇
        print(f"\n馃敡 娴嬭瘯閮ㄤ欢鎻愬彇:")
        components = extract_components_from_msfg(active_msfg)
        print(f"  馃搳 鎻愬彇鐨勯儴浠? {len(components)} 涓?)
        if components:
            print(f"  馃搵 閮ㄤ欢鍒楄〃: {components}")
        else:
            print(f"  鉂?娌℃湁鎻愬彇鍒伴儴浠?)
        
        # 妫€鏌ユ槸鍚︽湁component绫诲瀷鐨勮妭鐐?
        component_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='component'
        )
        print(f"  馃敡 component绫诲瀷鑺傜偣: {component_nodes.count()} 涓?)
        if component_nodes.exists():
            for node in component_nodes[:3]:
                print(f"    - ID: {node.id}, name: '{node.name}'")
            if component_nodes.count() > 3:
                print(f"    ... 杩樻湁 {component_nodes.count() - 3} 涓?)

if __name__ == "__main__":
    test_msfg_fix()

