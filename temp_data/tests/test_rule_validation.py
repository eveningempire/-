#!/usr/bin/env python
"""
娴嬭瘯瑙勫垯楠岃瘉鍔熻兘
楠岃瘉鏂拌鍒欒兘澶熸纭В鏋愬拰淇濆瓨
"""

import os
import sys
import django
import json
from datetime import datetime

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, PHMModel, PHMData
from rule_detection.models import RuleDefinition, FaultDefinition
from rule_detection.algorithms.rule.enhanced_rule_parser import EnhancedRuleParser
from rule_detection.algorithms.rule.rule_parser import RuleParser

def test_rule_parsing():
    """娴嬭瘯瑙勫垯瑙ｆ瀽鍔熻兘"""
    print("=" * 80)
    print("娴嬭瘯瑙勫垯瑙ｆ瀽鍔熻兘")
    print("=" * 80)
    
    # 娴嬭瘯鍙傛暟鍒楄〃
    parameter_names = ["楂橀€熻浆閫?, "浣庨€熻浆閫?, "娓╁害", "鍘嬪姏", "鎸姩"]
    
    # 娴嬭瘯瑙勫垯琛ㄨ揪寮?
    test_rules = [
        # 绠€鍗曡鍒?- 搴旇鎴愬姛
        "Para(\"楂橀€熻浆閫焅", 7000, 0.020027) > 3.0",
        
        # 楂樼骇缁熻鍑芥暟瑙勫垯 - 搴旇鎴愬姛
        "level(\"楂橀€熻浆閫焅", 7000, 0.020027) > 3.0",
        
        # 澶嶆潅鐨勯珮绾х粺璁″嚱鏁拌鍒?- 搴旇鎴愬姛
        "mean(\"楂橀€熻浆閫焅") > 5000 and std(\"娓╁害\") < 100",
        
        # 甯︾獥鍙ｇ殑缁熻鍑芥暟 - 搴旇鎴愬姛
        "slope(\"楂橀€熻浆閫焅", 10) > 0.5",
        
        # 鏃犳晥瑙勫垯 - 搴旇澶辫触
        "invalid_function(\"鍙傛暟\") > 100",
        
        # 璇硶閿欒 - 搴旇澶辫触
        "mean(\"楂橀€熻浆閫焅" > 5000",  # 缂哄皯鍙虫嫭鍙?
    ]
    
    print("\n1. 娴嬭瘯浼犵粺瑙ｆ瀽鍣?")
    parser = RuleParser(parameter_names=parameter_names)
    
    for i, rule in enumerate(test_rules[:2]):  # 鍙祴璇曞墠涓や釜绠€鍗曡鍒?
        print(f"\n瑙勫垯 {i+1}: {rule}")
        try:
            result = parser.parse(rule)
            if result:
                print(f"  鉁?瑙ｆ瀽鎴愬姛: {result}")
            else:
                print(f"  鉁?瑙ｆ瀽澶辫触")
        except Exception as e:
            print(f"  鉁?瑙ｆ瀽寮傚父: {e}")
    
    print("\n2. 娴嬭瘯澧炲己鐗堣В鏋愬櫒:")
    enhanced_parser = EnhancedRuleParser(parameter_names=parameter_names)
    
    for i, rule in enumerate(test_rules):
        print(f"\n瑙勫垯 {i+1}: {rule}")
        try:
            result = enhanced_parser.parse(rule)
            print(f"  琛ㄨ揪寮? {result.expression}")
            print(f"  鐩稿叧鍙傛暟: {result.related_parameters}")
            print(f"  閿欒鏁伴噺: {result.error_count}")
            print(f"  璀﹀憡鏁伴噺: {result.warning_count}")
            
            if result.error_count > 0:
                print("  閿欒淇℃伅:")
                for msg in result.log_messages:
                    if msg['type'] == 'error':
                        print(f"    - {msg['message']}")
            
            if result.warning_count > 0:
                print("  璀﹀憡淇℃伅:")
                for msg in result.log_messages:
                    if msg['type'] == 'warning':
                        print(f"    - {msg['message']}")
                        
        except Exception as e:
            print(f"  鉁?瑙ｆ瀽寮傚父: {e}")

