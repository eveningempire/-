#!/usr/bin/env python
"""
璋冭瘯娴嬬偣瑙勫垯瑙ｆ瀽闂
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

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_testpoint_rules():
    """璋冭瘯娴嬬偣瑙勫垯瑙ｆ瀽"""
    print("=== 璋冭瘯娴嬬偣瑙勫垯瑙ｆ瀽 ===")
    
    # 鑾峰彇鏁版嵁
    cmg = PHM.objects.first()
    data_point = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    
    print(f"PHM: {cmg.cmg_model}")
    print(f"鏁版嵁鐐? {data_point.timestamp}")
    print(f"MSFG: {msfg.name}")
    
    # 鑾峰彇娴嬭瘯鐐硅鍒?
    testpoint_rules = TestPointRule.objects.filter(msfg_definition=msfg)
    print(f"\n馃搳 娴嬭瘯鐐硅鍒欐暟閲? {len(testpoint_rules)}")
    
    # 鑾峰彇娴嬭瘯鏁版嵁
    test_data = data_point.results if hasattr(data_point, 'results') else {}
    
    # 鍒涘缓娴嬬偣璇勫垎鏈嶅姟
    scoring_service = TestPointScoringService()
    
    # 閫愪釜鍒嗘瀽瑙勫垯
    for i, rule in enumerate(testpoint_rules):
        print(f"\n馃攳 瑙勫垯 {i+1}: {rule.test_name}")
        print(f"瑙勫垯琛ㄨ揪寮? {rule.rule_expression}")
        print(f"鏉冮噸: {rule.weight}")
        print(f"瑙勫垯ID: {rule.rule_id}")
        
        # 鑾峰彇娴嬭瘯鐐圭殑瀹為檯鏁版嵁
        test_value = test_data.get(rule.test_name, None)
        print(f"瀹為檯鏁版嵁: {test_value}")
        
        # 鎵嬪姩瑙ｆ瀽瑙勫垯琛ㄨ揪寮?
        try:
            # 鍒涘缓瀹夊叏鐨勬墽琛岀幆澧?
            safe_globals = {
                '__builtins__': {},
                'abs': abs,
                'min': min,
                'max': max,
                'round': round,
                'float': float,
                'int': int,
                'len': len,
            }
            
            # 鏁板鍑芥暟
            import math
            import numpy as np
            safe_globals.update({
                'sqrt': math.sqrt,
                'log': math.log,
                'exp': math.exp,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'pi': math.pi,
                'e': math.e,
            })
            
            # 浣跨敤鎮ㄥ凡缁忓疄鐜扮殑MSFG涓撶敤鍑芥暟
            safe_globals.update({
                'level': scoring_service._level_function,
                'ma_diff': scoring_service._ma_diff_function,
                'rollstd': scoring_service._rollstd_function,
                'adiff': scoring_service._adiff_function,
                'mean': scoring_service._mean_function,
                'var': scoring_service._var_function,
                'std': scoring_service._std_function,
                'wmin': scoring_service._wmin_function,
                'wmax': scoring_service._wmax_function,
                'delta': scoring_service._delta_function,
                'slope': scoring_service._slope_function,
                'pct_change': scoring_service._pct_change_function,
                'between': scoring_service._between_function,
            })
            
            # 璁剧疆褰撳墠鏁版嵁渚汳SFG鍑芥暟浣跨敤
            scoring_service._current_data = test_data
            scoring_service._current_data_point = data_point
            
            # 娣诲姞鏁版嵁鍒版墽琛岀幆澧?
            safe_locals = dict(test_data)
            
            # 鎵ц瑙勫垯琛ㄨ揪寮?
            result = eval(rule.rule_expression, safe_globals, safe_locals)
            print(f"瑙勫垯鎵ц缁撴灉: {result}")
            
            # 璁＄畻姒傜巼
            if isinstance(result, (int, float)):
                if result > 0:
                    # 鍩轰簬缁撴灉鍊艰绠楁鐜?
                    if result <= 1.0:
                        probability = result
                    elif result <= 2.0:
                        probability = 0.3
                    elif result <= 3.0:
                        probability = 0.5
                    elif result <= 5.0:
                        probability = 0.8
                    else:
                        probability = 0.95
                else:
                    probability = 0.05
            else:
                probability = 0.2 if result else 0.05
            
            print(f"璁＄畻姒傜巼: {probability}")
            
        except Exception as e:
            print(f"鉂?瑙勫垯瑙ｆ瀽澶辫触: {e}")
            print(f"閿欒绫诲瀷: {type(e).__name__}")
            
            # 灏濊瘯鏇磋缁嗙殑閿欒鍒嗘瀽
            try:
                # 妫€鏌ヨ〃杈惧紡璇硶
                compile(rule.rule_expression, '<string>', 'eval')
                print("鉁?琛ㄨ揪寮忚娉曟纭?)
            except SyntaxError as se:
                print(f"鉂?璇硶閿欒: {se}")
            
            # 妫€鏌ュ彉閲忓悕
            import re
            variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', rule.rule_expression)
            print(f"琛ㄨ揪寮忎腑鐨勫彉閲? {variables}")
            
            # 妫€鏌ュ嚱鏁拌皟鐢?
            functions = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(', rule.rule_expression)
            print(f"琛ㄨ揪寮忎腑鐨勫嚱鏁拌皟鐢? {functions}")

def analyze_rule_patterns():
    """鍒嗘瀽瑙勫垯妯″紡"""
    print("\n=== 鍒嗘瀽瑙勫垯妯″紡 ===")
    
    cmg = PHM.objects.first()
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    testpoint_rules = TestPointRule.objects.filter(msfg_definition=msfg)
    
    # 缁熻瑙勫垯妯″紡
    patterns = {}
    for rule in testpoint_rules:
        pattern = rule.rule_expression.strip()
        if pattern not in patterns:
            patterns[pattern] = []
        patterns[pattern].append(rule.test_name)
    
    print(f"馃搳 瑙勫垯妯″紡缁熻:")
    for pattern, testpoints in patterns.items():
        print(f"\n妯″紡: {pattern}")
        print(f"浣跨敤璇ユā寮忕殑娴嬭瘯鐐? {', '.join(testpoints)}")
        print(f"浣跨敤娆℃暟: {len(testpoints)}")

if __name__ == "__main__":
    debug_testpoint_rules()
    analyze_rule_patterns()

