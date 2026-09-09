#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
娴嬭瘯瑙勫垯瑙﹀彂鏃剁殑鏁版嵁搴撲繚瀛?
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
from datetime import datetime, timezone

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def test_rule_trigger_with_artificial_data():
    """浣跨敤浜哄伐鏋勯€犵殑瑙﹀彂鏁版嵁娴嬭瘯瑙勫垯淇濆瓨"""
    print("=" * 60)
    print("娴嬭瘯瑙勫垯瑙﹀彂鏃剁殑鏁版嵁搴撲繚瀛?)
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
    
    print(f"浣跨敤妯″瀷: {cmg_model.model_name}")
    
    # 鏌ユ壘鍖呭惈鐗规畩鍑芥暟鐨勮鍒?
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
        
        # 瑙ｆ瀽瑙勫垯浠ヤ簡瑙ｅ弬鏁伴渶姹?
        parser = EnhancedRuleParser(["楂橀€熺數鏈虹數娴?, "浣庨€熻浆閫?, "楂橀€熻浆閫?, "浣庨€烝鐩哥數娴?])
        parse_result = parser.parse(rule.rule_expression)
        
        # 鏋勯€犱細瑙﹀彂瑙勫垯鐨勬暟鎹?
        trigger_data = {}
        
        if 'level(' in rule.rule_expression:
            # 瀵逛簬level鍑芥暟锛屾瀯閫犱竴涓細瑙﹀彂鐨勬暟鎹?
            if '浣庨€熻浆閫? in rule.rule_expression:
                # 瑙勫垯: level("浣庨€熻浆閫?, 0.002918, 2.51621) > 3.0
                # 鏋勯€犱竴涓細瑙﹀彂鐨勬暟鎹細璁﹍evel鍊?> 3.0
                median = 0.002918
                mad = 2.51621
                # 璁?|x - median| / mad > 3.0
                # 鍗?|x - 0.002918| > 3.0 * 2.51621 = 7.54863
                # 鎵€浠?x > 0.002918 + 7.54863 = 7.551548 鎴?x < 0.002918 - 7.54863 = -7.545712
                trigger_data['浣庨€熻浆閫?] = 10.0  # 杩滃ぇ浜庨槇鍊?
                
            elif '楂橀€熻浆閫? in rule.rule_expression:
                # 瑙勫垯: level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0
                median = 7000
                mad = 0.020027
                # 璁?|x - 7000| > 3.0 * 0.020027 = 0.060081
                trigger_data['楂橀€熻浆閫?] = 7100.0  # 杩滃ぇ浜庨槇鍊?
                
            elif '浣庨€烝鐩哥數娴? in rule.rule_expression:
                # 瑙勫垯: level("浣庨€烝鐩哥數娴?, 0.054688, 0.027344) > 3.0
                median = 0.054688
                mad = 0.027344
                # 璁?|x - 0.054688| > 3.0 * 0.027344 = 0.082032
                trigger_data['浣庨€烝鐩哥數娴?] = 0.2  # 杩滃ぇ浜庨槇鍊?
                
        elif 'ma_diff(' in rule.rule_expression:
            # 瀵逛簬ma_diff鍑芥暟锛屾瀯閫犱竴涓細瑙﹀彂鐨勬暟鎹?
            if '楂橀€熺數鏈虹數娴? in rule.rule_expression:
                # 瑙勫垯: ma_diff("楂橀€熺數鏈虹數娴?, 60) > 0.000207828 + 3*0.000138547
                # 闃堝€?= 0.000207828 + 3*0.000138547 = 0.000623469
                # 闇€瑕佹瀯閫犱竴涓猰a_diff鍊?> 0.000623469鐨勬暟鎹?
                # 鐢变簬ma_diff闇€瑕佸巻鍙叉暟鎹紝鎴戜滑璁剧疆涓€涓緝澶х殑褰撳墠鍊?
                trigger_data['楂橀€熺數鏈虹數娴?] = 2.0  # 璁剧疆涓€涓緝澶х殑鍊?
                
        elif 'rollstd(' in rule.rule_expression:
            # 瀵逛簬rollstd鍑芥暟锛屾瀯閫犱竴涓細瑙﹀彂鐨勬暟鎹?
            if '楂橀€熺數鏈虹數鍘? in rule.rule_expression:
                # 瑙勫垯: rollstd("楂橀€熺數鏈虹數鍘?, 120) > 0.013633 + 3*0.00527085
                # 闃堝€?= 0.013633 + 3*0.00527085 = 0.02944655
                # 闇€瑕佹瀯閫犱竴涓猺ollstd鍊?> 0.02944655鐨勬暟鎹?
                trigger_data['楂橀€熺數鏈虹數鍘?] = 5.0  # 璁剧疆涓€涓緝澶х殑鍊?
        
        print(f"鏋勯€犵殑瑙﹀彂鏁版嵁: {trigger_data}")
        
        # 鍒涘缓娴嬭瘯鏁版嵁鐐?
        test_data = {
            '婧愮爜': 'TEST_DATA',
            '缂栧彿': 999.0,
            '甯ц鏁?: 999.0,
            '鑷瀛?: 3000.0,
            ' +5V閬ユ祴': 3.671875,
            ' +12V閬ユ祴': 3.359375,
            ' +45V閬ユ祴': 4.140625,
            ' 100V閬ユ祴': 4.257813,
            'OSTM_Frame0': 0.0,
            'OSTM_Frame1': 0.0,
            '浣庨€熶綅缃?: 89.996738,
            '浣庨€熷３娓?: 2.460938,
            '浣庨€熻浆閫?: 0.005847,
            '楂橀€熻浆閫?: 7000.000477,
            '浣庨€烝鐩哥數娴?: 0.054688,
            '浣庨€烠鐩哥數娴?: -0.013672,
            '瀹氳閿佸畾绮惧害': 0.00086,
            '楂橀€熺數鏈虹數鍘?: 3.359375,
            '楂橀€熺數鏈虹數娴?: 0.884502,
            '楂橀€熷浐绱х杞存俯': 2.734375,
            '楂橀€熸粦鍔ㄧ杞存俯': 2.734375,
            '褰撳墠浣嶇疆閿佸畾绮惧害': '-',
            '楂橀€熻浆閫熸帶鍒剁簿搴?: 6e-05,
            '浣庨€熻閫熷害鎺у埗绮惧害': '-',
            '楂橀€熷浐绱х杞存俯娓╁害': 3.06,
            '楂橀€熸粦鍔ㄧ杞存俯娓╁害': 3.06,
            '楂橀€熻浆閫熸帶鍒剁ǔ瀹氬害': 0.00106,
            '浣庨€熻閫熷害鎺у埗绋冲畾搴?: '-'
        }
        
        # 鏇存柊瑙﹀彂鏁版嵁
        test_data.update(trigger_data)
        
        # 鍒涘缓PHMData瀵硅薄
        cmg_data = PHMData.objects.create(
            cmg=cmg,
            timestamp=datetime.now(timezone.utc),
            data=test_data
        )
        
        print(f"鍒涘缓娴嬭瘯鏁版嵁鐐? {cmg_data.id}")
        
        # 鎵ц瑙勫垯妫€娴?
        try:
            results = evaluate_rules_with_enhanced_detector(cmg_data)
            print(f"妫€娴嬬粨鏋? {len(results)} 鏉?)
            
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
        
        # 妫€鏌ユ暟鎹簱璁板綍
        rule_results = RuleDetectionResult.objects.filter(data_point=cmg_data)
        print(f"鏁版嵁搴撲腑鐨勮鍒欐娴嬬粨鏋? {rule_results.count()} 鏉?)
        
        for result in rule_results:
            print(f"  鉁?鏁版嵁搴撹褰?")
            print(f"    瑙勫垯: {result.rule_definition.rule_id}")
            print(f"    鏁呴殰: {result.fault_definition.fault_name}")
            print(f"    瑙﹀彂: {result.is_triggered}")
            print(f"    鍒嗘暟: {result.confidence_score}")
            print(f"    鍒涘缓鏃堕棿: {result.created_at}")
            print()
        
        # 娓呯悊娴嬭瘯鏁版嵁
        cmg_data.delete()
        print(f"娓呯悊娴嬭瘯鏁版嵁鐐? {cmg_data.id}")

def test_simple_rule_trigger():
    """娴嬭瘯绠€鍗曡鍒欑殑瑙﹀彂"""
    print("\n" + "=" * 60)
    print("娴嬭瘯绠€鍗曡鍒欒Е鍙?)
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
    
    # 鍒涘缓涓€涓畝鍗曠殑娴嬭瘯瑙勫垯锛堝鏋滀笉瀛樺湪锛?
    fault_def, created = FaultDefinition.objects.get_or_create(
        cmg_model=cmg_model,
        fault_name="娴嬭瘯鏁呴殰",
        defaults={
            'fault_level': 1,
            'component': '娴嬭瘯缁勪欢',
            'description': '娴嬭瘯鏁呴殰鎻忚堪'
        }
    )
    
    # 鍒涘缓涓€涓畝鍗曠殑娴嬭瘯瑙勫垯
    test_rule, created = RuleDefinition.objects.get_or_create(
        cmg_model=cmg_model,
        rule_id="test_simple_rule",
        defaults={
            'rule_expression': '楂橀€熺數鏈虹數娴?> 1.0',
            'fault_definition': fault_def,
            'is_online': True,
            'source': 'test',
            'plan_description': '娴嬭瘯瑙勫垯'
        }
    )
    
    print(f"浣跨敤娴嬭瘯瑙勫垯: {test_rule.rule_id}")
    print(f"琛ㄨ揪寮? {test_rule.rule_expression}")
    
    # 鍒涘缓浼氳Е鍙戣鍒欑殑鏁版嵁
    trigger_data = {
        '婧愮爜': 'TEST_SIMPLE',
        '缂栧彿': 888.0,
        '甯ц鏁?: 888.0,
        '鑷瀛?: 3000.0,
        '楂橀€熺數鏈虹數娴?: 1.5,  # 澶т簬1.0锛屼細瑙﹀彂瑙勫垯
        '楂橀€熺數鏈虹數鍘?: 3.359375,
        '浣庨€熻浆閫?: 0.005847,
        '楂橀€熻浆閫?: 7000.000477,
        '浣庨€烝鐩哥數娴?: 0.054688,
    }
    
    # 鍒涘缓PHMData瀵硅薄
    cmg_data = PHMData.objects.create(
        cmg=cmg,
        timestamp=datetime.now(timezone.utc),
        data=trigger_data
    )
    
    print(f"鍒涘缓娴嬭瘯鏁版嵁鐐? {cmg_data.id}")
    print(f"鏁版嵁: {trigger_data}")
    
    # 鎵ц瑙勫垯妫€娴?
    try:
        results = evaluate_rules_with_enhanced_detector(cmg_data)
        print(f"妫€娴嬬粨鏋? {len(results)} 鏉?)
        
        for result in results:
            print(f"  瑙勫垯: {result.get('rule_id')}")
            print(f"  鏁呴殰: {result.get('fault_name')}")
            print(f"  瑙﹀彂: {result.get('is_triggered')}")
            print(f"  鍒嗘暟: {result.get('score')}")
            print()
            
    except Exception as e:
        print(f"鉂?妫€娴嬪け璐? {e}")
        import traceback
        traceback.print_exc()
    
    # 妫€鏌ユ暟鎹簱璁板綍
    rule_results = RuleDetectionResult.objects.filter(data_point=cmg_data)
    print(f"鏁版嵁搴撲腑鐨勮鍒欐娴嬬粨鏋? {rule_results.count()} 鏉?)
    
    for result in rule_results:
        print(f"  鉁?鏁版嵁搴撹褰?")
        print(f"    瑙勫垯: {result.rule_definition.rule_id}")
        print(f"    鏁呴殰: {result.fault_definition.fault_name}")
        print(f"    瑙﹀彂: {result.is_triggered}")
        print(f"    鍒嗘暟: {result.confidence_score}")
        print()
    
    # 娓呯悊娴嬭瘯鏁版嵁
    cmg_data.delete()
    print(f"娓呯悊娴嬭瘯鏁版嵁鐐? {cmg_data.id}")

if __name__ == "__main__":
    print("寮€濮嬫祴璇曡鍒欒Е鍙戞椂鐨勬暟鎹簱淇濆瓨...")
    
    # 1. 娴嬭瘯绠€鍗曡鍒欒Е鍙?
    test_simple_rule_trigger()
    
    # 2. 娴嬭瘯澶嶆潅瑙勫垯瑙﹀彂
    test_rule_trigger_with_artificial_data()
    
    print("\n娴嬭瘯瀹屾垚!")