def test_rule_saving():
    """娴嬭瘯瑙勫垯淇濆瓨鍔熻兘"""
    print("\n" + "=" * 80)
    print("娴嬭瘯瑙勫垯淇濆瓨鍔熻兘")
    print("=" * 80)
    
    # 鑾峰彇鎴栧垱寤烘祴璇曟ā鍨?
    cmg_model, created = PHMModel.objects.get_or_create(
        model_name="TEST_VALIDATION_MODEL",
        defaults={
            "description": "鐢ㄤ簬娴嬭瘯瑙勫垯楠岃瘉鐨勬ā鍨?
        }
    )
    
    if created:
        print(f"鍒涘缓娴嬭瘯妯″瀷: {cmg_model.model_name}")
    else:
        print(f"浣跨敤鐜版湁妯″瀷: {cmg_model.model_name}")
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    cmg, created = PHM.objects.get_or_create(
        cmg_id="TEST_VALIDATION_PHM",
        defaults={
            "cmg_model": cmg_model,
            "name": "娴嬭瘯楠岃瘉PHM"
        }
    )
    
    if created:
        print(f"鍒涘缓娴嬭瘯PHM: {cmg.name}")
    else:
        print(f"浣跨敤鐜版湁PHM: {cmg.name}")
    
    # 鍒涘缓娴嬭瘯鏁版嵁鐐?
    test_data = {
        "楂橀€熻浆閫?: 6000.0,
        "浣庨€熻浆閫?: 3000.0,
        "娓╁害": 85.5,
        "鍘嬪姏": 2.1,
        "鎸姩": 0.15
    }
    
    cmg_data, created = PHMData.objects.get_or_create(
        cmg=cmg,
        timestamp=datetime.now(),
        defaults={
            "data": test_data
        }
    )
    
    if created:
        print(f"鍒涘缓娴嬭瘯鏁版嵁鐐?)
    else:
        print(f"浣跨敤鐜版湁鏁版嵁鐐?)
    
    # 娴嬭瘯瑙勫垯鏁版嵁
    test_table_data = [
        {
            "showId": "RULE_001",
            "faultName": "杞€熷紓甯?,
            "faultLevel": 2,
            "component": "鍙戝姩鏈?,
            "ruleExpress": "level(\"楂橀€熻浆閫焅", 7000, 0.020027) > 3.0",
            "source": "expert",
            "planDescript": "娴嬭瘯瑙勫垯1",
            "ruleOnline": True,
            "isNew": True,
            "editable": True
        },
        {
            "showId": "RULE_002", 
            "faultName": "娓╁害寮傚父",
            "faultLevel": 1,
            "component": "鍐峰嵈绯荤粺",
            "ruleExpress": "mean(\"娓╁害\") > 90 and std(\"娓╁害\") < 5",
            "source": "expert",
            "planDescript": "娴嬭瘯瑙勫垯2",
            "ruleOnline": True,
            "isNew": True,
            "editable": True
        },
        {
            "showId": "RULE_003",
            "faultName": "鏃犳晥瑙勫垯",
            "faultLevel": 1,
            "component": "娴嬭瘯",
            "ruleExpress": "invalid_function(\"鍙傛暟\") > 100",
            "source": "expert", 
            "planDescript": "娴嬭瘯鏃犳晥瑙勫垯",
            "ruleOnline": True,
            "isNew": True,
            "editable": True
        }
    ]
    
    print(f"\n娴嬭瘯淇濆瓨 {len(test_table_data)} 鏉¤鍒?..")
    
    # 妯℃嫙瑙勫垯淇濆瓨楠岃瘉杩囩▼
    parameter_names = list(test_data.keys())
    validation_errors = []
    
    for i, rule_data in enumerate(test_table_data):
        rule_expression = rule_data.get('ruleExpress', '') or ''
        if not rule_expression:
            continue
            
        # 妫€鏌ユ槸鍚﹀寘鍚珮绾х粺璁″嚱鏁?
        has_advanced_functions = any(func in rule_expression for func in [
            'mean(', 'std(', 'var(', 'mad(', 'rms(', 'slope(', 'diffmean(', 'diffstd(', 'ma(', 'ma_diff(', 'autocorr('
        ])
        
        print(f"\n楠岃瘉瑙勫垯 {i+1}: {rule_data['faultName']}")
        print(f"琛ㄨ揪寮? {rule_expression}")
        
        try:
            if has_advanced_functions:
                print("浣跨敤澧炲己鐗堣В鏋愬櫒...")
                parser = EnhancedRuleParser(parameter_names=parameter_names)
                parsed_result = parser.parse(rule_expression)
                
                if parsed_result.error_count > 0:
                    error_messages = [msg['message'] for msg in parsed_result.log_messages if msg['type'] == 'error']
                    validation_errors.append({
                        'rule_index': i,
                        'rule_id': rule_data.get('showId', f'瑙勫垯{i+1}'),
                        'fault_name': rule_data.get('faultName', ''),
                        'errors': error_messages
                    })
                    print(f"  鉁?楠岃瘉澶辫触: {error_messages}")
                else:
                    print(f"  鉁?楠岃瘉鎴愬姛")
            else:
                print("浣跨敤浼犵粺瑙ｆ瀽鍣?..")
                parser = RuleParser(parameter_names=parameter_names)
                parsed = parser.parse(rule_expression)
                if not parsed:
                    validation_errors.append({
                        'rule_index': i,
                        'rule_id': rule_data.get('showId', f'瑙勫垯{i+1}'),
                        'fault_name': rule_data.get('faultName', ''),
                        'errors': ['瑙勫垯琛ㄨ揪寮忚В鏋愬け璐?]
                    })
                    print(f"  鉁?楠岃瘉澶辫触: 瑙勫垯琛ㄨ揪寮忚В鏋愬け璐?)
                else:
                    print(f"  鉁?楠岃瘉鎴愬姛")
                    
        except Exception as e:
            validation_errors.append({
                'rule_index': i,
                'rule_id': rule_data.get('showId', f'瑙勫垯{i+1}'),
                'fault_name': rule_data.get('faultName', ''),
                'errors': [f'瑙勫垯楠岃瘉澶辫触: {str(e)}']
            })
            print(f"  鉁?楠岃瘉寮傚父: {e}")
    
    # 鏄剧ず楠岃瘉缁撴灉
    if validation_errors:
        print(f"\n鉂?鍙戠幇 {len(validation_errors)} 涓獙璇侀敊璇?")
        for error in validation_errors:
            print(f"  瑙勫垯 {error['rule_id']} ({error['fault_name']}):")
            for err in error['errors']:
                print(f"    - {err}")
    else:
        print(f"\n鉁?鎵€鏈夎鍒欓獙璇侀€氳繃!")
    
    # 娓呯悊娴嬭瘯鏁版嵁
    print(f"\n娓呯悊娴嬭瘯鏁版嵁...")
    try:
        PHMData.objects.filter(cmg=cmg).delete()
        PHM.objects.filter(cmg_id="TEST_VALIDATION_PHM").delete()
        PHMModel.objects.filter(model_name="TEST_VALIDATION_MODEL").delete()
        print("娴嬭瘯鏁版嵁娓呯悊瀹屾垚")
    except Exception as e:
        print(f"娓呯悊娴嬭瘯鏁版嵁鏃跺嚭閿? {e}")

if __name__ == "__main__":
    test_rule_parsing()
    test_rule_saving()
    print("\n娴嬭瘯瀹屾垚!")

