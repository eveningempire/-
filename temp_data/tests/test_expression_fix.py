#!/usr/bin/env python
"""
娴嬭瘯琛ㄨ揪寮忎慨澶?
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import TestPointRule, MSFGDefinition
from data_management.models import PHMModel, PHMData
from msfg_analysis.services.testpoint_scoring import TestPointScoringService

def test_expression_processing():
    print("=" * 60)
    print("娴嬭瘯琛ㄨ揪寮忓鐞?)
    print("=" * 60)
    
    # 娴嬭瘯鏁版嵁
    test_data = {
        '+12V閬ユ祴': 3.359375,
        '楂橀€熺數鏈虹數娴?: 0.875635,
        '楂橀€熻浆閫?: 6999.979019,
    }
    
    # 娴嬭瘯琛ㄨ揪寮?
    test_expressions = [
        'level(\\"+12V閬ユ祴\\", 3.35938, 0) > 3.0',
        'level(\\"楂橀€熺數鏈虹數娴乗\", 0.862334, 0.031035) > 3.0',
        '( level(\\"楂橀€熺數鏈虹數娴乗\", 0.862334, 0.031035) > 3.0 ) and ( (ma_diff(\\"楂橀€熺數鏈虹數娴乗\", 60) - 0.000207828) / max(0.000138547, 1e-9) > 3.0 )'
    ]
    
    scoring_service = TestPointScoringService()
    
    for i, expr in enumerate(test_expressions, 1):
        print(f"\n--- 娴嬭瘯琛ㄨ揪寮?{i} ---")
        print(f"鍘熷: {repr(expr)}")
        
        # 娴嬭瘯棰勫鐞?
        processed = scoring_service._preprocess_expression(expr, test_data)
        print(f"澶勭悊鍚? {repr(processed)}")
        
        # 妫€鏌ユ槸鍚﹁繕鏈夎浆涔夊瓧绗?
        if '\\' in processed:
            print("鈿狅笍  浠嶇劧鍖呭惈杞箟瀛楃")
        else:
            print("鉁?杞箟瀛楃宸叉竻鐞?)
        
        # 鎵嬪姩娴嬭瘯level鍑芥暟璁＄畻
        if 'level(' in processed:
            import re
            level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', processed)
            for param_name, median_str, mad_str in level_matches:
                print(f"level鍑芥暟鍙傛暟: {param_name}, {median_str}, {mad_str}")
                if param_name in test_data:
                    try:
                        param_val = float(test_data[param_name])
                        median_val = float(median_str)
                        mad_val = float(mad_str)
                        mad_safe = max(abs(mad_val), 1e-9)
                        level_result = abs(param_val - median_val) / mad_safe
                        
                        print(f"  褰撳墠鍊? {param_val}")
                        print(f"  涓綅鏁? {median_val}")
                        print(f"  MAD: {mad_val} -> {mad_safe}")
                        print(f"  level缁撴灉: {level_result:.6f}")
                        print(f"  level > 3.0: {level_result > 3.0}")
                        
                    except Exception as e:
                        print(f"  璁＄畻閿欒: {e}")
                else:
                    print(f"  鍙傛暟 {param_name} 涓嶅瓨鍦?)
        
        # 灏濊瘯鎵嬪姩鎵ц绠€鍗曡〃杈惧紡
        if processed.count('level(') == 1 and processed.count('>') == 1 and 'and' not in processed.lower():
            try:
                # 鍒涘缓鎵ц鐜
                safe_globals = {
                    '__builtins__': {},
                    'abs': abs,
                    'max': max,
                    'min': min,
                }
                
                # 绠€鍖栫増level鍑芥暟
                def simple_level(param_name, median, mad):
                    if param_name in test_data:
                        x = float(test_data[param_name])
                        mad_safe = max(abs(mad), 1e-9)
                        return abs(x - median) / mad_safe
                    return 0.0
                
                safe_globals['level'] = simple_level
                safe_locals = dict(test_data)
                
                result = eval(processed, safe_globals, safe_locals)
                print(f"鎵嬪姩鎵ц缁撴灉: {result} (绫诲瀷: {type(result)})")
                
            except Exception as e:
                print(f"鎵嬪姩鎵ц澶辫触: {e}")

if __name__ == "__main__":
    test_expression_processing()

