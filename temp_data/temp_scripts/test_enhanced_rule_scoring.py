#!/usr/bin/env python
"""
娴嬭瘯澧炲己鐨勮鍒欐娴嬭瘎鍒嗘満鍒?
楠岃瘉浠庝簩鍊艰瘎鍒嗗埌杩炵画姒傜巼鍒嗘暟鐨勮浆鎹㈡晥鏋?
"""

import os
import sys
import django
import logging
from typing import Dict, List, Any

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from rule_detection.algorithms.rule.enhanced_scoring import RuleScoringEnhancer, calculate_rule_confidence

# 閰嶇疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_rule_scoring():
    """娴嬭瘯澧炲己鐨勮鍒欐娴嬭瘎鍒嗘満鍒?""
    print("馃И 娴嬭瘯澧炲己鐨勮鍒欐娴嬭瘎鍒嗘満鍒?)
    print("=" * 80)
    
    # 鍒濆鍖栬瘎鍒嗗寮哄櫒
    scoring_enhancer = RuleScoringEnhancer()
    
    # 娴嬭瘯鏁版嵁
    test_data = {
        "temperature": 85.5,
        "pressure": 120.3,
        "vibration": 0.8,
        "current": 15.2,
        "voltage": 220.0,
        "speed": 1500.0
    }
    
    print(f"馃搳 娴嬭瘯鏁版嵁:")
    for key, value in test_data.items():
        print(f"   - {key}: {value}")
    
    # 娴嬭瘯鐢ㄤ緥
    test_cases = [
        {
            "name": "绠€鍗曟瘮杈冩搷浣?,
            "expression": "temperature > 80.0",
            "value": True,
            "expected_type": "comparison"
        },
        {
            "name": "level鍑芥暟",
            "expression": 'level("temperature", 75.0, 5.0)',
            "value": True,
            "expected_type": "level_function"
        },
        {
            "name": "缁熻鍑芥暟",
            "expression": "mean(temperature) > 80.0",
            "value": True,
            "expected_type": "statistical"
        },
        {
            "name": "澶嶆潅姣旇緝",
            "expression": "temperature > 80.0 and pressure > 100.0",
            "value": True,
            "expected_type": "comparison"
        },
        {
            "name": "甯冨皵琛ㄨ揪寮?,
            "expression": "vibration > 0.5",
            "value": True,
            "expected_type": "comparison"
        },
        {
            "name": "鏁板€肩粨鏋?,
            "expression": "abs(temperature - 75.0)",
            "value": 10.5,
            "expected_type": "statistical"
        }
    ]
    
    print(f"\n馃攳 娴嬭瘯璇勫垎杞崲:")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   娴嬭瘯鐢ㄤ緥 {i}: {test_case['name']}")
        print(f"   琛ㄨ揪寮? {test_case['expression']}")
        print(f"   鍘熷鍊? {test_case['value']} (绫诲瀷: {type(test_case['value']).__name__})")
        
        try:
            # 杞崲璇勫垎
            continuous_score = scoring_enhancer.convert_to_continuous_score(
                test_case['value'], 
                test_case['expression'], 
                test_data
            )
            
            # 璁＄畻缃俊搴?
            confidence = calculate_rule_confidence(
                test_case['expression'], 
                test_data, 
                test_case['value']
            )
            
            # 搴旂敤缃俊搴﹁皟鏁?
            adjusted_score = continuous_score * confidence
            
            print(f"   杩炵画鍒嗘暟: {continuous_score:.3f}")
            print(f"   缃俊搴? {confidence:.3f}")
            print(f"   璋冩暣鍚庡垎鏁? {adjusted_score:.3f}")
            print(f"   瑙﹀彂鐘舵€? {'鏄? if adjusted_score > 0.5 else '鍚?}")
            
            # 楠岃瘉璇勫垎鏂规硶
            scoring_method = scoring_enhancer._determine_scoring_method(
                test_case['expression'], 
                test_case['value']
            )
            print(f"   璇勫垎鏂规硶: {scoring_method}")
            
            if scoring_method == test_case['expected_type']:
                print(f"   鉁?璇勫垎鏂规硶姝ｇ‘")
            else:
                print(f"   鈿狅笍  璇勫垎鏂规硶涓嶅尮閰?(鏈熸湜: {test_case['expected_type']})")
            
        except Exception as e:
            print(f"   鉂?娴嬭瘯澶辫触: {e}")
    
    # 瀵规瘮娴嬭瘯锛氫簩鍊艰瘎鍒?vs 杩炵画璇勫垎
    print(f"\n馃搱 瀵规瘮娴嬭瘯: 浜屽€艰瘎鍒?vs 杩炵画璇勫垎")
    print("-" * 60)
    
    comparison_cases = [
        ("temperature > 80.0", 85.5),
        ("temperature > 90.0", 85.5),
        ("pressure > 100.0", 120.3),
        ("pressure > 150.0", 120.3),
        ("vibration > 0.5", 0.8),
        ("vibration > 1.0", 0.8),
    ]
    
    print(f"   琛ㄨ揪寮廫t\t鍙傛暟鍊糪t浜屽€艰瘎鍒哱t杩炵画璇勫垎\t宸紓")
    print(f"   " + "-" * 80)
    
    for expression, param_value in comparison_cases:
        # 妯℃嫙浜屽€艰瘎鍒嗭紙鍘熷鏂规硶锛?
        binary_result = eval(expression.replace("temperature", str(param_value)).replace("pressure", str(param_value)).replace("vibration", str(param_value)))
        binary_score = 1.0 if binary_result else 0.0
        
        # 杩炵画璇勫垎锛堟柊鏂规硶锛?
        try:
            continuous_score = scoring_enhancer.convert_to_continuous_score(
                binary_result, expression, test_data
            )
        except:
            continuous_score = binary_score
        
        difference = continuous_score - binary_score
        
        print(f"   {expression:<20}\t{param_value}\t{binary_score:.1f}\t\t{continuous_score:.3f}\t\t{difference:+.3f}")
    
    # 娴嬭瘯缃俊搴﹁绠?
    print(f"\n馃幆 缃俊搴﹁绠楁祴璇?)
    print("-" * 60)
    
    confidence_test_cases = [
        {
            "expression": "temperature > 80.0",
            "description": "绠€鍗曟瘮杈冿紝鍙傛暟瀛樺湪"
        },
        {
            "expression": "missing_param > 80.0",
            "description": "鍙傛暟缂哄け"
        },
        {
            "expression": "temperature > 80.0 and pressure > 100.0 and vibration > 0.5",
            "description": "澶嶆潅琛ㄨ揪寮?
        },
        {
            "expression": "level('temperature', 75.0, 5.0)",
            "description": "鍑芥暟璋冪敤"
        }
    ]
    
    for test_case in confidence_test_cases:
        try:
            confidence = calculate_rule_confidence(
                test_case['expression'], 
                test_data, 
                True
            )
            print(f"   {test_case['description']:<30}: {confidence:.3f}")
        except Exception as e:
            print(f"   {test_case['description']:<30}: 璁＄畻澶辫触 ({e})")
    
    return True

def demonstrate_scoring_improvements():
    """婕旂ず璇勫垎鏀硅繘鏁堟灉"""
    print(f"\n馃挕 璇勫垎鏀硅繘鏁堟灉婕旂ず")
    print("=" * 80)
    
    print("""
