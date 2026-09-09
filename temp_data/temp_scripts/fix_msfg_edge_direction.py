#!/usr/bin/env python
"""
淇MSFG杈圭殑鏂瑰悜闂
灏嗛敊璇殑 component -> test 鏂瑰悜淇涓烘纭殑 test -> component -> fault 鏂瑰悜
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel, MSFGNode, MSFGEdge
from django.db import transaction

def fix_msfg_edge_direction():
    print("馃敡 淇MSFG杈圭殑鏂瑰悜闂")
    print("=" * 60)
    
    try:
        # 鑾峰彇鏈€鏂扮殑MSFG瀹氫箟
        cmg_model = PHMModel.objects.filter(is_active=True).first()
        if not cmg_model:
            print("鉂?娌℃湁鎵惧埌婵€娲荤殑PHM妯″瀷")
            return
            
        msfg_definition = MSFGDefinition.objects.filter(cmg_model=cmg_model).order_by('-created_at').first()
        if not msfg_definition:
            print("鉂?娌℃湁鎵惧埌MSFG瀹氫箟")
            return
            
        print(f"馃搵 妫€鏌SFG: {msfg_definition}")
        
        # 鑾峰彇鎵€鏈夎妭鐐瑰拰杈?        nodes = MSFGNode.objects.filter(msfg_definition=msfg_definition)
        edges = MSFGEdge.objects.filter(msfg_definition=msfg_definition)
        
        print(f"\n馃搳 淇鍓嶇粺璁?")
        print(f"  鑺傜偣鏁? {nodes.count()}")
        print(f"  杈规暟: {edges.count()}")
        
        # 鍒嗘瀽褰撳墠杈圭殑鏂瑰悜
        edge_directions = {}
        for edge in edges:
            source_type = edge.source_node.node_type if edge.source_node else 'unknown'
            target_type = edge.target_node.node_type if edge.target_node else 'unknown'
            pattern = f"{source_type} -> {target_type}"
            
            if pattern not in edge_directions:
                edge_directions[pattern] = []
            edge_directions[pattern].append(edge)
        
        print(f"\n馃敆 褰撳墠杈规柟鍚?")
        for pattern, edge_list in edge_directions.items():
            print(f"  {pattern}: {len(edge_list)} 鏉?)
        
        # 妫€鏌ユ槸鍚﹂渶瑕佷慨澶?        needs_fix = False
        for pattern in edge_directions.keys():
            if 'component -> test' in pattern:
                needs_fix = True
                break
        
        if not needs_fix:
            print(f"\n鉁?杈规柟鍚戞纭紝鏃犻渶淇")
            return
        
        print(f"\n馃敡 寮€濮嬩慨澶嶈竟鏂瑰悜...")
        
        with transaction.atomic():
            # 鍒犻櫎鎵€鏈夌幇鏈夌殑杈?            edges.delete()
            print(f"  馃棏锔?鍒犻櫎浜?{edges.count()} 鏉¤竟")
            
            # 閲嶆柊鍒涘缓姝ｇ‘鐨勮竟
            new_edges = []
            
            # 鑾峰彇鎵€鏈夎妭鐐?            test_nodes = nodes.filter(node_type='test')
            component_nodes = nodes.filter(node_type='component')
            fault_nodes = nodes.filter(node_type='fault')
            
            print(f"  馃搳 鑺傜偣缁熻:")
            print(f"    娴嬭瘯鐐? {test_nodes.count()} 涓?)
            print(f"    閮ㄤ欢: {component_nodes.count()} 涓?)
            print(f"    鏁呴殰: {fault_nodes.count()} 涓?)
            
            # 涓烘瘡涓祴璇曠偣鍒涘缓鍒伴儴浠剁殑杩炴帴
            for test_node in test_nodes:
                for component_node in component_nodes:
                    # 鍒涘缓娴嬭瘯鐐?-> 閮ㄤ欢鐨勮竟
                    edge = MSFGEdge(
                        msfg_definition=msfg_definition,
                        edge_id=f"edge_{test_node.id}_{component_node.id}",
                        source_node=test_node,
                        target_node=component_node,
                        edge_type='polyline',
                        properties={}
                    )
                    new_edges.append(edge)
            
            # 涓烘瘡涓儴浠跺垱寤哄埌鏁呴殰鐨勮繛鎺ワ紙濡傛灉鏈夋晠闅滆妭鐐癸級
            if fault_nodes.exists():
                for component_node in component_nodes:
                    for fault_node in fault_nodes:
                        # 鍒涘缓閮ㄤ欢 -> 鏁呴殰鐨勮竟
                        edge = MSFGEdge(
                            msfg_definition=msfg_definition,
                            edge_id=f"edge_{component_node.id}_{fault_node.id}",
                            source_node=component_node,
                            target_node=fault_node,
                            edge_type='polyline',
                            properties={}
                        )
                        new_edges.append(edge)
            
            # 鎵归噺鍒涘缓杈?            if new_edges:
                MSFGEdge.objects.bulk_create(new_edges)
                print(f"  鉁?鍒涘缓浜?{len(new_edges)} 鏉℃柊杈?)
            else:
                print(f"  鈿狅笍 娌℃湁鍒涘缓浠讳綍鏂拌竟")
            
            # 楠岃瘉淇缁撴灉
            new_edges = MSFGEdge.objects.filter(msfg_definition=msfg_definition)
            print(f"\n馃搳 淇鍚庣粺璁?")
            print(f"  杈规暟: {new_edges.count()}")
            
            # 鍒嗘瀽鏂扮殑杈规柟鍚?            new_edge_directions = {}
            for edge in new_edges:
                source_type = edge.source_node.node_type if edge.source_node else 'unknown'
                target_type = edge.target_node.node_type if edge.target_node else 'unknown'
                pattern = f"{source_type} -> {target_type}"
                
                if pattern not in new_edge_directions:
                    new_edge_directions[pattern] = []
                new_edge_directions[pattern].append(edge)
            
            print(f"\n馃敆 淇鍚庤竟鏂瑰悜:")
            for pattern, edge_list in new_edge_directions.items():
                print(f"  {pattern}: {len(edge_list)} 鏉?)
        
        print(f"\n鉁?杈规柟鍚戜慨澶嶅畬鎴?)
        
    except Exception as e:
        print(f"鉂?淇杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬩慨澶嶈竟鏂瑰悜...")
    fix_msfg_edge_direction()

