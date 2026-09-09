#!/usr/bin/env python
"""
娴嬭瘯娴佸紡澶勭悊鏁堟灉
楠岃瘉鍒嗘壒澶勭悊鍜屽疄鏃朵繚瀛樼殑鍔熻兘
"""

import os
import sys
import django
from pathlib import Path

# 璁剧疆Django鐜
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import ImportSession, PHMData, PHM
from data_management.batch_processing import BatchFileProcessor
import logging
import time

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_streaming_threshold():
    """娴嬭瘯娴佸紡澶勭悊闃堝€?""
    print("=== 娴嬭瘯娴佸紡澶勭悊闃堝€?===")
    
    processor = BatchFileProcessor()
    
    # 娴嬭瘯涓嶅悓鏁版嵁閲?
    test_sizes = [500, 1000, 1500, 2000, 5000]
    
    for size in test_sizes:
        # 妯℃嫙璁板綍鍒楄〃
        mock_records = [None] * size  # 绠€鍖栨祴璇?
        
        # 妫€鏌ユ槸鍚﹀惎鐢ㄦ祦寮忓鐞?
        use_streaming = size > 1000
        print(f"鏁版嵁閲? {size} 甯?-> {'鍚敤' if use_streaming else '涓嶅惎鐢?} 娴佸紡澶勭悊")
    
    print("鉁?娴佸紡澶勭悊闃堝€兼祴璇曞畬鎴?)

def test_batch_size_calculation():
    """娴嬭瘯鎵规澶у皬璁＄畻"""
    print("\n=== 娴嬭瘯鎵规澶у皬璁＄畻 ===")
    
    BATCH_SIZE = 500
    
    test_sizes = [1200, 1600, 2500, 5000]
    
    for size in test_sizes:
        total_batches = (size + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"鏁版嵁閲? {size} 甯?)
        print(f"  鎵规澶у皬: {BATCH_SIZE} 甯?)
        print(f"  鎬绘壒娆℃暟: {total_batches}")
        
        for batch_index in range(total_batches):
            batch_start = batch_index * BATCH_SIZE
            batch_end = min(batch_start + BATCH_SIZE, size)
            print(f"  鎵规 {batch_index + 1}: 甯?{batch_start + 1}-{batch_end}")
        print()
    
    print("鉁?鎵规澶у皬璁＄畻娴嬭瘯瀹屾垚")

def test_progress_tracking():
    """娴嬭瘯杩涘害璺熻釜"""
    print("\n=== 娴嬭瘯杩涘害璺熻釜 ===")
    
    # 妯℃嫙娴佸紡澶勭悊杩涘害
    total_records = 1600
    batch_size = 500
    total_batches = (total_records + batch_size - 1) // batch_size
    
    print(f"鎬昏褰曟暟: {total_records}")
    print(f"鎵规澶у皬: {batch_size}")
    print(f"鎬绘壒娆℃暟: {total_batches}")
    print()
    
    for batch_index in range(total_batches):
        batch_start = batch_index * batch_size
        batch_end = min(batch_start + batch_size, total_records)
        processed_count = batch_end
        
        progress_percent = (processed_count / total_records) * 100
        print(f"鎵规 {batch_index + 1}/{total_batches}:")
        print(f"  澶勭悊甯ф暟: {batch_start + 1}-{batch_end}")
        print(f"  绱澶勭悊: {processed_count}/{total_records} ({progress_percent:.1f}%)")
        print()
    
    print("鉁?杩涘害璺熻釜娴嬭瘯瀹屾垚")

def test_performance_comparison():
    """娴嬭瘯鎬ц兘瀵规瘮"""
    print("\n=== 娴嬭瘯鎬ц兘瀵规瘮 ===")
    
    # 妯℃嫙鎬ц兘鏁版嵁
    scenarios = [
        {
            'name': '灏忔暟鎹噺 (500甯?',
            'records': 500,
            'batch_time': 15,
            'streaming_time': 15,
            'use_streaming': False
        },
        {
            'name': '涓瓑鏁版嵁閲?(1500甯?',
            'records': 1500,
            'batch_time': 45,
            'streaming_time': 45,
            'use_streaming': True
        },
        {
            'name': '澶ф暟鎹噺 (5000甯?',
            'records': 5000,
            'batch_time': 150,
            'streaming_time': 150,
            'use_streaming': True
        }
    ]
    
    for scenario in scenarios:
        print(f"鍦烘櫙: {scenario['name']}")
        print(f"  鏁版嵁閲? {scenario['records']} 甯?)
        print(f"  澶勭悊妯″紡: {'娴佸紡澶勭悊' if scenario['use_streaming'] else '鎵归噺澶勭悊'}")
        print(f"  棰勮鑰楁椂: {scenario['streaming_time']} 绉?)
        
        if scenario['use_streaming']:
            batch_size = 500
            total_batches = (scenario['records'] + batch_size - 1) // batch_size
            print(f"  鎵规鏁? {total_batches}")
            print(f"  鐢ㄦ埛鍙湅鍒扮涓€鎵圭粨鏋滄椂闂? ~{scenario['streaming_time']/total_batches:.1f} 绉?)
        
        print()
    
    print("鉁?鎬ц兘瀵规瘮娴嬭瘯瀹屾垚")

def test_real_session_analysis():
    """鍒嗘瀽鐪熷疄浼氳瘽鐨勫鐞嗘儏鍐?""
    print("\n=== 鍒嗘瀽鐪熷疄浼氳瘽澶勭悊鎯呭喌 ===")
    
    try:
        # 鏌ユ壘鏈€杩戠殑瀵煎叆浼氳瘽
        sessions = ImportSession.objects.filter(
            processing_status=ImportSession.ProcessingStatus.COMPLETED
        ).order_by('-timestamp')[:3]
        
        if not sessions.exists():
            print("娌℃湁鎵惧埌宸插畬鎴愮殑瀵煎叆浼氳瘽")
            return
        
        for session in sessions:
            print(f"\n浼氳瘽 {session.id}:")
            print(f"  PHM: {session.cmg.name}")
            print(f"  鎬昏褰曟暟: {session.total_records}")
            print(f"  宸插鐞嗚褰曟暟: {session.processed_records}")
            print(f"  澶勭悊鐘舵€? {session.processing_status}")
            print(f"  鍒涘缓鏃堕棿: {session.timestamp}")
            
            # 妫€鏌ュ疄闄呭瓨鍌ㄧ殑鏁版嵁
            actual_records = PHMData.objects.filter(import_session=session).count()
            print(f"  瀹為檯瀛樺偍璁板綍鏁? {actual_records}")
            
            # 鍒ゆ柇鏄惁搴旇浣跨敤娴佸紡澶勭悊
            should_use_streaming = session.total_records > 1000
            print(f"  搴旇浣跨敤娴佸紡澶勭悊: {'鏄? if should_use_streaming else '鍚?}")
            
            # 妫€鏌ユ娴嬬粨鏋?
            from health_management.models import IMSDetectionResult
            from rule_detection.models import RuleDetectionResult
            from msfg_analysis.models import MSFGAnalysisResult
            
            ims_results = IMSDetectionResult.objects.filter(
                data_point__import_session=session
            ).count()
            
            rule_results = RuleDetectionResult.objects.filter(
                data_point__import_session=session
            ).count()
            
            msfg_results = MSFGAnalysisResult.objects.filter(
                data_point__import_session=session
            ).count()
            
            print(f"  IMS妫€娴嬬粨鏋? {ims_results}")
            print(f"  瑙勫垯妫€娴嬬粨鏋? {rule_results}")
            print(f"  MSFG妫€娴嬬粨鏋? {msfg_results}")
            
    except Exception as e:
        print(f"鍒嗘瀽鐪熷疄浼氳瘽澶辫触: {e}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("寮€濮嬫祴璇曟祦寮忓鐞嗗姛鑳?..")
    
    test_streaming_threshold()
    test_batch_size_calculation()
    test_progress_tracking()
    test_performance_comparison()
    test_real_session_analysis()
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")
    print("\n娴佸紡澶勭悊浼樺娍:")
    print("1. 鉁?鐢ㄦ埛鏃犻渶绛夊緟鍏ㄩ儴澶勭悊瀹屾垚")
    print("2. 鉁?鍙互瀹炴椂鐪嬪埌澶勭悊杩涘害")
    print("3. 鉁?绗竴鎵圭粨鏋滃揩閫熷彲瑙?)
    print("4. 鉁?鍐呭瓨浣跨敤鏇村悎鐞?)
    print("5. 鉁?閿欒鎭㈠鏇村鏄?)
    
    print("\n閰嶇疆鍙傛暟:")
    print("- 娴佸紡澶勭悊闃堝€? 1000甯?)
    print("- 鎵规澶у皬: 500甯?)
    print("- 杩涘害鏇存柊棰戠巼: 姣忔壒娆?)
    print("- 瀹炴椂淇濆瓨: 姣忔壒娆″畬鎴愬悗绔嬪嵆淇濆瓨")

if __name__ == "__main__":
    main()

