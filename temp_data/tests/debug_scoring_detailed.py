#!/usr/bin/env python
"""
璇︾粏璋冭瘯娴嬬偣璇勫垎璁＄畻閫昏緫
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

def debug_detailed_scoring():
    print("=" * 60)
    print("璇︾粏璋冭瘯娴嬬偣璇勫垎璁＄畻閫昏緫")
    print("=" * 60)
    
    # 鑾峰彇娴嬭瘯鏁版嵁
    try:
        cmg_model = PHMModel.objects.get(id=3)
        print(f"PHM妯″瀷: {cmg_model.model_name}")
    except PHMModel.DoesNotExist:
        print("PHM妯″瀷ID 3涓嶅瓨鍦?)
        return
    
    # 鑾峰彇MSFG
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
    if not msfg:
        print("娌℃湁鎵惧埌婵€娲荤殑MSFG")
        return
    
    print(f"MSFG: {msfg.name}")
    
    # 鑾峰彇鏁版嵁鐐?
    data_point = PHMData.objects.filter(cmg__cmg_model=cmg_model).first()
    if not data_point:
        print("娌℃湁鎵惧埌鏁版嵁鐐?)
        return
    
    print(f"鏁版嵁鐐笽D: {data_point.id}")
    
    # 鑾峰彇瑙勫垯
    rules = TestPointRule.objects.filter(msfg_definition=msfg, is_online=True)
    print(f"瑙勫垯鏁伴噺: {rules.count()}")
    
    if rules.count() == 0:
        print("娌℃湁婵€娲荤殑瑙勫垯")
        return
    
    # 璇︾粏鍒嗘瀽鍓嶅嚑涓鍒?
    print("\n" + "=" * 40)
    print("璇︾粏瑙勫垯鍒嗘瀽")
    print("=" * 40)
    
    scoring_service = TestPointScoringService()
    
    for i, rule in enumerate(rules[:5], 1):
        print(f"\n--- 瑙勫垯 {i}: {rule.test_name} ---")
        print(f"瑙勫垯ID: {rule.rule_id}")
        print(f"鍘熷琛ㄨ揪寮? {repr(rule.rule_expression)}")
        print(f"鏉冮噸: {rule.weight}")
        
        # 妫€鏌ユ暟鎹腑鏄惁鏈夎繖涓弬鏁?
        if hasattr(data_point, 'raw_parameters') and data_point.raw_parameters:
            data = data_point.raw_parameters
            if rule.test_name in data:
                param_value = data[rule.test_name]
                print(f"鍙傛暟鍊? {param_value} (绫诲瀷: {type(param_value)})")
            else:
                # 鏌ユ壘鐩镐技鍙傛暟鍚?
                similar_params = []
                for key in data.keys():
                    if rule.test_name.strip() in key or key.strip() in rule.test_name:
                        similar_params.append(key)
                if similar_params:
                    print(f"鐩镐技鍙傛暟: {similar_params}")
                    actual_param = similar_params[0]
                    param_value = data[actual_param]
                    print(f"浣跨敤鍙傛暟: {actual_param} = {param_value}")
                else:
                    print(f"鈿狅笍  鍙傛暟 '{rule.test_name}' 涓嶅瓨鍦?)
                    continue
        
        # 灏濊瘯鎵ц瑙勫垯
        try:
            score = scoring_service._evaluate_rule_expression(rule.rule_expression, data_point)
            print(f"璇勫垎缁撴灉: {score}")
            
            # 鎵嬪姩鍒嗘瀽琛ㄨ揪寮?
            print(f"琛ㄨ揪寮忓垎鏋?")
            if 'level(' in rule.rule_expression:
                print("  - 鍖呭惈level鍑芥暟")
            if 'ma_diff(' in rule.rule_expression:
                print("  - 鍖呭惈ma_diff鍑芥暟")
            if 'rollstd(' in rule.rule_expression:
                print("  - 鍖呭惈rollstd鍑芥暟")
            if '>' in rule.rule_expression:
                print("  - 鍖呭惈澶т簬姣旇緝")
            if 'and' in rule.rule_expression:
                print("  - 鍖呭惈閫昏緫AND")
            if 'or' in rule.rule_expression:
                print("  - 鍖呭惈閫昏緫OR")
                
            # 灏濊瘯鎵嬪姩璁＄畻level鍑芥暟鐨勫€?
            if 'level(' in rule.rule_expression:
                import re
                level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', rule.rule_expression)
                for param_name, median_str, mad_str in level_matches:
                    try:
                        if param_name in data:
                            param_val = float(data[param_name])
                            median_val = float(median_str)
                            mad_val = float(mad_str)
                            mad_safe = max(abs(mad_val), 1e-9)
                            level_result = abs(param_val - median_val) / mad_safe
                            
                            print(f"  - level({param_name}, {median_val}, {mad_val}):")
                            print(f"    褰撳墠鍊? {param_val}")
                            print(f"    level鍊? {level_result:.6f}")
                            print(f"    level > 3.0: {level_result > 3.0}")
                            
                            # 濡傛灉鏄畝鍗曠殑level > 3.0琛ㄨ揪寮忥紝棰勬祴缁撴灉
                            if rule.rule_expression.strip() == f'level("{param_name}", {median_str}, {mad_str}) > 3.0':
                                expected_result = 1.0 if level_result > 3.0 else 0.0
                                print(f"    棰勬湡缁撴灉: {expected_result}")
                                if score != expected_result:
                                    print(f"    鈿狅笍  瀹為檯缁撴灉({score})涓庨鏈熶笉绗?")
                    except Exception as e:
                        print(f"    level璁＄畻閿欒: {e}")
                        
        except Exception as e:
            print(f"瑙勫垯鎵ц澶辫触: {e}")
            import traceback
            traceback.print_exc()
    
    # 娴嬭瘯瀹屾暣璇勫垎鏈嶅姟
    print("\n" + "=" * 40)
    print("瀹屾暣璇勫垎鏈嶅姟娴嬭瘯")
    print("=" * 40)
    
    try:
        all_scores = scoring_service.calculate_test_scores(data_point, msfg)
        print(f"鎬绘祴鐐规暟: {len(all_scores)}")
        
        # 鎸夊垎鏁板垎缁?
        zero_scores = {k: v for k, v in all_scores.items() if v == 0.0}
        one_scores = {k: v for k, v in all_scores.items() if v == 1.0}
        middle_scores = {k: v for k, v in all_scores.items() if 0.0 < v < 1.0}
        
        print(f"鍒嗘暟涓?.0鐨勬祴鐐? {len(zero_scores)}")
        if zero_scores:
            print(f"  绀轰緥: {list(zero_scores.items())[:3]}")
            
        print(f"鍒嗘暟涓?.0鐨勬祴鐐? {len(one_scores)}")
        if one_scores:
            print(f"  绀轰緥: {list(one_scores.items())[:3]}")
            
        print(f"涓棿鍒嗘暟鐨勬祴鐐? {len(middle_scores)}")
        if middle_scores:
            print(f"  璇︾粏: {middle_scores}")
            
    except Exception as e:
        print(f"瀹屾暣璇勫垎鏈嶅姟澶辫触: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_detailed_scoring()

