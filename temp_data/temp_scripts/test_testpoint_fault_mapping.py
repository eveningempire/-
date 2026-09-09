#!/usr/bin/env python
"""
娴嬭瘯娴嬭瘯鐐?鏁呴殰鏄犲皠鐨勬帹鐞嗘晥鏋?
楠岃瘉鐢ㄦ埛瀹氫箟鐨勬槧灏勬槸鍚﹁兘姝ｇ‘褰卞搷鎺ㄧ悊缁撴灉
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
from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping, FaultComponentMapping, TestPointFaultMapping
from msfg_analysis.algorithms.msfg.fusion import enhanced_msfg_analysis

# 閰嶇疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_testpoint_fault_mapping():
    """娴嬭瘯娴嬭瘯鐐?鏁呴殰鏄犲皠鐨勬帹鐞嗘晥鏋?""
    print("馃И 娴嬭瘯娴嬭瘯鐐?鏁呴殰鏄犲皠鎺ㄧ悊鏁堟灉")
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
    
    print(f"馃搳 MSFG缁撴瀯: {len(test_nodes)} 涓祴璇曠偣, {len(fault_nodes)} 涓晠闅?)
    
    # 3. 妫€鏌ョ幇鏈夌殑娴嬭瘯鐐?鏁呴殰鏄犲皠
    existing_mappings = TestPointFaultMapping.objects.filter(msfg_definition=msfg)
    print(f"馃搳 鐜版湁娴嬭瘯鐐?鏁呴殰鏄犲皠: {existing_mappings.count()} 涓?)
    
    if existing_mappings.count() > 0:
        print("   鐜版湁鏄犲皠:")
        for mapping in existing_mappings[:5]:
            print(f"   - {mapping.test_point_name} 鈫?{mapping.fault_name} (鏉冮噸:{mapping.weight}, 缃俊搴?{mapping.confidence})")
        if existing_mappings.count() > 5:
            print(f"   ... 杩樻湁 {existing_mappings.count() - 5} 涓?)
    else:
        print("   鈿狅笍  娌℃湁娴嬭瘯鐐?鏁呴殰鏄犲皠锛屽皢浣跨敤鏅鸿兘鍖归厤")
    
    # 4. 鍒涘缓娴嬭瘯鏁版嵁
    test_scores = {}
    for test_node in test_nodes[:5]:  # 浣跨敤鍓?涓祴璇曠偣
        import random
        test_scores[test_node.name] = random.uniform(0.6, 0.9)  # 杈冮珮鐨勫紓甯稿垎鏁?
    
    print(f"\n馃搳 娴嬭瘯鐐瑰垎鏁?")
    for test_name, score in test_scores.items():
        print(f"   - {test_name}: {score:.3f}")
    
    # 5. 杩愯鎺ㄧ悊娴嬭瘯
    print(f"\n馃И 鎺ㄧ悊娴嬭瘯:")
    
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
            print(f"   鏁呴殰鍒嗘暟 (鍓?涓?:")
            for fault_name, score in list(fault_results.items())[:5]:
                print(f"   - {fault_name}: {score:.3f}")
        
        # 6. 鍒嗘瀽鎺ㄧ悊璐ㄩ噺
        print(f"\n馃搳 鎺ㄧ悊璐ㄩ噺鍒嗘瀽:")
        
        if len(fault_results) == 0:
            print("   鉂?娌℃湁妫€娴嬪埌浠讳綍鏁呴殰")
        elif len(fault_results) == 1:
            print("   鈿狅笍  鍙娴嬪埌1涓晠闅滐紝鍙兘鎺ㄧ悊涓嶅鏁忔劅")
        else:
            print(f"   鉁?妫€娴嬪埌 {len(fault_results)} 涓晠闅?)
        
        # 妫€鏌ユ槸鍚︿娇鐢ㄤ簡鐢ㄦ埛鏄犲皠
        if existing_mappings.count() > 0 and len(fault_results) > 0:
            print("   鉁?浣跨敤浜嗙敤鎴峰畾涔夌殑娴嬭瘯鐐?鏁呴殰鏄犲皠")
            
            # 楠岃瘉鏄犲皠鏄惁鐢熸晥
            mapped_faults = set()
            for mapping in existing_mappings:
                if mapping.test_point_name in test_scores:
                    mapped_faults.add(mapping.fault_name)
            
            detected_mapped_faults = [fault for fault in fault_results.keys() if fault in mapped_faults]
            print(f"   - 鏄犲皠鐨勬晠闅滀腑妫€娴嬪埌: {len(detected_mapped_faults)} 涓?)
            
            if detected_mapped_faults:
                print("   鉁?鐢ㄦ埛鏄犲皠鐢熸晥锛屾帹鐞嗙簿搴︽彁鍗?)
            else:
                print("   鈿狅笍  鐢ㄦ埛鏄犲皠鏈敓鏁堬紝闇€瑕佹鏌ユ槧灏勯厤缃?)
        else:
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

def create_sample_mappings():
    """鍒涘缓绀轰緥娴嬭瘯鐐?鏁呴殰鏄犲皠"""
    print(f"\n馃敡 鍒涘缓绀轰緥娴嬭瘯鐐?鏁呴殰鏄犲皠:")
    print("-" * 40)
    
    cmg_model = PHMModel.objects.filter(is_active=True).first()
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
    
    if not msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG")
        return False
    
    # 鑾峰彇娴嬭瘯鐐瑰拰鏁呴殰
    test_nodes = [n for n in msfg.nodes.all() if n.node_type == 'test']
    fault_nodes = [n for n in msfg.nodes.all() if n.node_type == 'fault']
    
    if len(test_nodes) == 0 or len(fault_nodes) == 0:
        print("鉂?娌℃湁鎵惧埌娴嬭瘯鐐规垨鏁呴殰鑺傜偣")
        return False
    
    # 鍒犻櫎鐜版湁鏄犲皠
    TestPointFaultMapping.objects.filter(msfg_definition=msfg).delete()
    
    # 鍒涘缓绀轰緥鏄犲皠
    sample_mappings = []
    
    # 涓哄墠3涓祴璇曠偣鍒涘缓鏄犲皠
    for i, test_node in enumerate(test_nodes[:3]):
        # 涓烘瘡涓祴璇曠偣鏄犲皠鍒?-3涓晠闅?
        for j in range(min(2, len(fault_nodes))):
            fault_node = fault_nodes[(i + j) % len(fault_nodes)]
            
            mapping = TestPointFaultMapping(
                msfg_definition=msfg,
                test_point_name=test_node.name,
                fault_name=fault_node.name,
                mapping_type='one_to_many' if j > 0 else 'one_to_one',
                weight=1.0 - (j * 0.2),  # 鏉冮噸閫掑噺
                confidence=0.8 - (j * 0.1),  # 缃俊搴﹂€掑噺
                description=f"绀轰緥鏄犲皠: {test_node.name} 鈫?{fault_node.name}"
            )
            sample_mappings.append(mapping)
    
    # 鎵归噺鍒涘缓
    if sample_mappings:
        TestPointFaultMapping.objects.bulk_create(sample_mappings)
        print(f"鉁?鍒涘缓浜?{len(sample_mappings)} 涓ず渚嬫祴璇曠偣-鏁呴殰鏄犲皠")
        
        print("   鍒涘缓鐨勬槧灏?")
        for mapping in sample_mappings:
            print(f"   - {mapping.test_point_name} 鈫?{mapping.fault_name} (鏉冮噸:{mapping.weight}, 缃俊搴?{mapping.confidence})")
    else:
        print("鉂?娌℃湁鍒涘缓浠讳綍鏄犲皠")
    
    return True

if __name__ == "__main__":
    print("馃殌 寮€濮嬫祴璇曟祴璇曠偣-鏁呴殰鏄犲皠鎺ㄧ悊鏁堟灉")
    print("=" * 60)
    
    # 璇㈤棶鏄惁鍒涘缓绀轰緥鏄犲皠
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--create-mappings':
        success = create_sample_mappings()
    else:
        success = test_testpoint_fault_mapping()
    
    print("\n" + "=" * 60)
    if success:
        print("馃帀 娴嬭瘯瀹屾垚!")
    else:
        print("鉂?娴嬭瘯澶辫触")
    
    print("=" * 60)

