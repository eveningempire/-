#!/usr/bin/env python
"""
妫€娴嬮鐜囨帶鍒跺姛鑳芥祴璇曡剼鏈?
"""

import os
import sys
import django
from datetime import datetime, timedelta

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.utils import timezone
from data_management.models import PHM, PHMData
from health_management.detection_frequency_controller import detection_frequency_controller, DetectionMode


def create_test_data(cmg_id="TEST_PHM", frame_count=1000, interval_seconds=1):
    """鍒涘缓娴嬭瘯鏁版嵁"""
    print(f"鍒涘缓娴嬭瘯鏁版嵁: {frame_count}甯э紝闂撮殧{interval_seconds}绉?)
    
    # 鑾峰彇鎴栧垱寤篊MG
    cmg, created = PHM.objects.get_or_create(
        cmg_id=cmg_id,
        defaults={
            'name': f'娴嬭瘯PHM_{cmg_id}',
            'cmg_model': 'TEST_MODEL'
        }
    )
    
    if created:
        print(f"鍒涘缓鏂癈MG: {cmg.name}")
    else:
        print(f"浣跨敤鐜版湁PHM: {cmg.name}")
    
    # 鍒犻櫎鐜版湁娴嬭瘯鏁版嵁
    PHMData.objects.filter(cmg=cmg).delete()
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    start_time = timezone.now() - timedelta(hours=1)
    test_data = []
    
    for i in range(frame_count):
        timestamp = start_time + timedelta(seconds=i * interval_seconds)
        data = {
            'temperature': 20 + i * 0.1,
            'pressure': 100 + i * 0.5,
            'voltage': 220 + i * 0.2,
            'current': 10 + i * 0.1
        }
        
        test_data.append(PHMData(
            cmg=cmg,
            timestamp=timestamp,
            data=data
        ))
    
    # 鎵归噺鍒涘缓
    PHMData.objects.bulk_create(test_data)
    print(f"鍒涘缓浜?{len(test_data)} 鏉℃祴璇曟暟鎹?)
    
    return cmg


def test_detection_frequency(cmg, mode_name):
    """娴嬭瘯妫€娴嬮鐜囨帶鍒?""
    print(f"\n娴嬭瘯妯″紡: {mode_name}")
    print("-" * 50)
    
    # 鑾峰彇鎵€鏈夎褰?
    records = list(PHMData.objects.filter(cmg=cmg).order_by('timestamp'))
    total_frames = len(records)
    
    print(f"鎬诲抚鏁? {total_frames}")
    
    # 璁剧疆妫€娴嬫ā寮?
    if mode_name == 'disabled':
        detection_frequency_controller.config.mode = DetectionMode.DISABLED
        detection_frequency_controller.config.enabled = False
    else:
        detection_frequency_controller.config.mode = DetectionMode(mode_name)
        detection_frequency_controller.config.enabled = True
    
    # 閫夋嫨甯?
    selected_indices = detection_frequency_controller.select_frames_for_detection(records)
    
    # 鑾峰彇鎽樿
    summary = detection_frequency_controller.get_detection_summary(total_frames, len(selected_indices))
    
    # 杈撳嚭缁撴灉
    print(f"閫変腑甯ф暟: {summary['selected_frames']}")
    print(f"妫€娴嬫瘮渚? {summary['detection_ratio']*100:.1f}%")
    print(f"鏃堕棿鑺傜渷: {summary['estimated_time_saving']}")
    print(f"妫€娴嬫ā寮? {summary['mode']}")
    print(f"鍚敤鐘舵€? {summary['enabled']}")
    
    # 鏄剧ず閫変腑鐨勫抚
    if selected_indices:
        print(f"\n閫変腑鐨勫抚 (鍓?0涓?:")
        for i, idx in enumerate(selected_indices[:10]):
            record = records[idx]
            print(f"  {i+1}. 绱㈠紩{idx}: {record.timestamp}")
        
        if len(selected_indices) > 10:
            print(f"  ... 杩樻湁 {len(selected_indices) - 10} 甯?)
    
    return summary


def main():
    """涓诲嚱鏁?""
    print("妫€娴嬮鐜囨帶鍒跺姛鑳芥祴璇?)
    print("=" * 60)
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    cmg = create_test_data("TEST_PHM_001", 5000, 1)
    
    # 娴嬭瘯涓嶅悓妯″紡
    modes = ['disabled', 'high_frequency', 'medium_frequency', 'low_frequency', 'adaptive']
    results = {}
    
    for mode in modes:
        results[mode] = test_detection_frequency(cmg, mode)
    
    # 杈撳嚭瀵规瘮缁撴灉
    print("\n" + "=" * 60)
    print("娴嬭瘯缁撴灉瀵规瘮")
    print("=" * 60)
    print(f"{'妯″紡':<15} {'妫€娴嬪抚鏁?:<10} {'妫€娴嬫瘮渚?:<10} {'鏃堕棿鑺傜渷':<10}")
    print("-" * 60)
    
    for mode, result in results.items():
        print(f"{mode:<15} {result['selected_frames']:<10} "
              f"{result['detection_ratio']*100:<9.1f}% {result['estimated_time_saving']:<10}")
    
    print("\n娴嬭瘯瀹屾垚锛?)


if __name__ == "__main__":
    main()

