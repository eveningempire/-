#!/usr/bin/env python
"""
妫€鏌ubsystem-node绫诲瀷鐨勮妭鐐?
"""

import os
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge
from msfg_analysis.algorithms.msfg.component_integration import get_active_msfg_for_cmg_model

def check_subsystem_nodes():
    """妫€鏌ubsystem-node绫诲瀷鐨勮妭鐐?""
    print("馃攳 妫€鏌ubsystem-node绫诲瀷鐨勮妭鐐?)
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            print(f"  鉂?娌℃湁婵€娲荤殑MSFG瀹氫箟")
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 妫€鏌ユ墍鏈夎妭鐐圭被鍨?
        all_nodes = MSFGNode.objects.filter(msfg_definition=active_msfg)
        print(f"  馃搳 鎬昏妭鐐规暟: {all_nodes.count()}")
        
        # 鎸夌被鍨嬬粺璁¤妭鐐?
        node_types = {}
        for node in all_nodes:
            node_type = node.node_type
            if node_type not in node_types:
                node_types[node_type] = []
            node_types[node_type].append(node.name)
        
        print(f"  馃彈锔? 鑺傜偣绫诲瀷鍒嗗竷:")
        for node_type, names in node_types.items():
            print(f"    {node_type}: {len(names)} 涓?)
            if names:
                print(f"      绀轰緥: {names[:3]}{'...' if len(names) > 3 else ''}")
        
        # 鐗瑰埆妫€鏌ubsystem-node绫诲瀷
        subsystem_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='subsystem-node'
        )
        
        print(f"\n  馃敡 subsystem-node鑺傜偣: {subsystem_nodes.count()} 涓?)
        if subsystem_nodes.exists():
            print(f"  馃搵 subsystem-node鑺傜偣鍒楄〃:")
            for node in subsystem_nodes:
                print(f"    - {node.name} (ID: {node.id})")
        
        # 妫€鏌ユ槸鍚︽湁鍏朵粬鍙兘鐨勯儴浠惰妭鐐圭被鍨?
        component_like_types = ['component', 'component-node', 'system', 'subsystem']
        for node_type in component_like_types:
            nodes = MSFGNode.objects.filter(
                msfg_definition=active_msfg,
                node_type=node_type
            )
            if nodes.exists():
                print(f"\n  馃敡 {node_type}鑺傜偣: {nodes.count()} 涓?)
                for node in nodes[:5]:  # 鏄剧ず鍓?涓?
                    print(f"    - {node.name} (ID: {node.id})")

def check_node_connections():
    """妫€鏌ヨ妭鐐硅繛鎺ュ叧绯?""
    print("\n馃敆 妫€鏌ヨ妭鐐硅繛鎺ュ叧绯?)
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 鑾峰彇娴嬭瘯鐐硅妭鐐?
        test_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='test'
        )
        
        print(f"  馃搳 娴嬭瘯鐐硅妭鐐? {test_nodes.count()} 涓?)
        
        # 鑾峰彇subsystem-node鑺傜偣
        subsystem_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='subsystem-node'
        )
        
        print(f"  馃敡 subsystem-node鑺傜偣: {subsystem_nodes.count()} 涓?)
        
        # 妫€鏌ヤ粠娴嬭瘯鐐瑰埌subsystem-node鐨勮繛鎺?
        edges = MSFGEdge.objects.filter(msfg_definition=active_msfg)
        print(f"  馃敆 鎬昏竟鏁? {edges.count()}")
        
        # 缁熻杩炴帴绫诲瀷
        connection_types = {}
        for edge in edges:
            source_type = edge.source_node.node_type if edge.source_node else 'unknown'
            target_type = edge.target_node.node_type if edge.target_node else 'unknown'
            connection_key = f"{source_type} -> {target_type}"
            
            if connection_key not in connection_types:
                connection_types[connection_key] = 0
            connection_types[connection_key] += 1
        
        print(f"  馃搱 杩炴帴绫诲瀷缁熻:")
        for connection_type, count in connection_types.items():
            print(f"    {connection_type}: {count} 鏉?)

def main():
    """涓诲嚱鏁?""
    print("馃殌 寮€濮嬫鏌ubsystem-node鑺傜偣")
    
    # 1. 妫€鏌ubsystem-node绫诲瀷鐨勮妭鐐?
    check_subsystem_nodes()
    
    # 2. 妫€鏌ヨ妭鐐硅繛鎺ュ叧绯?
    check_node_connections()
    
    print("\n" + "=" * 60)
    print("鉁?妫€鏌ュ畬鎴?)
    print("=" * 60)

if __name__ == "__main__":
    main()

