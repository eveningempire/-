#!/usr/bin/env python
"""
娴嬭瘯鏃堕棿鎴冲鐞嗙殑瀹屾暣鎬?
楠岃瘉鏁版嵁瀵煎叆銆佸瓨鍌ㄣ€佹娴嬬粨鏋滅殑鏃堕棿鎴充竴鑷存€?
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

User = get_user_model()

def test_timestamp_integration():
    """娴嬭瘯鏃堕棿鎴冲鐞嗙殑瀹屾暣鎬?""
    print("=== 娴嬭瘯鏃堕棿鎴冲鐞嗙殑瀹屾暣鎬?===")
    
    # 鍒涘缓瀹㈡埛绔?
    client = Client(HTTP_HOST='localhost:8000')
    
    # 鑾峰彇PHM鍒楄〃
    try:
        response = client.get('/api/v1/data/cmgs/')
        if response.status_code == 200:
            cmgs = response.json()
            if cmgs:
                cmg_id = cmgs[0]['cmg_id']
                print(f"浣跨敤PHM ID: {cmg_id}")
                
                # 娴嬭瘯1: 妫€鏌ユ暟鎹椂闂存埑
                print("\n1. 妫€鏌ユ暟鎹椂闂存埑...")
                response = client.get(f'/api/v1/data/data/?cmg_id={cmg_id}&limit=100')
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data:
                        records = data['results']
                    else:
                        records = data
                    
                    if records:
                        print(f"鑾峰彇鍒?{len(records)} 鏉℃暟鎹褰?)
                        
                        # 妫€鏌ユ椂闂存埑鏍煎紡
                        timestamps = []
                        for record in records:
                            if 'timestamp' in record:
                                ts = record['timestamp']
                                timestamps.append(ts)
                                # 妫€鏌ユ槸鍚︽湁姣
                                if '.' in ts:
                                    print(f"  鏃堕棿鎴冲寘鍚绉? {ts}")
                        
                        # 妫€鏌ユ椂闂存埑鍞竴鎬?
                        unique_timestamps = set(timestamps)
                        print(f"  鎬绘椂闂存埑鏁? {len(timestamps)}")
                        print(f"  鍞竴鏃堕棿鎴虫暟: {len(unique_timestamps)}")
                        
                        if len(timestamps) != len(unique_timestamps):
                            print("  鈿狅笍  鍙戠幇閲嶅鏃堕棿鎴筹紒")
                        else:
                            print("  鉁?鏃堕棿鎴冲敮涓€鎬ф鏌ラ€氳繃")
                        
                        # 娴嬭瘯2: 妫€鏌MS妫€娴嬬粨鏋?
                        print("\n2. 妫€鏌MS妫€娴嬬粨鏋?..")
                        response = client.get(f'/health/ims-results/anomaly-data/?cmg_id={cmg_id}&limit=100')
                        if response.status_code == 200:
                            ims_data = response.json()
                            print(f"鑾峰彇鍒?{len(ims_data)} 鏉MS妫€娴嬬粨鏋?)
                            
                            if ims_data:
                                # 妫€鏌MS缁撴灉鐨勬椂闂存埑
                                ims_timestamps = []
                                for item in ims_data:
                                    if 'timestamp' in item:
                                        ims_timestamps.append(item['timestamp'])
                                
                                print(f"  IMS缁撴灉鏃堕棿鎴虫暟: {len(ims_timestamps)}")
                                
                                # 妫€鏌MS缁撴灉鏃堕棿鎴虫槸鍚﹀湪鏁版嵁鏃堕棿鎴充腑
                                data_timestamp_set = set(timestamps)
                                ims_timestamp_set = set(ims_timestamps)
                                
                                missing_timestamps = ims_timestamp_set - data_timestamp_set
                                if missing_timestamps:
                                    print(f"  鈿狅笍  鍙戠幇 {len(missing_timestamps)} 涓狪MS缁撴灉鏃堕棿鎴冲湪鏁版嵁涓笉瀛樺湪")
                                    for ts in list(missing_timestamps)[:5]:  # 鍙樉绀哄墠5涓?
                                        print(f"    缂哄け鏃堕棿鎴? {ts}")
                                else:
                                    print("  鉁?IMS缁撴灉鏃堕棿鎴冲尮閰嶆鏌ラ€氳繃")
                        
                        # 娴嬭瘯3: 妫€鏌ヨ鍒欐娴嬬粨鏋?
                        print("\n3. 妫€鏌ヨ鍒欐娴嬬粨鏋?..")
                        response = client.get(f'/rules/results/?cmg_id={cmg_id}&limit=100')
                        if response.status_code == 200:
                            rule_data = response.json()
                            if 'results' in rule_data:
                                rule_records = rule_data['results']
                            else:
                                rule_records = rule_data
                            
                            print(f"鑾峰彇鍒?{len(rule_records)} 鏉¤鍒欐娴嬬粨鏋?)
                            
                            if rule_records:
                                # 妫€鏌ヨ鍒欑粨鏋滅殑鏃堕棿鎴?
                                rule_timestamps = []
                                for item in rule_records:
                                    if 'timestamp' in item:
                                        rule_timestamps.append(item['timestamp'])
                                
                                print(f"  瑙勫垯缁撴灉鏃堕棿鎴虫暟: {len(rule_timestamps)}")
                                
                                # 妫€鏌ヨ鍒欑粨鏋滄椂闂存埑鏄惁鍦ㄦ暟鎹椂闂存埑涓?
                                rule_timestamp_set = set(rule_timestamps)
                                missing_rule_timestamps = rule_timestamp_set - data_timestamp_set
                                if missing_rule_timestamps:
                                    print(f"  鈿狅笍  鍙戠幇 {len(missing_rule_timestamps)} 涓鍒欑粨鏋滄椂闂存埑鍦ㄦ暟鎹腑涓嶅瓨鍦?)
                                else:
                                    print("  鉁?瑙勫垯缁撴灉鏃堕棿鎴冲尮閰嶆鏌ラ€氳繃")
                        
                        # 娴嬭瘯4: 妫€鏌SFG妫€娴嬬粨鏋?
                        print("\n4. 妫€鏌SFG妫€娴嬬粨鏋?..")
                        response = client.get(f'/msfg/results/?cmg_id={cmg_id}&limit=100')
                        if response.status_code == 200:
                            msfg_data = response.json()
                            if 'results' in msfg_data:
                                msfg_records = msfg_data['results']
                            else:
                                msfg_records = msfg_data
                            
                            print(f"鑾峰彇鍒?{len(msfg_records)} 鏉SFG妫€娴嬬粨鏋?)
                            
                            if msfg_records:
                                # 妫€鏌SFG缁撴灉鐨勬椂闂存埑
                                msfg_timestamps = []
                                for item in msfg_records:
                                    if 'timestamp' in item:
                                        msfg_timestamps.append(item['timestamp'])
                                
                                print(f"  MSFG缁撴灉鏃堕棿鎴虫暟: {len(msfg_timestamps)}")
                                
                                # 妫€鏌SFG缁撴灉鏃堕棿鎴虫槸鍚﹀湪鏁版嵁鏃堕棿鎴充腑
                                msfg_timestamp_set = set(msfg_timestamps)
                                missing_msfg_timestamps = msfg_timestamp_set - data_timestamp_set
                                if missing_msfg_timestamps:
                                    print(f"  鈿狅笍  鍙戠幇 {len(missing_msfg_timestamps)} 涓狹SFG缁撴灉鏃堕棿鎴冲湪鏁版嵁涓笉瀛樺湪")
                                else:
                                    print("  鉁?MSFG缁撴灉鏃堕棿鎴冲尮閰嶆鏌ラ€氳繃")
                    else:
                        print("娌℃湁鎵惧埌鏁版嵁璁板綍")
                else:
                    print(f"鏁版嵁鏌ヨ澶辫触: {response.status_code}")
            else:
                print("娌℃湁鎵惧埌PHM")
        else:
            print(f"PHM鏌ヨ澶辫触: {response.status_code}")
    except Exception as e:
        print(f"娴嬭瘯杩囩▼涓嚭鐜伴敊璇? {e}")
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")

if __name__ == '__main__':
    test_timestamp_integration()