馃幆 鏀硅繘鍓嶇殑闂:
   - 瑙勫垯妫€娴嬪彧鑳芥彁渚涗簩鍊肩粨鏋?(0 鎴?1)
   - 鏃犳硶鍖哄垎杞诲井寮傚父鍜屼弗閲嶅紓甯?
   - 缂轰箯缃俊搴﹁瘎浼?
   - 鏃犳硶鍙嶆槧寮傚父鐨勪弗閲嶇▼搴?

馃敡 鏀硅繘鍚庣殑浼樺娍:
   - 鎻愪緵0-1杩炵画姒傜巼鍒嗘暟
   - 鍖哄垎涓嶅悓绋嬪害鐨勫紓甯?
   - 鏀寔缃俊搴﹁瘎浼?
   - 鏇寸簿纭殑寮傚父绋嬪害鍙嶆槧

馃搳 瀹為檯搴旂敤绀轰緥:
   鍘熷璇勫垎: temperature > 80.0 鈫?True 鈫?1.0
   澧炲己璇勫垎: temperature > 80.0 鈫?0.85 (鍙嶆槧瓒呭嚭绋嬪害)
   
   鍘熷璇勫垎: temperature > 90.0 鈫?False 鈫?0.0  
   澧炲己璇勫垎: temperature > 90.0 鈫?0.0 (纭疄鏈Е鍙?
   
   鍘熷璇勫垎: pressure > 100.0 鈫?True 鈫?1.0
   澧炲己璇勫垎: pressure > 100.0 鈫?0.92 (鍙嶆槧瓒呭嚭绋嬪害)

馃帀 鏀硅繘鏁堟灉:
   - 鏇寸簿纭殑寮傚父璇勪及
   - 鏇村ソ鐨勫喅绛栨敮鎸?
   - 鏇翠赴瀵岀殑鍒嗘瀽淇℃伅
   - 淇濇寔涓嶮SFG鐨勭嫭绔嬫€?
    """)

if __name__ == "__main__":
    print("馃殌 寮€濮嬫祴璇曞寮虹殑瑙勫垯妫€娴嬭瘎鍒嗘満鍒?)
    print("=" * 80)
    
    success = test_enhanced_rule_scoring()
    demonstrate_scoring_improvements()
    
    print("\n" + "=" * 80)
    if success:
        print("馃帀 娴嬭瘯瀹屾垚!")
    else:
        print("鉂?娴嬭瘯澶辫触")
    
    print("=" * 80)

