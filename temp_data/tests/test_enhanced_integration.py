#!/usr/bin/env python
"""
娴嬭瘯澧炲己鐗堣鍒欐娴嬪櫒涓庢壒閲忓鐞嗙郴缁熺殑闆嗘垚
楠岃瘉鏂拌鍒欒兘澶熺湡姝ｇ敤浜庢娴?
"""

import os
import sys
import django
import numpy as np
import time
from datetime import datetime, timedelta

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, PHMModel, PHMData
from rule_detection.models import RuleDefinition, FaultDefinition
from rule_detection.service import evaluate_rules_for_data_point
from data_management.batch_processing import BatchFileProcessor

def create_test_data():
    """鍒涘缓娴嬭瘯鏁版嵁"""
    print("=" * 80)
    print("鍒涘缓娴嬭瘯鏁版嵁")
    print("=" * 80)
    
    # 鑾峰彇鎴栧垱寤篊MG妯″瀷
    cmg_model, created = PHMModel.objects.get_or_create(
        model_name="TEST_MODEL_001",
        defaults={
            "description": "鐢ㄤ簬娴嬭瘯澧炲己鐗堣鍒欐娴嬪櫒鐨勬ā鍨?
        }
    )
    
    # 鑾峰彇鎴栧垱寤篊MG
    cmg, created = PHM.objects.get_or_create(
        cmg_id="TEST_PHM_001",
        defaults={
            "cmg_model": cmg_model,
            "name": "娴嬭瘯PHM"
        }
    )
    
    print(f"浣跨敤PHM妯″瀷: {cmg_model.model_name}")
    print(f"浣跨敤PHM: {cmg.name}")
    
    # 鍒涘缓娴嬭瘯鏁呴殰瀹氫箟
    fault_defs = []
    for fault_name, component in [
        ("娓╁害寮傚父", "鍙戝姩鏈?),
        ("鍘嬪姏娉㈠姩", "娑插帇绯荤粺"),
        ("杞€熻繃楂?, "浼犲姩绯荤粺"),
        ("鎸姩寮傚父", "浼犲姩绯荤粺")
    ]:
        fault_def, created = FaultDefinition.objects.get_or_create(
            cmg_model=cmg_model,
            fault_name=fault_name,
            defaults={
                "fault_level": 2,
                "component": component,
                "description": f"娴嬭瘯鏁呴殰: {fault_name}"
            }
        )
        fault_defs.append(fault_def)
        print(f"鏁呴殰瀹氫箟: {fault_name} -> {component}")
    
    # 鍒涘缓娴嬭瘯瑙勫垯瀹氫箟
    test_rules = [
        {
            "rule_id": "TEMP_MEAN_RULE",
            "rule_expression": 'mean("娓╁害") > 80',
            "fault_name": "娓╁害寮傚父",
            "description": "娓╁害鍘嗗彶鍧囧€艰秴杩?0搴?
        },
        {
            "rule_id": "PRESSURE_STD_RULE", 
            "rule_expression": 'std("鍘嬪姏") > 5',
            "fault_name": "鍘嬪姏娉㈠姩",
            "description": "鍘嬪姏鍘嗗彶鏍囧噯宸秴杩?"
        },
        {
            "rule_id": "TEMP_SLOPE_RULE",
            "rule_expression": 'slope("娓╁害", 10) > 0.3',
            "fault_name": "娓╁害寮傚父",
            "description": "娓╁害鍦?0甯у唴涓婂崌杩囧揩"
        },
        {
            "rule_id": "RPM_MA_RULE",
            "rule_expression": 'ma("杞€?, 15) > 1800',
            "fault_name": "杞€熻繃楂?,
            "description": "杞€?5甯хЩ鍔ㄥ钩鍧囪秴杩?800"
        },
        {
            "rule_id": "VIBRATION_AUTOCORR_RULE",
            "rule_expression": 'autocorr("鎸姩", 3) < 0.5',
            "fault_name": "鎸姩寮傚父",
            "description": "鎸姩鑷浉鍏虫€у紓甯?
        },
        {
            "rule_id": "COMPLEX_RULE",
            "rule_expression": 'mean("娓╁害") > 75 and std("鍘嬪姏") > 3 and slope("杞€?, 20) > 0.1',
            "fault_name": "娓╁害寮傚父",
            "description": "澶嶆潅瑙勫垯锛氭俯搴﹀潎鍊?75涓斿帇鍔涙爣鍑嗗樊>3涓旇浆閫熻秼鍔?0.1"
        }
    ]
    
    rule_defs = []
    for rule_info in test_rules:
        fault_def = next(f for f in fault_defs if f.fault_name == rule_info["fault_name"])
        rule_def, created = RuleDefinition.objects.get_or_create(
            cmg_model=cmg_model,
            rule_id=rule_info["rule_id"],
            defaults={
                "rule_expression": rule_info["rule_expression"],
                "fault_definition": fault_def,
                "is_online": True,
                "source": "test",
                "plan_description": rule_info["description"]
            }
        )
        rule_defs.append(rule_def)
        print(f"瑙勫垯瀹氫箟: {rule_info['rule_id']} -> {rule_info['rule_expression']}")
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    print("\n鍒涘缓娴嬭瘯鏁版嵁...")
    test_data_records = []
    from django.utils import timezone
    current_time = timezone.now()
    
    for i in range(50):  # 鍒涘缓50甯ф祴璇曟暟鎹?
        # 妯℃嫙娓╁害閫愭笎涓婂崌
        base_temp = 70 + i * 1.2
        temp = base_temp + np.random.normal(0, 2)
        
        # 妯℃嫙鍘嬪姏娉㈠姩
        base_pressure = 100 + np.sin(i * 0.3) * 8
        pressure = base_pressure + np.random.normal(0, 3)
        
        # 妯℃嫙杞€熺ǔ瀹氫笂鍗?
        base_rpm = 1500 + i * 8
        rpm = base_rpm + np.random.normal(0, 30)
        
        # 妯℃嫙鎸姩锛堝悗鏈熷鍔犲櫔澹帮級
        if i < 30:
            vibration = 5 + np.random.normal(0, 1)
        else:
            vibration = 5 + np.random.normal(0, 4)  # 澧炲姞鍣０
        
        # 鍒涘缓鏁版嵁璁板綍
        data_point = {
            "娓╁害": temp,
            "鍘嬪姏": pressure,
            "杞€?: rpm,
            "鎸姩": vibration,
            "鐢垫祦": 50 + np.random.normal(0, 2),
            "鐢靛帇": 220 + np.random.normal(0, 5)
        }
        
        timestamp = current_time + timedelta(seconds=i)
        
        # 淇濆瓨鍒版暟鎹簱
        cmg_data = PHMData.objects.create(
            cmg=cmg,
            timestamp=timestamp,
            data=data_point
        )
        test_data_records.append(cmg_data)
        
        if (i + 1) % 10 == 0:
            print(f"宸插垱寤?{i + 1}/50 甯ф暟鎹?)
    
    print(f"娴嬭瘯鏁版嵁鍒涘缓瀹屾垚锛屽叡 {len(test_data_records)} 甯?)
    
    return cmg, test_data_records, rule_defs

def test_single_point_detection():
    """娴嬭瘯鍗曠偣瑙勫垯妫€娴?""
    print("\n" + "=" * 80)
    print("娴嬭瘯鍗曠偣瑙勫垯妫€娴?)
    print("=" * 80)
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    cmg, test_data_records, rule_defs = create_test_data()
    
    # 閫夋嫨鍑犱釜鍏抽敭甯ц繘琛屾祴璇?
    test_frames = [10, 25, 40, 45]  # 涓嶅悓闃舵鐨勫抚
    
    for frame_index in test_frames:
        if frame_index < len(test_data_records):
            record = test_data_records[frame_index]
            print(f"\n娴嬭瘯甯?{frame_index}: {record.timestamp}")
            print(f"鏁版嵁: {record.data}")
            
            # 鎵ц瑙勫垯妫€娴?
            start_time = time.time()
            results = evaluate_rules_for_data_point(record)
            detection_time = time.time() - start_time
            
            print(f"妫€娴嬭€楁椂: {detection_time:.3f}绉?)
            print(f"妫€娴嬬粨鏋滄暟閲? {len(results)}")
            
            # 鏄剧ず瑙﹀彂缁撴灉
            triggered_rules = [r for r in results if r.get('is_triggered')]
            if triggered_rules:
                print("瑙﹀彂鐨勮鍒?")
                for result in triggered_rules:
                    print(f"  - {result.get('rule_id')}: {result.get('fault_name')} (缃俊搴? {result.get('score', 0):.2f})")
            else:
                print("娌℃湁瑙勫垯琚Е鍙?)

def test_batch_processing():
    """娴嬭瘯鎵归噺澶勭悊"""
    print("\n" + "=" * 80)
    print("娴嬭瘯鎵归噺澶勭悊")
    print("=" * 80)
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    cmg, test_data_records, rule_defs = create_test_data()
    
    print(f"寮€濮嬫壒閲忓鐞?{len(test_data_records)} 甯ф暟鎹?..")
    
    # 鍒涘缓鎵归噺澶勭悊鍣?
    processor = BatchFileProcessor()
    
    # 妯℃嫙鎵归噺澶勭悊
    start_time = time.time()
    
    # 鑾峰彇鎵€鏈夋暟鎹褰?
    records = list(PHMData.objects.filter(cmg=cmg).order_by('timestamp'))
    
    # 棰勫姞杞芥ā鍨嬮厤缃?
    models_config = processor._preload_detection_models(cmg)
    
    # 妯℃嫙IMS妫€娴嬬粨鏋滐紙绠€鍖栧鐞嗭級
    ims_results = [{"is_anomaly": True} for _ in records]  # 鍋囪鎵€鏈夊抚閮芥槸寮傚父甯?
    
    # 鎵ц瑙勫垯妫€娴?
    anomaly_records = [(i, record) for i, record in enumerate(records)]
    rule_results = processor._run_batch_rule_detection_optimized(anomaly_records, models_config)
    
    processing_time = time.time() - start_time
    
    print(f"鎵归噺澶勭悊瀹屾垚锛岃€楁椂: {processing_time:.2f}绉?)
    print(f"妫€娴嬪埌 {len(rule_results)} 涓鍒欒Е鍙?)
    
    # 鏄剧ず瑙﹀彂缁撴灉
    if rule_results:
        print("\n瑙﹀彂鐨勮鍒欒鎯?")
        for result in rule_results:
            print(f"  - {result.get('rule_name')}: {result.get('fault_name')} (缃俊搴? {result.get('confidence_score', 0):.2f})")
    
    # 妫€鏌ユ暟鎹簱涓殑缁撴灉
    from rule_detection.models import RuleDetectionResult
    db_results = RuleDetectionResult.objects.filter(data_point__cmg=cmg)
    print(f"\n鏁版嵁搴撲腑鐨勮鍒欐娴嬬粨鏋? {db_results.count()} 鏉?)
    
    for result in db_results[:5]:  # 鏄剧ず鍓?鏉?
        print(f"  - {result.rule_definition.rule_id}: {result.fault_definition.fault_name} (瑙﹀彂: {result.is_triggered})")

def test_rule_parsing():
    """娴嬭瘯瑙勫垯瑙ｆ瀽"""
    print("\n" + "=" * 80)
    print("娴嬭瘯瑙勫垯瑙ｆ瀽")
    print("=" * 80)
    
    from rule_detection.algorithms.rule.enhanced_rule_parser import EnhancedRuleParser
    
    # 娴嬭瘯瑙勫垯琛ㄨ揪寮?
    test_expressions = [
        'mean("娓╁害") > 80',
        'std("鍘嬪姏") > 5',
        'slope("娓╁害", 10) > 0.3',
        'ma("杞€?, 15) > 1800',
        'autocorr("鎸姩", 3) < 0.5',
        'mean("娓╁害") > 75 and std("鍘嬪姏") > 3 and slope("杞€?, 20) > 0.1'
    ]
    
    parameters = ["娓╁害", "鍘嬪姏", "杞€?, "鎸姩", "鐢垫祦", "鐢靛帇"]
    faults = ["娓╁害寮傚父", "鍘嬪姏娉㈠姩", "杞€熻繃楂?, "鎸姩寮傚父"]
    
    parser = EnhancedRuleParser(parameters, faults)
    
    for i, expression in enumerate(test_expressions, 1):
        print(f"\n{i}. 娴嬭瘯琛ㄨ揪寮? {expression}")
        result = parser.parse(expression)
        
        print(f"   瑙ｆ瀽缁撴灉: {result.expression}")
        print(f"   鐩稿叧鍙傛暟: {list(result.related_parameters)}")
        print(f"   绐楀彛闇€姹? {result.window_requirements}")
        print(f"   閿欒鏁? {result.error_count}, 璀﹀憡鏁? {result.warning_count}")

def cleanup_test_data():
    """娓呯悊娴嬭瘯鏁版嵁"""
    print("\n" + "=" * 80)
    print("娓呯悊娴嬭瘯鏁版嵁")
    print("=" * 80)
    
    try:
        # 鍒犻櫎娴嬭瘯PHM
        test_cmgs = PHM.objects.filter(cmg_id__startswith="TEST_PHM_")
        for cmg in test_cmgs:
            # 鍒犻櫎鐩稿叧鏁版嵁
            PHMData.objects.filter(cmg=cmg).delete()
            cmg.delete()
        
        # 鍒犻櫎娴嬭瘯妯″瀷
        test_models = PHMModel.objects.filter(model_name__startswith="TEST_MODEL_")
        for model in test_models:
            # 鍒犻櫎鐩稿叧瑙勫垯鍜屾晠闅滃畾涔?
            RuleDefinition.objects.filter(cmg_model=model).delete()
            FaultDefinition.objects.filter(cmg_model=model).delete()
            model.delete()
        
        print("娴嬭瘯鏁版嵁娓呯悊瀹屾垚")
        
    except Exception as e:
        print(f"娓呯悊娴嬭瘯鏁版嵁鏃跺嚭閿? {e}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("PHM澧炲己鐗堣鍒欐娴嬪櫒闆嗘垚娴嬭瘯")
    print("=" * 80)
    
    try:
        # 娴嬭瘯瑙勫垯瑙ｆ瀽
        test_rule_parsing()
        
        # 娴嬭瘯鍗曠偣妫€娴?
        test_single_point_detection()
        
        # 娴嬭瘯鎵归噺澶勭悊
        test_batch_processing()
        
        print("\n" + "=" * 80)
        print("鎵€鏈夋祴璇曞畬鎴愶紒")
        print("=" * 80)
        
    except Exception as e:
        print(f"娴嬭瘯杩囩▼涓嚭鐜伴敊璇? {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 娓呯悊娴嬭瘯鏁版嵁
        cleanup_test_data()

if __name__ == "__main__":
    main()

