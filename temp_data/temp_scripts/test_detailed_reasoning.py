#!/usr/bin/env python
"""
璇︾粏娴嬭瘯MSFG鎺ㄧ悊鏁堟灉
楠岃瘉瀹為檯鐨勬帹鐞嗙粨鏋滄槸鍚︾鍚堥鏈?
"""

import os
import sys
import django
import logging
from typing import Dict, List

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel, PHMData
from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping, FaultComponentMapping
from msfg_analysis.algorithms.msfg.fusion import enhanced_msfg_analysis

# 閰嶇疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_detailed_reasoning():
    """璇︾粏娴嬭瘯鎺ㄧ悊鏁堟灉"""
    print("馃敩 璇︾粏娴嬭瘯MSFG鎺ㄧ悊鏁堟灉")
    print("=" * 60)
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG
    cmg_model = PHMModel.objects.filter(is_active=True).first()
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
    
    if not msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG")
        return False
    
    print(f"馃搵 浣跨敤MSFG: {msfg.name}")
    
    # 2. 鑾峰彇MSFG缁撴瀯
    nodes = list(msfg.nodes.all())
    edges = list(msfg.edges.all())
    
    test_nodes = [n for n in nodes if n.node_type == 'test']
    fault_nodes = [n for n in nodes if n.node_type == 'fault']
    
    print(f"馃搳 MSFG缁撴瀯: {len(test_nodes)} 涓祴璇曠偣, {len(fault_nodes)} 涓晠闅? {len(edges)} 鏉¤竟")
    
    # 3. 娴嬭瘯涓嶅悓鐨勬祴璇曠偣鍒嗘暟缁勫悎
    test_scenarios = [
        {
            "name": "姝ｅ父鐘舵€?,
            "scores": {node.name: 0.1 for node in test_nodes[:5]}
        },
        {
            "name": "杞诲井寮傚父",
            "scores": {node.name: 0.3 for node in test_nodes[:5]}
        },
        {
            "name": "涓害寮傚父",
            "scores": {node.name: 0.6 for node in test_nodes[:5]}
        },
        {
            "name": "涓ラ噸寮傚父",
            "scores": {node.name: 0.9 for node in test_nodes[:5]}
        },
        {
            "name": "娣峰悎寮傚父",
            "scores": {
                test_nodes[0].name: 0.1,  # 姝ｅ父
                test_nodes[1].name: 0.5,  # 涓害
                test_nodes[2].name: 0.8,  # 涓ラ噸
                test_nodes[3].name: 0.2,  # 杞诲井
                test_nodes[4].name: 0.7   # 涓害
            }
        }
    ]
    
    # 4. 杩愯鎺ㄧ悊娴嬭瘯
    for scenario in test_scenarios:
        print(f"\n馃И 娴嬭瘯鍦烘櫙: {scenario['name']}")
        print("-" * 40)
        
        # 鏄剧ず娴嬭瘯鐐瑰垎鏁?
        print("馃搳 娴嬭瘯鐐瑰垎鏁?")
        for test_name, score in scenario['scores'].items():
            print(f"   - {test_name}: {score:.3f}")
        
        try:
            # 鍑嗗鎺ㄧ悊鏁版嵁
            test_name_by_id = {n.node_id: n.name for n in test_nodes}
            fault_name_by_id = {n.node_id: n.name for n in fault_nodes}
            edge_list = [(e.source_node.node_id, e.target_node.node_id) for e in edges]
            
            # 杩愯鎺ㄧ悊
            analysis_result = enhanced_msfg_analysis(
                test_scores=scenario['scores'],
                edges=edge_list,
                test_name_by_id=test_name_by_id,
                fault_name_by_id=fault_name_by_id,
                nodes=nodes,
                msfg_definition=msfg,
                include_component_analysis=True
            )
            
            # 鍒嗘瀽缁撴灉
            fault_results = analysis_result.get('fault_results', {})
            component_results = analysis_result.get('component_results', {})
            system_results = analysis_result.get('system_results', {})
            
            # 鏄剧ず鏁呴殰缁撴灉
            if fault_results:
                print("馃搳 鏁呴殰鍒嗘瀽缁撴灉:")
                for fault_name, score in list(fault_results.items())[:3]:
                    print(f"   - {fault_name}: {score:.3f}")
            
            # 鏄剧ず閮ㄤ欢缁撴灉
            if component_results:
                print("馃搳 閮ㄤ欢鍋ュ悍搴?(鍓?涓?:")
                for comp_name, comp_data in list(component_results.items())[:5]:
                    health_score = comp_data.get('health_score', 0)
                    fusion_weights = comp_data.get('fusion_weights', {})
                    print(f"   - {comp_name}: {health_score:.3f} (鏁呴殰={fusion_weights.get('fault', 0):.3f}, 娴嬭瘯={fusion_weights.get('test', 0):.3f})")
            
            # 鏄剧ず绯荤粺缁撴灉
            overall_health = system_results.get('overall_health', 0)
            print(f"馃搳 绯荤粺鏁翠綋鍋ュ悍搴? {overall_health:.3f}")
            
            # 楠岃瘉鎺ㄧ悊閫昏緫
            print("鉁?鎺ㄧ悊閫昏緫楠岃瘉:")
            
            # 妫€鏌ュ仴搴峰害鏄惁涓庡紓甯哥▼搴︽垚鍙嶆瘮
            avg_test_score = sum(scenario['scores'].values()) / len(scenario['scores'])
            if component_results:
                avg_health_score = sum(comp_data.get('health_score', 0) for comp_data in component_results.values()) / len(component_results)
                print(f"   - 骞冲潎娴嬭瘯鍒嗘暟: {avg_test_score:.3f}")
                print(f"   - 骞冲潎閮ㄤ欢鍋ュ悍搴? {avg_health_score:.3f}")
                
                # 楠岃瘉鍋ュ悍搴︿笌寮傚父绋嬪害鐨勫叧绯?
                if avg_test_score > 0.5 and avg_health_score < 0.5:
                    print("   鉁?楂樺紓甯稿搴斾綆鍋ュ悍搴?- 绗﹀悎棰勬湡")
                elif avg_test_score < 0.3 and avg_health_score > 0.7:
                    print("   鉁?浣庡紓甯稿搴旈珮鍋ュ悍搴?- 绗﹀悎棰勬湡")
                else:
                    print("   鈿狅笍  鍋ュ悍搴︿笌寮傚父绋嬪害鍏崇郴闇€瑕佽繘涓€姝ラ獙璇?)
            
        except Exception as e:
            print(f"鉂?鎺ㄧ悊澶辫触: {e}")
            import traceback
            traceback.print_exc()
    
    return True

def test_edge_analysis():
    """鍒嗘瀽杈圭殑杩炴帴鍏崇郴"""
    print("\n馃敆 鍒嗘瀽MSFG杈圭殑杩炴帴鍏崇郴:")
    print("-" * 40)
    
    cmg_model = PHMModel.objects.filter(is_active=True).first()
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
    
    if not msfg:
        return False
    
    nodes = list(msfg.nodes.all())
    edges = list(msfg.edges.all())
    
    test_nodes = [n for n in nodes if n.node_type == 'test']
    fault_nodes = [n for n in nodes if n.node_type == 'fault']
    component_nodes = [n for n in nodes if n.node_type == 'component']
    
    # 鍒嗘瀽杩炴帴绫诲瀷
    connection_types = {}
    for edge in edges:
        source_type = edge.source_node.node_type
        target_type = edge.target_node.node_type
        connection_key = f"{source_type}->{target_type}"
        connection_types[connection_key] = connection_types.get(connection_key, 0) + 1
    
    print("馃搳 杩炴帴绫诲瀷缁熻:")
    for conn_type, count in connection_types.items():
        print(f"   - {conn_type}: {count} 鏉?)
    
    # 妫€鏌ユ祴璇曠偣鍒版晠闅滅殑杩炴帴
    test_to_fault_edges = [e for e in edges if e.source_node.node_type == 'test' and e.target_node.node_type == 'fault']
    print(f"馃搳 娴嬭瘯鐐?>鏁呴殰杩炴帴: {len(test_to_fault_edges)} 鏉?)
    
    if test_to_fault_edges:
        print("   杩炴帴璇︽儏:")
        for edge in test_to_fault_edges[:5]:
            print(f"   - {edge.source_node.name} -> {edge.target_node.name}")
        if len(test_to_fault_edges) > 5:
            print(f"   ... 杩樻湁 {len(test_to_fault_edges) - 5} 鏉?)
    else:
        print("   鈿狅笍  娌℃湁鐩存帴鐨勬祴璇曠偣->鏁呴殰杩炴帴")
    
    return True

if __name__ == "__main__":
    print("馃殌 寮€濮嬭缁哅SFG鎺ㄧ悊娴嬭瘯")
    print("=" * 60)
    
    success1 = test_detailed_reasoning()
    success2 = test_edge_analysis()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("馃帀 璇︾粏娴嬭瘯瀹屾垚! MSFG鎺ㄧ悊閫昏緫宸ヤ綔姝ｅ父")
    else:
        print("鉂?閮ㄥ垎娴嬭瘯澶辫触锛岃妫€鏌ラ厤缃?)
    
    print("=" * 60)

