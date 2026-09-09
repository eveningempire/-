#!/usr/bin/env python
"""
鍒嗘瀽MSFG鎺ㄧ悊閫昏緫鐨勯棶棰?
楠岃瘉涓夊眰鍏崇郴鐨勫畬鏁存€?
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

def analyze_reasoning_logic():
    """鍒嗘瀽鎺ㄧ悊閫昏緫鐨勯棶棰?""
    print("馃攳 鍒嗘瀽MSFG鎺ㄧ悊閫昏緫闂")
    print("=" * 60)
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG
    cmg_model = PHMModel.objects.filter(is_active=True).first()
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
    
    if not msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG")
        return False
    
    print(f"馃搵 浣跨敤MSFG: {msfg.name}")
    
    # 2. 鍒嗘瀽MSFG缁撴瀯
    nodes = list(msfg.nodes.all())
    edges = list(msfg.edges.all())
    
    test_nodes = [n for n in nodes if n.node_type == 'test']
    fault_nodes = [n for n in nodes if n.node_type == 'fault']
    component_nodes = [n for n in nodes if n.node_type == 'component']
    
    print(f"\n馃彈锔?MSFG缁撴瀯鍒嗘瀽:")
    print(f"   - 娴嬭瘯鐐? {len(test_nodes)} 涓?)
    print(f"   - 鏁呴殰: {len(fault_nodes)} 涓?)
    print(f"   - 閮ㄤ欢: {len(component_nodes)} 涓?)
    print(f"   - 杈? {len(edges)} 鏉?)
    
    # 3. 鍒嗘瀽杩炴帴鍏崇郴
    print(f"\n馃敆 杩炴帴鍏崇郴鍒嗘瀽:")
    
    # 缁熻杩炴帴绫诲瀷
    connection_types = {}
    for edge in edges:
        source_type = edge.source_node.node_type
        target_type = edge.target_node.node_type
        connection_key = f"{source_type}->{target_type}"
        connection_types[connection_key] = connection_types.get(connection_key, 0) + 1
    
    for conn_type, count in connection_types.items():
        print(f"   - {conn_type}: {count} 鏉?)
    
    # 4. 妫€鏌ヤ笁灞傚叧绯荤殑瀹屾暣鎬?
    print(f"\n馃攳 涓夊眰鍏崇郴瀹屾暣鎬ф鏌?")
    
    # 妫€鏌ユ祴璇曠偣鈫掓晠闅滅殑鐩存帴杩炴帴
    test_to_fault_edges = [e for e in edges if e.source_node.node_type == 'test' and e.target_node.node_type == 'fault']
    print(f"   - 娴嬭瘯鐐光啋鏁呴殰鐩存帴杩炴帴: {len(test_to_fault_edges)} 鏉?)
    
    if test_to_fault_edges:
        print("     杩炴帴璇︽儏:")
        for edge in test_to_fault_edges[:5]:
            print(f"     - {edge.source_node.name} 鈫?{edge.target_node.name}")
    else:
        print("     鈿狅笍  缂哄皯娴嬭瘯鐐光啋鏁呴殰鐨勭洿鎺ヨ繛鎺?)
    
    # 妫€鏌ユ祴璇曠偣鈫掗儴浠剁殑杩炴帴
    test_to_component_edges = [e for e in edges if e.source_node.node_type == 'test' and e.target_node.node_type == 'component']
    print(f"   - 娴嬭瘯鐐光啋閮ㄤ欢鐩存帴杩炴帴: {len(test_to_component_edges)} 鏉?)
    
    # 妫€鏌ラ儴浠垛啋鏁呴殰鐨勮繛鎺?
    component_to_fault_edges = [e for e in edges if e.source_node.node_type == 'component' and e.target_node.node_type == 'fault']
    print(f"   - 閮ㄤ欢鈫掓晠闅滅洿鎺ヨ繛鎺? {len(component_to_fault_edges)} 鏉?)
    
    # 5. 鍒嗘瀽鏄犲皠鍏崇郴
    print(f"\n馃椇锔?鏄犲皠鍏崇郴鍒嗘瀽:")
    
    # 娴嬭瘯鐐?閮ㄤ欢鏄犲皠
    test_component_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg)
    print(f"   - 娴嬭瘯鐐?閮ㄤ欢鏄犲皠: {test_component_mappings.count()} 涓?)
    
    # 鏁呴殰-閮ㄤ欢鏄犲皠
    fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg)
    print(f"   - 鏁呴殰-閮ㄤ欢鏄犲皠: {fault_component_mappings.count()} 涓?)
    
    # 6. 鍒嗘瀽鎺ㄧ悊璺緞
    print(f"\n馃洡锔?鎺ㄧ悊璺緞鍒嗘瀽:")
    
    if test_to_fault_edges:
        print("   鉁?瀛樺湪鐩存帴鎺ㄧ悊璺緞: 娴嬭瘯鐐?鈫?鏁呴殰")
    elif test_to_component_edges and component_to_fault_edges:
        print("   鉁?瀛樺湪闂存帴鎺ㄧ悊璺緞: 娴嬭瘯鐐?鈫?閮ㄤ欢 鈫?鏁呴殰")
    elif test_component_mappings.exists() and fault_component_mappings.exists():
        print("   鈿狅笍  瀛樺湪鏄犲皠鎺ㄧ悊璺緞: 娴嬭瘯鐐?鈫?閮ㄤ欢(鏄犲皠) 鈫?鏁呴殰(鏄犲皠)")
        print("   鈿狅笍  浣嗙己灏戝浘缁撴瀯鏀寔")
    else:
        print("   鉂?缂哄皯鎺ㄧ悊璺緞")
    
    # 7. 楠岃瘉鎺ㄧ悊鏁堟灉
    print(f"\n馃И 楠岃瘉鎺ㄧ悊鏁堟灉:")
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    test_scores = {}
    for test_node in test_nodes[:3]:  # 浣跨敤鍓?涓祴璇曠偣
        import random
        test_scores[test_node.name] = random.uniform(0.5, 0.8)
    
    print(f"   娴嬭瘯鐐瑰垎鏁?")
    for test_name, score in test_scores.items():
        print(f"   - {test_name}: {score:.3f}")
    
    try:
        # 鍑嗗鎺ㄧ悊鏁版嵁
        test_name_by_id = {n.node_id: n.name for n in test_nodes}
        fault_name_by_id = {n.node_id: n.name for n in fault_nodes}
        edge_list = [(e.source_node.node_id, e.target_node.node_id) for e in edges]
        
        # 杩愯鎺ㄧ悊
        analysis_result = enhanced_msfg_analysis(
            test_scores=test_scores,
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
        
        print(f"   鎺ㄧ悊缁撴灉:")
        print(f"   - 妫€娴嬪埌鐨勬晠闅? {len(fault_results)} 涓?)
        print(f"   - 閮ㄤ欢鍋ュ悍搴? {len(component_results)} 涓?)
        
        if fault_results:
            print(f"   鏁呴殰鍒嗘暟:")
            for fault_name, score in list(fault_results.items())[:3]:
                print(f"   - {fault_name}: {score:.3f}")
        
        # 8. 鍒嗘瀽鎺ㄧ悊璐ㄩ噺
        print(f"\n馃搳 鎺ㄧ悊璐ㄩ噺鍒嗘瀽:")
        
        if len(fault_results) == 0:
            print("   鉂?娌℃湁妫€娴嬪埌浠讳綍鏁呴殰")
        elif len(fault_results) == 1:
            print("   鈿狅笍  鍙娴嬪埌1涓晠闅滐紝鍙兘鎺ㄧ悊涓嶅鏁忔劅")
        else:
            print(f"   鉁?妫€娴嬪埌 {len(fault_results)} 涓晠闅?)
        
        # 妫€鏌ユ槸鍚︿娇鐢ㄤ簡鏅鸿兘鍖归厤
        if len(test_to_fault_edges) == 0 and len(fault_results) > 0:
            print("   鈿狅笍  浣跨敤浜嗘櫤鑳藉尮閰嶏紝鎺ㄧ悊绮惧害鍙兘涓嶅")
        
        # 妫€鏌ラ儴浠跺仴搴峰害鐨勫悎鐞嗘€?
        if component_results:
            avg_health = sum(comp_data.get('health_score', 0) for comp_data in component_results.values()) / len(component_results)
            print(f"   - 骞冲潎閮ㄤ欢鍋ュ悍搴? {avg_health:.3f}")
            
            # 妫€鏌ヨ瀺鍚堟潈閲?
            test_weights = []
            fault_weights = []
            for comp_data in component_results.values():
                weights = comp_data.get('fusion_weights', {})
                test_weights.append(weights.get('test', 0))
                fault_weights.append(weights.get('fault', 0))
            
            avg_test_weight = sum(test_weights) / len(test_weights) if test_weights else 0
            avg_fault_weight = sum(fault_weights) / len(fault_weights) if fault_weights else 0
            
            print(f"   - 骞冲潎娴嬭瘯鏉冮噸: {avg_test_weight:.3f}")
            print(f"   - 骞冲潎鏁呴殰鏉冮噸: {avg_fault_weight:.3f}")
            
            if avg_test_weight > 0.8:
                print("   鈿狅笍  涓昏渚濊禆娴嬭瘯璺緞锛屾晠闅滄帹鐞嗕笉瓒?)
            elif avg_fault_weight > 0.8:
                print("   鉁?涓昏渚濊禆鏁呴殰璺緞锛屾帹鐞嗗悎鐞?)
            else:
                print("   鉁?娴嬭瘯鍜屾晠闅滆矾寰勫钩琛?)
        
    except Exception as e:
        print(f"   鉂?鎺ㄧ悊澶辫触: {e}")
        import traceback
        traceback.print_exc()
    
    return True

def suggest_improvements():
    """寤鸿鏀硅繘鏂规"""
    print(f"\n馃挕 鏀硅繘寤鸿:")
    print("=" * 60)
    
    print("1. 馃敆 娣诲姞鐩存帴鐨勬祴璇曠偣鈫掓晠闅滆繛鎺?")
    print("   - 鍦∕SFG鍥句腑娣诲姞娴嬭瘯鐐瑰埌鏁呴殰鐨勭洿鎺ヨ竟")
    print("   - 杩欐牱鍙互閬垮厤渚濊禆鏅鸿兘鍖归厤")
    
    print("\n2. 馃椇锔?瀹屽杽涓夊眰鏄犲皠鍏崇郴:")
    print("   - 娴嬭瘯鐐光啋閮ㄤ欢鏄犲皠 (宸叉湁)")
    print("   - 鏁呴殰鈫掗儴浠舵槧灏?(宸叉湁)")
    print("   - 娴嬭瘯鐐光啋鏁呴殰鏄犲皠 (闇€瑕佹坊鍔?")
    
    print("\n3. 馃 鏀硅繘鎺ㄧ悊绠楁硶:")
    print("   - 浼樺厛浣跨敤鐩存帴鐨勫浘缁撴瀯杩炴帴")
    print("   - 鍏舵浣跨敤鏄犲皠鍏崇郴")
    print("   - 鏈€鍚庢墠浣跨敤鏅鸿兘鍖归厤")
    
    print("\n4. 馃搳 澧炲姞鎺ㄧ悊璐ㄩ噺璇勪及:")
    print("   - 娣诲姞鎺ㄧ悊缃俊搴︽寚鏍?)
    print("   - 鍖哄垎鐩存帴鎺ㄧ悊鍜岄棿鎺ユ帹鐞嗙粨鏋?)
    print("   - 鎻愪緵鎺ㄧ悊璺緞鐨勫彲瑙嗗寲")

if __name__ == "__main__":
    print("馃殌 寮€濮嬪垎鏋怣SFG鎺ㄧ悊閫昏緫闂")
    print("=" * 60)
    
    success = analyze_reasoning_logic()
    suggest_improvements()
    
    print("\n" + "=" * 60)
    if success:
        print("馃帀 鍒嗘瀽瀹屾垚!")
    else:
        print("鉂?鍒嗘瀽澶辫触")
    
    print("=" * 60)

