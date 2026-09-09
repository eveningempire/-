#!/usr/bin/env python
"""
娴嬭瘯鍏堣繘MSFG铻嶅悎绠楁硶
楠岃瘉鍩轰簬鑰佸钩鍙伴€昏緫鐨勭瀛﹀悎鐞嗛儴浠跺仴搴峰害鎺ㄧ悊
"""

import os
import sys
import django
import numpy as np
from django.test import Client

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

def test_advanced_msfg_fusion():
    """娴嬭瘯鍏堣繘MSFG铻嶅悎绠楁硶"""
    print("=== 娴嬭瘯鍏堣繘MSFG铻嶅悎绠楁硶 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    print("\n1. 鑾峰彇娲昏穬MSFG瀹氫箟...")
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?鎵惧埌娲昏穬MSFG: {active_msfg.name}")
    print(f"   PHM妯″瀷: {active_msfg.cmg_model.model_name}")
    
    # 2. 鑾峰彇MSFG鑺傜偣鍜岃竟
    print("\n2. 鑾峰彇MSFG鑺傜偣鍜岃竟...")
    nodes = MSFGNode.objects.filter(msfg_definition=active_msfg)
    edges = MSFGEdge.objects.filter(msfg_definition=active_msfg)
    
    test_nodes = [n for n in nodes if n.node_type == 'test']
    fault_nodes = [n for n in nodes if n.node_type == 'fault']
    
    print(f"   娴嬭瘯鑺傜偣鏁伴噺: {len(test_nodes)}")
    print(f"   鏁呴殰鑺傜偣鏁伴噺: {len(fault_nodes)}")
    print(f"   杈规暟閲? {len(edges)}")
    
    if len(test_nodes) == 0 or len(fault_nodes) == 0:
        print("鉂?缂哄皯娴嬭瘯鑺傜偣鎴栨晠闅滆妭鐐?)
        return False
    
    # 3. 鑾峰彇娴嬭瘯鐐?閮ㄤ欢鏄犲皠
    print("\n3. 鑾峰彇娴嬭瘯鐐?閮ㄤ欢鏄犲皠...")
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    print(f"   鏄犲皠鏁伴噺: {mappings.count()}")
    
    if mappings.count() == 0:
        print("鈿狅笍 娌℃湁娴嬭瘯鐐?閮ㄤ欢鏄犲皠锛屽皢鍒涘缓榛樿鏄犲皠")
        # 鍒涘缓榛樿鏄犲皠
        component_mappings = create_default_component_mappings(fault_nodes)
    else:
        # 鏋勫缓鏄犲皠瀛楀吀
        component_mappings = {}
        for mapping in mappings:
            component_name = mapping.component_name
            if component_name not in component_mappings:
                component_mappings[component_name] = []
            # 杩欓噷闇€瑕佷粠鏁呴殰鍚嶇О鎺ㄦ柇锛屾殏鏃朵娇鐢ㄩ粯璁ゆ槧灏?
            component_mappings[component_name] = [fault_node.name for fault_node in fault_nodes]
    
    print(f"   閮ㄤ欢鏁伴噺: {len(component_mappings)}")
    for component, faults in component_mappings.items():
        print(f"     {component}: {len(faults)} 涓晠闅?)
    
    # 4. 鍒涘缓娴嬭瘯鏁版嵁
    print("\n4. 鍒涘缓娴嬭瘯鏁版嵁...")
    test_scores = {}
    
    # 涓烘瘡涓祴璇曠偣鍒涘缓妯℃嫙鍒嗘暟
    for test_node in test_nodes:
        # 鍒涘缓澶氫釜鍒嗘暟鏉ユ祴璇曡瀺鍚堥€昏緫
        scores = []
        for i in range(3):  # 姣忎釜娴嬭瘯鐐?涓垎鏁?
            score = round(np.random.uniform(0, 0.8), 3)
            scores.append(score)
        test_scores[test_node.name] = scores
        print(f"   娴嬭瘯鐐?{test_node.name}: {scores}")
    
    # 5. 鍒濆鍖栧厛杩涜瀺鍚堢畻娉?
    print("\n5. 鍒濆鍖栧厛杩涜瀺鍚堢畻娉?..")
    fusion_algorithm = AdvancedMSFGFusion(eps=1e-15, n_round=5)
    
    # 6. 杩愯瀹屾暣鍒嗘瀽
    print("\n6. 杩愯瀹屾暣MSFG鍒嗘瀽...")
    try:
        analysis_result = fusion_algorithm.run_advanced_analysis(
            test_scores=test_scores,
            test_nodes=test_nodes,
            fault_nodes=fault_nodes,
            edges=edges,
            component_mappings=component_mappings
        )
        
        print("鉁?鍒嗘瀽瀹屾垚")
        
        # 7. 楠岃瘉鍒嗘瀽缁撴灉
        print("\n7. 楠岃瘉鍒嗘瀽缁撴灉...")
        
        # 楠岃瘉娴嬭瘯缁撴灉
        print(f"   娴嬭瘯缁撴灉鏁伴噺: {len(analysis_result['test_results'])}")
        for test_name, result in analysis_result['test_results'].items():
            print(f"     {test_name}: 铻嶅悎鍒嗘暟={result['score']}, 鍘熷鍒嗘暟={result['raw_scores']}")
        
        # 楠岃瘉鏁呴殰缁撴灉
        print(f"   鏁呴殰缁撴灉鏁伴噺: {len(analysis_result['fault_results'])}")
        for fault_name, result in analysis_result['fault_results'].items():
            print(f"     {fault_name}: 鏁呴殰姒傜巼={result['fault_probability']}, 妯＄硦姒傜巼={result['fuzzy_probability']}")
        
        # 楠岃瘉閮ㄤ欢缁撴灉
        print(f"   閮ㄤ欢缁撴灉鏁伴噺: {len(analysis_result['component_results'])}")
        for component_name, result in analysis_result['component_results'].items():
            print(f"     {component_name}:")
            print(f"       鍋ュ悍鍒嗘暟: {result['health_score']}")
            print(f"       鏁呴殰姒傜巼: {result['fault_probability']}")
            print(f"       妯＄硦姒傜巼: {result['fuzzy_probability']}")
            print(f"       鏁呴殰鏁伴噺: {result['fault_count']}")
            print(f"       鏈€澶ф晠闅滄鐜? {result['max_fault_prob']}")
            print(f"       骞冲潎鏁呴殰姒傜巼: {result['avg_fault_prob']}")
        
        # 楠岃瘉绯荤粺缁撴灉
        system_result = analysis_result['system_results']
        print(f"   绯荤粺鏁翠綋鍋ュ悍搴? {system_result['overall_health']}")
        print(f"   閮ㄤ欢鏁伴噺: {system_result['component_count']}")
        print(f"   鍏抽敭閮ㄤ欢: {system_result['critical_components']}")
        print(f"   鏈€宸儴浠? {system_result['worst_component']}")
        print(f"   鍋ュ悍搴﹀垎甯? {system_result['health_distribution']}")
        print(f"   鏈€灏忓仴搴峰害: {system_result['min_health']}")
        print(f"   鏈€澶у仴搴峰害: {system_result['max_health']}")
        print(f"   骞冲潎鍋ュ悍搴? {system_result['avg_health']}")
        
        # 楠岃瘉鍏冩暟鎹?
        metadata = analysis_result['analysis_metadata']
        print(f"   D鐭╅樀褰㈢姸: {metadata['d_matrix_shape']}")
        print(f"   绠楁硶鐗堟湰: {metadata['algorithm_version']}")
        
        # 8. 楠岃瘉璁＄畻閫昏緫鐨勫悎鐞嗘€?
        print("\n8. 楠岃瘉璁＄畻閫昏緫鐨勫悎鐞嗘€?..")
        
        # 楠岃瘉鍋ュ悍鍒嗘暟鑼冨洿
        all_health_scores = [result['health_score'] for result in analysis_result['component_results'].values()]
        if all(0 <= score <= 1 for score in all_health_scores):
            print("   鉁?鍋ュ悍鍒嗘暟閮藉湪鍚堢悊鑼冨洿鍐?[0, 1]")
        else:
            print("   鉂?鍋ュ悍鍒嗘暟瓒呭嚭鍚堢悊鑼冨洿")
        
        # 楠岃瘉鏁呴殰姒傜巼涓庡仴搴峰垎鏁扮殑鍏崇郴
        for component_name, result in analysis_result['component_results'].items():
            expected_health = 1.0 - result['fault_probability']
            if abs(result['health_score'] - expected_health) < 0.001:
                print(f"   鉁?{component_name} 鍋ュ悍鍒嗘暟璁＄畻姝ｇ‘")
            else:
                print(f"   鉂?{component_name} 鍋ュ悍鍒嗘暟璁＄畻閿欒")
        
        # 楠岃瘉绯荤粺鍋ュ悍搴︾殑鍔犳潈骞冲潎
        if system_result['component_count'] > 0:
            avg_health = system_result['avg_health']
            if abs(system_result['overall_health'] - avg_health) < 0.1:  # 鍏佽涓€瀹氳宸?
                print("   鉁?绯荤粺鍋ュ悍搴﹁绠楀悎鐞?)
            else:
                print("   鈿狅笍 绯荤粺鍋ュ悍搴﹀彲鑳介渶瑕佽皟鏁存潈閲?)
        
        print("\n鉁?鍏堣繘MSFG铻嶅悎绠楁硶娴嬭瘯瀹屾垚")
        return True
        
    except Exception as e:
        print(f"鉂?鍒嗘瀽澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_default_component_mappings(fault_nodes):
    """鍒涘缓榛樿鐨勯儴浠舵槧灏?""
    component_mappings = {
        '杞瓙杞存壙': [],
        '杞瓙椹卞姩鐢垫満': [],
        '鐢垫簮鏉?: [],
        '妗嗘灦鎺у埗鍣?: [],
        '杞瓙鐢垫祦閲囨牱': []
    }
    
    # 鏍规嵁鏁呴殰鍚嶇О杩涜鏅鸿兘鏄犲皠
    for fault_node in fault_nodes:
        fault_name = fault_node.name.lower()
        
        if '杞存壙' in fault_name or '杞存俯' in fault_name:
            component_mappings['杞瓙杞存壙'].append(fault_node.name)
        elif '鐢垫満' in fault_name or '杞€? in fault_name:
            component_mappings['杞瓙椹卞姩鐢垫満'].append(fault_node.name)
        elif '鐢靛帇' in fault_name or 'v' in fault_name:
            component_mappings['鐢垫簮鏉?].append(fault_node.name)
        elif '妗嗘灦' in fault_name or '澹虫俯' in fault_name:
            component_mappings['妗嗘灦鎺у埗鍣?].append(fault_node.name)
        elif '鐢垫祦' in fault_name:
            component_mappings['杞瓙鐢垫祦閲囨牱'].append(fault_node.name)
        else:
            # 榛樿鏄犲皠鍒拌浆瀛愯酱鎵?
            component_mappings['杞瓙杞存壙'].append(fault_node.name)
    
    # 绉婚櫎绌虹殑閮ㄤ欢
    component_mappings = {k: v for k, v in component_mappings.items() if v}
    
    return component_mappings

if __name__ == '__main__':
    test_advanced_msfg_fusion()

