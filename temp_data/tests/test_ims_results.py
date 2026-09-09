#!/usr/bin/env python
"""
娴嬭瘯IMS妫€娴嬬粨鏋滄煡璇㈤棶棰?
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
from health_management.models import IMSDetectionResult
from rule_detection.models import RuleDetectionResult
from msfg_analysis.models import MSFGAnalysisResult
import logging

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ims_results_query():
    """娴嬭瘯IMS妫€娴嬬粨鏋滄煡璇?""
    print("=== 娴嬭瘯IMS妫€娴嬬粨鏋滄煡璇?===")
    
    try:
        # 1. 妫€鏌ユ渶杩戠殑瀵煎叆浼氳瘽
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
            
            # 2. 妫€鏌ュ疄闄呭瓨鍌ㄧ殑鏁版嵁
            actual_records = PHMData.objects.filter(import_session=session).count()
            print(f"  瀹為檯瀛樺偍璁板綍鏁? {actual_records}")
            
            # 3. 妫€鏌MS妫€娴嬬粨鏋?
            ims_results = IMSDetectionResult.objects.filter(
                data_point__import_session=session
            ).count()
            print(f"  IMS妫€娴嬬粨鏋滄暟: {ims_results}")
            
            # 4. 妫€鏌ヨ鍒欐娴嬬粨鏋?
            rule_results = RuleDetectionResult.objects.filter(
                data_point__import_session=session
            ).count()
            print(f"  瑙勫垯妫€娴嬬粨鏋滄暟: {rule_results}")
            
            # 5. 妫€鏌SFG妫€娴嬬粨鏋?
            msfg_results = MSFGAnalysisResult.objects.filter(
                data_point__import_session=session
            ).count()
            print(f"  MSFG妫€娴嬬粨鏋滄暟: {msfg_results}")
            
            # 6. 妫€鏌ユ椂闂存埑鍒嗗竷
            from django.db.models import Count
            timestamp_distribution = PHMData.objects.filter(
                import_session=session
            ).values('timestamp').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            print("  鏃堕棿鎴冲垎甯?(鍓?涓?:")
            for item in timestamp_distribution:
                print(f"    {item['timestamp']}: {item['count']} 鏉¤褰?)
            
            # 7. 妫€鏌MS缁撴灉鐨勬椂闂存埑鍒嗗竷
            ims_timestamp_distribution = IMSDetectionResult.objects.filter(
                data_point__import_session=session
            ).values('data_point__timestamp').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            print("  IMS缁撴灉鏃堕棿鎴冲垎甯?(鍓?涓?:")
            for item in ims_timestamp_distribution:
                print(f"    {item['data_point__timestamp']}: {item['count']} 鏉¤褰?)
                
    except Exception as e:
        print(f"娴嬭瘯澶辫触: {e}")

def test_database_counts():
    """娴嬭瘯鏁版嵁搴撴€绘暟缁熻"""
    print("\n=== 娴嬭瘯鏁版嵁搴撴€绘暟缁熻 ===")
    
    try:
        # 1. PHM鏁版嵁鎬绘暟
        cmg_data_count = PHMData.objects.count()
        print(f"PHM鏁版嵁鎬绘暟: {cmg_data_count}")
        
        # 2. IMS妫€娴嬬粨鏋滄€绘暟
        ims_count = IMSDetectionResult.objects.count()
        print(f"IMS妫€娴嬬粨鏋滄€绘暟: {ims_count}")
        
        # 3. 瑙勫垯妫€娴嬬粨鏋滄€绘暟
        rule_count = RuleDetectionResult.objects.count()
        print(f"瑙勫垯妫€娴嬬粨鏋滄€绘暟: {rule_count}")
        
        # 4. MSFG妫€娴嬬粨鏋滄€绘暟
        msfg_count = MSFGAnalysisResult.objects.count()
        print(f"MSFG妫€娴嬬粨鏋滄€绘暟: {msfg_count}")
        
        # 5. 鎸塁MG鍒嗙粍缁熻
        print("\n鎸塁MG鍒嗙粍缁熻:")
        cmgs = PHM.objects.all()
        for cmg in cmgs:
            cmg_data = PHMData.objects.filter(cmg=cmg).count()
            cmg_ims = IMSDetectionResult.objects.filter(data_point__cmg=cmg).count()
            cmg_rule = RuleDetectionResult.objects.filter(data_point__cmg=cmg).count()
            cmg_msfg = MSFGAnalysisResult.objects.filter(data_point__cmg=cmg).count()
            
            print(f"  {cmg.name} ({cmg.cmg_id}):")
            print(f"    鏁版嵁: {cmg_data}, IMS: {cmg_ims}, 瑙勫垯: {cmg_rule}, MSFG: {cmg_msfg}")
            
    except Exception as e:
        print(f"鏁版嵁搴撶粺璁″け璐? {e}")

def test_api_endpoints():
    """娴嬭瘯API绔偣"""
    print("\n=== 娴嬭瘯API绔偣 ===")
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # 1. 娴嬭瘯IMS缁撴灉API
        print("娴嬭瘯IMS缁撴灉API...")
        response = client.get('/api/v1/health/ims-results/')
        print(f"  IMS缁撴灉API鐘舵€佺爜: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  杩斿洖鏁版嵁鏍煎紡: {type(data)}")
            if isinstance(data, dict) and 'results' in data:
                print(f"  缁撴灉鏁伴噺: {len(data['results'])}")
                print(f"  鎬绘暟: {data.get('count', 'N/A')}")
            elif isinstance(data, list):
                print(f"  缁撴灉鏁伴噺: {len(data)}")
        
        # 2. 娴嬭瘯瑙勫垯缁撴灉API
        print("娴嬭瘯瑙勫垯缁撴灉API...")
        response = client.get('/api/v1/rules/results/')
        print(f"  瑙勫垯缁撴灉API鐘舵€佺爜: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  杩斿洖鏁版嵁鏍煎紡: {type(data)}")
            if isinstance(data, list):
                print(f"  缁撴灉鏁伴噺: {len(data)}")
        
        # 3. 娴嬭瘯MSFG缁撴灉API
        print("娴嬭瘯MSFG缁撴灉API...")
        response = client.get('/api/v1/msfg/results/')
        print(f"  MSFG缁撴灉API鐘舵€佺爜: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  杩斿洖鏁版嵁鏍煎紡: {type(data)}")
            if isinstance(data, list):
                print(f"  缁撴灉鏁伴噺: {len(data)}")
                
    except Exception as e:
        print(f"API娴嬭瘯澶辫触: {e}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("寮€濮嬫祴璇旾MS妫€娴嬬粨鏋滄煡璇㈤棶棰?..")
    
    test_ims_results_query()
    test_database_counts()
    test_api_endpoints()
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")
    print("\n闂鍒嗘瀽:")
    print("1. 妫€鏌ユ暟鎹瓨鍌ㄦ槸鍚﹀畬鏁?)
    print("2. 妫€鏌ユ娴嬬粨鏋滄槸鍚︽纭繚瀛?)
    print("3. 妫€鏌PI绔偣鏄惁姝ｅ父")
    print("4. 妫€鏌ュ墠绔煡璇㈤€昏緫鏄惁姝ｇ‘")

if __name__ == "__main__":
    main()

