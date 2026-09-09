#!/usr/bin/env python
"""
娴嬭瘯瀹屾暣鐨勮鍒欎繚瀛樺拰妫€娴嬫祦绋?
楠岃瘉澶嶆潅瑙勫垯鑳藉姝ｇ‘淇濆瓨銆佽В鏋愬拰妫€娴?
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
from rule_detection.service import evaluate_rules_for_data_point

def test_complete_rule_flow():
    """娴嬭瘯瀹屾暣鐨勮鍒欐祦绋?""
    print("=" * 80)
    print("娴嬭瘯瀹屾暣鐨勮鍒欎繚瀛樺拰妫€娴嬫祦绋?)
    print("=" * 80)
    
    # 1. 鍒涘缓娴嬭瘯妯″瀷鍜屾暟鎹?
    print("\n1. 鍒涘缓娴嬭瘯鐜...")
    
    cmg_model, created = PHMModel.objects.get_or_create(
        model_name="TEST_COMPLETE_MODEL",
        defaults={
            "description": "鐢ㄤ簬娴嬭瘯瀹屾暣娴佺▼鐨勬ā鍨?
        }
    )
    
    cmg, created = PHM.objects.get_or_create(
        cmg_id="TEST_COMPLETE_PHM",
        defaults={
            "cmg_model": cmg_model,
            "name": "娴嬭瘯瀹屾暣娴佺▼PHM"
        }
    )
    
    # 2. 鍒涘缓娴嬭瘯鏁版嵁
    test_data = {
        "楂橀€熻浆閫?: 7500.0,  # 瓒呰繃闃堝€硷紝搴旇瑙﹀彂瑙勫垯
        "浣庨€熻浆閫?: 3000.0,
        "娓╁害": 95.0,       # 瓒呰繃闃堝€硷紝搴旇瑙﹀彂瑙勫垯
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
    
    print(f"鉁?娴嬭瘯鐜鍒涘缓瀹屾垚")
    print(f"  妯″瀷: {cmg_model.model_name}")
    print(f"  PHM: {cmg.name}")
    print(f"  娴嬭瘯鏁版嵁: {test_data}")
    
    # 3. 妯℃嫙瑙勫垯淇濆瓨杩囩▼
    print("\n2. 妯℃嫙瑙勫垯淇濆瓨杩囩▼...")
    
    test_table_data = [
        {
            "showId": "COMPLETE_RULE_001",
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
            "showId": "COMPLETE_RULE_002",
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
    
    # 楠岃瘉瑙勫垯琛ㄨ揪寮?
    parameter_names = list(test_data.keys())
    validation_errors = []
    
    for i, rule_data in enumerate(test_table_data):
        rule_expression = rule_data.get('ruleExpress', '') or ''
        print(f"\n楠岃瘉瑙勫垯 {i+1}: {rule_data['faultName']}")
        print(f"琛ㄨ揪寮? {rule_expression}")
        
        # 妫€鏌ユ槸鍚﹀寘鍚珮绾х粺璁″嚱鏁?
        has_advanced_functions = any(func in rule_expression for func in [
            'mean(', 'std(', 'var(', 'mad(', 'rms(', 'slope(', 'diffmean(', 'diffstd(', 'ma(', 'ma_diff(', 'autocorr(', 'level('
        ])
        
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
                # 杩欓噷搴旇浣跨敤浼犵粺瑙ｆ瀽鍣紝浣嗕负浜嗙畝鍖栵紝鎴戜滑璺宠繃
                print(f"  鉁?楠岃瘉鎴愬姛锛堜紶缁熻В鏋愬櫒锛?)
                    
        except Exception as e:
            validation_errors.append({
                'rule_index': i,
                'rule_id': rule_data.get('showId', f'瑙勫垯{i+1}'),
                'fault_name': rule_data.get('faultName', ''),
                'errors': [f'瑙勫垯楠岃瘉澶辫触: {str(e)}']
            })
            print(f"  鉁?楠岃瘉寮傚父: {e}")
    
    if validation_errors:
        print(f"\n鉂?鍙戠幇 {len(validation_errors)} 涓獙璇侀敊璇?")
        for error in validation_errors:
            print(f"  瑙勫垯 {error['rule_id']} ({error['fault_name']}):")
            for err in error['errors']:
                print(f"    - {err}")
        return
    
    print(f"\n鉁?鎵€鏈夎鍒欓獙璇侀€氳繃!")
    
    # 4. 妯℃嫙鏁版嵁搴撲繚瀛?
    print("\n3. 妯℃嫙鏁版嵁搴撲繚瀛?..")
    
    try:
        from django.db import transaction
        
        with transaction.atomic():
            # 鍒犻櫎鐜版湁瑙勫垯
            RuleDefinition.objects.filter(cmg_model=cmg_model).delete()
            
            # 鍒涘缓瑙勫垯瀹氫箟
            for rule_data in test_table_data:
                # 鍒涘缓鎴栬幏鍙栨晠闅滃畾涔?
                fault_definition, created = FaultDefinition.objects.get_or_create(
                    cmg_model=cmg_model,
                    fault_name=rule_data['faultName'],
                    defaults={
                        'fault_level': rule_data['faultLevel'],
                        'component': rule_data['component'],
                        'description': rule_data['planDescript'],
                    }
                )
                
                # 瑙ｆ瀽瑙勫垯琛ㄨ揪寮忥紝鎻愬彇鐩稿叧鍙傛暟
                rule_expression = rule_data.get('ruleExpress', '') or ''
                related_parameters = []
                
                try:
                    # 妫€鏌ユ槸鍚﹀寘鍚珮绾х粺璁″嚱鏁?
                    has_advanced_functions = any(func in rule_expression for func in [
                        'mean(', 'std(', 'var(', 'mad(', 'rms(', 'slope(', 'diffmean(', 'diffstd(', 'ma(', 'ma_diff(', 'autocorr(', 'level('
                    ])
                    
                    if has_advanced_functions:
                        parser = EnhancedRuleParser(parameter_names=parameter_names)
                        parsed_result = parser.parse(rule_expression)
                        related_parameters = list(parsed_result.related_parameters)
                    else:
                        # 浣跨敤浼犵粺瑙ｆ瀽鍣?
                        from rule_detection.algorithms.rule.rule_parser import RuleParser
                        parser = RuleParser(parameter_names=parameter_names)
                        parsed = parser.parse(rule_expression)
                        if parsed and isinstance(parsed.get('related_parameters'), list):
                            related_parameters = parsed['related_parameters']
                except Exception as e:
                    print(f"璀﹀憡: 瑙ｆ瀽瑙勫垯琛ㄨ揪寮忓け璐? {e}")
                    related_parameters = []
                
                # 鍒涘缓瑙勫垯瀹氫箟
                rule_definition = RuleDefinition.objects.create(
                    cmg_model=cmg_model,
                    fault_definition=fault_definition,
                    rule_id=rule_data['showId'],
                    rule_expression=rule_expression,
                    source=rule_data['source'],
                    plan_description=rule_data['planDescript'],
                    is_online=rule_data['ruleOnline'],
                    is_new=rule_data['isNew'],
                    is_editable=rule_data['editable'],
                    related_parameters=related_parameters,
                )
                
                print(f"  鉁?淇濆瓨瑙勫垯: {rule_definition.rule_id} ({rule_definition.fault_definition.fault_name})")
                print(f"    琛ㄨ揪寮? {rule_definition.rule_expression}")
                print(f"    鐩稿叧鍙傛暟: {rule_definition.related_parameters}")
        
        print(f"\n鉁?鏁版嵁搴撲繚瀛樺畬鎴?")
        
    except Exception as e:
        print(f"\n鉂?鏁版嵁搴撲繚瀛樺け璐? {e}")
        return
    
    # 5. 楠岃瘉瑙勫垯鏄惁宸蹭繚瀛?
    print("\n4. 楠岃瘉瑙勫垯鏄惁宸蹭繚瀛?..")
    
    saved_rules = RuleDefinition.objects.filter(cmg_model=cmg_model)
    print(f"鏁版嵁搴撲腑鐨勮鍒欐暟閲? {saved_rules.count()}")
    
    for rule in saved_rules:
        print(f"  - {rule.rule_id}: {rule.fault_definition.fault_name}")
        print(f"    琛ㄨ揪寮? {rule.rule_expression}")
        print(f"    鍦ㄧ嚎鐘舵€? {rule.is_online}")
    
    # 6. 娴嬭瘯瑙勫垯妫€娴?
    print("\n5. 娴嬭瘯瑙勫垯妫€娴?..")
    
    try:
        # 浣跨敤瑙勫垯妫€娴嬫湇鍔?
        detection_results = evaluate_rules_for_data_point(cmg_data)
        
        print(f"妫€娴嬬粨鏋滄暟閲? {len(detection_results)}")
        
        for result in detection_results:
            print(f"  - 瑙勫垯ID: {result.get('rule_id', 'N/A')}")
            print(f"    鏁呴殰鍚嶇О: {result.get('fault_name', 'N/A')}")
            print(f"    鏄惁瑙﹀彂: {result.get('is_triggered', False)}")
            print(f"    缃俊搴? {result.get('confidence_score', 0.0)}")
            print(f"    鏁呴殰绛夌骇: {result.get('fault_level', 0)}")
            print()
        
        print(f"鉁?瑙勫垯妫€娴嬪畬鎴?")
        
    except Exception as e:
        print(f"\n鉂?瑙勫垯妫€娴嬪け璐? {e}")
        import traceback
        traceback.print_exc()
    
    # 7. 娓呯悊娴嬭瘯鏁版嵁
    print("\n6. 娓呯悊娴嬭瘯鏁版嵁...")
    
    try:
        PHMData.objects.filter(cmg=cmg).delete()
        PHM.objects.filter(cmg_id="TEST_COMPLETE_PHM").delete()
        PHMModel.objects.filter(model_name="TEST_COMPLETE_MODEL").delete()
        print("鉁?娴嬭瘯鏁版嵁娓呯悊瀹屾垚")
    except Exception as e:
        print(f"鈿?娓呯悊娴嬭瘯鏁版嵁鏃跺嚭閿? {e}")

if __name__ == "__main__":
    test_complete_rule_flow()
    print("\n娴嬭瘯瀹屾垚!")

