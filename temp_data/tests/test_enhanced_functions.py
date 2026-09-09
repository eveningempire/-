#!/usr/bin/env python
"""
娴嬭瘯澧炲己鐗堣鍒欐娴嬪姛鑳?
楠岃瘉楂樼骇缁熻鍑芥暟鍜屽尯闂存娴?
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

from rule_detection.algorithms.rule.enhanced_rule_parser import EnhancedRuleParser
from rule_detection.algorithms.rule.enhanced_rule_detector import EnhancedRuleDetector, AdvancedStatisticalFunctions

def test_advanced_statistical_functions():
    """娴嬭瘯楂樼骇缁熻鍑芥暟"""
    print("=" * 80)
    print("娴嬭瘯楂樼骇缁熻鍑芥暟")
    print("=" * 80)
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    test_data = [10, 12, 15, 18, 22, 25, 28, 30, 32, 35]
    timestamps = [1000 + i * 100 for i in range(len(test_data))]
    
    calculator = AdvancedStatisticalFunctions()
    
    # 娴嬭瘯鍩虹缁熻鍑芥暟
    print(f"娴嬭瘯鏁版嵁: {test_data}")
    print(f"鏃堕棿鎴? {timestamps}")
    print()
    
    print("鍩虹缁熻鍑芥暟娴嬭瘯:")
    print(f"  mean: {calculator.mean(test_data):.2f}")
    print(f"  std: {calculator.std(test_data):.2f}")
    print(f"  var: {calculator.var(test_data):.2f}")
    print(f"  mad: {calculator.mad(test_data):.2f}")
    print(f"  rms: {calculator.rms(test_data):.2f}")
    print(f"  max: {calculator.max(test_data):.2f}")
    print(f"  min: {calculator.min(test_data):.2f}")
    print(f"  range: {calculator.range(test_data):.2f}")
    print()
    
    print("楂樼骇缁熻鍑芥暟娴嬭瘯:")
    print(f"  slope: {calculator.slope(test_data, timestamps):.4f}")
    print(f"  diffmean: {calculator.diffmean(test_data):.2f}")
    print(f"  diffstd: {calculator.diffstd(test_data):.2f}")
    print(f"  ma(5): {calculator.ma(test_data, 5):.2f}")
    print(f"  ma_diff(5): {calculator.ma_diff(test_data, 5):.2f}")
    print(f"  autocorr(1): {calculator.autocorr(test_data, 1):.4f}")
    print()

def test_enhanced_parser():
    """娴嬭瘯澧炲己鐗堣В鏋愬櫒"""
    print("=" * 80)
    print("娴嬭瘯澧炲己鐗堣鍒欒В鏋愬櫒")
    print("=" * 80)
    
    parameters = ["娓╁害", "鍘嬪姏", "杞€?, "鐢垫祦", "鐢靛帇", "鎸姩"]
    faults = ["杩囩儹鏁呴殰", "鍘嬪姏寮傚父", "杞€熻繃楂?, "鐢垫祦杩囧ぇ", "鎸姩寮傚父"]
    
    parser = EnhancedRuleParser(parameters, faults)
    
    # 娴嬭瘯瑙勫垯
    test_rules = [
        'mean("娓╁害") > 80',
        'std("鍘嬪姏") > 10',
        'var("杞€?) > 100',
        'slope("娓╁害", 20) > 0.5',
        'ma("鍘嬪姏", 10) > 100',
        'autocorr("鎸姩", 5) > 0.8',
        'mean("娓╁害") > 80 and std("鍘嬪姏") < 5',
        'slope("杞€?, 15) > 0.1 or ma_diff("鐢垫祦", 8) > 2',
        'diffmean("娓╁害", 10) > 1.0 and diffstd("鍘嬪姏", 5) < 2.0',
        'range("鎸姩") > 15 and autocorr("鎸姩", 3) < 0.6'
    ]
    
    for i, rule in enumerate(test_rules, 1):
        print(f"\n{i}. 娴嬭瘯瑙勫垯: {rule}")
        result = parser.parse(rule)
        
        print(f"   瑙ｆ瀽缁撴灉: {result.expression}")
        print(f"   鐩稿叧鍙傛暟: {list(result.related_parameters)}")
        print(f"   绐楀彛闇€姹? {result.window_requirements}")
        print(f"   閿欒鏁? {result.error_count}, 璀﹀憡鏁? {result.warning_count}")
        
        if result.log_messages:
            print(f"   鏃ュ織娑堟伅:")
            for msg in result.log_messages:
                print(f"     {msg['type']}: {msg['message']}")

def test_enhanced_detector():
    """娴嬭瘯澧炲己鐗堟娴嬪櫒"""
    print("=" * 80)
    print("娴嬭瘯澧炲己鐗堣鍒欐娴嬪櫒")
    print("=" * 80)
    
    # 鍒涘缓娴嬭瘯瑙勫垯閰嶇疆
    rule_config = {
        "rules": [
            {
                "rule_id": "temp_mean_rule",
                "fault_name": "娓╁害鍧囧€煎紓甯?,
                "fault_level": 2,
                "component": "鍙戝姩鏈?,
                "expression": 'mean("娓╁害") > 85',
                "related_parameters": ["娓╁害"],
                "is_online": True
            },
            {
                "rule_id": "pressure_std_rule",
                "fault_name": "鍘嬪姏娉㈠姩寮傚父",
                "fault_level": 1,
                "component": "娑插帇绯荤粺",
                "expression": 'std("鍘嬪姏") > 8',
                "related_parameters": ["鍘嬪姏"],
                "is_online": True
            },
            {
                "rule_id": "temp_slope_rule",
                "fault_name": "娓╁害涓婂崌杩囧揩",
                "fault_level": 3,
                "component": "鍙戝姩鏈?,
                "expression": 'slope("娓╁害", 10) > 0.3',
                "related_parameters": ["娓╁害"],
                "is_online": True
            },
            {
                "rule_id": "vibration_autocorr_rule",
                "fault_name": "鎸姩鐩稿叧鎬у紓甯?,
                "fault_level": 2,
                "component": "浼犲姩绯荤粺",
                "expression": 'autocorr("鎸姩", 3) < 0.5',
                "related_parameters": ["鎸姩"],
                "is_online": True
            },
            {
                "rule_id": "complex_rule",
                "fault_name": "缁煎悎寮傚父",
                "fault_level": 4,
                "component": "绯荤粺",
                "expression": 'mean("娓╁害") > 80 and std("鍘嬪姏") > 5 and slope("杞€?, 15) > 0.1',
                "related_parameters": ["娓╁害", "鍘嬪姏", "杞€?],
                "is_online": True
            }
        ],
        "parameter_names": ["娓╁害", "鍘嬪姏", "杞€?, "鐢垫祦", "鐢靛帇", "鎸姩"],
        "fault_name_map": {}
    }
    
    # 鍒涘缓妫€娴嬪櫒
    detector = EnhancedRuleDetector(rule_config)
    
    print("妫€娴嬪櫒鍒濆鍖栧畬鎴?)
    print(f"鍙傛暟缂撳啿鍖? {list(detector.parameter_buffers.keys())}")
    print()
    
    # 妯℃嫙鏁版嵁鏇存柊鍜屾娴?
    current_time = time.time()
    
    print("寮€濮嬫ā鎷熸暟鎹娴?..")
    print("-" * 60)
    
    for i in range(30):
        # 妯℃嫙娓╁害閫愭笎涓婂崌
        base_temp = 70 + i * 1.5
        temp = base_temp + np.random.normal(0, 2)
        
        # 妯℃嫙鍘嬪姏娉㈠姩
        base_pressure = 100 + np.sin(i * 0.5) * 10
        pressure = base_pressure + np.random.normal(0, 3)
        
        # 妯℃嫙杞€熺ǔ瀹氫笂鍗?
        base_rpm = 1500 + i * 10
        rpm = base_rpm + np.random.normal(0, 20)
        
        # 妯℃嫙鎸姩锛堝悗鏈熷鍔犲櫔澹帮級
        if i < 20:
            vibration = 5 + np.random.normal(0, 1)
        else:
            vibration = 5 + np.random.normal(0, 3)  # 澧炲姞鍣０
        
        data_frame = {
            "娓╁害": temp,
            "鍘嬪姏": pressure,
            "杞€?: rpm,
            "鐢垫祦": 50 + np.random.normal(0, 2),
            "鐢靛帇": 220 + np.random.normal(0, 5),
            "鎸姩": vibration
        }
        
        timestamp = datetime.fromtimestamp(current_time + i)
        
        # 鏇存柊鏁版嵁
        detector.update_data(data_frame, timestamp, i)
        
        # 鎵ц妫€娴?
        results = detector.detect(data_frame, timestamp)
        
        if results:
            print(f"鏃堕棿 {timestamp.strftime('%H:%M:%S')}: 妫€娴嬪埌 {len(results)} 涓晠闅?)
            for result in results:
                print(f"  - {result['fault_name']} (绛夌骇{result['fault_level']}): 缃俊搴result['confidence_score']:.2f}")
        else:
            print(f"鏃堕棿 {timestamp.strftime('%H:%M:%S')}: 鏃犳晠闅?)
    
    print("-" * 60)
    
    # 鏄剧ず缂撳啿鍖轰俊鎭?
    print("\n缂撳啿鍖轰俊鎭?")
    buffer_info = detector.get_buffer_info()
    for param, info in buffer_info.items():
        print(f"  {param}: 澶у皬={info['current_size']}, 鏈€鏂板€?{info['latest_value']:.2f}")

def test_window_buffer():
    """娴嬭瘯绐楀彛缂撳啿鍖?""
    print("=" * 80)
    print("娴嬭瘯绐楀彛缂撳啿鍖?)
    print("=" * 80)
    
    from rule_detection.algorithms.rule.enhanced_rule_detector import WindowBuffer
    
    # 鍒涘缓缂撳啿鍖?
    buffer = WindowBuffer("娴嬭瘯鍙傛暟", max_window_size=10)
    
    print(f"鍒涘缓缂撳啿鍖? {buffer.param_name}, 鏈€澶х獥鍙? {buffer.max_window_size}")
    
    # 娣诲姞鏁版嵁鐐?
    for i in range(15):
        value = 10 + i * 2 + np.random.normal(0, 0.5)
        timestamp = 1000 + i * 100
        frame_index = i
        
        buffer.add_data_point(value, timestamp, frame_index)
        
        print(f"娣诲姞鏁版嵁鐐?{i}: 鍊?{value:.2f}, 鏃堕棿={timestamp}, 甯?{frame_index}")
        print(f"  褰撳墠缂撳啿鍖哄ぇ灏? {len(buffer.data_points)}")
        print(f"  褰撳墠鍊煎垪琛? {[f'{dp.value:.1f}' for dp in buffer.data_points]}")
        print()
    
    # 娴嬭瘯鑾峰彇涓嶅悓绐楀彛澶у皬鐨勬暟鎹?
    print("娴嬭瘯涓嶅悓绐楀彛澶у皬鐨勬暟鎹幏鍙?")
    for window_size in [5, 8, 10, 15]:
        values = buffer.get_values(window_size)
        timestamps = buffer.get_timestamps(window_size)
        print(f"  绐楀彛澶у皬 {window_size}: 鍊?{[f'{v:.1f}' for v in values]}")
        print(f"  鏃堕棿鎴? {timestamps}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("PHM澧炲己鐗堣鍒欐娴嬪姛鑳芥祴璇?)
    print("=" * 80)
    
    try:
        # 娴嬭瘯楂樼骇缁熻鍑芥暟
        test_advanced_statistical_functions()
        
        # 娴嬭瘯澧炲己鐗堣В鏋愬櫒
        test_enhanced_parser()
        
        # 娴嬭瘯绐楀彛缂撳啿鍖?
        test_window_buffer()
        
        # 娴嬭瘯澧炲己鐗堟娴嬪櫒
        test_enhanced_detector()
        
        print("\n" + "=" * 80)
        print("鎵€鏈夋祴璇曞畬鎴愶紒")
        print("=" * 80)
        
    except Exception as e:
        print(f"娴嬭瘯杩囩▼涓嚭鐜伴敊璇? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

