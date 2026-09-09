#!/usr/bin/env python
"""
娴嬭瘯姝ｇ‘鏍煎紡鐨勮鍒欒〃杈惧紡
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.services.testpoint_scoring import TestPointScoringService
from data_management.models import PHMData, PHMModel
from msfg_analysis.models import MSFGDefinition

def test_correct_rules():
    print("=" * 60)
    print("娴嬭瘯姝ｇ‘鏍煎紡鐨勮鍒欒〃杈惧紡")
    print("=" * 60)
    
    # 娴嬭瘯鏁版嵁锛堟潵鑷敤鎴锋彁渚涚殑瀹為檯鏁版嵁锛?
    test_data = {
        '婧愮爜': '4AAA AB00 04F7 CB08 BA41 1000 565E 6A6D 3F57 018D 0800 07FB 4646 0088 0000 0000 0000 0000 0000 0000 02B8 ',
        '缂栧彿': 0.0,
        '甯ц鏁?: 2.0,
        '鑷瀛?: 1000.0,
        ' +5V閬ユ祴': 3.671875,
        ' +12V閬ユ祴': 3.359375,
        ' +45V閬ユ祴': 4.140625,
        ' 100V閬ユ祴': 4.257813,
        'OSTM_Frame0': 0.0,
        'OSTM_Frame1': 0.0,
        '浣庨€熶綅缃?: 98.184986,
        '浣庨€熷３娓?: 2.460938,
        '浣庨€熻浆閫?: 3.493084,
        '楂橀€熻浆閫?: 7000.000477,
        '浣庨€烝鐩哥數娴?: 0.0,
        '浣庨€烠鐩哥數娴?: -0.068359,
        '瀹氳閿佸畾绮惧害': 3.23702,
        '楂橀€熺數鏈虹數鍘?: 3.398438,
        '楂橀€熺數鏈虹數娴?: 0.880068,
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
    
    # 姝ｇ‘鏍煎紡鐨勬祴璇曡鍒欙紙鍩轰簬YAML鏂囦欢锛?
    test_rules = [
        {
            'name': '+12V閬ユ祴',
            'expression': 'level("+12V閬ユ祴", 3.35938, 0) > 3.0',
            'description': '娴嬭瘯+12V閬ユ祴鐨刲evel鍑芥暟'
        },
        {
            'name': '楂橀€熺數鏈虹數娴?,
            'expression': 'level("楂橀€熺數鏈虹數娴?, 0.862334, 0.031035) > 3.0',
            'description': '娴嬭瘯楂橀€熺數鏈虹數娴佺殑绠€鍗昹evel鍑芥暟'
        },
        {
            'name': '楂橀€熻浆閫?,
            'expression': 'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0',
            'description': '娴嬭瘯楂橀€熻浆閫熺殑level鍑芥暟'
        },
        {
            'name': '浣庨€熶綅缃?,
            'expression': 'level("浣庨€熶綅缃?, 96.9303, 6.93993) > 3.0',
            'description': '娴嬭瘯浣庨€熶綅缃殑level鍑芥暟'
        }
    ]
    
    scoring_service = TestPointScoringService()
    
    for i, rule in enumerate(test_rules, 1):
        print(f"\n--- 娴嬭瘯瑙勫垯 {i}: {rule['name']} ---")
        print(f"琛ㄨ揪寮? {rule['expression']}")
        print(f"鎻忚堪: {rule['description']}")
        
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
                actual_key = similar_keys[0]
                param_value = test_data[actual_key]
                print(f"浣跨敤鍙傛暟: {actual_key} = {param_value}")
            else:
                print(f"鈿狅笍  鍙傛暟 '{param_name}' 涓嶅瓨鍦?)
                continue
        
        # 鎵嬪姩璁＄畻level鍑芥暟
        if 'level(' in rule['expression']:
            import re
            level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', rule['expression'])
            for param_name, median_str, mad_str in level_matches:
                print(f"level鍑芥暟鍒嗘瀽:")
                print(f"  鍙傛暟鍚? {param_name}")
                print(f"  涓綅鏁? {median_str}")
                print(f"  MAD: {mad_str}")
                
                # 鏌ユ壘瀹為檯鍙傛暟鍊?
                actual_value = None
                if param_name in test_data:
                    actual_value = test_data[param_name]
                else:
                    # 鏌ユ壘鐩镐技鍙傛暟
                    for key in test_data.keys():
                        if param_name.strip() == key.strip():
                            actual_value = test_data[key]
                            print(f"  浣跨敤鐩镐技鍙傛暟: {key}")
                            break
                
                if actual_value is not None:
                    try:
                        x = float(actual_value)
                        median = float(median_str)
                        mad = float(mad_str)
                        mad_safe = max(abs(mad), 1e-9)
                        level_result = abs(x - median) / mad_safe
                        
                        print(f"  褰撳墠鍊? {x}")
                        print(f"  璁＄畻: abs({x} - {median}) / {mad_safe} = {level_result:.6f}")
                        print(f"  level > 3.0: {level_result > 3.0}")
                        
                        # 棰勬湡缁撴灉
                        expected_score = 1.0 if level_result > 3.0 else 0.0
                        print(f"  棰勬湡璇勫垎: {expected_score}")
                        
                    except Exception as e:
                        print(f"  璁＄畻閿欒: {e}")
                else:
                    print(f"  鏃犳硶鎵惧埌鍙傛暟鍊?)
        
        # 娴嬭瘯瀹屾暣琛ㄨ揪寮忔墽琛?
        try:
            # 鍒涘缓瀹夊叏鎵ц鐜
            safe_globals = {
                '__builtins__': {},
                'abs': abs,
                'max': max,
                'min': min,
            }
            
            # 娣诲姞level鍑芥暟
            def test_level(param_name, median, mad):
                # 鏌ユ壘鍙傛暟鍊?
                actual_value = None
                if param_name in test_data:
                    actual_value = test_data[param_name]
                else:
                    for key in test_data.keys():
                        if param_name.strip() == key.strip():
                            actual_value = test_data[key]
                            break
                
                if actual_value is not None:
                    x = float(actual_value)
                    mad_safe = max(abs(mad), 1e-9)
                    return abs(x - median) / mad_safe
                return 0.0
            
            safe_globals['level'] = test_level
            safe_locals = dict(test_data)
            
            result = eval(rule['expression'], safe_globals, safe_locals)
            print(f"鉁?琛ㄨ揪寮忔墽琛岀粨鏋? {result} (绫诲瀷: {type(result)})")
            
        except Exception as e:
            print(f"鉁?琛ㄨ揪寮忔墽琛屽け璐? {e}")
    
    print(f"\n{'='*60}")
    print("娴嬭瘯瀹屾垚")

if __name__ == "__main__":
    test_correct_rules()

