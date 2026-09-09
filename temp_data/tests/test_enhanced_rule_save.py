#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
娴嬭瘯澧炲己瑙勫垯妫€娴嬬殑淇濆瓨鍜岀疆淇″害璁＄畻
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
import logging
from datetime import datetime, timezone

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_rule_save():
    """娴嬭瘯澧炲己瑙勫垯妫€娴嬬殑淇濆瓨鍔熻兘"""
    print("=" * 60)
    print("娴嬭瘯澧炲己瑙勫垯妫€娴嬬殑淇濆瓨鍔熻兘")
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
    
    # 鑾峰彇鎵€鏈夊湪绾胯鍒?
    all_rules = RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True)
    print(f"鍦ㄧ嚎瑙勫垯鎬绘暟: {all_rules.count()}")
    
    for rule in all_rules:
        print(f"  - {rule.rule_id}: {rule.fault_definition.fault_name}")
    
    # 鍒涘缓娴嬭瘯鏁版嵁鐐?
    test_data = {
        '婧愮爜': 'TEST_ENHANCED_SAVE',
        '缂栧彿': 777.0,
        '甯ц鏁?: 777.0,
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
    
    # 鍒涘缓PHMData瀵硅薄
    cmg_data = PHMData.objects.create(
        cmg=cmg,
        timestamp=datetime.now(timezone.utc),
        data=test_data
    )
    
    print(f"\n鍒涘缓娴嬭瘯鏁版嵁鐐? {cmg_data.id}")
    print(f"鏁版嵁鍙傛暟: {list(test_data.keys())}")
    
    # 鎵ц澧炲己瑙勫垯妫€娴?
    try:
        results = evaluate_rules_with_enhanced_detector(cmg_data)
        print(f"\n妫€娴嬬粨鏋? {len(results)} 鏉?)
        
        for result in results:
            print(f"  瑙勫垯: {result.get('rule_id')}")
            print(f"  鏁呴殰: {result.get('fault_name')}")
            print(f"  瑙﹀彂: {result.get('is_triggered')}")
            print(f"  鍒嗘暟: {result.get('score')}")
            print(f"  绛夌骇: {result.get('fault_level')}")
            print(f"  缁勪欢: {result.get('component')}")
            if 'detection_note' in result:
                print(f"  澶囨敞: {result.get('detection_note')}")
            print()
            
    except Exception as e:
        print(f"鉂?妫€娴嬪け璐? {e}")
        import traceback
        traceback.print_exc()
    
    # 妫€鏌ユ暟鎹簱璁板綍
    rule_results = RuleDetectionResult.objects.filter(data_point=cmg_data)
    print(f"鏁版嵁搴撲腑鐨勮鍒欐娴嬬粨鏋? {rule_results.count()} 鏉?)
    
    if rule_results.count() != all_rules.count():
        print(f"鈿狅笍  璀﹀憡: 鏁版嵁搴撹褰曟暟 ({rule_results.count()}) 涓庤鍒欐暟 ({all_rules.count()}) 涓嶅尮閰?)
    
    # 缁熻瑙﹀彂鍜屾湭瑙﹀彂鐨勮鍒?
    triggered_count = 0
    non_triggered_count = 0
    
    for result in rule_results:
        print(f"  馃搳 鏁版嵁搴撹褰?")
        print(f"    瑙勫垯: {result.rule_definition.rule_id}")
        print(f"    鏁呴殰: {result.fault_definition.fault_name}")
        print(f"    瑙﹀彂: {result.is_triggered}")
        print(f"    鍒嗘暟: {result.confidence_score}")
        print(f"    鍒涘缓鏃堕棿: {result.created_at}")
        
        if result.is_triggered:
            triggered_count += 1
        else:
            non_triggered_count += 1
        print()
    
    print(f"馃搱 缁熻缁撴灉:")
    print(f"  鎬昏鍒欐暟: {all_rules.count()}")
    print(f"  鏁版嵁搴撹褰曟暟: {rule_results.count()}")
    print(f"  瑙﹀彂瑙勫垯鏁? {triggered_count}")
    print(f"  鏈Е鍙戣鍒欐暟: {non_triggered_count}")
    
    # 妫€鏌ョ疆淇″害鍒嗗竷
    confidence_scores = [result.confidence_score for result in rule_results]
    if confidence_scores:
        print(f"  缃俊搴︾粺璁?")
        print(f"    鏈€灏忓€? {min(confidence_scores):.4f}")
        print(f"    鏈€澶у€? {max(confidence_scores):.4f}")
        print(f"    骞冲潎鍊? {sum(confidence_scores)/len(confidence_scores):.4f}")
        
        # 妫€鏌ユ槸鍚︽湁杩炵画鐨勭疆淇″害鍊?
        unique_scores = set(confidence_scores)
        print(f"    鍞竴鍊兼暟閲? {len(unique_scores)}")
        if len(unique_scores) > 2:
            print(f"    鉁?缃俊搴﹀€艰繛缁垎甯冭壇濂?)
        else:
            print(f"    鈿狅笍  缃俊搴﹀€煎垎甯冨彲鑳借繃浜庣鏁?)
    
    # 娓呯悊娴嬭瘯鏁版嵁
    cmg_data.delete()
    print(f"\n娓呯悊娴嬭瘯鏁版嵁鐐? {cmg_data.id}")

def test_confidence_calculation():
    """娴嬭瘯缃俊搴﹁绠?""
    print("\n" + "=" * 60)
    print("娴嬭瘯缃俊搴﹁绠?)
    print("=" * 60)
    
    from rule_detection.algorithms.rule.enhanced_rule_detector import EnhancedRuleDetector
    
    # 鍒涘缓娴嬭瘯妫€娴嬪櫒
    rule_config = {
        "rules": [],
        "parameter_names": ["楂橀€熺數鏈虹數娴?, "浣庨€熻浆閫?, "楂橀€熻浆閫?],
        "fault_name_map": {}
    }
    
    detector = EnhancedRuleDetector(rule_config)
    
    # 娴嬭瘯涓嶅悓绫诲瀷鐨勮鍒欒〃杈惧紡
    test_cases = [
        # (缁撴灉鍊? 瑙勫垯琛ㄨ揪寮? 鏈熸湜鐨勭疆淇″害鐗瑰緛)
        (True, 'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0', "甯冨皵鐪熷€?),
        (False, 'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0', "甯冨皵鍋囧€?),
        (5.0, 'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0', "澶т簬闃堝€?),
        (2.0, 'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0', "灏忎簬闃堝€?),
        (0.5, 'ma_diff("楂橀€熺數鏈虹數娴?, 60) > 0.000623469', "鎺ヨ繎闃堝€?),
        (0.0, 'ma_diff("楂橀€熺數鏈虹數娴?, 60) > 0.000623469', "杩滀綆浜庨槇鍊?),
        (None, 'level("楂橀€熻浆閫?, 7000, 0.020027) > 3.0', "绌哄€?),
    ]
    
    for result, expression, description in test_cases:
        confidence = detector._calculate_confidence_score(result, expression)
        print(f"  娴嬭瘯: {description}")
        print(f"    缁撴灉: {result}")
        print(f"    琛ㄨ揪寮? {expression}")
        print(f"    缃俊搴? {confidence:.4f}")
        print(f"    鏄惁鍦?-1鑼冨洿: {'鉁? if 0.0 <= confidence <= 1.0 else '鉂?}")
        print()

if __name__ == "__main__":
    print("寮€濮嬫祴璇曞寮鸿鍒欐娴嬬殑淇濆瓨鍜岀疆淇″害璁＄畻...")
    
    # 1. 娴嬭瘯缃俊搴﹁绠?
    test_confidence_calculation()
    
    # 2. 娴嬭瘯澧炲己瑙勫垯淇濆瓨
    test_enhanced_rule_save()
    
    print("\n娴嬭瘯瀹屾垚!")

