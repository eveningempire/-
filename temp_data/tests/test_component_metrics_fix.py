#!/usr/bin/env python
"""
娴嬭瘯娲昏穬鏁呴殰鍜屾渶澶ф晠闅滃垎鏁扮殑淇鏁堟灉
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge
from msfg_analysis.algorithms.msfg.component_integration import calculate_msfg_component_health
from msfg_analysis.algorithms.msfg.fusion import calculate_component_scores

def test_component_metrics_calculation():
    """娴嬭瘯閮ㄤ欢鎸囨爣璁＄畻"""
    print("馃И 娴嬭瘯娲昏穬鏁呴殰鍜屾渶澶ф晠闅滃垎鏁扮殑淇鏁堟灉")
    print("="*50)
    
    # 鑾峰彇婵€娲荤殑MSFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌婵€娲荤殑MSFG瀹氫箟")
        return
    
    print(f"鉁?浣跨敤MSFG: {active_msfg.name}")
    
    # 妯℃嫙娴嬭瘯鐐瑰垎鏁?
    test_scores = {
        "浣庨€熸鏋惰浆閫熻秴闄?: 0.8,  # 楂樺紓甯?
        "楂橀€熻浆瀛愮數娴佸紓甯?: 0.4,  # 涓瓑寮傚父
        "娓╁害杩囬珮": 0.2,         # 浣庡紓甯?
        "鐢靛帇寮傚父": 0.9,         # 楂樺紓甯?
        "鐢垫祦姝ｅ父": 0.1          # 姝ｅ父
    }
    
    # 妯℃嫙鏁呴殰鍒嗘暟
    fault_scores = {
        "妗嗘灦鏁呴殰": {"fault_probability": 0.8, "fuzzy_probability": 0.1},
        "杞瓙鏁呴殰": {"fault_probability": 0.4, "fuzzy_probability": 0.3},
        "娓╁害鏁呴殰": {"fault_probability": 0.2, "fuzzy_probability": 0.1},
        "鐢垫簮鏁呴殰": {"fault_probability": 0.9, "fuzzy_probability": 0.2},
        "閫氫俊鏁呴殰": {"fault_probability": 0.1, "fuzzy_probability": 0.05}
    }
    
    print(f"\n馃搳 妯℃嫙鏁版嵁:")
    print(f"  娴嬭瘯鐐瑰垎鏁? {test_scores}")
    print(f"  鏁呴殰鍒嗘暟: {fault_scores}")
    
    # 娴嬭瘯component_integration.py鐨勮绠?
    print(f"\n馃敡 娴嬭瘯component_integration.py璁＄畻:")
    try:
        component_health = calculate_msfg_component_health(
            test_scores=test_scores,
            msfg_definition=active_msfg,
            include_unmapped_components=True
        )
        
        print(f"  璁＄畻缁撴灉閮ㄤ欢鏁伴噺: {len(component_health)}")
        for comp_name, comp_data in list(component_health.items())[:3]:
            print(f"    {comp_name}:")
            print(f"      health_score: {comp_data.get('health_score')}")
            print(f"      active_fault_count: {comp_data.get('active_fault_count')}")
            print(f"      max_fault_score: {comp_data.get('max_fault_score')}")
            
    except Exception as e:
        print(f"  鉂?component_integration璁＄畻澶辫触: {e}")
    
    # 娴嬭瘯fusion.py鐨勮绠?
    print(f"\n馃敡 娴嬭瘯fusion.py璁＄畻:")
    try:
        nodes = list(active_msfg.nodes.all())
        edges_qs = list(active_msfg.edges.all())
        edges = [(e.source_node.node_id, e.target_node.node_id) for e in edges_qs]
        
        component_scores = calculate_component_scores(
            fault_scores=fault_scores,
            test_scores=test_scores,
            nodes=nodes,
            edges=edges,
            msfg_definition=active_msfg
        )
        
        print(f"  璁＄畻缁撴灉閮ㄤ欢鏁伴噺: {len(component_scores)}")
        for comp_name, comp_data in list(component_scores.items())[:3]:
            print(f"    {comp_name}:")
            print(f"      health_score: {comp_data.get('health_score')}")
            print(f"      active_fault_count: {comp_data.get('active_fault_count')}")
            print(f"      max_fault_score: {comp_data.get('max_fault_score')}")
            
    except Exception as e:
        print(f"  鉂?fusion璁＄畻澶辫触: {e}")
    
    # 娴嬭瘯娲昏穬鏁呴殰璁＄畻閫昏緫
    print(f"\n馃攳 娴嬭瘯娲昏穬鏁呴殰璁＄畻閫昏緫:")
    
    # 娴嬭瘯鐐瑰垎鏁伴槇鍊兼祴璇?
    test_thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
    for threshold in test_thresholds:
        active_count = sum(1 for score in test_scores.values() if score > threshold)
        print(f"  娴嬭瘯鐐瑰垎鏁?> {threshold}: {active_count} 涓椿璺冩晠闅?)
    
    # 鏁呴殰姒傜巼闃堝€兼祴璇?
    print(f"\n  鏁呴殰姒傜巼闃堝€兼祴璇?")
    for fault_name, fault_data in fault_scores.items():
        if isinstance(fault_data, dict):
            fault_prob = fault_data.get('fault_probability', 0)
            fuzzy_prob = fault_data.get('fuzzy_probability', 0)
            is_active = fault_prob > 0.3 or fuzzy_prob > 0.2
            print(f"    {fault_name}: 鏁呴殰姒傜巼={fault_prob:.2f}, 妯＄硦姒傜巼={fuzzy_prob:.2f}, 娲昏穬={is_active}")
    
    print(f"\n鉁?娴嬭瘯瀹屾垚")

if __name__ == "__main__":
    test_component_metrics_calculation()

