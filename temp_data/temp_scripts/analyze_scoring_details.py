#!/usr/bin/env python
"""
璇︾粏鍒嗘瀽娴嬬偣璇勫垎璁＄畻杩囩▼
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

def analyze_scoring_details():
    """璇︾粏鍒嗘瀽娴嬬偣璇勫垎璁＄畻杩囩▼"""
    print("=== 璇︾粏鍒嗘瀽娴嬬偣璇勫垎璁＄畻杩囩▼ ===")
    
    # 鑾峰彇鏁版嵁
    cmg = PHM.objects.first()
    data_point = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    
    print(f"PHM: {cmg.cmg_model}")
    print(f"鏁版嵁鐐? {data_point.timestamp}")
    print(f"MSFG: {msfg.name}")
    
    # 鑾峰彇娴嬭瘯鏁版嵁
    test_data = data_point.data or {}
    if not test_data and hasattr(data_point, 'raw_parameters') and data_point.raw_parameters:
        test_data = data_point.raw_parameters
    
    print(f"\n馃搳 娴嬭瘯鏁版嵁:")
    for key, value in test_data.items():
        print(f"  {key}: {value}")
    
    # 鑾峰彇娴嬭瘯鐐硅鍒?
    testpoint_rules = TestPointRule.objects.filter(msfg_definition=msfg)
    print(f"\n馃搵 娴嬬偣瑙勫垯鏁伴噺: {len(testpoint_rules)}")
    
    # 鍒涘缓娴嬬偣璇勫垎鏈嶅姟
    scoring_service = TestPointScoringService()
    
    # 閫愪釜鍒嗘瀽瑙勫垯
    for i, rule in enumerate(testpoint_rules):
        print(f"\n馃攳 瑙勫垯 {i+1}: {rule.test_name}")
        print(f"瑙勫垯琛ㄨ揪寮? {rule.rule_expression}")
        
        # 鏌ユ壘瀵瑰簲鐨勬暟鎹?
        test_value = None
        for key, value in test_data.items():
            if key.strip() == rule.test_name.strip():
                test_value = value
                print(f"鉁?鎵惧埌鍖归厤鏁版嵁: {key} = {value}")
                break
        
        if test_value is None:
            print(f"鉂?鏈壘鍒板尮閰嶆暟鎹?)
            # 灏濊瘯妯＄硦鍖归厤
            for key, value in test_data.items():
                if rule.test_name.strip() in key.strip() or key.strip() in rule.test_name.strip():
                    print(f"馃攳 妯＄硦鍖归厤: {key} = {value}")
                    test_value = value
                    break
        
        # 鎵嬪姩璁＄畻level鍑芥暟
        if 'level(' in rule.rule_expression:
            import re
            level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', rule.rule_expression)
            for param_name, median_str, mad_str in level_matches:
                print(f"\n馃搳 Level鍑芥暟鍒嗘瀽:")
                print(f"  鍙傛暟鍚? {param_name}")
                print(f"  涓綅鏁? {median_str}")
                print(f"  MAD: {mad_str}")
                
                # 鏌ユ壘瀹為檯鍙傛暟鍊?
                actual_value = None
                for key, value in test_data.items():
                    if key.strip() == param_name.strip():
                        actual_value = value
                        print(f"  瀹為檯鍊? {value}")
                        break
                
                if actual_value is not None:
                    try:
                        x = float(actual_value)
                        median = float(median_str)
                        mad = float(mad_str)
                        mad_safe = max(abs(mad), 1e-9)
                        level_result = abs(x - median) / mad_safe
                        print(f"  Level璁＄畻缁撴灉: |{x} - {median}| / {mad_safe} = {level_result}")
                        print(f"  鏄惁澶т簬3.0: {level_result > 3.0}")
                    except (ValueError, TypeError) as e:
                        print(f"  鉂?璁＄畻澶辫触: {e}")
                else:
                    print(f"  鉂?鏈壘鍒板弬鏁板€?)
        
        # 鎵ц瑙勫垯琛ㄨ揪寮?
        try:
            # 璁剧疆褰撳墠鏁版嵁渚汳SFG鍑芥暟浣跨敤
            scoring_service._current_data = test_data
            scoring_service._current_data_point = data_point
            
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
            
            # MSFG涓撶敤鍑芥暟
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
            
            # 娣诲姞鏁版嵁鍒版墽琛岀幆澧?
            safe_locals = dict(test_data)
            
            # 鎵ц瑙勫垯琛ㄨ揪寮?
            result = eval(rule.rule_expression, safe_globals, safe_locals)
            print(f"瑙勫垯鎵ц缁撴灉: {result}")
            
            # 璁＄畻姒傜巼
            if isinstance(result, bool):
                probability = 1.0 if result else 0.0
            elif isinstance(result, (int, float)):
                if result > 0:
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
            print(f"鉂?瑙勫垯鎵ц澶辫触: {e}")

if __name__ == "__main__":
    analyze_scoring_details()

