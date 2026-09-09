#!/usr/bin/env python
"""
娴嬭瘯妫€娴嬮鐜囨帶鍒禪I鍔熻兘
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
from data_management.config import get_config, update_config
from health_management.detection_frequency_controller import detection_frequency_controller, DetectionMode


def test_ui_configuration():
    """娴嬭瘯UI閰嶇疆鍔熻兘"""
    print("=== 妫€娴嬮鐜囨帶鍒禪I閰嶇疆娴嬭瘯 ===")
    
    try:
        # 1. 娴嬭瘯鑾峰彇褰撳墠閰嶇疆
        print("\n1. 鑾峰彇褰撳墠閰嶇疆:")
        current_config = get_config('detection_frequency', {})
        print(f"   褰撳墠妫€娴嬮鐜囬厤缃? {current_config}")
        
        # 2. 娴嬭瘯鏇存柊閰嶇疆
        print("\n2. 娴嬭瘯鏇存柊閰嶇疆:")
        test_config = {
            'enabled': True,
            'mode': 'medium_frequency',
            'high_frequency': {
                'interval_seconds': 2,
                'frames_per_interval': 1
            },
            'medium_frequency': {
                'interval_seconds': 45,
                'frames_per_interval': 1
            },
            'low_frequency': {
                'interval_seconds': 120,
                'frames_per_interval': 1
            },
            'adaptive': {
                'small_dataset_threshold': 500,
                'medium_dataset_threshold': 3000,
                'large_dataset_threshold': 8000,
                'small_dataset_interval': 2,
                'medium_dataset_interval': 45,
                'large_dataset_interval': 120
            }
        }
        
        update_config({'detection_frequency': test_config})
        print("   閰嶇疆宸叉洿鏂?)
        
        # 3. 楠岃瘉鏇存柊
        print("\n3. 楠岃瘉鏇存柊鍚庣殑閰嶇疆:")
        updated_config = get_config('detection_frequency', {})
        print(f"   鏇存柊鍚庨厤缃? {updated_config}")
        
        # 4. 娴嬭瘯閲嶇疆閰嶇疆
        print("\n4. 娴嬭瘯閲嶇疆閰嶇疆:")
        from data_management.config import system_config
        system_config.reset_to_default()
        reset_config = get_config('detection_frequency', {})
        print(f"   閲嶇疆鍚庨厤缃? {reset_config}")
        
        print("\n=== UI閰嶇疆娴嬭瘯瀹屾垚 ===")
        
    except Exception as e:
        print(f"鉁?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()


def test_detection_frequency_controller():
    """娴嬭瘯妫€娴嬮鐜囨帶鍒跺櫒"""
    print("\n=== 妫€娴嬮鐜囨帶鍒跺櫒娴嬭瘯 ===")
    
    try:
        # 鍒涘缓娴嬭瘯鏁版嵁
        from data_management.models import PHMModel
        
        # 鍏堝垱寤烘垨鑾峰彇PHM妯″瀷
        cmg_model, _ = PHMModel.objects.get_or_create(
            model_name="UI_TEST_MODEL",
            defaults={
                'description': '鐢ㄤ簬UI娴嬭瘯鐨凜MG妯″瀷'
            }
        )
        
        # 鍒涘缓PHM
        cmg, created = PHM.objects.get_or_create(
            cmg_id="UI_TEST_PHM",
            defaults={
                'name': 'UI娴嬭瘯PHM',
                'cmg_model': cmg_model
            }
        )
        
        # 鍒犻櫎鐜版湁娴嬭瘯鏁版嵁
        PHMData.objects.filter(cmg=cmg).delete()
        
        # 鍒涘缓娴嬭瘯鏁版嵁
        start_time = timezone.now() - timedelta(hours=1)
        test_data = []
        
        for i in range(3000):  # 3000甯ф暟鎹?
            timestamp = start_time + timedelta(seconds=i * 1)
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
        print(f"   鍒涘缓浜?{len(test_data)} 鏉℃祴璇曟暟鎹?)
        
        # 娴嬭瘯涓嶅悓妯″紡
        records = list(PHMData.objects.filter(cmg=cmg).order_by('timestamp'))
        
        modes = ['disabled', 'high_frequency', 'medium_frequency', 'low_frequency', 'adaptive']
        
        for mode in modes:
            print(f"\n   娴嬭瘯妯″紡: {mode}")
            
            # 涓存椂璁剧疆妯″紡
            original_config = detection_frequency_controller.config
            if mode != 'disabled':
                detection_frequency_controller.config.mode = DetectionMode(mode)
                detection_frequency_controller.config.enabled = True
            else:
                detection_frequency_controller.config.mode = DetectionMode.DISABLED
                detection_frequency_controller.config.enabled = False
            
            # 閫夋嫨甯?
            selected_indices = detection_frequency_controller.select_frames_for_detection(records)
            summary = detection_frequency_controller.get_detection_summary(len(records), len(selected_indices))
            
            print(f"     鎬诲抚鏁? {summary['total_frames']}")
            print(f"     閫変腑甯ф暟: {summary['selected_frames']}")
            print(f"     妫€娴嬫瘮渚? {summary['detection_ratio']*100:.1f}%")
            print(f"     鏃堕棿鑺傜渷: {summary['estimated_time_saving']}")
            
            # 鎭㈠鍘熷閰嶇疆
            detection_frequency_controller.config = original_config
        
        print("\n=== 妫€娴嬮鐜囨帶鍒跺櫒娴嬭瘯瀹屾垚 ===")
        
    except Exception as e:
        print(f"鉁?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()


def main():
    """涓诲嚱鏁?""
    print("妫€娴嬮鐜囨帶鍒禪I鍔熻兘娴嬭瘯")
    print("=" * 60)
    
    # 娴嬭瘯UI閰嶇疆
    test_ui_configuration()
    
    # 娴嬭瘯妫€娴嬮鐜囨帶鍒跺櫒
    test_detection_frequency_controller()
    
    print("\n鎵€鏈夋祴璇曞畬鎴愶紒")


if __name__ == "__main__":
    main()

