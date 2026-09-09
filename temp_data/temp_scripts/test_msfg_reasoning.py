#!/usr/bin/env python
"""
娴嬭瘯MSFG鎺ㄧ悊閫昏緫
楠岃瘉娴嬬偣-閮ㄤ欢鍜屾晠闅?閮ㄤ欢鏄犲皠鏄惁姝ｇ‘宸ヤ綔
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

def test_msfg_reasoning():
    """娴嬭瘯MSFG鎺ㄧ悊閫昏緫"""
    print("馃殌 寮€濮嬫祴璇昅SFG鎺ㄧ悊閫昏緫")
    print("=" * 60)
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG
    try:
        cmg_model = PHMModel.objects.filter(is_active=True).first()
        if not cmg_model:
            print("鉂?娌℃湁鎵惧埌娲昏穬鐨凜MG妯″瀷")
            return False
            
        print(f"馃搵 浣跨敤PHM妯″瀷: {cmg_model.model_name}")
        
        msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
        if not msfg:
            print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
            return False
            
        print(f"鉁?鎵惧埌娲昏穬MSFG: {msfg.name} (ID: {msfg.id})")
        
    except Exception as e:
        print(f"鉂?鑾峰彇MSFG澶辫触: {e}")
        return False
    
    # 2. 妫€鏌ユ槧灏勫叧绯?    print("\n馃攳 妫€鏌ユ槧灏勫叧绯?")
    print("-" * 40)
    
    # 妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠
    test_component_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg)
    print(f"馃搳 娴嬭瘯鐐?閮ㄤ欢鏄犲皠: {test_component_mappings.count()} 涓?)
    
    if test_component_mappings.exists():
        print("   鏄犲皠璇︽儏:")
        for mapping in test_component_mappings[:5]:  # 鏄剧ず鍓?涓?            print(f"   - {mapping.test_point_name} -> {mapping.component_name}")
        if test_component_mappings.count() > 5:
            print(f"   ... 杩樻湁 {test_component_mappings.count() - 5} 涓?)
    else:
        print("   鈿狅笍  娌℃湁娴嬭瘯鐐?閮ㄤ欢鏄犲皠")
    
    # 妫€鏌ユ晠闅?閮ㄤ欢鏄犲皠
    fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg)
    print(f"馃搳 鏁呴殰-閮ㄤ欢鏄犲皠: {fault_component_mappings.count()} 涓?)
    
    if fault_component_mappings.exists():
        print("   鏄犲皠璇︽儏:")
        for mapping in fault_component_mappings[:5]:  # 鏄剧ず鍓?涓?            print(f"   - {mapping.fault_name} -> {mapping.component_name}")
        if fault_component_mappings.count() > 5:
            print(f"   ... 杩樻湁 {fault_component_mappings.count() - 5} 涓?)
    else:
        print("   鈿狅笍  娌℃湁鏁呴殰-閮ㄤ欢鏄犲皠")
    
    # 3. 鑾峰彇MSFG缁撴瀯
    print("\n馃彈锔?鑾峰彇MSFG缁撴瀯:")
    print("-" * 40)
    
    nodes = list(msfg.nodes.all())
    edges = list(msfg.edges.all())
    
    test_nodes = [n for n in nodes if n.node_type == 'test']
    fault_nodes = [n for n in nodes if n.node_type == 'fault']
    component_nodes = [n for n in nodes if n.node_type == 'component']
    
    print(f"馃搳 鑺傜偣缁熻:")
    print(f"   - 娴嬭瘯鐐? {len(test_nodes)} 涓?)
    print(f"   - 鏁呴殰: {len(fault_nodes)} 涓?)
    print(f"   - 閮ㄤ欢: {len(component_nodes)} 涓?)
    print(f"   - 杈? {len(edges)} 鏉?)
    
    # 4. 鍒涘缓娴嬭瘯鏁版嵁
    print("\n馃И 鍒涘缓娴嬭瘯鏁版嵁:")
    print("-" * 40)
    
    # 妯℃嫙涓€浜涙祴璇曠偣鍒嗘暟
    test_scores = {}
    for test_node in test_nodes[:5]:  # 浣跨敤鍓?涓祴璇曠偣
        import random
        test_scores[test_node.name] = random.uniform(0.1, 0.9)
    
    print(f"馃搳 娴嬭瘯鐐瑰垎鏁?(鍓?涓?:")
    for test_name, score in test_scores.items():
        print(f"   - {test_name}: {score:.3f}")
    
    # 5. 杩愯鎺ㄧ悊
    print("\n馃敩 杩愯MSFG鎺ㄧ悊:")
    print("-" * 40)
    
    try:
        # 鍑嗗鎺ㄧ悊鏁版嵁
        test_name_by_id = {n.node_id: n.name for n in test_nodes}
        fault_name_by_id = {n.node_id: n.name for n in fault_nodes}
        edge_list = [(e.source_node.node_id, e.target_node.node_id) for e in edges]
        
        # 杩愯澧炲己鐨凪SFG鍒嗘瀽
        analysis_result = enhanced_msfg_analysis(
            test_scores=test_scores,
            edges=edge_list,
            test_name_by_id=test_name_by_id,
            fault_name_by_id=fault_name_by_id,
            nodes=nodes,
            msfg_definition=msfg,
            include_component_analysis=True
        )
        
        print("鉁?MSFG鎺ㄧ悊鎴愬姛!")
        
        # 6. 鍒嗘瀽缁撴灉
        print("\n馃搱 鎺ㄧ悊缁撴灉鍒嗘瀽:")
        print("-" * 40)
        
        # 鏁呴殰缁撴灉
        fault_results = analysis_result.get('fault_results', {})
        print(f"馃搳 鏁呴殰鍒嗘瀽缁撴灉: {len(fault_results)} 涓晠闅?)
        if fault_results:
            print("   鏁呴殰鍒嗘暟 (鍓?涓?:")
            for i, (fault_name, score) in enumerate(list(fault_results.items())[:5]):
                print(f"   - {fault_name}: {score:.3f}")
        
        # 閮ㄤ欢缁撴灉
        component_results = analysis_result.get('component_results', {})
        print(f"馃搳 閮ㄤ欢鍒嗘瀽缁撴灉: {len(component_results)} 涓儴浠?)
        if component_results:
            print("   閮ㄤ欢鍋ュ悍搴?(鍓?涓?:")
            for i, (comp_name, comp_data) in enumerate(list(component_results.items())[:5]):
                health_score = comp_data.get('health_score', 0)
                print(f"   - {comp_name}: {health_score:.3f}")
        
        # 绯荤粺缁撴灉
        system_results = analysis_result.get('system_results', {})
        print(f"馃搳 绯荤粺鍒嗘瀽缁撴灉:")
        overall_health = system_results.get('overall_health', 0)
        print(f"   - 鏁翠綋鍋ュ悍搴? {overall_health:.3f}")
        
        # 7. 楠岃瘉鎺ㄧ悊閫昏緫
        print("\n鉁?鎺ㄧ悊閫昏緫楠岃瘉:")
        print("-" * 40)
        
        # 妫€鏌ユ槸鍚︽湁閮ㄤ欢绾у埆鐨勫垎鏋?        if component_results:
            print("鉁?閮ㄤ欢绾у埆鍒嗘瀽姝ｅ父")
            
            # 妫€鏌ュ仴搴峰害鑼冨洿
            valid_health_scores = True
            for comp_name, comp_data in component_results.items():
                health_score = comp_data.get('health_score', 0)
                if not (0 <= health_score <= 1):
                    valid_health_scores = False
                    print(f"   鈿狅笍  閮ㄤ欢 {comp_name} 鍋ュ悍搴﹁秴鍑鸿寖鍥? {health_score}")
            
            if valid_health_scores:
                print("鉁?鍋ュ悍搴﹁寖鍥撮獙璇侀€氳繃 (0-1)")
            
            # 妫€鏌ヨ瀺鍚堟潈閲?            has_fusion_weights = False
            for comp_name, comp_data in component_results.items():
                if 'fusion_weights' in comp_data:
                    has_fusion_weights = True
                    weights = comp_data['fusion_weights']
                    print(f"   - {comp_name} 铻嶅悎鏉冮噸: 鏁呴殰={weights.get('fault', 0):.3f}, 娴嬭瘯={weights.get('test', 0):.3f}")
            
            if has_fusion_weights:
                print("鉁?铻嶅悎鏉冮噸璁＄畻姝ｅ父")
        
        # 妫€鏌ユ晠闅滄帹鐞?        if fault_results:
            print("鉁?鏁呴殰鎺ㄧ悊姝ｅ父")
            
            # 妫€鏌ユ晠闅滃垎鏁拌寖鍥?            valid_fault_scores = True
            for fault_name, score in fault_results.items():
                if not (0 <= score <= 1):
                    valid_fault_scores = False
                    print(f"   鈿狅笍  鏁呴殰 {fault_name} 鍒嗘暟瓒呭嚭鑼冨洿: {score}")
            
            if valid_fault_scores:
                print("鉁?鏁呴殰鍒嗘暟鑼冨洿楠岃瘉閫氳繃 (0-1)")
        
        # 妫€鏌ョ郴缁熷仴搴峰害
        if 0 <= overall_health <= 1:
            print("鉁?绯荤粺鍋ュ悍搴﹁寖鍥撮獙璇侀€氳繃 (0-1)")
        else:
            print(f"鈿狅笍  绯荤粺鍋ュ悍搴﹁秴鍑鸿寖鍥? {overall_health}")
        
        print("\n馃帀 MSFG鎺ㄧ悊閫昏緫娴嬭瘯瀹屾垚!")
        return True
        
    except Exception as e:
        print(f"鉂?MSFG鎺ㄧ悊澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mapping_consistency():
    """娴嬭瘯鏄犲皠涓€鑷存€?""
    print("\n馃攳 娴嬭瘯鏄犲皠涓€鑷存€?")
    print("-" * 40)
    
    try:
        cmg_model = PHMModel.objects.filter(is_active=True).first()
        msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
        
        if not msfg:
            print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG")
            return False
        
        # 鑾峰彇鎵€鏈夋槧灏?        test_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg)
        fault_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg)
        
        # 妫€鏌ユ槧灏勭殑閮ㄤ欢鏄惁涓€鑷?        test_components = set(mapping.component_name for mapping in test_mappings)
        fault_components = set(mapping.component_name for mapping in fault_mappings)
        
        print(f"馃搳 鏄犲皠涓€鑷存€ф鏌?")
        print(f"   - 娴嬭瘯鐐规槧灏勬秹鍙婄殑閮ㄤ欢: {len(test_components)} 涓?)
        print(f"   - 鏁呴殰鏄犲皠娑夊強鐨勯儴浠? {len(fault_components)} 涓?)
        
        # 妫€鏌ラ噸鍙?        overlap = test_components & fault_components
        print(f"   - 閲嶅彔閮ㄤ欢: {len(overlap)} 涓?)
        
        if overlap:
            print("   鉁?瀛樺湪閲嶅彔閮ㄤ欢锛屾槧灏勪竴鑷存€ц壇濂?)
        else:
            print("   鈿狅笍  娌℃湁閲嶅彔閮ㄤ欢锛屽彲鑳介渶瑕佹鏌ユ槧灏?)
        
        # 妫€鏌ヨ鐩栫巼
        all_components = test_components | fault_components
        print(f"   - 鎬婚儴浠舵暟: {len(all_components)} 涓?)
        
        return True
        
    except Exception as e:
        print(f"鉂?鏄犲皠涓€鑷存€ф祴璇曞け璐? {e}")
        return False

if __name__ == "__main__":
    print("馃殌 寮€濮婱SFG鎺ㄧ悊閫昏緫娴嬭瘯")
    print("=" * 60)
    
    # 杩愯娴嬭瘯
    success1 = test_msfg_reasoning()
    success2 = test_mapping_consistency()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("馃帀 鎵€鏈夋祴璇曢€氳繃! MSFG鎺ㄧ悊閫昏緫宸ヤ綔姝ｅ父")
    else:
        print("鉂?閮ㄥ垎娴嬭瘯澶辫触锛岃妫€鏌ラ厤缃?)
    
    print("=" * 60)

