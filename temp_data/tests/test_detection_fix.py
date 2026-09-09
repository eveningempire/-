#!/usr/bin/env python
"""
妫€娴嬬粨鏋滃叆搴撴祴璇曡剼鏈?
鐢ㄤ簬楠岃瘉淇鍚庣殑妫€娴嬬粨鏋滄槸鍚﹁兘姝ｇ‘鍏ュ簱
"""

import os
import sys
import django
from pathlib import Path

# 璁剧疆Django鐜
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, PHMData
from health_management.models import IMSDetectionResult
from rule_detection.models import RuleDetectionResult
from msfg_analysis.models import MSFGAnalysisResult

def check_detection_results():
    """妫€鏌ユ娴嬬粨鏋滄槸鍚﹀叆搴?""
    print("=== 妫€娴嬬粨鏋滃叆搴撴鏌?===")
    
    # 妫€鏌MG鏁版嵁
    cmgs = PHM.objects.all()
    print(f"PHM鎬绘暟: {cmgs.count()}")
    
    for cmg in cmgs:
        print(f"\nPHM: {cmg.cmg_id}")
        
        # 妫€鏌ユ暟鎹褰?
        data_count = PHMData.objects.filter(cmg=cmg).count()
        print(f"  鏁版嵁璁板綍: {data_count}")
        
        # 妫€鏌MS妫€娴嬬粨鏋?
        ims_count = IMSDetectionResult.objects.filter(data_point__cmg=cmg).count()
        print(f"  IMS妫€娴嬬粨鏋? {ims_count}")
        
        # 妫€鏌ヨ鍒欐娴嬬粨鏋?
        rule_count = RuleDetectionResult.objects.filter(data_point__cmg=cmg).count()
        print(f"  瑙勫垯妫€娴嬬粨鏋? {rule_count}")
        
        # 妫€鏌SFG妫€娴嬬粨鏋?
        msfg_count = MSFGAnalysisResult.objects.filter(data_point__cmg=cmg).count()
        print(f"  MSFG妫€娴嬬粨鏋? {msfg_count}")
        
        # 妫€鏌ュ紓甯稿抚
        anomaly_count = IMSDetectionResult.objects.filter(
            data_point__cmg=cmg, 
            is_anomaly=True
        ).count()
        print(f"  寮傚父甯ф暟: {anomaly_count}")
        
        # 妫€鏌ヨЕ鍙戣鍒?
        triggered_count = RuleDetectionResult.objects.filter(
            data_point__cmg=cmg, 
            is_triggered=True
        ).count()
        print(f"  瑙﹀彂瑙勫垯鏁? {triggered_count}")

if __name__ == "__main__":
    check_detection_results()

