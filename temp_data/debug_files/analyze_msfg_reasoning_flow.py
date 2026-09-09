#!/usr/bin/env python
"""
璇︾粏鍒嗘瀽MSFG鎺ㄧ悊娴佺▼
浠庢祴鐐瑰垎鏁板埌鏁呴殰鍒嗘暟銆侀儴浠跺垎鏁般€佺郴缁熷仴搴锋€诲垎鐨勫畬鏁存帹瀵艰繃绋?
"""

import os
import sys
import django
import logging
from typing import Dict, List, Tuple
import numpy as np

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel, PHMData
from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping, FaultComponentMapping, TestPointFaultMapping
from msfg_analysis.algorithms.msfg.fusion import enhanced_msfg_analysis, fuse_test_to_fault, summarize_system, fuse_component_results

# 閰嶇疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_msfg_reasoning_flow():
    """璇︾粏鍒嗘瀽MSFG鎺ㄧ悊娴佺▼"""
    print("馃攳 璇︾粏鍒嗘瀽MSFG鎺ㄧ悊娴佺▼")
    print("=" * 80)
    
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
    component_nodes = [n for n in nodes if n.node_type == 'component']
    
    print(f"\n馃彈锔?MSFG缁撴瀯:")
    print(f"   - 娴嬭瘯鐐? {len(test_nodes)} 涓?)
    print(f"   - 鏁呴殰: {len(fault_nodes)} 涓?)
    print(f"   - 閮ㄤ欢: {len(component_nodes)} 涓?)
    print(f"   - 杈? {len(edges)} 鏉?)
    
    # 3. 鍒涘缓妯℃嫙娴嬭瘯鐐瑰垎鏁?
    print(f"\n馃搳 姝ラ1: 娴嬬偣鍒嗘暟璇勪环")
    print("-" * 40)
    
    test_scores = {}
    for i, test_node in enumerate(test_nodes[:5]):  # 浣跨敤鍓?涓祴璇曠偣
        import random
        # 妯℃嫙涓嶅悓绋嬪害鐨勫紓甯?
        if i == 0:
            test_scores[test_node.name] = 0.1  # 姝ｅ父
        elif i == 1:
            test_scores[test_node.name] = 0.3  # 杞诲井寮傚父
        elif i == 2:
            test_scores[test_node.name] = 0.6  # 涓害寮傚父
        elif i == 3:
            test_scores[test_node.name] = 0.8  # 涓ラ噸寮傚父
        else:
            test_scores[test_node.name] = 0.5  # 涓害寮傚父
    
    print("   娴嬬偣鍒嗘暟 (0=姝ｅ父, 1=涓ラ噸寮傚父):")
    for test_name, score in test_scores.items():
        status = "姝ｅ父" if score < 0.3 else "杞诲井寮傚父" if score < 0.5 else "涓害寮傚父" if score < 0.7 else "涓ラ噸寮傚父"
        print(f"   - {test_name}: {score:.3f} ({status})")
    
    # 4. 鍒嗘瀽鏁呴殰鍒嗘暟鎺ㄥ
    print(f"\n馃攳 姝ラ2: 鏁呴殰鍒嗘暟鎺ㄥ")
    print("-" * 40)
    
    # 鍑嗗鎺ㄧ悊鏁版嵁
    test_name_by_id = {n.node_id: n.name for n in test_nodes}
    fault_name_by_id = {n.node_id: n.name for n in fault_nodes}
    edge_list = [(e.source_node.node_id, e.target_node.node_id) for e in edges]
    
    # 妫€鏌ユ槧灏勫叧绯?
    testpoint_fault_mappings = TestPointFaultMapping.objects.filter(msfg_definition=msfg)
    print(f"   娴嬭瘯鐐?鏁呴殰鏄犲皠: {testpoint_fault_mappings.count()} 涓?)
    
    if testpoint_fault_mappings.count() > 0:
        print("   鐜版湁鏄犲皠鍏崇郴:")
        for mapping in testpoint_fault_mappings[:3]:
            print(f"   - {mapping.test_point_name} 鈫?{mapping.fault_name} (鏉冮噸:{mapping.weight}, 缃俊搴?{mapping.confidence})")
    
    # 杩愯鏁呴殰鍒嗘暟鎺ㄥ
    print(f"\n   鏁呴殰鍒嗘暟鎺ㄥ杩囩▼:")
    fault_scores = fuse_test_to_fault(test_scores, edge_list, test_name_by_id, fault_name_by_id, msfg)
    
    print(f"   鎺ㄥ缁撴灉: {len(fault_scores)} 涓晠闅滃垎鏁?)
    if fault_scores:
        print("   鏁呴殰鍒嗘暟璇︽儏:")
        for fault_name, score in list(fault_scores.items())[:5]:
            status = "姝ｅ父" if score < 0.3 else "杞诲井寮傚父" if score < 0.5 else "涓害寮傚父" if score < 0.7 else "涓ラ噸寮傚父"
            print(f"   - {fault_name}: {score:.3f} ({status})")
    
    # 5. 鍒嗘瀽閮ㄤ欢鍒嗘暟鎺ㄥ
    print(f"\n馃敡 姝ラ3: 閮ㄤ欢鍒嗘暟鎺ㄥ")
    print("-" * 40)
    
    # 妫€鏌ラ儴浠舵槧灏?
    test_component_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg)
    fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg)
    
    print(f"   娴嬭瘯鐐?閮ㄤ欢鏄犲皠: {test_component_mappings.count()} 涓?)
    print(f"   鏁呴殰-閮ㄤ欢鏄犲皠: {fault_component_mappings.count()} 涓?)
    
    # 杩愯瀹屾暣鍒嗘瀽
    print(f"\n   閮ㄤ欢鍒嗘暟鎺ㄥ杩囩▼:")
    analysis_result = enhanced_msfg_analysis(
        test_scores=test_scores,
        edges=edge_list,
        test_name_by_id=test_name_by_id,
        fault_name_by_id=fault_name_by_id,
        nodes=nodes,
        msfg_definition=msfg,
        include_component_analysis=True
    )
    
    component_results = analysis_result.get('component_results', {})
    print(f"   鎺ㄥ缁撴灉: {len(component_results)} 涓儴浠跺仴搴峰害")
    
    if component_results:
        print("   閮ㄤ欢鍋ュ悍搴﹁鎯?")
        for comp_name, comp_data in list(component_results.items())[:5]:
            health_score = comp_data.get('health_score', 0)
            fusion_weights = comp_data.get('fusion_weights', {})
            fault_weight = fusion_weights.get('fault', 0)
            test_weight = fusion_weights.get('test', 0)
            
            status = "鍋ュ悍" if health_score > 0.7 else "鑹ソ" if health_score > 0.5 else "涓€鑸? if health_score > 0.3 else "宸?
            print(f"   - {comp_name}: {health_score:.3f} ({status}) [鏁呴殰鏉冮噸:{fault_weight:.3f}, 娴嬭瘯鏉冮噸:{test_weight:.3f}]")
    
    # 6. 鍒嗘瀽绯荤粺鍋ュ悍鎬诲垎鎺ㄥ
    print(f"\n馃彞 姝ラ4: 绯荤粺鍋ュ悍鎬诲垎鎺ㄥ")
    print("-" * 40)
    
    system_results = analysis_result.get('system_results', {})
    
    print("   绯荤粺鍋ュ悍搴﹁绠?")
    overall_health = system_results.get('overall_health', 0)
    fault_count = system_results.get('fault_count', 0)
    worst_fault_score = system_results.get('worst_fault_score', 0)
    average_fault_score = system_results.get('average_fault_score', 0)
    
    print(f"   - 鏁翠綋鍋ュ悍搴? {overall_health:.3f}")
    print(f"   - 鏁呴殰鏁伴噺: {fault_count}")
    print(f"   - 鏈€涓ラ噸鏁呴殰鍒嗘暟: {worst_fault_score:.3f}")
    print(f"   - 骞冲潎鏁呴殰鍒嗘暟: {average_fault_score:.3f}")
    
    # 7. 璇︾粏鍒嗘瀽鎺ㄧ悊閫昏緫
    print(f"\n馃 鎺ㄧ悊閫昏緫璇︾粏鍒嗘瀽")
    print("-" * 40)
    
    print("   1. 娴嬬偣鍒嗘暟 鈫?鏁呴殰鍒嗘暟:")
    print("      - 浼樺厛绾?: 鐢ㄦ埛瀹氫箟鐨勬祴璇曠偣-鏁呴殰鏄犲皠")
    print("      - 浼樺厛绾?: MSFG鍥剧殑鐩存帴杩炴帴")
    print("      - 浼樺厛绾?: 鏅鸿兘鍖归厤锛堝叧閿瘝鍖归厤锛?)
    
    print("\n   2. 鏁呴殰鍒嗘暟 鈫?閮ㄤ欢鍋ュ悍搴?")
    print("      - 閫氳繃鏁呴殰-閮ㄤ欢鏄犲皠鍏崇郴")
    print("      - 铻嶅悎娴嬭瘯鐐硅矾寰勫拰鏁呴殰璺緞")
    print("      - 浣跨敤缃俊搴︽潈閲嶅钩琛′袱绉嶈矾寰?)
    
    print("\n   3. 閮ㄤ欢鍋ュ悍搴?鈫?绯荤粺鍋ュ悍搴?")
    print("      - 鍩轰簬鏁呴殰鍒嗘暟鐨勭粺璁℃眹鎬?)
    print("      - 鑰冭檻鏁呴殰鏁伴噺鍜屼弗閲嶇▼搴?)
    print("      - 浣跨敤姒傜巼璁烘柟娉曡绠楁暣浣撳仴搴峰害")
    
    # 8. 楠岃瘉鎺ㄧ悊涓€鑷存€?
    print(f"\n鉁?鎺ㄧ悊涓€鑷存€ч獙璇?)
    print("-" * 40)
    
    # 楠岃瘉鏁呴殰鍒嗘暟涓庢祴鐐瑰垎鏁扮殑鍏崇郴
    print("   楠岃瘉1: 鏁呴殰鍒嗘暟涓庢祴鐐瑰垎鏁扮殑鍏崇郴")
    for mapping in testpoint_fault_mappings[:3]:
        test_name = mapping.test_point_name
        fault_name = mapping.fault_name
        if test_name in test_scores and fault_name in fault_scores:
            test_score = test_scores[test_name]
            fault_score = fault_scores[fault_name]
            expected_score = test_score * mapping.weight * mapping.confidence
            print(f"   - {test_name}({test_score:.3f}) 鈫?{fault_name}({fault_score:.3f}) [鏈熸湜:{expected_score:.3f}]")
    
    # 楠岃瘉閮ㄤ欢鍋ュ悍搴︿笌鏁呴殰鍒嗘暟鐨勫叧绯?
    print("\n   楠岃瘉2: 閮ㄤ欢鍋ュ悍搴︿笌鏁呴殰鍒嗘暟鐨勫叧绯?)
    for comp_name, comp_data in list(component_results.items())[:3]:
        health_score = comp_data.get('health_score', 0)
        max_fault_score = comp_data.get('max_fault_score', 0)
        expected_health = 1 - max_fault_score  # 绠€鍖栫殑鍋ュ悍搴﹁绠?
        print(f"   - {comp_name}: 鍋ュ悍搴health_score:.3f}, 鏈€澶ф晠闅滃垎鏁皗max_fault_score:.3f} [鏈熸湜鍋ュ悍搴?{expected_health:.3f}]")
    
    # 楠岃瘉绯荤粺鍋ュ悍搴︿笌鏁呴殰鍒嗘暟鐨勫叧绯?
    print("\n   楠岃瘉3: 绯荤粺鍋ュ悍搴︿笌鏁呴殰鍒嗘暟鐨勫叧绯?)
    if fault_scores:
        max_fault = max(fault_scores.values())
        avg_fault = sum(fault_scores.values()) / len(fault_scores)
        expected_system_health = 1 - max_fault  # 绠€鍖栫殑绯荤粺鍋ュ悍搴﹁绠?
        print(f"   - 鏈€澶ф晠闅滃垎鏁? {max_fault:.3f}")
        print(f"   - 骞冲潎鏁呴殰鍒嗘暟: {avg_fault:.3f}")
        print(f"   - 绯荤粺鍋ュ悍搴? {overall_health:.3f} [鏈熸湜:{expected_system_health:.3f}]")
    
    return True

def explain_reasoning_mechanism():
    """瑙ｉ噴鎺ㄧ悊鏈哄埗"""
    print(f"\n馃摎 MSFG鎺ㄧ悊鏈哄埗璇﹁В")
    print("=" * 80)
    
    print("""
馃幆 MSFG鎺ㄧ悊娴佺▼姒傝堪:

1. 馃搳 娴嬬偣鍒嗘暟璇勪环 (杈撳叆灞?
   - 鍩轰簬TestPointRule瑙勫垯琛ㄨ揪寮忚绠?
   - 鍒嗘暟鑼冨洿: 0(姝ｅ父) ~ 1(涓ラ噸寮傚父)
   - 鏀寔鏉冮噸鍜岀疆淇″害璋冩暣

2. 馃攳 鏁呴殰鍒嗘暟鎺ㄥ (鎺ㄧ悊灞?
   - 杈撳叆: 娴嬬偣鍒嗘暟 + 鏄犲皠鍏崇郴
   - 鏂规硶: 浼樺厛浣跨敤鐢ㄦ埛鏄犲皠 鈫?鍥捐繛鎺?鈫?鏅鸿兘鍖归厤
   - 杈撳嚭: 姣忎釜鏁呴殰鐨勫紓甯告鐜囧垎鏁?

3. 馃敡 閮ㄤ欢鍋ュ悍搴﹁绠?(铻嶅悎灞?
   - 杈撳叆: 鏁呴殰鍒嗘暟 + 閮ㄤ欢鏄犲皠鍏崇郴
   - 鏂规硶: 铻嶅悎娴嬭瘯璺緞鍜屾晠闅滆矾寰?
   - 杈撳嚭: 姣忎釜閮ㄤ欢鐨勫仴搴峰害鍒嗘暟(0~1)

4. 馃彞 绯荤粺鍋ュ悍鎬诲垎 (鑱氬悎灞?
   - 杈撳叆: 鏁呴殰鍒嗘暟 + 閮ㄤ欢鍋ュ悍搴?
   - 鏂规硶: 缁熻姹囨€?+ 姒傜巼璁鸿绠?
   - 杈撳嚭: 绯荤粺鏁翠綋鍋ュ悍搴﹀垎鏁?0~1)

馃敩 鏍稿績绠楁硶鍘熺悊:

1. 鏁呴殰姒傜巼璁＄畻:
   - 鍩轰簬娴嬭瘯鐐?鏁呴殰鐨勭洿鎺ユ槧灏勫叧绯?
   - 搴旂敤鏉冮噸鍜岀疆淇″害璋冩暣
   - 浣跨敤鏈€澶у€肩瓥鐣ュ鐞嗗鏄犲皠

2. 閮ㄤ欢鍋ュ悍搴﹁瀺鍚?
   - 娴嬭瘯璺緞: 鍩轰簬娴嬭瘯鐐?閮ㄤ欢鏄犲皠
   - 鏁呴殰璺緞: 鍩轰簬鏁呴殰-閮ㄤ欢鏄犲皠
   - 铻嶅悎绛栫暐: 缃俊搴﹀姞鏉冨钩鍧?

3. 绯荤粺鍋ュ悍搴﹁仛鍚?
   - 鏁呴殰缁熻: 鏁伴噺銆佹渶澶у€笺€佸钩鍧囧€?
   - 鍋ュ悍搴﹁绠? 1 - 鏁呴殰姒傜巼
   - 鏁翠綋璇勪及: 鑰冭檻鎵€鏈夋晠闅滅殑缁煎悎褰卞搷

馃挕 鎺ㄧ悊浼樺娍:

1. 澶氬眰娆℃帹鐞? 娴嬬偣鈫掓晠闅溾啋閮ㄤ欢鈫掔郴缁?
2. 鐢ㄦ埛鍙厤缃? 鏀寔鑷畾涔夋槧灏勫叧绯?
3. 鏅鸿兘铻嶅悎: 骞宠　澶氱鎺ㄧ悊璺緞
4. 姒傜巼璁哄熀纭€: 绉戝鐨勫仴搴峰害璁＄畻
    """)

if __name__ == "__main__":
    print("馃殌 寮€濮嬪垎鏋怣SFG鎺ㄧ悊娴佺▼")
    print("=" * 80)
    
    success = analyze_msfg_reasoning_flow()
    explain_reasoning_mechanism()
    
    print("\n" + "=" * 80)
    if success:
        print("馃帀 鍒嗘瀽瀹屾垚!")
    else:
        print("鉂?鍒嗘瀽澶辫触")
    
    print("=" * 80)

