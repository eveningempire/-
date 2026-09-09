#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
娴嬭瘯鏁呴殰-缁勪欢鏄犲皠鐨勬晥鏋?
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.algorithms.msfg.fusion import calculate_component_scores, extract_component_from_fault_name
from msfg_analysis.models import MSFGDefinition

def test_fault_component_mapping():
    """娴嬭瘯鏁呴殰-缁勪欢鏄犲皠"""
    print("馃И 娴嬭瘯鏁呴殰-缁勪欢鏄犲皠鏁堟灉")
    print("=" * 50)
    
    # 妯℃嫙鏁呴殰鍒嗘暟鏁版嵁
    fault_scores = {
        '妗嗘灦鏁呴殰': 0.8,
        '杞瓙鏁呴殰': 0.4,
        '娓╁害鏁呴殰': 0.2,
        '鐢垫簮鏁呴殰': 0.9,
        '閫氫俊鏁呴殰': 0.1,
        '鐢垫満鏁呴殰': 0.7,
        '杞存壙鏁呴殰': 0.3,
        '浼犳劅鍣ㄦ晠闅?: 0.6
    }
    
    # 妯℃嫙娴嬭瘯鐐瑰垎鏁?
    test_scores = {
        '浣庨€熸鏋惰浆閫熻秴闄?: 0.8,
        '楂橀€熻浆瀛愮數娴佸紓甯?: 0.4,
        '娓╁害杩囬珮': 0.2,
        '鐢靛帇寮傚父': 0.9,
        '鐢垫祦姝ｅ父': 0.1
    }
    
    # 妯℃嫙MSFG鑺傜偣锛堝寘鍚晠闅滆妭鐐癸級
    class MockNode:
        def __init__(self, name, node_type, properties=None):
            self.name = name
            self.node_type = node_type
            self.properties = properties or {}
    
    # 鍒涘缓鏁呴殰鑺傜偣锛屽寘鍚粍浠朵俊鎭?
    fault_nodes = [
        MockNode('妗嗘灦鏁呴殰', 'fault', {'component': '妗嗘灦鎺у埗鍣?}),
        MockNode('杞瓙鏁呴殰', 'fault', {'component': '杞瓙椹卞姩鐢垫満'}),
        MockNode('娓╁害鏁呴殰', 'fault', {'component': '娓╁害鐩戞帶绯荤粺'}),
        MockNode('鐢垫簮鏁呴殰', 'fault', {'component': '鐢垫簮绠＄悊绯荤粺'}),
        MockNode('閫氫俊鏁呴殰', 'fault', {'component': '1553B鎺ュ彛'}),
        MockNode('鐢垫満鏁呴殰', 'fault', {'component': '杞瓙椹卞姩鐢垫満'}),
        MockNode('杞存壙鏁呴殰', 'fault', {'component': '杞存壙绯荤粺'}),
        MockNode('浼犳劅鍣ㄦ晠闅?, 'fault', {'component': '浼犳劅鍣ㄧ郴缁?})
    ]
    
    # 妯℃嫙杈瑰叧绯?
    edges = []
    
    print("鉁?浣跨敤鏁呴殰-缁勪欢鏄犲皠璁＄畻閮ㄤ欢鍋ュ悍鍒嗘暟")
    print(f"   鏁呴殰鏁伴噺: {len(fault_scores)}")
    print(f"   鏁呴殰鑺傜偣鏁伴噺: {len(fault_nodes)}")
    
    # 璁＄畻閮ㄤ欢鍋ュ悍鍒嗘暟
    component_results = calculate_component_scores(
        fault_scores=fault_scores,
        test_scores=test_scores,
        nodes=fault_nodes,
        edges=edges,
        msfg_definition=None
    )
    
    print(f"\n馃搳 璁＄畻缁撴灉:")
    print(f"   閮ㄤ欢鏁伴噺: {len(component_results)}")
    
    for component_name, data in component_results.items():
        print(f"\n   馃敡 {component_name}:")
        print(f"     鍋ュ悍鍒嗘暟: {data.get('health_score', 'N/A')}")
        print(f"     娲昏穬鏁呴殰鏁伴噺: {data.get('active_fault_count', 'N/A')}")
        print(f"     鏈€澶ф晠闅滃垎鏁? {data.get('max_fault_score', 'N/A')}")
        print(f"     骞冲潎鏁呴殰鍒嗘暟: {data.get('avg_fault_score', 'N/A')}")
        print(f"     鎬绘晠闅滄暟閲? {data.get('total_fault_count', 'N/A')}")
        print(f"     娲昏穬鏁呴殰: {data.get('active_faults', [])}")
        print(f"     鏁版嵁鏉ユ簮: {data.get('source', 'N/A')}")
    
    # 娴嬭瘯鏁呴殰鍚嶇О鎺ㄦ柇
    print(f"\n馃攳 娴嬭瘯鏁呴殰鍚嶇О鎺ㄦ柇:")
    test_faults = [
        '鐢垫満杩囪浇鏁呴殰',
        '杞存壙纾ㄦ崯鏁呴殰', 
        '榻胯疆绠辨晠闅?,
        '娓╁害浼犳劅鍣ㄦ晠闅?,
        '鎺у埗鍣ㄦ晠闅?,
        '鏈煡鏁呴殰'
    ]
    
    for fault_name in test_faults:
        inferred_component = extract_component_from_fault_name(fault_name)
        print(f"   {fault_name} -> {inferred_component}")

def test_component_health_calculation():
    """娴嬭瘯閮ㄤ欢鍋ュ悍鍒嗘暟璁＄畻閫昏緫"""
    print(f"\n馃И 娴嬭瘯閮ㄤ欢鍋ュ悍鍒嗘暟璁＄畻閫昏緫")
    print("=" * 50)
    
    from msfg_analysis.algorithms.msfg.fusion import calculate_component_health
    
    # 娴嬭瘯涓嶅悓鍦烘櫙
    test_cases = [
        ([0.1, 0.2, 0.05], "姝ｅ父鎯呭喌"),
        ([0.8, 0.9, 0.7], "涓ラ噸鏁呴殰"),
        ([0.4, 0.3, 0.5], "涓瓑鏁呴殰"),
        ([0.6, 0.7, 0.8], "澶氫釜鏁呴殰"),
        ([], "绌烘晠闅滃垪琛?)
    ]
    
    for fault_scores, description in test_cases:
        health_score = calculate_component_health(fault_scores)
        print(f"   {description}: {fault_scores} -> 鍋ュ悍鍒嗘暟: {health_score:.3f}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("馃殌 寮€濮嬫祴璇曟晠闅?缁勪欢鏄犲皠")
    print("=" * 60)
    
    try:
        test_fault_component_mapping()
        test_component_health_calculation()
        
        print("\n" + "=" * 60)
        print("鉁?娴嬭瘯瀹屾垚锛?)
        print("\n馃搵 鏁呴殰-缁勪欢鏄犲皠浼樺娍:")
        print("1. 鉁?鐩存帴鎬э細鏁呴殰鐩存帴瀵瑰簲鍒板叿浣撶粍浠?)
        print("2. 鉁?鍑嗙‘鎬э細鏁呴殰淇℃伅鏇村噯纭湴鍙嶆槧缁勪欢鐘舵€?)
        print("3. 鉁?瀹屾暣鎬э細涓€涓粍浠跺彲浠ユ湁澶氫釜鏁呴殰")
        print("4. 鉁?鏅鸿兘鎺ㄦ柇锛氭敮鎸佷粠鏁呴殰鍚嶇О鎺ㄦ柇缁勪欢")
        print("5. 鉁?鐏垫椿璁＄畻锛氭敮鎸佸绉嶅仴搴峰垎鏁拌绠楃瓥鐣?)
        
    except Exception as e:
        print(f"\n鉂?娴嬭瘯杩囩▼涓嚭鐜伴敊璇? {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

