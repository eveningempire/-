#!/usr/bin/env python
"""
娴嬭瘯MSFG璁＄畻閫昏緫鐨勬纭€?
楠岃瘉娴嬭瘯鐐瑰垎鏁般€佹晠闅滃垎鏁板拰閮ㄤ欢鍒嗘暟鐨勮绠楅€昏緫
"""

import os
import sys
import django
import numpy as np
from django.test import Client

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge
from msfg_analysis.algorithms.msfg.fusion import (
    fuse_test_to_fault, 
    summarize_system, 
    calculate_component_scores,
    enhanced_msfg_analysis
)
from msfg_analysis.algorithms.msfg.component_integration import (
    calculate_msfg_component_health,
    extract_components_from_msfg
)

def test_msfg_calculation_logic():
    """娴嬭瘯MSFG璁＄畻閫昏緫"""
    print("=== 娴嬭瘯MSFG璁＄畻閫昏緫 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    print("\n1. 鑾峰彇娲昏穬MSFG瀹氫箟...")
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?鎵惧埌娲昏穬MSFG: {active_msfg.name}")
    print(f"   PHM妯″瀷: {active_msfg.cmg_model.model_name}")
    print(f"   娴嬭瘯鐐规暟閲? {len(active_msfg.test_names or [])}")
    print(f"   鏁呴殰鏁伴噺: {len(active_msfg.fault_names or [])}")
    print(f"   閮ㄤ欢鏁伴噺: {len(active_msfg.component_names or [])}")
    
    # 2. 鑾峰彇MSFG鑺傜偣鍜岃竟
    print("\n2. 鑾峰彇MSFG鑺傜偣鍜岃竟...")
    nodes = MSFGNode.objects.filter(msfg_definition=active_msfg)
    edges = MSFGEdge.objects.filter(msfg_definition=active_msfg)
    
    test_nodes = [n for n in nodes if n.node_type == 'test']
    fault_nodes = [n for n in nodes if n.node_type == 'fault']
    
    print(f"   娴嬭瘯鑺傜偣鏁伴噺: {len(test_nodes)}")
    print(f"   鏁呴殰鑺傜偣鏁伴噺: {len(fault_nodes)}")
    print(f"   杈规暟閲? {len(edges)}")
    
    # 3. 鍒涘缓娴嬭瘯鏁版嵁
    print("\n3. 鍒涘缓娴嬭瘯鏁版嵁...")
    test_scores = {}
    test_name_by_id = {}
    fault_name_by_id = {}
    
    # 涓烘祴璇曠偣鍒涘缓妯℃嫙鍒嗘暟
    for i, node in enumerate(test_nodes):
        test_name = node.name
        test_scores[test_name] = round(np.random.uniform(0, 0.8), 3)  # 0-0.8鐨勯殢鏈哄垎鏁?
        test_name_by_id[node.node_id] = test_name
        print(f"   娴嬭瘯鐐?{test_name}: {test_scores[test_name]}")
    
    # 涓烘晠闅滆妭鐐瑰垱寤篒D鏄犲皠
    for node in fault_nodes:
        fault_name_by_id[node.node_id] = node.name
    
    # 鍒涘缓杈瑰垪琛?
    edge_list = [(edge.source_node.node_id, edge.target_node.node_id) for edge in edges]
    
    # 4. 娴嬭瘯鏁呴殰鍒嗘暟璁＄畻
    print("\n4. 娴嬭瘯鏁呴殰鍒嗘暟璁＄畻...")
    try:
        fault_scores = fuse_test_to_fault(test_scores, edge_list, test_name_by_id, fault_name_by_id)
        print(f"鉁?鏁呴殰鍒嗘暟璁＄畻鎴愬姛锛岃绠椾簡 {len(fault_scores)} 涓晠闅滃垎鏁?)
        
        for fault_name, score in fault_scores.items():
            print(f"   鏁呴殰 {fault_name}: {score}")
            
        # 楠岃瘉鏁呴殰鍒嗘暟閫昏緫
        print("\n   楠岃瘉鏁呴殰鍒嗘暟閫昏緫...")
        for fault_name, fault_score in fault_scores.items():
            # 鎵惧埌涓庤鏁呴殰鐩稿叧鐨勬祴璇曠偣
            related_tests = []
            for edge in edges:
                if edge.target_node.name == fault_name:
                    source_test = edge.source_node.name
                    if source_test in test_scores:
                        related_tests.append(test_scores[source_test])
            
            if related_tests:
                expected_score = max(related_tests)  # 搴旇鍙栨渶澶у€?
                if abs(fault_score - expected_score) < 0.001:
                    print(f"   鉁?鏁呴殰 {fault_name} 鍒嗘暟姝ｇ‘: {fault_score} (鏈熸湜: {expected_score})")
                else:
                    print(f"   鉂?鏁呴殰 {fault_name} 鍒嗘暟閿欒: {fault_score} (鏈熸湜: {expected_score})")
            else:
                print(f"   鈿狅笍 鏁呴殰 {fault_name} 娌℃湁鐩稿叧娴嬭瘯鐐?)
                
    except Exception as e:
        print(f"鉂?鏁呴殰鍒嗘暟璁＄畻澶辫触: {e}")
        return False
    
    # 5. 娴嬭瘯绯荤粺姒傝璁＄畻
    print("\n5. 娴嬭瘯绯荤粺姒傝璁＄畻...")
    try:
        system_summary = summarize_system(fault_scores)
        print(f"鉁?绯荤粺姒傝璁＄畻鎴愬姛")
        print(f"   鏁翠綋鍋ュ悍鍒嗘暟: {system_summary['overall_health']}")
        print(f"   鏁呴殰鏁伴噺: {system_summary['fault_count']}")
        print(f"   鍏抽敭鏁呴殰: {system_summary['critical_faults']}")
        print(f"   鏈€涓ラ噸鏁呴殰鍒嗘暟: {system_summary['worst_fault_score']}")
        print(f"   骞冲潎鏁呴殰鍒嗘暟: {system_summary['average_fault_score']}")
        
        # 楠岃瘉绯荤粺鍋ュ悍鍒嗘暟閫昏緫
        fault_values = list(fault_scores.values())
        worst_fault = max(fault_values) if fault_values else 0
        triggered_faults = [v for v in fault_values if v > 0.5]
        fault_count = len(triggered_faults)
        
        print(f"\n   楠岃瘉绯荤粺鍋ュ悍鍒嗘暟閫昏緫...")
        print(f"   鏈€涓ラ噸鏁呴殰: {worst_fault}")
        print(f"   瑙﹀彂鏁呴殰鏁伴噺: {fault_count}")
        print(f"   璁＄畻鍋ュ悍鍒嗘暟: {system_summary['overall_health']}")
        
    except Exception as e:
        print(f"鉂?绯荤粺姒傝璁＄畻澶辫触: {e}")
        return False
    
    # 6. 娴嬭瘯閮ㄤ欢鍒嗘暟璁＄畻
    print("\n6. 娴嬭瘯閮ㄤ欢鍒嗘暟璁＄畻...")
    try:
        # 浣跨敤MSFG閮ㄤ欢闆嗘垚鏂规硶
        component_health = calculate_msfg_component_health(
            test_scores=test_scores,
            msfg_definition=active_msfg,
            include_unmapped_components=True
        )
        
        print(f"鉁?閮ㄤ欢鍋ュ悍璁＄畻鎴愬姛锛岃绠椾簡 {len(component_health)} 涓儴浠?)
        
        for component_name, health_data in component_health.items():
            print(f"\n   閮ㄤ欢: {component_name}")
            print(f"     鍋ュ悍鍒嗘暟: {health_data['health_score']}")
            print(f"     鏈€澶ф祴璇曞垎鏁? {health_data['max_test_score']}")
            print(f"     骞冲潎娴嬭瘯鍒嗘暟: {health_data['avg_test_score']}")
            print(f"     娲昏穬鏁呴殰鏁伴噺: {health_data['active_fault_count']}")
            print(f"     娴嬭瘯鐐规暟閲? {health_data['test_point_count']}")
            print(f"     鏄惁鍏抽敭: {health_data['is_critical']}")
            print(f"     鏁版嵁鏉ユ簮: {health_data['source']}")
            
            # 楠岃瘉閮ㄤ欢鍋ュ悍鍒嗘暟閫昏緫
            if health_data['test_point_count'] > 0:
                test_details = health_data['test_details']
                if test_details:
                    test_scores_list = [detail['score'] for detail in test_details.values()]
                    max_score = max(test_scores_list)
                    avg_score = sum(test_scores_list) / len(test_scores_list)
                    
                    # 楠岃瘉璁＄畻鏄惁姝ｇ‘
                    if abs(health_data['max_test_score'] - max_score) < 0.001:
                        print(f"     鉁?鏈€澶ф祴璇曞垎鏁版纭? {health_data['max_test_score']}")
                    else:
                        print(f"     鉂?鏈€澶ф祴璇曞垎鏁伴敊璇? {health_data['max_test_score']} (鏈熸湜: {max_score})")
                    
                    if abs(health_data['avg_test_score'] - avg_score) < 0.001:
                        print(f"     鉁?骞冲潎娴嬭瘯鍒嗘暟姝ｇ‘: {health_data['avg_test_score']}")
                    else:
                        print(f"     鉂?骞冲潎娴嬭瘯鍒嗘暟閿欒: {health_data['avg_test_score']} (鏈熸湜: {avg_score})")
        
    except Exception as e:
        print(f"鉂?閮ㄤ欢鍋ュ悍璁＄畻澶辫触: {e}")
        return False
    
    # 7. 娴嬭瘯瀹屾暣MSFG鍒嗘瀽
    print("\n7. 娴嬭瘯瀹屾暣MSFG鍒嗘瀽...")
    try:
        full_analysis = enhanced_msfg_analysis(
            test_scores=test_scores,
            edges=edge_list,
            test_name_by_id=test_name_by_id,
            fault_name_by_id=fault_name_by_id,
            nodes=list(nodes),
            msfg_definition=active_msfg,
            include_component_analysis=True
        )
        
        print(f"鉁?瀹屾暣MSFG鍒嗘瀽鎴愬姛")
        print(f"   娴嬭瘯缁撴灉鏁伴噺: {len(full_analysis['test_results'])}")
        print(f"   鏁呴殰缁撴灉鏁伴噺: {len(full_analysis['fault_results'])}")
        print(f"   閮ㄤ欢缁撴灉鏁伴噺: {len(full_analysis['component_results'])}")
        print(f"   绯荤粺鍋ュ悍鍒嗘暟: {full_analysis['system_results']['overall_health']}")
        
        # 楠岃瘉缁撴灉涓€鑷存€?
        print(f"\n   楠岃瘉缁撴灉涓€鑷存€?..")
        if len(full_analysis['fault_results']) == len(fault_scores):
            print(f"   鉁?鏁呴殰缁撴灉鏁伴噺涓€鑷? {len(full_analysis['fault_results'])}")
        else:
            print(f"   鉂?鏁呴殰缁撴灉鏁伴噺涓嶄竴鑷? {len(full_analysis['fault_results'])} vs {len(fault_scores)}")
        
        if len(full_analysis['component_results']) == len(component_health):
            print(f"   鉁?閮ㄤ欢缁撴灉鏁伴噺涓€鑷? {len(full_analysis['component_results'])}")
        else:
            print(f"   鉂?閮ㄤ欢缁撴灉鏁伴噺涓嶄竴鑷? {len(full_analysis['component_results'])} vs {len(component_health)}")
        
    except Exception as e:
        print(f"鉂?瀹屾暣MSFG鍒嗘瀽澶辫触: {e}")
        return False
    
    # 8. 娴嬭瘯杈圭晫鎯呭喌
    print("\n8. 娴嬭瘯杈圭晫鎯呭喌...")
    
    # 娴嬭瘯绌烘暟鎹?
    try:
        empty_fault_scores = fuse_test_to_fault({}, [], {}, {})
        empty_system = summarize_system({})
        print(f"鉁?绌烘暟鎹鐞嗘甯?)
        print(f"   绌烘晠闅滃垎鏁? {empty_fault_scores}")
        print(f"   绌虹郴缁熸瑙? {empty_system}")
    except Exception as e:
        print(f"鉂?绌烘暟鎹鐞嗗け璐? {e}")
    
    # 娴嬭瘯鏋佺鍒嗘暟
    try:
        extreme_scores = {'test1': 1.0, 'test2': 0.0}
        extreme_fault_scores = fuse_test_to_fault(extreme_scores, edge_list, test_name_by_id, fault_name_by_id)
        extreme_system = summarize_system(extreme_fault_scores)
        print(f"鉁?鏋佺鍒嗘暟澶勭悊姝ｅ父")
        print(f"   鏋佺绯荤粺鍋ュ悍鍒嗘暟: {extreme_system['overall_health']}")
    except Exception as e:
        print(f"鉂?鏋佺鍒嗘暟澶勭悊澶辫触: {e}")
    
    print("\n鉁?MSFG璁＄畻閫昏緫娴嬭瘯瀹屾垚")
    return True

if __name__ == '__main__':
    test_msfg_calculation_logic()

