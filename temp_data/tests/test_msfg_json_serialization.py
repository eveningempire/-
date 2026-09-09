#!/usr/bin/env python
"""
娴嬭瘯MSFG鍒嗘瀽缁撴灉鐨凧SON搴忓垪鍖?
楠岃瘉淇鍚庣殑numpy绫诲瀷杞崲鏄惁鏈夋晥
"""

import os
import sys
import django
import json
import numpy as np

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge

def test_msfg_json_serialization():
    """娴嬭瘯MSFG鍒嗘瀽缁撴灉鐨凧SON搴忓垪鍖?""
    print("寮€濮嬫祴璇昅SFG鍒嗘瀽缁撴灉鐨凧SON搴忓垪鍖?..")
    
    try:
        # 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
        active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
        if not active_msfg:
            print("鏈壘鍒版椿璺冪殑MSFG瀹氫箟锛屽垱寤烘祴璇曟暟鎹?..")
            return
        
        print(f"浣跨敤娲昏穬鐨凪SFG: {active_msfg.name}")
        
        # 鑾峰彇MSFG鑺傜偣鍜岃竟
        nodes = MSFGNode.objects.filter(msfg_definition=active_msfg).order_by('id')
        edges = MSFGEdge.objects.filter(msfg_definition=active_msfg).order_by('id')
        
        # 鍒嗙娴嬭瘯鐐瑰拰鏁呴殰鐐?
        test_nodes = [node for node in nodes if node.node_type == 'test']
        fault_nodes = [node for node in nodes if node.node_type == 'fault']
        
        print(f"娴嬭瘯鐐规暟閲? {len(test_nodes)}")
        print(f"鏁呴殰鐐规暟閲? {len(fault_nodes)}")
        print(f"杈规暟閲? {len(edges)}")
        
        if not test_nodes or not fault_nodes:
            print("MSFG缂哄皯娴嬭瘯鐐规垨鏁呴殰鐐癸紝鏃犳硶杩涜娴嬭瘯")
            return
        
        # 鍒涘缓妯℃嫙鐨勬祴璇曠偣鍒嗘暟
        test_scores = {}
        for test_node in test_nodes:
            # 涓烘瘡涓祴璇曠偣鍒涘缓涓€浜涙ā鎷熷垎鏁?
            test_scores[test_node.name] = [0.1 + i * 0.1 for i in range(3)]
        
        # 鍒涘缓榛樿鐨勯儴浠舵槧灏?
        component_mappings = {
            '杞瓙杞存壙': [fault.name for fault in fault_nodes[:2]] if len(fault_nodes) >= 2 else [],
            '杞瓙椹卞姩鐢垫満': [fault.name for fault in fault_nodes[2:4]] if len(fault_nodes) >= 4 else [],
            '鐢垫簮鏉?: [fault.name for fault in fault_nodes[4:6]] if len(fault_nodes) >= 6 else [],
        }
        
        # 绉婚櫎绌虹殑閮ㄤ欢鏄犲皠
        component_mappings = {k: v for k, v in component_mappings.items() if v}
        
        print(f"閮ㄤ欢鏄犲皠: {component_mappings}")
        
        # 鍒涘缓MSFG铻嶅悎绠楁硶瀹炰緥
        fusion_algorithm = AdvancedMSFGFusion(eps=1e-15, n_round=5)
        
        # 杩愯鍒嗘瀽
        print("杩愯MSFG鍒嗘瀽...")
        analysis_result = fusion_algorithm.run_advanced_analysis(
            test_scores=test_scores,
            test_nodes=test_nodes,
            fault_nodes=fault_nodes,
            edges=edges,
            component_mappings=component_mappings
        )
        
        print("鍒嗘瀽瀹屾垚锛屽紑濮嬫祴璇旿SON搴忓垪鍖?..")
        
        # 娴嬭瘯JSON搴忓垪鍖?
        try:
            json_str = json.dumps(analysis_result, ensure_ascii=False, indent=2)
            print("鉁?JSON搴忓垪鍖栨垚鍔燂紒")
            print(f"搴忓垪鍖栫粨鏋滈暱搴? {len(json_str)} 瀛楃")
            
            # 娴嬭瘯鍙嶅簭鍒楀寲
            parsed_result = json.loads(json_str)
            print("鉁?JSON鍙嶅簭鍒楀寲鎴愬姛锛?)
            
            # 楠岃瘉鍏抽敭瀛楁
            assert 'test_results' in parsed_result
            assert 'fault_results' in parsed_result
            assert 'component_results' in parsed_result
            assert 'system_results' in parsed_result
            print("鉁?缁撴灉缁撴瀯楠岃瘉閫氳繃锛?)
            
            # 楠岃瘉鏁板€肩被鍨?
            for test_name, test_data in parsed_result['test_results'].items():
                assert isinstance(test_data['score'], (int, float))
                print(f"鉁?娴嬭瘯鐐?{test_name} 鍒嗘暟绫诲瀷姝ｇ‘: {type(test_data['score'])}")
            
            for fault_name, fault_data in parsed_result['fault_results'].items():
                assert isinstance(fault_data['fault_probability'], (int, float))
                assert isinstance(fault_data['fuzzy_probability'], (int, float))
                print(f"鉁?鏁呴殰鐐?{fault_name} 姒傜巼绫诲瀷姝ｇ‘")
            
            for component_name, component_data in parsed_result['component_results'].items():
                assert isinstance(component_data['health_score'], (int, float))
                print(f"鉁?閮ㄤ欢 {component_name} 鍋ュ悍搴︾被鍨嬫纭? {type(component_data['health_score'])}")
            
            system_data = parsed_result['system_results']
            assert isinstance(system_data['overall_health'], (int, float))
            print(f"鉁?绯荤粺鍋ュ悍搴︾被鍨嬫纭? {type(system_data['overall_health'])}")
            
            print("\n馃帀 鎵€鏈夋祴璇曢€氳繃锛丮SFG鍒嗘瀽缁撴灉鍙互姝ｅ父搴忓垪鍖栦负JSON")
            
        except Exception as e:
            print(f"鉂?JSON搴忓垪鍖栧け璐? {e}")
            raise
            
    except Exception as e:
        print(f"鉂?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_msfg_json_serialization()

