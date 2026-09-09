#!/usr/bin/env python
"""
璇︾粏鍒嗘瀽鏄犲皠瑕嗙洊鐜囦綆鐨勫師鍥?
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel, TestPointComponentMapping, FaultComponentMapping, MSFGNode, MSFGEdge

def debug_mapping_coverage():
    print("馃攳 璇︾粏鍒嗘瀽鏄犲皠瑕嗙洊鐜囦綆鐨勫師鍥?)
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
        
        # 鑾峰彇鎵€鏈夎妭鐐瑰拰杈?
        nodes = MSFGNode.objects.filter(msfg_definition=msfg_definition)
        edges = MSFGEdge.objects.filter(msfg_definition=msfg_definition)
        
        print(f"\n馃搳 鍥剧粨鏋勭粺璁?")
        print(f"  鎬昏妭鐐规暟: {nodes.count()}")
        print(f"  鎬昏竟鏁? {edges.count()}")
        
        # 鎸夌被鍨嬬粺璁¤妭鐐?
        node_types = {}
        for node in nodes:
            node_type = node.node_type
            if node_type not in node_types:
                node_types[node_type] = []
            node_types[node_type].append(node.name)
        
        print(f"\n馃搵 鑺傜偣绫诲瀷鍒嗗竷:")
        for node_type, names in node_types.items():
            print(f"  {node_type}: {len(names)} 涓?)
            if len(names) <= 10:
                print(f"    绀轰緥: {names}")
            else:
                print(f"    绀轰緥: {names[:5]} ... {names[-5:]}")
        
        # 鍒嗘瀽杈圭殑杩炴帴妯″紡
        print(f"\n馃敆 杈圭殑杩炴帴妯″紡鍒嗘瀽:")
        edge_patterns = {}
        for edge in edges:
            source_node = edge.source_node
            target_node = edge.target_node
            
            if source_node and target_node:
                pattern = f"{source_node.node_type} -> {target_node.node_type}"
                if pattern not in edge_patterns:
                    edge_patterns[pattern] = []
                edge_patterns[pattern].append(f"{source_node.name} -> {target_node.name}")
        
        for pattern, examples in edge_patterns.items():
            print(f"  {pattern}: {len(examples)} 鏉?)
            if len(examples) <= 5:
                print(f"    绀轰緥: {examples}")
            else:
                print(f"    绀轰緥: {examples[:3]} ... {examples[-2:]}")
        
        # 鍒嗘瀽涓轰粈涔堟槧灏勮鐩栫巼浣?
        print(f"\n馃攳 鏄犲皠瑕嗙洊鐜囧垎鏋?")
        
        # 1. 娴嬬偣-閮ㄤ欢鏄犲皠鍒嗘瀽
        test_nodes = [n for n in nodes if n.node_type == 'test']
        component_nodes = [n for n in nodes if n.node_type == 'component']
        
        print(f"  娴嬭瘯鐐规暟閲? {len(test_nodes)}")
        print(f"  閮ㄤ欢鏁伴噺: {len(component_nodes)}")
        
        # 妫€鏌ユ祴璇曠偣鏄惁鏈夊埌閮ㄤ欢鐨勮竟
        test_to_component_edges = []
        for edge in edges:
            if (edge.source_node and edge.target_node and
                edge.source_node.node_type == 'test' and 
                edge.target_node.node_type == 'component'):
                test_to_component_edges.append(edge)
        
        print(f"  娴嬭瘯鐐?>閮ㄤ欢杈? {len(test_to_component_edges)} 鏉?)
        if test_to_component_edges:
            print(f"    绀轰緥:")
            for edge in test_to_component_edges[:5]:
                print(f"      {edge.source_node.name} -> {edge.target_node.name}")
        
        # 2. 鏁呴殰-閮ㄤ欢鏄犲皠鍒嗘瀽
        fault_nodes = [n for n in nodes if n.node_type == 'fault']
        print(f"  鏁呴殰鏁伴噺: {len(fault_nodes)}")
        
        # 妫€鏌ユ晠闅滄槸鍚︽湁鍒伴儴浠剁殑杈?
        fault_to_component_edges = []
        for edge in edges:
            if (edge.source_node and edge.target_node and
                edge.source_node.node_type == 'fault' and 
                edge.target_node.node_type == 'component'):
                fault_to_component_edges.append(edge)
        
        print(f"  鏁呴殰->閮ㄤ欢杈? {len(fault_to_component_edges)} 鏉?)
        if fault_to_component_edges:
            print(f"    绀轰緥:")
            for edge in fault_to_component_edges[:5]:
                print(f"      {edge.source_node.name} -> {edge.target_node.name}")
        
        # 3. 妫€鏌ュ弽鍚戣竟锛堥儴浠?>娴嬭瘯鐐癸紝閮ㄤ欢->鏁呴殰锛?
        component_to_test_edges = []
        component_to_fault_edges = []
        
        for edge in edges:
            if (edge.source_node and edge.target_node and
                edge.source_node.node_type == 'component'):
                if edge.target_node.node_type == 'test':
                    component_to_test_edges.append(edge)
                elif edge.target_node.node_type == 'fault':
                    component_to_fault_edges.append(edge)
        
        print(f"  閮ㄤ欢->娴嬭瘯鐐硅竟: {len(component_to_test_edges)} 鏉?)
        print(f"  閮ㄤ欢->鏁呴殰杈? {len(component_to_fault_edges)} 鏉?)
        
        # 4. 鍒嗘瀽褰撳墠鏄犲皠
        current_test_component_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
        current_fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg_definition)
        
        print(f"\n馃搵 褰撳墠鏄犲皠鐘舵€?")
        print(f"  娴嬬偣-閮ㄤ欢鏄犲皠: {current_test_component_mappings.count()} 涓?)
        print(f"  鏁呴殰-閮ㄤ欢鏄犲皠: {current_fault_component_mappings.count()} 涓?)
        
        # 5. 鍒嗘瀽鏈槧灏勭殑鍘熷洜
        print(f"\n鈿狅笍 鏈槧灏勫師鍥犲垎鏋?")
        
        # 娴嬬偣鏈槧灏勫師鍥?
        mapped_tests = set(current_test_component_mappings.values_list('test_point_name', flat=True))
        unmapped_tests = [n.name for n in test_nodes if n.name not in mapped_tests]
        
        print(f"  鏈槧灏勭殑娴嬭瘯鐐? {len(unmapped_tests)} 涓?)
        if unmapped_tests:
            print(f"    鍒楄〃: {unmapped_tests}")
        
        # 鏁呴殰鏈槧灏勫師鍥?
        mapped_faults = set(current_fault_component_mappings.values_list('fault_name', flat=True))
        unmapped_faults = [n.name for n in fault_nodes if n.name not in mapped_faults]
        
        print(f"  鏈槧灏勭殑鏁呴殰: {len(unmapped_faults)} 涓?)
        if len(unmapped_faults) <= 10:
            print(f"    鍒楄〃: {unmapped_faults}")
        else:
            print(f"    鍓?0涓? {unmapped_faults[:10]}")
            print(f"    鍚?0涓? {unmapped_faults[-10:]}")
        
        # 6. 寤鸿鏀硅繘鏂规
        print(f"\n馃挕 鏀硅繘寤鸿:")
        
        if len(test_to_component_edges) == 0 and len(component_to_test_edges) > 0:
            print(f"  1. 鍥剧粨鏋勪腑鐨勮竟鏂瑰悜鏄?閮ㄤ欢->娴嬭瘯鐐癸紝闇€瑕佸弽鍚戝鐞?)
        
        if len(fault_to_component_edges) == 0 and len(component_to_fault_edges) > 0:
            print(f"  2. 鍥剧粨鏋勪腑鐨勮竟鏂瑰悜鏄?閮ㄤ欢->鏁呴殰锛岄渶瑕佸弽鍚戝鐞?)
        
        if len(test_to_component_edges) == 0 and len(component_to_test_edges) == 0:
            print(f"  3. 娴嬭瘯鐐瑰拰閮ㄤ欢涔嬮棿娌℃湁鐩存帴杩炴帴锛岄渶瑕侀€氳繃鍏朵粬鑺傜偣寤虹珛鏄犲皠")
        
        if len(fault_to_component_edges) == 0 and len(component_to_fault_edges) == 0:
            print(f"  4. 鏁呴殰鍜岄儴浠朵箣闂存病鏈夌洿鎺ヨ繛鎺ワ紝闇€瑕侀€氳繃鍏朵粬鑺傜偣寤虹珛鏄犲皠")
        
        print(f"  5. 寤鸿鎵嬪姩琛ュ厖缂哄け鐨勬槧灏勫叧绯?)
        
    except Exception as e:
        print(f"鉂?鍒嗘瀽杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬭缁嗗垎鏋愭槧灏勮鐩栫巼...")
    debug_mapping_coverage()



