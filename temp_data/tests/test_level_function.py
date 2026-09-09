#!/usr/bin/env python
"""
娴嬭瘯level鍑芥暟鐨勮В鏋愬拰妫€娴嬪姛鑳?
楠岃瘉澶嶆潅瑙勫垯鑳藉姝ｇ‘淇濆瓨鍜屾娴?
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
from rule_detection.algorithms.rule.enhanced_rule_detector import EnhancedRuleDetector
from rule_detection.algorithms.rule.rule_parser import RuleParser

def test_level_function_parsing():
    """娴嬭瘯level鍑芥暟鐨勮В鏋愬姛鑳?""
    print("=" * 80)
    print("娴嬭瘯level鍑芥暟瑙ｆ瀽鍔熻兘")
    print("=" * 80)
    
    # 娴嬭瘯鍙傛暟鍒楄〃
    parameter_names = ["楂橀€熻浆閫?, "浣庨€熻浆閫?, "娓╁害", "鍘嬪姏", "鎸姩"]
    
    # 娴嬭瘯瑙勫垯琛ㄨ揪寮?
    test_rules = [
        # level鍑芥暟瑙勫垯
        'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0',
        
        # 澶嶆潅level鍑芥暟瑙勫垯
        '(level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0) and (level("娓╁害", 85, 5) > 2.0)',
        
        # level鍑芥暟涓庡叾浠栧嚱鏁版贩鍚?
        'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0 and mean("娓╁害") > 90',
        
        # 绠€鍗曡鍒?
        'Para("楂橀€熻浆閫?, 7000, 0.020027) > 3.0',
    ]
    
    print("\n1. 娴嬭瘯澧炲己鐗堣В鏋愬櫒:")
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

def test_level_function_detection():
    """娴嬭瘯level鍑芥暟鐨勬娴嬪姛鑳?""
    print("\n" + "=" * 80)
    print("娴嬭瘯level鍑芥暟妫€娴嬪姛鑳?)
    print("=" * 80)
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    test_data = {
        "楂橀€熻浆閫?: 7500.0,  # 瓒呰繃闃堝€?
        "浣庨€熻浆閫?: 3000.0,
        "娓╁害": 90.0,
        "鍘嬪姏": 2.1,
        "鎸姩": 0.15
    }
    
    # 鍒涘缓娴嬭瘯瑙勫垯
    test_rules = [
        {
            'rule_id': 'TEST_LEVEL_001',
            'rule_expression': 'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0',
            'fault_name': '杞€熷紓甯?,
            'fault_level': 2,
            'is_online': True
        },
        {
            'rule_id': 'TEST_LEVEL_002',
            'rule_expression': 'level("娓╁害", 85, 5) > 2.0',
            'fault_name': '娓╁害寮傚父',
            'fault_level': 1,
            'is_online': True
        }
    ]
    
    # 鍒涘缓澧炲己鐗堟娴嬪櫒
    rule_config = {
        'rules': test_rules,
        'parameter_names': list(test_data.keys()),
        'fault_name_map': {rule['fault_name']: rule for rule in test_rules}
    }
    
    detector = EnhancedRuleDetector(rule_config)
    
    print(f"\n娴嬭瘯鏁版嵁: {test_data}")
    
    # 鎵ц妫€娴?
    results = detector.detect(test_data)
    
    print(f"\n妫€娴嬬粨鏋?")
    for result in results:
        print(f"  瑙勫垯ID: {result['rule_id']}")
        print(f"  鏁呴殰鍚嶇О: {result['fault_name']}")
        print(f"  鏄惁瑙﹀彂: {result['is_triggered']}")
        print(f"  缃俊搴? {result['confidence_score']}")
        print(f"  琛ㄨ揪寮? {result['rule_expression']}")
        print()

def test_rule_saving_with_level():
    """娴嬭瘯鍖呭惈level鍑芥暟鐨勮鍒欎繚瀛樺姛鑳?""
    print("\n" + "=" * 80)
    print("娴嬭瘯鍖呭惈level鍑芥暟鐨勮鍒欎繚瀛樺姛鑳?)
    print("=" * 80)
    
    # 鑾峰彇鎴栧垱寤烘祴璇曟ā鍨?
    cmg_model, created = PHMModel.objects.get_or_create(
        model_name="TEST_LEVEL_MODEL",
        defaults={
            "description": "鐢ㄤ簬娴嬭瘯level鍑芥暟鐨勬ā鍨?
        }
    )
    
    if created:
        print(f"鍒涘缓娴嬭瘯妯″瀷: {cmg_model.model_name}")
    else:
        print(f"浣跨敤鐜版湁妯″瀷: {cmg_model.model_name}")
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    cmg, created = PHM.objects.get_or_create(
        cmg_id="TEST_LEVEL_PHM",
        defaults={
            "cmg_model": cmg_model,
            "name": "娴嬭瘯Level PHM"
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
            "showId": "LEVEL_RULE_001",
            "faultName": "杞€熷紓甯?,
            "faultLevel": 2,
            "component": "鍙戝姩鏈?,
            "ruleExpress": 'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0',
            "source": "expert",
            "planDescript": "娴嬭瘯level鍑芥暟瑙勫垯",
            "ruleOnline": True,
            "isNew": True,
            "editable": True
        },
        {
            "showId": "LEVEL_RULE_002",
            "faultName": "娓╁害寮傚父",
            "faultLevel": 1,
            "component": "鍐峰嵈绯荤粺",
            "ruleExpress": 'level("娓╁害", 85, 5) > 2.0 and mean("娓╁害") > 90',
            "source": "expert",
            "planDescript": "娴嬭瘯娣峰悎鍑芥暟瑙勫垯",
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
            'mean(', 'std(', 'var(', 'mad(', 'rms(', 'slope(', 'diffmean(', 'diffstd(', 'ma(', 'ma_diff(', 'autocorr(', 'level('
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
                    print(f"    瑙ｆ瀽鍚庤〃杈惧紡: {parsed_result.expression}")
                    print(f"    鐩稿叧鍙傛暟: {parsed_result.related_parameters}")
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
        PHM.objects.filter(cmg_id="TEST_LEVEL_PHM").delete()
        PHMModel.objects.filter(model_name="TEST_LEVEL_MODEL").delete()
        print("娴嬭瘯鏁版嵁娓呯悊瀹屾垚")
    except Exception as e:
        print(f"娓呯悊娴嬭瘯鏁版嵁鏃跺嚭閿? {e}")

if __name__ == "__main__":
    test_level_function_parsing()
    test_level_function_detection()
    test_rule_saving_with_level()
    print("\n娴嬭瘯瀹屾垚!")

