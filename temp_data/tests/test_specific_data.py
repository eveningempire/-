#!/usr/bin/env python
"""
娴嬭瘯鐗瑰畾鏁版嵁鐐圭殑璇勫垎
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.services.testpoint_scoring import TestPointScoringService

def test_specific_data():
    print("=" * 60)
    print("娴嬭瘯鐗瑰畾鏁版嵁鐐圭殑璇勫垎")
    print("=" * 60)
    
    # 娴嬭瘯鏁版嵁
    test_data = {
        '婧愮爜': '4AAA 9C00 04ED 5008 B069 1000 565E 6A6D 3F57 018B 0800 07FB 4646 0088 0000 0000 0000 0000 0000 0000 0032 ',
        '缂栧彿': 0.0,
        '甯ц鏁?: 0.0,
        '鑷瀛?: 1000.0,
        ' +5V閬ユ祴': 3.671875,
        ' +12V閬ユ祴': 3.359375,
        ' +45V閬ユ祴': 4.140625,
        ' 100V閬ユ祴': 4.257813,
        'OSTM_Frame0': 0.0,
        'OSTM_Frame1': 0.0,
        '浣庨€熶綅缃?: 97.752399,
        '浣庨€熷３娓?: 2.460938,
        '浣庨€熻浆閫?: 3.464298,
        '楂橀€熻浆閫?: 6999.979019,
        '浣庨€烝鐩哥數娴?: 0.0,
        '浣庨€烠鐩哥數娴?: -0.068359,
        '瀹氳閿佸畾绮惧害': 3.19548,
        '楂橀€熺數鏈虹數鍘?: 3.398438,
        '楂橀€熺數鏈虹數娴?: 0.875635,
        '楂橀€熷浐绱х杞存俯': 2.734375,
        '楂橀€熸粦鍔ㄧ杞存俯': 2.734375,
        '褰撳墠浣嶇疆閿佸畾绮惧害': '-',
        '楂橀€熻浆閫熸帶鍒剁簿搴?: 6e-05,
        '浣庨€熻閫熷害鎺у埗绮惧害': '-',
        '楂橀€熷浐绱х杞存俯娓╁害': 3.06,
        '楂橀€熸粦鍔ㄧ杞存俯娓╁害': 3.06,
        '楂橀€熻浆閫熸帶鍒剁ǔ瀹氬害': 0.0011,
        '浣庨€熻閫熷害鎺у埗绋冲畾搴?: '-'
    }
    
    print(f"鏁版嵁鐐瑰寘鍚?{len(test_data)} 涓弬鏁?)
    
    # 娴嬭瘯瑙勫垯琛ㄨ揪寮?
    test_rules = [
        {
            'name': '+12V閬ユ祴',
            'expression': 'level("+12V閬ユ祴", 3.35938, 0) > 3.0',
            'description': '娴嬭瘯+12V閬ユ祴鐨刲evel鍑芥暟'
        },
        {
            'name': '楂橀€熺數鏈虹數娴?,
            'expression': '( level("楂橀€熺數鏈虹數娴?, 0.862334, 0.031035) > 3.0 ) and ( (ma_diff("楂橀€熺數鏈虹數娴?, 60) - 0.000207828) / max(0.000138547, 1e-9) > 3.0 )',
            'description': '娴嬭瘯楂橀€熺數鏈虹數娴佺殑澶嶅悎琛ㄨ揪寮?
        },
        {
            'name': '楂橀€熻浆閫?,
            'expression': 'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0',
            'description': '娴嬭瘯楂橀€熻浆閫熺殑level鍑芥暟'
        }
    ]
    
    scoring_service = TestPointScoringService()
    
    print("\n" + "=" * 40)
    print("閫愪釜娴嬭瘯瑙勫垯琛ㄨ揪寮?)
    print("=" * 40)
    
    for i, rule in enumerate(test_rules, 1):
        print(f"\n瑙勫垯 {i}: {rule['name']}")
        print(f"鎻忚堪: {rule['description']}")
        print(f"鍘熷琛ㄨ揪寮? {repr(rule['expression'])}")
        
        # 妫€鏌ュ弬鏁版槸鍚﹀瓨鍦?
        param_name = rule['name']
        if param_name in test_data:
            param_value = test_data[param_name]
            print(f"鍙傛暟鍊? {param_name} = {param_value}")
        else:
            # 鏌ユ壘鐩镐技鍙傛暟鍚嶏紙澶勭悊绌烘牸闂锛?
            similar_keys = []
            for key in test_data.keys():
                if param_name.strip() == key.strip():
                    similar_keys.append(key)
                elif param_name in key or key in param_name:
                    similar_keys.append(key)
            
            if similar_keys:
                print(f"鎵惧埌鐩镐技鍙傛暟: {similar_keys}")
                # 浣跨敤绗竴涓浉浼煎弬鏁?
                actual_key = similar_keys[0]
                param_value = test_data[actual_key]
                print(f"浣跨敤鍙傛暟: {actual_key} = {param_value}")
                
                # 鏇存柊琛ㄨ揪寮忎腑鐨勫弬鏁板悕
                updated_expr = rule['expression'].replace(f'"{param_name}"', f'"{actual_key}"')
                print(f"鏇存柊琛ㄨ揪寮? {repr(updated_expr)}")
                rule['expression'] = updated_expr
            else:
                print(f"鈿狅笍  鍙傛暟 '{param_name}' 涓嶅瓨鍦?)
                continue
        
        # 棰勫鐞嗚〃杈惧紡
        processed_expr = scoring_service._preprocess_expression(rule['expression'], test_data)
        print(f"澶勭悊鍚庤〃杈惧紡: {repr(processed_expr)}")
        
        # 鎵嬪姩娴嬭瘯level鍑芥暟
        if 'level(' in rule['expression']:
            import re
            level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', rule['expression'])
            for param_name, median_str, mad_str in level_matches:
                if param_name in test_data:
                    try:
                        param_val = float(test_data[param_name])
                        median_val = float(median_str)
                        mad_val = float(mad_str)
                        mad_safe = max(abs(mad_val), 1e-9)
                        level_result = abs(param_val - median_val) / mad_safe
                        
                        print(f"鎵嬪姩璁＄畻level鍑芥暟:")
                        print(f"  鍙傛暟鍊? {param_val}")
                        print(f"  涓綅鏁? {median_val}")
                        print(f"  MAD: {mad_val} -> {mad_safe}")
                        print(f"  level缁撴灉: abs({param_val} - {median_val}) / {mad_safe} = {level_result}")
                        print(f"  level > 3.0: {level_result > 3.0}")
                        
                    except Exception as e:
                        print(f"鎵嬪姩璁＄畻level澶辫触: {e}")
        
        # 鎵ц瑙勫垯
        try:
            score = scoring_service._evaluate_single_rule(rule['expression'], test_data)
            print(f"鉁?璇勫垎缁撴灉: {score}")
            
            if score == 0.0:
                print("  鍒嗘瀽: 琛ㄨ揪寮忕粨鏋滀负False鎴?")
            elif score > 0.0:
                print("  鍒嗘瀽: 琛ㄨ揪寮忕粨鏋滀负True鎴栨鏁?)
                
        except Exception as e:
            print(f"鉁?瑙勫垯鎵ц澶辫触: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 40)
    print("娴嬭瘯鎵€鏈塎SFG涓撶敤鍑芥暟")
    print("=" * 40)
    
    # 娴嬭瘯鍚勪釜鍑芥暟
    test_functions = [
        ('level("+12V閬ユ祴", 3.35938, 0)', '+12V閬ユ祴鐨刲evel鍑芥暟'),
        ('ma_diff("楂橀€熺數鏈虹數娴?, 60)', '楂橀€熺數鏈虹數娴佺殑ma_diff鍑芥暟'),
        ('rollstd("楂橀€熺數鏈虹數娴?, 120)', '楂橀€熺數鏈虹數娴佺殑rollstd鍑芥暟'),
        ('mean("楂橀€熻浆閫?)', '楂橀€熻浆閫熺殑mean鍑芥暟'),
    ]
    
    for func_expr, desc in test_functions:
        print(f"\n娴嬭瘯: {desc}")
        print(f"琛ㄨ揪寮? {func_expr}")
        
        try:
            # 鍒涘缓涓€涓畝鍗曠殑鎵ц鐜
            safe_globals = {
                '__builtins__': {},
                'abs': abs,
                'max': max,
                'min': min,
                'float': float,
                'int': int,
                'level': scoring_service._level_function,
                'ma_diff': scoring_service._ma_diff_function,
                'rollstd': scoring_service._rollstd_function,
                'mean': scoring_service._mean_function,
            }
            
            safe_locals = dict(test_data)
            result = eval(func_expr, safe_globals, safe_locals)
            print(f"鉁?缁撴灉: {result}")
            
        except Exception as e:
            print(f"鉁?鎵ц澶辫触: {e}")

if __name__ == "__main__":
    test_specific_data()

