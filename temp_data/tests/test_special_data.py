#!/usr/bin/env python
"""
浣跨敤鐗规畩鏁版嵁娴嬭瘯MSFG璇勫垎绯荤粺
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.services.testpoint_scoring import TestPointScoringService
from data_management.models import PHMData
from msfg_analysis.models import MSFGDefinition

# 鍒涘缓妯℃嫙鏁版嵁鐐?
class MockPHMData:
    def __init__(self, raw_parameters):
        self.raw_parameters = raw_parameters
        self.data = raw_parameters

def test_special_scoring():
    print("=" * 60)
    print("浣跨敤鐗规畩鏁版嵁娴嬭瘯MSFG璇勫垎绯荤粺")
    print("=" * 60)
    
    # 鐗规畩娴嬭瘯鏁版嵁 - 璁捐涓€浜涗細瑙﹀彂寮傚父鐨勫€?
    test_data = {
        '+12V閬ユ祴': 5.0,  # 杩滅姝ｅ父鍊?.35938锛屽簲璇ヨЕ鍙戝紓甯?
        '楂橀€熺數鏈虹數娴?: 1.5,  # 杩滅姝ｅ父鍊?.862334锛屽簲璇ヨЕ鍙戝紓甯? 
        '楂橀€熻浆閫?: 6950.0,  # 杩滅姝ｅ父鍊?000锛屽簲璇ヨЕ鍙戝紓甯?
        '浣庨€熶綅缃?: 120.0,  # 杩滅姝ｅ父鍊?6.9303锛屽簲璇ヨЕ鍙戝紓甯?
        '瀹氳閿佸畾绮惧害': 8.0,  # 杩滅姝ｅ父鍊?.42155锛屽簲璇ヨЕ鍙戝紓甯?
    }
    
    # 娴嬭瘯瑙勫垯琛ㄨ揪寮忥紙甯﹁浆涔夊瓧绗︼紝妯℃嫙鏁版嵁搴撳瓨鍌ㄦ牸寮忥級
    test_rules = [
        {
            'name': '+12V閬ユ祴',
            'expression': 'level(\\"+12V閬ユ祴\\", 3.35938, 0) > 3.0',
            'description': '娴嬭瘯+12V閬ユ祴寮傚父妫€娴?
        },
        {
            'name': '楂橀€熺數鏈虹數娴?,
            'expression': 'level(\\"楂橀€熺數鏈虹數娴乗\", 0.862334, 0.031035) > 3.0',
            'description': '娴嬭瘯楂橀€熺數鏈虹數娴佸紓甯告娴?
        },
        {
            'name': '楂橀€熻浆閫?,
            'expression': 'level(\\"楂橀€熻浆閫焅\", 7000, 0.020027) > 3.0',
            'description': '娴嬭瘯楂橀€熻浆閫熷紓甯告娴?
        },
        {
            'name': '浣庨€熶綅缃?,
            'expression': 'level(\\"浣庨€熶綅缃甛\", 96.9303, 6.93993) > 3.0',
            'description': '娴嬭瘯浣庨€熶綅缃紓甯告娴?
        },
        {
            'name': '瀹氳閿佸畾绮惧害',
            'expression': '( (level(\\"瀹氳閿佸畾绮惧害\\", 2.42155, 2.37228) > 3.0) + ( (adiff(\\"瀹氳閿佸畾绮惧害\\", 2) - 0.05802) / max(0.05578, 1e-9) > 3.0 ) ) / 2',
            'description': '娴嬭瘯瀹氳閿佸畾绮惧害澶嶅悎瑙勫垯'
        }
    ]
    
    scoring_service = TestPointScoringService()
    mock_data_point = MockPHMData(test_data)
    
    print("娴嬭瘯鏁版嵁:")
    for name, value in test_data.items():
        print(f"  {name}: {value}")
    
    print(f"\n{'='*40}")
    print("瑙勫垯璇勫垎娴嬭瘯")
    print('='*40)
    
    for i, rule in enumerate(test_rules, 1):
        print(f"\n--- 瑙勫垯 {i}: {rule['name']} ---")
        print(f"鍘熷琛ㄨ揪寮? {repr(rule['expression'])}")
        print(f"鎻忚堪: {rule['description']}")
        
        # 娴嬭瘯棰勫鐞?
        processed = scoring_service._preprocess_expression(rule['expression'], test_data)
        print(f"澶勭悊鍚庤〃杈惧紡: {repr(processed)}")
        
        # 妫€鏌ヨ浆涔夋槸鍚﹁姝ｇ‘澶勭悊
        if '\\' in processed:
            print("鈿狅笍  浠嶇劧鍖呭惈杞箟瀛楃")
        else:
            print("鉁?杞箟瀛楃宸叉竻鐞?)
        
        # 鎵嬪姩璁＄畻level鍑芥暟鍊?
        if 'level(' in processed:
            import re
            level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', processed)
            for param_name, median_str, mad_str in level_matches:
                if param_name in test_data:
                    try:
                        x = float(test_data[param_name])
                        median = float(median_str)
                        mad = float(mad_str)
                        mad_safe = max(abs(mad), 1e-9)
                        level_result = abs(x - median) / mad_safe
                        
                        print(f"level鍑芥暟璁＄畻:")
                        print(f"  鍙傛暟: {param_name} = {x}")
                        print(f"  涓綅鏁? {median}")
                        print(f"  MAD: {mad} -> {mad_safe}")
                        print(f"  level鍊? abs({x} - {median}) / {mad_safe} = {level_result:.6f}")
                        print(f"  level > 3.0: {level_result > 3.0}")
                        
                        # 棰勬祴姒傜巼鍒嗘暟
                        if level_result <= 1.0:
                            expected_prob = 0.1
                        elif level_result <= 2.0:
                            expected_prob = 0.3
                        elif level_result <= 3.0:
                            expected_prob = 0.5
                        elif level_result <= 5.0:
                            expected_prob = 0.8
                        else:
                            expected_prob = 0.95
                        print(f"  棰勬湡姒傜巼鍒嗘暟: {expected_prob}")
                        
                    except Exception as e:
                        print(f"  璁＄畻閿欒: {e}")
        
        # 娴嬭瘯瀹為檯璇勫垎
        try:
            score = scoring_service._evaluate_rule_expression(rule['expression'], mock_data_point)
            print(f"鉁?瀹為檯璇勫垎缁撴灉: {score}")
            
            if score is not None and score > 0.0:
                print(f"  鎴愬姛妫€娴嬪埌寮傚父锛屾鐜囧垎鏁? {score:.3f}")
            elif score == 0.0:
                print(f"  鏈娴嬪埌寮傚父")
            else:
                print(f"  璇勫垎澶辫触")
                
        except Exception as e:
            print(f"鉁?璇勫垎澶辫触: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("娴嬭瘯瀹屾垚")
    
    # 鎬荤粨
    print("\n棰勬湡缁撴灉:")
    print("- +12V閬ユ祴: 搴旇妫€娴嬪埌楂樺紓甯?(5.0 vs 3.35938)")
    print("- 楂橀€熺數鏈虹數娴? 搴旇妫€娴嬪埌楂樺紓甯?(1.5 vs 0.862334)")  
    print("- 楂橀€熻浆閫? 搴旇妫€娴嬪埌涓瓑寮傚父 (6950 vs 7000)")
    print("- 浣庨€熶綅缃? 搴旇妫€娴嬪埌涓瓑寮傚父 (120 vs 96.9303)")
    print("- 瀹氳閿佸畾绮惧害: 搴旇妫€娴嬪埌楂樺紓甯?(8.0 vs 2.42155)")

if __name__ == "__main__":
    test_special_scoring()

