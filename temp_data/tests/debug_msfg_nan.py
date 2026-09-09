#!/usr/bin/env python
"""
璋冭瘯MSFG璁＄畻涓璑aN鐨勯棶棰?
"""

import os
import sys
import django
import numpy as np

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, PHMData
from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

def debug_msfg_nan():
    """璋冭瘯MSFG璁＄畻涓璑aN鐨勯棶棰?""
    print("寮€濮嬭皟璇昅SFG NaN闂...")
    
    try:
        # 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
        active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
        if not active_msfg:
            print("鉂?鏈壘鍒版椿璺冪殑MSFG瀹氫箟")
            return
        
        print(f"鉁?浣跨敤娲昏穬鐨凪SFG: {active_msfg.name}")
        
        # 鑾峰彇MSFG鑺傜偣鍜岃竟
        test_nodes = list(active_msfg.nodes.filter(node_type='test').order_by('created_at'))
        fault_nodes = list(active_msfg.nodes.filter(node_type='fault').order_by('created_at'))
        edges = list(active_msfg.edges.all())
        
        print(f"娴嬭瘯鐐规暟閲? {len(test_nodes)}")
        print(f"鏁呴殰鐐规暟閲? {len(fault_nodes)}")
        print(f"杈规暟閲? {len(edges)}")
        
        # 鎵撳嵃娴嬭瘯鐐瑰悕绉?
        print("\n娴嬭瘯鐐瑰悕绉?")
        for i, node in enumerate(test_nodes):
            print(f"  {i}: {node.name}")
        
        # 鎵撳嵃鏁呴殰鐐瑰悕绉?
        print("\n鏁呴殰鐐瑰悕绉?")
        for i, node in enumerate(fault_nodes):
            print(f"  {i}: {node.name}")
        
        # 鑾峰彇涓€涓狢MG瀹炰緥
        cmg = PHM.objects.first()
        if not cmg:
            print("鉂?鏈壘鍒癈MG瀹炰緥")
            return
        
        print(f"\n鉁?浣跨敤PHM: {cmg.name}")
        
        # 鑾峰彇鏈€鏂扮殑PHMData璁板綍
        latest_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
        if not latest_data:
            print("鉂?鏈壘鍒癈MG鏁版嵁")
            return
        
        print(f"鉁?浣跨敤鏁版嵁璁板綍: {latest_data.id}, 鏃堕棿: {latest_data.timestamp}")
        print(f"鏁版嵁鍐呭: {latest_data.data}")
        
        # 妯℃嫙娴嬭瘯鐐瑰垎鏁拌绠?
        raw_data = latest_data.data or {}
        test_scores = {}
        numeric_params = []
        
        print(f"\n鍘熷鏁版嵁鍙傛暟:")
        for key, value in raw_data.items():
            try:
                fv = float(value)
                numeric_params.append((key, fv))
                print(f"  {key}: {fv}")
            except (ValueError, TypeError):
                print(f"  {key}: {value} (闈炴暟鍊?")
                continue
        
        print(f"\n鏁板€煎弬鏁版暟閲? {len(numeric_params)}")
        
        # 涓烘瘡涓祴璇曠偣鍒涘缓鍒嗘暟鍒楄〃
        print(f"\n娴嬭瘯鐐瑰垎鏁拌绠?")
        for i, test_node in enumerate(test_nodes):
            if i < len(numeric_params):
                param_key, param_value = numeric_params[i]
                # 灏嗘暟鍊煎綊涓€鍖栧埌0-1鑼冨洿浣滀负娴嬭瘯鐐瑰垎鏁?
                score = max(0.0, min(1.0, abs(param_value) / (abs(param_value) + 1.0)))
                test_scores[test_node.name] = [score]
                print(f"  {test_node.name}: {param_key}({param_value}) -> {score:.3f}")
            else:
                test_scores[test_node.name] = [0.2]
                print(f"  {test_node.name}: 榛樿鍊?-> 0.200")
        
        print(f"\n鏈€缁堟祴璇曠偣鍒嗘暟: {test_scores}")
        
        # 妫€鏌ユ槸鍚︽湁NaN鍊?
        for test_name, scores in test_scores.items():
            for score in scores:
                if np.isnan(score):
                    print(f"鉂?鍙戠幇NaN: {test_name} = {score}")
        
        # 鍒涘缓榛樿鐨勯儴浠舵槧灏?
        component_mappings = {
            '杞瓙杞存壙': [fault.name for fault in fault_nodes[:2]] if len(fault_nodes) >= 2 else [],
            '杞瓙椹卞姩鐢垫満': [fault.name for fault in fault_nodes[2:4]] if len(fault_nodes) >= 4 else [],
            '鐢垫簮鏉?: [fault.name for fault in fault_nodes[4:6]] if len(fault_nodes) >= 6 else [],
        }
        
        # 绉婚櫎绌虹殑閮ㄤ欢鏄犲皠
        component_mappings = {k: v for k, v in component_mappings.items() if v}
        print(f"\n閮ㄤ欢鏄犲皠: {component_mappings}")
        
        # 杩愯MSFG鍒嗘瀽
        print(f"\n寮€濮婱SFG鍒嗘瀽...")
        fusion_algorithm = AdvancedMSFGFusion(eps=1e-15, n_round=5)
        
        analysis_result = fusion_algorithm.run_advanced_analysis(
            test_scores=test_scores,
            test_nodes=test_nodes,
            fault_nodes=fault_nodes,
            edges=edges,
            component_mappings=component_mappings
        )
        
        print(f"\n鍒嗘瀽缁撴灉:")
        print(f"娴嬭瘯缁撴灉鏁伴噺: {len(analysis_result.get('test_results', {}))}")
        print(f"鏁呴殰缁撴灉鏁伴噺: {len(analysis_result.get('fault_results', {}))}")
        print(f"閮ㄤ欢缁撴灉鏁伴噺: {len(analysis_result.get('component_results', {}))}")
        
        # 妫€鏌ユ祴璇曠粨鏋滀腑鐨凬aN
        test_results = analysis_result.get('test_results', {})
        for test_name, test_data in test_results.items():
            score = test_data.get('score')
            if score is not None and np.isnan(score):
                print(f"鉂?娴嬭瘯缁撴灉NaN: {test_name} = {score}")
        
        # 妫€鏌ユ晠闅滅粨鏋滀腑鐨凬aN
        fault_results = analysis_result.get('fault_results', {})
        for fault_name, fault_data in fault_results.items():
            fault_prob = fault_data.get('fault_probability')
            fuzzy_prob = fault_data.get('fuzzy_probability')
            if fault_prob is not None and np.isnan(fault_prob):
                print(f"鉂?鏁呴殰姒傜巼NaN: {fault_name} = {fault_prob}")
            if fuzzy_prob is not None and np.isnan(fuzzy_prob):
                print(f"鉂?妯＄硦姒傜巼NaN: {fault_name} = {fuzzy_prob}")
        
        # 妫€鏌ラ儴浠剁粨鏋滀腑鐨凬aN
        component_results = analysis_result.get('component_results', {})
        for component_name, component_data in component_results.items():
            health_score = component_data.get('health_score')
            if health_score is not None and np.isnan(health_score):
                print(f"鉂?閮ㄤ欢鍋ュ悍搴aN: {component_name} = {health_score}")
        
        print(f"\n馃帀 璋冭瘯瀹屾垚锛?)
        
    except Exception as e:
        print(f"鉂?璋冭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_msfg_nan()

