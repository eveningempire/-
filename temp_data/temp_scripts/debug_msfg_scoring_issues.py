#!/usr/bin/env python
"""
璋冭瘯MSFG娴嬬偣璇勫垎鍜屾晠闅滃垎鏁拌绠楅棶棰?
"""

import os
import sys
import django
from pathlib import Path

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

import logging
import numpy as np
from data_management.models import PHM, PHMData
from msfg_analysis.models import MSFGDefinition, TestPointRule
from msfg_analysis.services.testpoint_scoring import TestPointScoringService
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_testpoint_scoring():
    """璋冭瘯娴嬬偣璇勫垎闂"""
    print("=== 璋冭瘯娴嬬偣璇勫垎闂 ===")
    
    # 1. 鑾峰彇娴嬭瘯鏁版嵁
    cmg = PHM.objects.filter(cmg_id='01').first()
    if not cmg:
        print("鉂?鎵句笉鍒癈MG 01")
        return
    
    # 鑾峰彇鏈€鏂扮殑鏁版嵁鐐?
    latest_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    if not latest_data:
        print("鉂?鎵句笉鍒版祴璇曟暟鎹?)
        return
    
    print(f"鉁?浣跨敤鏁版嵁鐐? {latest_data.timestamp}")
    print(f"鏁版嵁鍐呭: {latest_data.data}")
    
    # 2. 鑾峰彇MSFG瀹氫箟
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    if not msfg:
        print("鉂?鎵句笉鍒版椿璺冪殑MSFG瀹氫箟")
        return
    
    print(f"鉁?浣跨敤MSFG: {msfg.name}")
    
    # 3. 妫€鏌ユ祴鐐硅鍒?
    rules = TestPointRule.objects.filter(msfg_definition=msfg, is_online=True)
    print(f"馃搵 娴嬬偣瑙勫垯鏁伴噺: {rules.count()}")
    
    for rule in rules:
        print(f"  瑙勫垯: {rule.test_name} -> {rule.rule_expression} (鏉冮噸: {rule.weight})")
    
    # 4. 娴嬭瘯娴嬬偣璇勫垎鏈嶅姟
    scoring_service = TestPointScoringService()
    test_scores = scoring_service.calculate_test_scores(latest_data, msfg)
    
    print(f"\n馃搳 娴嬬偣璇勫垎缁撴灉:")
    for test_name, score in test_scores.items():
        print(f"  {test_name}: {score:.3f}")
    
    # 5. 妫€鏌ユ槸鍚︽湁闂
    print(f"\n馃攳 闂鍒嗘瀽:")
    
    # 妫€鏌ユ槸鍚︽湁榛樿鍒嗘暟
    default_scores = [name for name, score in test_scores.items() if abs(score - 0.2) < 0.001]
    if default_scores:
        print(f"  鈿狅笍 浣跨敤榛樿鍒嗘暟鐨勬祴鐐? {default_scores}")
    
    # 妫€鏌ュ垎鏁拌寖鍥?
    low_scores = [name for name, score in test_scores.items() if score < 0.1]
    if low_scores:
        print(f"  鈿狅笍 鍒嗘暟杩囦綆鐨勬祴鐐? {low_scores}")
    
    return test_scores

def debug_fault_probability_calculation():
    """璋冭瘯鏁呴殰姒傜巼璁＄畻闂"""
    print("\n=== 璋冭瘯鏁呴殰姒傜巼璁＄畻闂 ===")
    
    # 1. 鑾峰彇娴嬭瘯鏁版嵁
    cmg = PHM.objects.filter(cmg_id='01').first()
    if not cmg:
        print("鉂?鎵句笉鍒癈MG 01")
        return
    
    latest_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    if not latest_data:
        print("鉂?鎵句笉鍒版祴璇曟暟鎹?)
        return
    
    # 2. 鑾峰彇MSFG瀹氫箟
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    if not msfg:
        print("鉂?鎵句笉鍒版椿璺冪殑MSFG瀹氫箟")
        return
    
    # 3. 鑾峰彇MSFG鑺傜偣鍜岃竟
    test_nodes = list(msfg.nodes.filter(node_type='test').order_by('created_at'))
    fault_nodes = list(msfg.nodes.filter(node_type='fault').order_by('created_at'))
    edges = list(msfg.edges.all())
    
    print(f"馃搵 MSFG缁撴瀯:")
    print(f"  娴嬭瘯鑺傜偣: {len(test_nodes)} 涓?)
    print(f"  鏁呴殰鑺傜偣: {len(fault_nodes)} 涓?)
    print(f"  杈? {len(edges)} 涓?)
    
    # 4. 璁＄畻娴嬬偣鍒嗘暟
    scoring_service = TestPointScoringService()
    test_scores_dict = scoring_service.calculate_test_scores(latest_data, msfg)
    
    # 杞崲涓鸿瀺鍚堢畻娉曢渶瑕佺殑鏍煎紡
    test_scores = {name: [score] for name, score in test_scores_dict.items()}
    
    print(f"\n馃搳 娴嬬偣鍒嗘暟:")
    for test_name, scores in test_scores.items():
        print(f"  {test_name}: {scores}")
    
    # 5. 浣跨敤铻嶅悎绠楁硶
    fusion_algorithm = AdvancedMSFGFusion(eps=1e-15, n_round=5)
    
    # 鏋勫缓D鐭╅樀
    D_matrix, test_name_to_idx, fault_name_to_idx = fusion_algorithm.build_d_matrix(
        test_nodes, fault_nodes, edges, msfg
    )
    
    print(f"\n馃攳 D鐭╅樀淇℃伅:")
    print(f"  褰㈢姸: {D_matrix.shape}")
    print(f"  闈為浂鍏冪礌: {D_matrix.nnz}")
    print(f"  绋€鐤忓害: {1 - D_matrix.nnz / (D_matrix.shape[0] * D_matrix.shape[1]):.3f}")
    
    # 铻嶅悎娴嬭瘯鐐瑰垎鏁?
    fused_test_scores = fusion_algorithm.fuse_test_scores(test_scores)
    
    print(f"\n馃搳 铻嶅悎鍚庣殑娴嬬偣鍒嗘暟:")
    for test_name, score in fused_test_scores.items():
        print(f"  {test_name}: {score:.3f}")
    
    # 杞崲涓烘暟缁勬牸寮?
    test_scores_array = np.array([
        fused_test_scores.get(test_node.name, 0.2) 
        for test_node in test_nodes
    ], dtype=np.float32)
    
    print(f"\n馃搳 娴嬭瘯鍒嗘暟鏁扮粍:")
    print(f"  鏁扮粍: {test_scores_array}")
    print(f"  鏈€灏忓€? {test_scores_array.min():.3f}")
    print(f"  鏈€澶у€? {test_scores_array.max():.3f}")
    print(f"  骞冲潎鍊? {test_scores_array.mean():.3f}")
    
    # 璁＄畻鏁呴殰姒傜巼
    fault_prob = fusion_algorithm.calculate_fault_probability(D_matrix, test_scores_array)
    
    print(f"\n馃搳 鏁呴殰姒傜巼缁撴灉:")
    print(f"  鏁呴殰姒傜巼鏁扮粍: {fault_prob}")
    print(f"  鏈€灏忓€? {fault_prob.min():.3f}")
    print(f"  鏈€澶у€? {fault_prob.max():.3f}")
    print(f"  骞冲潎鍊? {fault_prob.mean():.3f}")
    
    # 妫€鏌ユ槸鍚﹀叏涓?
    all_ones = np.allclose(fault_prob, 1.0, atol=1e-6)
    if all_ones:
        print(f"  馃毃 闂鍙戠幇: 鎵€鏈夋晠闅滄鐜囬兘鏄?!")
    else:
        print(f"  鉁?鏁呴殰姒傜巼姝ｅ父")
    
    # 6. 鍒嗘瀽D鐭╅樀
    print(f"\n馃攳 D鐭╅樀鍒嗘瀽:")
    
    # 妫€鏌鐭╅樀鏄惁涓虹┖
    if D_matrix.nnz == 0:
        print(f"  馃毃 闂鍙戠幇: D鐭╅樀涓虹┖锛屾病鏈夋祴璇?鏁呴殰杩炴帴!")
        return
    
    # 妫€鏌ユ瘡琛岀殑杩炴帴鏁?
    for i, fault_node in enumerate(fault_nodes):
        row = D_matrix.getrow(i)
        connections = len(row.indices)
        print(f"  鏁呴殰 {fault_node.name}: {connections} 涓祴璇曡繛鎺?)
        
        if connections == 0:
            print(f"    鈿狅笍 璀﹀憡: 鏁呴殰 {fault_node.name} 娌℃湁娴嬭瘯杩炴帴")
    
    # 妫€鏌ユ瘡鍒楃殑杩炴帴鏁?
    for j, test_node in enumerate(test_nodes):
        col = D_matrix.getcol(j)
        connections = len(col.indices)
        print(f"  娴嬭瘯 {test_node.name}: {connections} 涓晠闅滆繛鎺?)
        
        if connections == 0:
            print(f"    鈿狅笍 璀﹀憡: 娴嬭瘯 {test_node.name} 娌℃湁鏁呴殰杩炴帴")

def debug_rule_evaluation():
    """璋冭瘯瑙勫垯鎵ц"""
    print("\n=== 璋冭瘯瑙勫垯鎵ц ===")
    
    # 1. 鑾峰彇娴嬭瘯鏁版嵁
    cmg = PHM.objects.filter(cmg_id='01').first()
    if not cmg:
        print("鉂?鎵句笉鍒癈MG 01")
        return
    
    latest_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    if not latest_data:
        print("鉂?鎵句笉鍒版祴璇曟暟鎹?)
        return
    
    # 2. 鑾峰彇MSFG瀹氫箟
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    if not msfg:
        print("鉂?鎵句笉鍒版椿璺冪殑MSFG瀹氫箟")
        return
    
    # 3. 鑾峰彇娴嬬偣瑙勫垯
    rules = TestPointRule.objects.filter(msfg_definition=msfg, is_online=True)
    
    print(f"馃搵 瑙勫垯鎵ц娴嬭瘯:")
    
    scoring_service = TestPointScoringService()
    
    for rule in rules:
        print(f"\n馃攳 瑙勫垯: {rule.test_name} -> {rule.rule_expression}")
        
        try:
            # 鎵ц瑙勫垯
            result = scoring_service._evaluate_rule_expression(rule.rule_expression, latest_data)
            print(f"  鎵ц缁撴灉: {result}")
            
            # 妫€鏌ユ暟鎹?
            data = latest_data.data or {}
            print(f"  鍙敤鏁版嵁: {list(data.keys())}")
            
            # 妫€鏌ヨ鍒欎腑浣跨敤鐨勫弬鏁?
            import re
            param_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
            params_in_rule = re.findall(param_pattern, rule.rule_expression)
            print(f"  瑙勫垯涓殑鍙傛暟: {params_in_rule}")
            
            # 妫€鏌ュ弬鏁版槸鍚﹀湪鏁版嵁涓?
            missing_params = [param for param in params_in_rule if param not in data]
            if missing_params:
                print(f"  鈿狅笍 缂哄け鍙傛暟: {missing_params}")
            
        except Exception as e:
            print(f"  鉂?鎵ц澶辫触: {e}")

def main():
    """涓诲嚱鏁?""
    print("馃殌 寮€濮嬭皟璇昅SFG璇勫垎闂...")
    
    try:
        # 1. 璋冭瘯娴嬬偣璇勫垎
        test_scores = debug_testpoint_scoring()
        
        # 2. 璋冭瘯鏁呴殰姒傜巼璁＄畻
        debug_fault_probability_calculation()
        
        # 3. 璋冭瘯瑙勫垯鎵ц
        debug_rule_evaluation()
        
        print("\n鉁?璋冭瘯瀹屾垚!")
        
    except Exception as e:
        print(f"鉂?璋冭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

