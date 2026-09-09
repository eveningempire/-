#!/usr/bin/env python
"""
妫€娴嬫€ц兘娴嬭瘯鑴氭湰
鐢ㄤ簬娴嬭瘯浼樺寲鍚庣殑妫€娴嬫€ц兘
"""

import os
import sys
import django
import time
from pathlib import Path

# 璁剧疆Django鐜
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, PHMData, ImportSession
from data_management.batch_processing import BatchFileProcessor
from django.utils import timezone
import logging

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_detection_performance():
    """娴嬭瘯妫€娴嬫€ц兘"""
    print("=== 妫€娴嬫€ц兘娴嬭瘯 ===")
    
    # 鑾峰彇娴嬭瘯鏁版嵁
    try:
        cmg = PHM.objects.first()
        if not cmg:
            print("娌℃湁鎵惧埌PHM鏁版嵁锛岃鍏堝鍏ヤ竴浜涙暟鎹?)
            return
        
        # 鑾峰彇鏈€杩戠殑1600鏉¤褰?
        records = list(PHMData.objects.filter(cmg=cmg).order_by('-timestamp')[:1600])
        if not records:
            print(f"PHM {cmg.cmg_id} 娌℃湁鏁版嵁璁板綍")
            return
        
        print(f"娴嬭瘯PHM: {cmg.cmg_id}")
        print(f"娴嬭瘯璁板綍鏁? {len(records)}")
        
        # 鍒涘缓鎵归噺澶勭悊鍣?
        processor = BatchFileProcessor()
        
        # 娴嬭瘯妫€娴嬫€ц兘
        start_time = time.time()
        detection_summary = processor._run_detection_pipeline(None, records)
        end_time = time.time()
        
        # 杈撳嚭缁撴灉
        print("\n=== 妫€娴嬬粨鏋?===")
        print(f"鎬昏€楁椂: {end_time - start_time:.2f}绉?)
        print(f"澶勭悊閫熷害: {len(records) / (end_time - start_time):.1f} 甯?绉?)
        print(f"IMS妫€娴? {detection_summary['ims_evaluations']} 娆?)
        print(f"寮傚父甯? {detection_summary['ims_anomalies']} 涓?)
        print(f"瑙勫垯妫€娴? {detection_summary['rule_evaluations']} 娆?)
        print(f"瑙﹀彂瑙勫垯: {detection_summary['rule_triggers']} 涓?)
        
        if 'performance_metrics' in detection_summary:
            metrics = detection_summary['performance_metrics']
            print("\n=== 璇︾粏鎬ц兘鎸囨爣 ===")
            print(f"妯″瀷棰勫姞杞? {metrics.get('preload_time', 0):.2f}绉?)
            print(f"IMS妫€娴? {metrics.get('ims_time', 0):.2f}绉?)
            print(f"瑙勫垯妫€娴? {metrics.get('rule_time', 0):.2f}绉?)
            print(f"缁撴灉淇濆瓨: {metrics.get('save_time', 0):.2f}绉?)
        
    except Exception as e:
        print(f"娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detection_performance()

