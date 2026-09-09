#!/usr/bin/env python
"""
璋冭瘯娴嬬偣璇勫垎杩囩▼
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

def debug_scoring():
    print("=" * 60)
    print("璋冭瘯娴嬬偣璇勫垎杩囩▼")
    print("=" * 60)
    
    # 1. 鑾峰彇娴嬭瘯鏁版嵁
    try:
        cmg_model = PHMModel.objects.get(id=3)
        print(f"PHM妯″瀷: {cmg_model.model_name}")
    except PHMModel.DoesNotExist:
        print("PHM妯″瀷ID 3涓嶅瓨鍦?)
        return
    
    # 鑾峰彇鏁版嵁鐐?
    data_point = PHMData.objects.filter(cmg__cmg_model=cmg_model).first()
    if not data_point:
        print("娌℃湁鎵惧埌鏁版嵁鐐?)
        return
    
    print(f"鏁版嵁鐐笽D: {data_point.id}")
    print(f"鏁版嵁鐐规椂闂? {data_point.timestamp}")
    
    # 2. 妫€鏌ュ師濮嬪弬鏁版暟鎹?
    if hasattr(data_point, 'raw_parameters') and data_point.raw_parameters:
        params = data_point.raw_parameters
        print(f"鍘熷鍙傛暟鏁伴噺: {len(params)}")
        
        # 鏄剧ず鍓嶅嚑涓弬鏁?
        param_items = list(params.items())[:5]
        print("鍙傛暟绀轰緥:")
        for name, value in param_items:
            print(f"  {name}: {value} (绫诲瀷: {type(value)})")
    else:
        print("娌℃湁鎵惧埌鍘熷鍙傛暟鏁版嵁")
        return
    
    # 3. 鑾峰彇MSFG鍜岃鍒?
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
    if not msfg:
        print("娌℃湁鎵惧埌婵€娲荤殑MSFG")
        return
    
    print(f"MSFG: {msfg.name}")
    
    # 鑾峰彇瑙勫垯
    rules = TestPointRule.objects.filter(msfg_definition=msfg, is_online=True)
    print(f"婵€娲昏鍒欐暟閲? {rules.count()}")
    
    if rules.count() == 0:
        print("娌℃湁婵€娲荤殑瑙勫垯")
        return
    
    # 4. 娴嬭瘯鍗曚釜瑙勫垯鐨勮瘎鍒?
    print("\n" + "=" * 40)
    print("娴嬭瘯鍗曚釜瑙勫垯璇勫垎")
    print("=" * 40)
    
    scoring_service = TestPointScoringService()
    
    for i, rule in enumerate(rules[:3], 1):
        print(f"\n瑙勫垯 {i}: {rule.test_point_name}")
        print(f"瑙勫垯ID: {rule.rule_id}")
        print(f"鍘熷琛ㄨ揪寮? {repr(rule.rule_expression)}")
        
        # 棰勫鐞嗚〃杈惧紡
        processed_expr = scoring_service._preprocess_expression(rule.rule_expression, params)
        print(f"澶勭悊鍚庤〃杈惧紡: {repr(processed_expr)}")
        
        # 妫€鏌ユ祴鐐瑰悕鏄惁鍦ㄦ暟鎹腑
        test_point_name = rule.test_point_name
        if test_point_name in params:
            param_value = params[test_point_name]
            print(f"娴嬬偣 '{test_point_name}' 鐨勫€? {param_value} (绫诲瀷: {type(param_value)})")
        else:
            print(f"鈿狅笍  娴嬬偣 '{test_point_name}' 涓嶅湪鏁版嵁涓?)
            # 鏌ユ壘鐩镐技鐨勫弬鏁板悕
            similar_names = [name for name in params.keys() if test_point_name in name or name in test_point_name]
            if similar_names:
                print(f"鐩镐技鐨勫弬鏁板悕: {similar_names[:3]}")
        
        # 灏濊瘯鎵ц瑙勫垯
        try:
            score = scoring_service._evaluate_single_rule(rule.rule_expression, params)
            print(f"璇勫垎缁撴灉: {score}")
            
            if score == 0.0:
                print("鈿狅笍  璇勫垎涓?锛屽彲鑳界殑鍘熷洜:")
                print("   1. 琛ㄨ揪寮忕粨鏋滀负False鎴?")
                print("   2. 鍙傛暟鍚嶄笉鍖归厤")
                print("   3. 鍑芥暟鎵ц鍑洪敊")
                
                # 灏濊瘯鎵嬪姩鎵ц琛ㄨ揪寮忕殑鍚勪釜閮ㄥ垎
                print("\n灏濊瘯鍒嗚В鎵ц:")
                try:
                    # 妫€鏌evel鍑芥暟閮ㄥ垎
                    if 'level(' in processed_expr:
                        print("   - 琛ㄨ揪寮忓寘鍚玪evel鍑芥暟")
                        # 灏濊瘯鎻愬彇level鍑芥暟鐨勫弬鏁?
                        import re
                        level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', processed_expr)
                        for param_name, median, mad in level_matches:
                            if param_name in params:
                                param_val = params[param_name]
                                print(f"     level鍙傛暟: {param_name}={param_val}, median={median}, mad={mad}")
                                # 鎵嬪姩璁＄畻level鍊?
                                try:
                                    median_val = float(median)
                                    mad_val = float(mad)
                                    mad_safe = max(abs(mad_val), 1e-9)
                                    level_result = abs(param_val - median_val) / mad_safe
                                    print(f"     level缁撴灉: {level_result}")
                                    print(f"     level > 3.0: {level_result > 3.0}")
                                except Exception as e:
                                    print(f"     level璁＄畻閿欒: {e}")
                            else:
                                print(f"     鍙傛暟 {param_name} 涓嶅瓨鍦?)
                except Exception as e:
                    print(f"   鍒嗚В鎵ц澶辫触: {e}")
                    
        except Exception as e:
            print(f"瑙勫垯鎵ц澶辫触: {e}")
    
    # 5. 娴嬭瘯瀹屾暣鐨勮瘎鍒嗘湇鍔?
    print("\n" + "=" * 40)
    print("娴嬭瘯瀹屾暣璇勫垎鏈嶅姟")
    print("=" * 40)
    
    try:
        from msfg_analysis.services.testpoint_scoring import calculate_msfg_test_scores
        scores = calculate_msfg_test_scores(data_point, msfg)
        print(f"瀹屾暣璇勫垎缁撴灉: {scores}")
        
        if not scores:
            print("鈿狅笍  娌℃湁寰楀埌浠讳綍璇勫垎缁撴灉")
        else:
            zero_scores = [name for name, score in scores.items() if score == 0.0]
            if zero_scores:
                print(f"璇勫垎涓?鐨勬祴鐐? {zero_scores}")
            
            non_zero_scores = {name: score for name, score in scores.items() if score > 0.0}
            if non_zero_scores:
                print(f"闈為浂璇勫垎: {non_zero_scores}")
                
    except Exception as e:
        print(f"瀹屾暣璇勫垎鏈嶅姟澶辫触: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_scoring()

