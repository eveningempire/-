#!/usr/bin/env python
"""
璋冭瘯MSFG D鐭╅樀鏋勫缓鍜屾祴鐐硅鍒欓棶棰?
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
from msfg_analysis.models import MSFGDefinition, TestPointRule, TestPointFaultMapping, TestPointComponentMapping, FaultComponentMapping
from msfg_analysis.services.testpoint_scoring import TestPointScoringService
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_d_matrix_construction():
    """鍒嗘瀽D鐭╅樀鏋勫缓闂"""
    print("=== 鍒嗘瀽D鐭╅樀鏋勫缓闂 ===")
    
    # 1. 鑾峰彇MSFG瀹氫箟
    cmg = PHM.objects.filter(cmg_id='01').first()
    if not cmg:
        print("鉂?鎵句笉鍒癈MG 01")
        return
    
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    if not msfg:
        print("鉂?鎵句笉鍒版椿璺冪殑MSFG瀹氫箟")
        return
    
    print(f"鉁?浣跨敤MSFG: {msfg.name}")
    
    # 2. 鑾峰彇MSFG鑺傜偣
    test_nodes = list(msfg.nodes.filter(node_type='test').order_by('created_at'))
    fault_nodes = list(msfg.nodes.filter(node_type='fault').order_by('created_at'))
    edges = list(msfg.edges.all())
    
    print(f"\n馃搵 MSFG鑺傜偣缁熻:")
    print(f"  娴嬭瘯鑺傜偣: {len(test_nodes)} 涓?)
    print(f"  鏁呴殰鑺傜偣: {len(fault_nodes)} 涓?)
    print(f"  杈? {len(edges)} 涓?)
    
    # 3. 妫€鏌ョ敤鎴疯嚜瀹氫箟鏄犲皠
    print(f"\n馃攳 鐢ㄦ埛鑷畾涔夋槧灏勫垎鏋?")
    
    # 娴嬭瘯鐐?鏁呴殰鏄犲皠
    test_fault_mappings = TestPointFaultMapping.objects.filter(msfg_definition=msfg)
    print(f"  娴嬭瘯鐐?鏁呴殰鏄犲皠: {test_fault_mappings.count()} 涓?)
    
    # 娴嬭瘯鐐?閮ㄤ欢鏄犲皠
    test_component_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg)
    print(f"  娴嬭瘯鐐?閮ㄤ欢鏄犲皠: {test_component_mappings.count()} 涓?)
    
    # 鏁呴殰-閮ㄤ欢鏄犲皠
    fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg)
    print(f"  鏁呴殰-閮ㄤ欢鏄犲皠: {fault_component_mappings.count()} 涓?)
    
    # 4. 鍒嗘瀽鏄犲皠鍐呭
    print(f"\n馃搳 鏄犲皠鍐呭鍒嗘瀽:")
    
    # 娴嬭瘯鐐?鏁呴殰鏄犲皠璇︽儏
    if test_fault_mappings.exists():
        print(f"  娴嬭瘯鐐?鏁呴殰鏄犲皠璇︽儏:")
        for mapping in test_fault_mappings[:10]:  # 鍙樉绀哄墠10涓?
            print(f"    {mapping.test_point_name} -> {mapping.fault_name} (鏉冮噸: {mapping.weight}, 缃俊搴? {mapping.confidence})")
        if test_fault_mappings.count() > 10:
            print(f"    ... 杩樻湁 {test_fault_mappings.count() - 10} 涓槧灏?)
    
    # 5. 鏋勫缓D鐭╅樀
    print(f"\n馃敡 鏋勫缓D鐭╅樀:")
    fusion_algorithm = AdvancedMSFGFusion()
    
    D_matrix, test_name_to_idx, fault_name_to_idx = fusion_algorithm.build_d_matrix(
        test_nodes, fault_nodes, edges, msfg
    )
    
    print(f"  D鐭╅樀褰㈢姸: {D_matrix.shape}")
    print(f"  闈為浂鍏冪礌: {D_matrix.nnz}")
    print(f"  绋€鐤忓害: {1 - D_matrix.nnz / (D_matrix.shape[0] * D_matrix.shape[1]):.3f}")
    
    # 6. 鍒嗘瀽D鐭╅樀鐨勬瀯寤烘潵婧?
    print(f"\n馃攳 D鐭╅樀鏋勫缓鏉ユ簮鍒嗘瀽:")
    
    # 妫€鏌ョ洿鎺ュ浘杩炴帴
    direct_connections = 0
    for edge in edges:
        if edge.source_node.node_type == 'test' and edge.target_node.node_type == 'fault':
            direct_connections += 1
    
    print(f"  鐩存帴鍥捐繛鎺? {direct_connections} 涓?)
    print(f"  鐢ㄦ埛鑷畾涔夋槧灏? {test_fault_mappings.count()} 涓?)
    
    # 7. 妫€鏌ユ槧灏勮鐩栨儏鍐?
    print(f"\n馃搳 鏄犲皠瑕嗙洊鎯呭喌:")
    
    # 娴嬭瘯鐐硅鐩?
    mapped_test_points = set()
    for mapping in test_fault_mappings:
        mapped_test_points.add(mapping.test_point_name)
    
    all_test_points = set(node.name for node in test_nodes)
    unmapped_tests = all_test_points - mapped_test_points
    
    print(f"  娴嬭瘯鐐规€绘暟: {len(all_test_points)}")
    print(f"  宸叉槧灏勬祴璇曠偣: {len(mapped_test_points)}")
    print(f"  鏈槧灏勬祴璇曠偣: {len(unmapped_tests)}")
    if unmapped_tests:
        print(f"    鏈槧灏勭殑娴嬭瘯鐐? {list(unmapped_tests)}")
    
    # 鏁呴殰鐐硅鐩?
    mapped_faults = set()
    for mapping in test_fault_mappings:
        mapped_faults.add(mapping.fault_name)
    
    all_faults = set(node.name for node in fault_nodes)
    unmapped_faults = all_faults - mapped_faults
    
    print(f"  鏁呴殰鐐规€绘暟: {len(all_faults)}")
    print(f"  宸叉槧灏勬晠闅滅偣: {len(mapped_faults)}")
    print(f"  鏈槧灏勬晠闅滅偣: {len(unmapped_faults)}")
    if unmapped_faults:
        print(f"    鏈槧灏勭殑鏁呴殰鐐? {list(unmapped_faults)}")

def analyze_testpoint_rules():
    """鍒嗘瀽娴嬬偣瑙勫垯闂"""
    print("\n=== 鍒嗘瀽娴嬬偣瑙勫垯闂 ===")
    
    # 1. 鑾峰彇MSFG瀹氫箟
    cmg = PHM.objects.filter(cmg_id='01').first()
    if not cmg:
        print("鉂?鎵句笉鍒癈MG 01")
        return
    
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    if not msfg:
        print("鉂?鎵句笉鍒版椿璺冪殑MSFG瀹氫箟")
        return
    
    # 2. 鑾峰彇娴嬭瘯鏁版嵁
    latest_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    if not latest_data:
        print("鉂?鎵句笉鍒版祴璇曟暟鎹?)
        return
    
    print(f"鉁?浣跨敤鏁版嵁鐐? {latest_data.timestamp}")
    
    # 3. 鑾峰彇娴嬬偣瑙勫垯
    rules = TestPointRule.objects.filter(msfg_definition=msfg, is_online=True)
    print(f"馃搵 娴嬬偣瑙勫垯鏁伴噺: {rules.count()}")
    
    # 4. 鍒嗘瀽瑙勫垯鎵ц
    scoring_service = TestPointScoringService()
    
    print(f"\n馃攳 瑙勫垯鎵ц鍒嗘瀽:")
    for rule in rules:
        print(f"\n瑙勫垯: {rule.test_name}")
        print(f"  琛ㄨ揪寮? {rule.rule_expression}")
        print(f"  鏉冮噸: {rule.weight}")
        
        try:
            # 鎵ц瑙勫垯
            result = scoring_service._evaluate_rule_expression(rule.rule_expression, latest_data)
            print(f"  鎵ц缁撴灉: {result}")
            
            # 妫€鏌ユ暟鎹彲鐢ㄦ€?
            data = latest_data.data or {}
            if hasattr(latest_data, 'raw_parameters') and latest_data.raw_parameters:
                data.update(latest_data.raw_parameters)
            
            # 鍒嗘瀽琛ㄨ揪寮忎腑鐨勫弬鏁?
            import re
            param_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
            params_in_rule = re.findall(param_pattern, rule.rule_expression)
            
            # 杩囨护鎺夊嚱鏁板悕鍜屽叧閿瓧
            function_names = {'level', 'ma_diff', 'rollstd', 'adiff', 'mean', 'var', 'std', 
                            'wmin', 'wmax', 'delta', 'slope', 'pct_change', 'between', 'max', 'min', 'abs'}
            data_params = [p for p in params_in_rule if p not in function_names and p not in data]
            
            if data_params:
                print(f"  缂哄け鏁版嵁鍙傛暟: {data_params}")
            else:
                print(f"  鉁?鎵€鏈夋暟鎹弬鏁板彲鐢?)
                
        except Exception as e:
            print(f"  鉂?鎵ц澶辫触: {e}")
    
    # 5. 娴嬭瘯瀹屾暣璇勫垎
    print(f"\n馃搳 瀹屾暣娴嬬偣璇勫垎娴嬭瘯:")
    test_scores = scoring_service.calculate_test_scores(latest_data, msfg)
    
    print(f"娴嬬偣璇勫垎缁撴灉:")
    for test_name, score in test_scores.items():
        print(f"  {test_name}: {score:.3f}")
    
    # 6. 鍒嗘瀽寮傚父鍒嗘暟
    print(f"\n馃攳 寮傚父鍒嗘暟鍒嗘瀽:")
    high_scores = [(name, score) for name, score in test_scores.items() if score > 0.8]
    low_scores = [(name, score) for name, score in test_scores.items() if score < 0.1]
    
    if high_scores:
        print(f"  楂樺垎娴嬬偣 (>0.8):")
        for name, score in high_scores:
            print(f"    {name}: {score:.3f}")
    
    if low_scores:
        print(f"  浣庡垎娴嬬偣 (<0.1):")
        for name, score in low_scores:
            print(f"    {name}: {score:.3f}")

def analyze_data_availability():
    """鍒嗘瀽鏁版嵁鍙敤鎬?""
    print("\n=== 鍒嗘瀽鏁版嵁鍙敤鎬?===")
    
    # 1. 鑾峰彇娴嬭瘯鏁版嵁
    cmg = PHM.objects.filter(cmg_id='01').first()
    if not cmg:
        print("鉂?鎵句笉鍒癈MG 01")
        return
    
    latest_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    if not latest_data:
        print("鉂?鎵句笉鍒版祴璇曟暟鎹?)
        return
    
    print(f"鉁?浣跨敤鏁版嵁鐐? {latest_data.timestamp}")
    
    # 2. 鍒嗘瀽鏁版嵁鍐呭
    data = latest_data.data or {}
    if hasattr(latest_data, 'raw_parameters') and latest_data.raw_parameters:
        data.update(latest_data.raw_parameters)
    
    print(f"馃搳 鏁版嵁鍙傛暟缁熻:")
    print(f"  鎬诲弬鏁版暟閲? {len(data)}")
    
    # 3. 鍒嗘瀽鏁板€煎瀷鍙傛暟
    numeric_params = []
    non_numeric_params = []
    
    for key, value in data.items():
        try:
            float_value = float(value)
            if not np.isnan(float_value) and not np.isinf(float_value):
                numeric_params.append((key, float_value))
            else:
                non_numeric_params.append(key)
        except (ValueError, TypeError):
            non_numeric_params.append(key)
    
    print(f"  鏁板€煎瀷鍙傛暟: {len(numeric_params)} 涓?)
    print(f"  闈炴暟鍊煎瀷鍙傛暟: {len(non_numeric_params)} 涓?)
    
    # 4. 鏄剧ず鏁板€煎瀷鍙傛暟
    print(f"\n馃搵 鏁板€煎瀷鍙傛暟鍒楄〃:")
    for i, (key, value) in enumerate(numeric_params[:20]):  # 鍙樉绀哄墠20涓?
        print(f"  {i+1:2d}. {key}: {value}")
    if len(numeric_params) > 20:
        print(f"  ... 杩樻湁 {len(numeric_params) - 20} 涓弬鏁?)
    
    # 5. 鏄剧ず闈炴暟鍊煎瀷鍙傛暟
    if non_numeric_params:
        print(f"\n馃搵 闈炴暟鍊煎瀷鍙傛暟鍒楄〃:")
        for i, key in enumerate(non_numeric_params[:10]):  # 鍙樉绀哄墠10涓?
            print(f"  {i+1:2d}. {key}: {data[key]}")
        if len(non_numeric_params) > 10:
            print(f"  ... 杩樻湁 {len(non_numeric_params) - 10} 涓弬鏁?)

def main():
    """涓诲嚱鏁?""
    print("馃殌 寮€濮嬭皟璇昅SFG D鐭╅樀鍜屾祴鐐硅鍒欓棶棰?..")
    
    try:
        # 1. 鍒嗘瀽D鐭╅樀鏋勫缓
        analyze_d_matrix_construction()
        
        # 2. 鍒嗘瀽娴嬬偣瑙勫垯
        analyze_testpoint_rules()
        
        # 3. 鍒嗘瀽鏁版嵁鍙敤鎬?
        analyze_data_availability()
        
        print("\n鉁?璋冭瘯瀹屾垚!")
        
    except Exception as e:
        print(f"鉂?璋冭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

