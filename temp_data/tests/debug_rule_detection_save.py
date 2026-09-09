#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
璋冭瘯瑙勫垯妫€娴嬬粨鏋滀繚瀛橀棶棰?
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMData, PHM, PHMModel
from rule_detection.models import RuleDefinition, FaultDefinition, RuleDetectionResult
from rule_detection.service import evaluate_rules_with_enhanced_detector
from rule_detection.algorithms.rule.enhanced_rule_parser import EnhancedRuleParser
from rule_detection.algorithms.rule.enhanced_rule_detector import EnhancedRuleDetector
import logging

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def debug_rule_parsing():
    """璋冭瘯瑙勫垯瑙ｆ瀽"""
    print("=" * 60)
    print("璋冭瘯瑙勫垯瑙ｆ瀽")
    print("=" * 60)
    
    # 鑾峰彇涓€涓狢MG妯″瀷
    cmg_model = PHMModel.objects.first()
    if not cmg_model:
        print("鉂?娌℃湁鎵惧埌PHM妯″瀷")
        return
    
    print(f"浣跨敤妯″瀷: {cmg_model.model_name}")
    
    # 鑾峰彇鎵€鏈夎鍒?
    rules = RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True)
    print(f"鎵惧埌 {rules.count()} 鏉″湪绾胯鍒?)
    
    # 娴嬭瘯鍙傛暟鍒楄〃
    test_parameters = ["楂橀€熺數鏈虹數娴?, "浣庨€熺數鏈虹數娴?, "娓╁害", "鍘嬪姏", "杞€?]
    parser = EnhancedRuleParser(test_parameters)
    
    for rule in rules:
        print(f"\n瑙勫垯 {rule.rule_id}:")
        print(f"  琛ㄨ揪寮? {rule.rule_expression}")
        print(f"  鏁呴殰: {rule.fault_definition.fault_name}")
        print(f"  绛夌骇: {rule.fault_definition.fault_level}")
        
        # 瑙ｆ瀽瑙勫垯
        parse_result = parser.parse(rule.rule_expression)
        print(f"  瑙ｆ瀽缁撴灉: {parse_result.expression}")
        print(f"  鐩稿叧鍙傛暟: {list(parse_result.related_parameters)}")
        print(f"  閿欒鏁? {parse_result.error_count}")
        print(f"  璀﹀憡鏁? {parse_result.warning_count}")
        
        # 妫€鏌ユ槸鍚﹀寘鍚玪evel鍑芥暟
        if 'level(' in rule.rule_expression:
            print(f"  馃攳 鍖呭惈level鍑芥暟")
        
        # 妫€鏌ユ槸鍚﹀寘鍚玬a_diff鍑芥暟
        if 'ma_diff(' in rule.rule_expression:
            print(f"  馃攳 鍖呭惈ma_diff鍑芥暟")

def debug_rule_detection():
    """璋冭瘯瑙勫垯妫€娴?""
    print("\n" + "=" * 60)
    print("璋冭瘯瑙勫垯妫€娴?)
    print("=" * 60)
    
    # 鑾峰彇涓€涓狢MG妯″瀷
    cmg_model = PHMModel.objects.first()
    if not cmg_model:
        print("鉂?娌℃湁鎵惧埌PHM妯″瀷")
        return
    
    # 鑾峰彇涓€涓狢MG瀹炰緥
    cmg = PHM.objects.filter(cmg_model=cmg_model).first()
    if not cmg:
        print("鉂?娌℃湁鎵惧埌PHM瀹炰緥")
        return
    
    # 鑾峰彇鏈€鏂扮殑鏁版嵁鐐?
    latest_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    if not latest_data:
        print("鉂?娌℃湁鎵惧埌鏁版嵁鐐?)
        return
    
    print(f"浣跨敤鏁版嵁鐐? {latest_data.timestamp}")
    print(f"鏁版嵁鍙傛暟: {list(latest_data.data.keys()) if isinstance(latest_data.data, dict) else 'None'}")
    
    # 鎵ц澧炲己瑙勫垯妫€娴?
    try:
        results = evaluate_rules_with_enhanced_detector(latest_data)
        print(f"\n妫€娴嬬粨鏋? {len(results)} 鏉?)
        
        for result in results:
            print(f"  瑙勫垯: {result.get('rule_id')}")
            print(f"  鏁呴殰: {result.get('fault_name')}")
            print(f"  瑙﹀彂: {result.get('is_triggered')}")
            print(f"  鍒嗘暟: {result.get('score')}")
            print(f"  绛夌骇: {result.get('fault_level')}")
            print(f"  缁勪欢: {result.get('component')}")
            print()
            
    except Exception as e:
        print(f"鉂?妫€娴嬪け璐? {e}")
        import traceback
        traceback.print_exc()

def debug_database_records():
    """璋冭瘯鏁版嵁搴撹褰?""
    print("\n" + "=" * 60)
    print("璋冭瘯鏁版嵁搴撹褰?)
    print("=" * 60)
    
    # 鑾峰彇涓€涓狢MG妯″瀷
    cmg_model = PHMModel.objects.first()
    if not cmg_model:
        print("鉂?娌℃湁鎵惧埌PHM妯″瀷")
        return
    
    # 鑾峰彇涓€涓狢MG瀹炰緥
    cmg = PHM.objects.filter(cmg_model=cmg_model).first()
    if not cmg:
        print("鉂?娌℃湁鎵惧埌PHM瀹炰緥")
        return
    
    # 鑾峰彇鏈€鏂扮殑鏁版嵁鐐?
    latest_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    if not latest_data:
        print("鉂?娌℃湁鎵惧埌鏁版嵁鐐?)
        return
    
    print(f"鏁版嵁鐐? {latest_data.timestamp}")
    
    # 妫€鏌ヨ鏁版嵁鐐圭殑瑙勫垯妫€娴嬬粨鏋?
    rule_results = RuleDetectionResult.objects.filter(data_point=latest_data)
    print(f"鏁版嵁搴撲腑鐨勮鍒欐娴嬬粨鏋? {rule_results.count()} 鏉?)
    
    for result in rule_results:
        print(f"  瑙勫垯: {result.rule_definition.rule_id}")
        print(f"  鏁呴殰: {result.fault_definition.fault_name}")
        print(f"  瑙﹀彂: {result.is_triggered}")
        print(f"  鍒嗘暟: {result.confidence_score}")
        print(f"  鍒涘缓鏃堕棿: {result.created_at}")
        print()
    
    # 妫€鏌ユ墍鏈夎鍒?
    all_rules = RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True)
    print(f"鍦ㄧ嚎瑙勫垯鎬绘暟: {all_rules.count()}")
    
    for rule in all_rules:
        # 妫€鏌ユ槸鍚︽湁瀵瑰簲鐨勬娴嬬粨鏋?
        has_result = RuleDetectionResult.objects.filter(
            data_point=latest_data,
            rule_definition=rule
        ).exists()
        
        status = "鉁? if has_result else "鉂?
        print(f"{status} 瑙勫垯 {rule.rule_id}: {rule.fault_definition.fault_name}")
        
        # 妫€鏌ユ槸鍚﹀寘鍚壒瀹氬嚱鏁?
        if 'level(' in rule.rule_expression:
            print(f"    馃攳 鍖呭惈level鍑芥暟")
        if 'ma_diff(' in rule.rule_expression:
            print(f"    馃攳 鍖呭惈ma_diff鍑芥暟")

def test_specific_rule_detection():
    """娴嬭瘯鐗瑰畾瑙勫垯鐨勬娴?""
    print("\n" + "=" * 60)
    print("娴嬭瘯鐗瑰畾瑙勫垯妫€娴?)
    print("=" * 60)
    
    # 鑾峰彇涓€涓狢MG妯″瀷
    cmg_model = PHMModel.objects.first()
    if not cmg_model:
        print("鉂?娌℃湁鎵惧埌PHM妯″瀷")
        return
    
    # 鑾峰彇涓€涓狢MG瀹炰緥
    cmg = PHM.objects.filter(cmg_model=cmg_model).first()
    if not cmg:
        print("鉂?娌℃湁鎵惧埌PHM瀹炰緥")
        return
    
    # 鑾峰彇鏈€鏂扮殑鏁版嵁鐐?
    latest_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    if not latest_data:
        print("鉂?娌℃湁鎵惧埌鏁版嵁鐐?)
        return
    
    # 鏌ユ壘鍖呭惈level鎴杕a_diff鍑芥暟鐨勮鍒?
    special_rules = RuleDefinition.objects.filter(
        cmg_model=cmg_model,
        is_online=True
    ).filter(
        rule_expression__icontains='level'
    ) | RuleDefinition.objects.filter(
        cmg_model=cmg_model,
        is_online=True
    ).filter(
        rule_expression__icontains='ma_diff'
    )
    
    print(f"鎵惧埌 {special_rules.count()} 鏉″寘鍚壒娈婂嚱鏁扮殑瑙勫垯")
    
    for rule in special_rules:
        print(f"\n娴嬭瘯瑙勫垯: {rule.rule_id}")
        print(f"琛ㄨ揪寮? {rule.rule_expression}")
        print(f"鏁呴殰: {rule.fault_definition.fault_name}")
        
        # 鍒涘缓娴嬭瘯鏁版嵁
        test_data = latest_data.data.copy() if isinstance(latest_data.data, dict) else {}
        
        # 纭繚鍖呭惈蹇呰鐨勫弬鏁?
        if '楂橀€熺數鏈虹數娴? not in test_data:
            test_data['楂橀€熺數鏈虹數娴?] = 0.8
        if '浣庨€熺數鏈虹數娴? not in test_data:
            test_data['浣庨€熺數鏈虹數娴?] = 0.6
        if '娓╁害' not in test_data:
            test_data['娓╁害'] = 75.0
        if '鍘嬪姏' not in test_data:
            test_data['鍘嬪姏'] = 100.0
        if '杞€? not in test_data:
            test_data['杞€?] = 1500.0
        
        print(f"娴嬭瘯鏁版嵁: {test_data}")
        
        # 鍒涘缓澧炲己妫€娴嬪櫒
        from rule_detection.algorithms.rule.enhanced_rule_parser import EnhancedRuleParser
        from rule_detection.algorithms.rule.enhanced_rule_detector import EnhancedRuleDetector
        
        parameter_names = list(test_data.keys())
        parser = EnhancedRuleParser(parameter_names)
        parse_result = parser.parse(rule.rule_expression)
        
        rule_config = {
            "rules": [{
                "rule_id": rule.rule_id,
                "fault_name": rule.fault_definition.fault_name,
                "fault_level": rule.fault_definition.fault_level,
                "component": rule.fault_definition.component,
                "expression": rule.rule_expression,
                "related_parameters": list(parse_result.related_parameters),
                "is_online": rule.is_online,
                "parse_result": parse_result
            }],
            "parameter_names": parameter_names,
            "fault_name_map": {}
        }
        
        detector = EnhancedRuleDetector(rule_config)
        
        # 鎵ц妫€娴?
        try:
            results = detector.detect(test_data, latest_data.timestamp)
            print(f"妫€娴嬬粨鏋? {len(results)} 鏉?)
            
            for result in results:
                print(f"  瑙﹀彂: {result.get('is_triggered')}")
                print(f"  鍒嗘暟: {result.get('confidence_score')}")
                print(f"  璇︽儏: {result}")
                
        except Exception as e:
            print(f"鉂?妫€娴嬪け璐? {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("寮€濮嬭皟璇曡鍒欐娴嬬粨鏋滀繚瀛橀棶棰?..")
    
    # 1. 璋冭瘯瑙勫垯瑙ｆ瀽
    debug_rule_parsing()
    
    # 2. 璋冭瘯瑙勫垯妫€娴?
    debug_rule_detection()
    
    # 3. 璋冭瘯鏁版嵁搴撹褰?
    debug_database_records()
    
    # 4. 娴嬭瘯鐗瑰畾瑙勫垯妫€娴?
    test_specific_rule_detection()
    
    print("\n璋冭瘯瀹屾垚!")

