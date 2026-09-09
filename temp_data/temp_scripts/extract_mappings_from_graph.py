#!/usr/bin/env python
"""
浠嶮SFG鍥剧粨鏋勪腑鎻愬彇鏄犲皠鍏崇郴
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel, MSFGNode, MSFGEdge, TestPointComponentMapping, FaultComponentMapping
from django.db import transaction

def extract_mappings_from_graph():
    print("馃攳 浠嶮SFG鍥剧粨鏋勪腑鎻愬彇鏄犲皠鍏崇郴")
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
        print(f"  鑺傜偣鏁? {nodes.count()}")
        print(f"  杈规暟: {edges.count()}")
        
        # 鎸夌被鍨嬪垎缁勮妭鐐?
        test_nodes = nodes.filter(node_type='test')
        fault_nodes = nodes.filter(node_type='fault')
        component_nodes = nodes.filter(node_type='component')
        
        print(f"  娴嬭瘯鐐? {test_nodes.count()} 涓?)
        print(f"  鏁呴殰: {fault_nodes.count()} 涓?)
        print(f"  閮ㄤ欢: {component_nodes.count()} 涓?)
        
        # 鎻愬彇鏄犲皠鍏崇郴
        fault_component_mappings = []
        test_component_mappings = []
        test_fault_mappings = []
        
        print(f"\n馃敆 鍒嗘瀽杈硅繛鎺?..")
        
        for edge in edges:
            source_node = edge.source_node
            target_node = edge.target_node
            
            if not source_node or not target_node:
                continue
                
            source_type = source_node.node_type
            target_type = target_node.node_type
            
            # 1. fault -> component: 鏁呴殰-閮ㄤ欢鏄犲皠
            if source_type == 'fault' and target_type == 'component':
                fault_component_mappings.append({
                    'fault_name': source_node.name,
                    'component_name': target_node.name,
                    'weight': 1.0,
                    'description': f'浠庡浘缁撴瀯鎻愬彇: {source_node.name} -> {target_node.name}'
                })
                print(f"  鉁?鏁呴殰-閮ㄤ欢: {source_node.name} -> {target_node.name}")
            
            # 2. component -> test: 娴嬬偣-閮ㄤ欢鏄犲皠
            elif source_type == 'component' and target_type == 'test':
                test_component_mappings.append({
                    'test_point_name': target_node.name,
                    'component_name': source_node.name,
                    'weight': 1.0,
                    'description': f'浠庡浘缁撴瀯鎻愬彇: {target_node.name} -> {source_node.name}'
                })
                print(f"  鉁?娴嬬偣-閮ㄤ欢: {target_node.name} -> {source_node.name}")
            
            # 3. fault -> test: 娴嬬偣-鏁呴殰鏄犲皠
            elif source_type == 'fault' and target_type == 'test':
                test_fault_mappings.append({
                    'test_point_name': target_node.name,
                    'fault_name': source_node.name,
                    'weight': 1.0,
                    'description': f'浠庡浘缁撴瀯鎻愬彇: {target_node.name} -> {source_node.name}'
                })
                print(f"  鉁?娴嬬偣-鏁呴殰: {target_node.name} -> {source_node.name}")
        
        print(f"\n馃搳 鎻愬彇缁撴灉:")
        print(f"  鏁呴殰-閮ㄤ欢鏄犲皠: {len(fault_component_mappings)} 涓?)
        print(f"  娴嬬偣-閮ㄤ欢鏄犲皠: {len(test_component_mappings)} 涓?)
        print(f"  娴嬬偣-鏁呴殰鏄犲皠: {len(test_fault_mappings)} 涓?)
        
        # 淇濆瓨鍒版暟鎹簱
        if fault_component_mappings or test_component_mappings or test_fault_mappings:
            print(f"\n馃捑 淇濆瓨鏄犲皠鍒版暟鎹簱...")
            
            with transaction.atomic():
                # 淇濆瓨鏁呴殰-閮ㄤ欢鏄犲皠
                if fault_component_mappings:
                    for mapping in fault_component_mappings:
                        FaultComponentMapping.objects.get_or_create(
                            msfg_definition=msfg_definition,
                            fault_name=mapping['fault_name'],
                            component_name=mapping['component_name'],
                            defaults={
                                'weight': mapping['weight'],
                                'description': mapping['description']
                            }
                        )
                    print(f"  鉁?淇濆瓨浜?{len(fault_component_mappings)} 涓晠闅?閮ㄤ欢鏄犲皠")
                
                # 淇濆瓨娴嬬偣-閮ㄤ欢鏄犲皠
                if test_component_mappings:
                    for mapping in test_component_mappings:
                        TestPointComponentMapping.objects.get_or_create(
                            msfg_definition=msfg_definition,
                            test_point_name=mapping['test_point_name'],
                            component_name=mapping['component_name'],
                            defaults={
                                'weight': mapping['weight'],
                                'description': mapping['description']
                            }
                        )
                    print(f"  鉁?淇濆瓨浜?{len(test_component_mappings)} 涓祴鐐?閮ㄤ欢鏄犲皠")
                
                # 娉ㄦ剰锛氭祴鐐?鏁呴殰鏄犲皠闇€瑕佸垱寤烘柊鐨勬ā鍨嬫垨浣跨敤鐜版湁缁撴瀯
                # 杩欓噷鍏堟墦鍗板嚭鏉ワ紝渚涚敤鎴峰弬鑰?
                if test_fault_mappings:
                    print(f"  馃搵 娴嬬偣-鏁呴殰鏄犲皠锛堥渶瑕佹墜鍔ㄩ厤缃級:")
                    for mapping in test_fault_mappings:
                        print(f"    {mapping['test_point_name']} -> {mapping['fault_name']}")
        
        print(f"\n鉁?鏄犲皠鎻愬彇瀹屾垚")
        print(f"\n馃挕 寤鸿:")
        print(f"  1. 鏁呴殰-閮ㄤ欢鏄犲皠宸茶嚜鍔ㄤ繚瀛樺埌鏁版嵁搴?)
        print(f"  2. 娴嬬偣-閮ㄤ欢鏄犲皠宸茶嚜鍔ㄤ繚瀛樺埌鏁版嵁搴?)
        print(f"  3. 娴嬬偣-鏁呴殰鏄犲皠闇€瑕佸湪鍓嶇鐣岄潰鎵嬪姩閰嶇疆")
        print(f"  4. 鍙互閫氳繃鍓嶇鐣岄潰杩涗竴姝ヨ皟鏁存槧灏勬潈閲嶅拰鍏崇郴")
        
    except Exception as e:
        print(f"鉂?鎻愬彇杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫彁鍙栨槧灏勫叧绯?..")
    extract_mappings_from_graph()



