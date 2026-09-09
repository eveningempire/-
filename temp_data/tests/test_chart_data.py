#!/usr/bin/env python
"""
娴嬭瘯鍥捐〃鏁版嵁瀹屾暣鎬?
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

User = get_user_model()

def test_chart_data_integrity():
    """娴嬭瘯鍥捐〃鏁版嵁瀹屾暣鎬?""
    print("=== 娴嬭瘯鍥捐〃鏁版嵁瀹屾暣鎬?===")
    
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
                
                # 娴嬭瘯鍘嗗彶鏁版嵁鏌ヨ
                print("\n娴嬭瘯鍘嗗彶鏁版嵁鏌ヨ...")
                
                # 鏌ヨ鏈€杩戠殑鏁版嵁
                response = client.get(f'/api/v1/data/data/?cmg_id={cmg_id}&limit=1000')
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data:
                        records = data['results']
                    else:
                        records = data
                    
                    print(f"鑾峰彇鍒?{len(records)} 鏉¤褰?)
                    
                    if records:
                        # 妫€鏌ユ暟鎹繛缁€?
                        timestamps = []
                        for record in records:
                            if 'timestamp' in record:
                                timestamps.append(record['timestamp'])
                        
                        timestamps.sort()
                        print(f"鏃堕棿鑼冨洿: {timestamps[0]} 鍒?{timestamps[-1]}")
                        print(f"鎬昏褰曟暟: {len(timestamps)}")
                        
                        # 妫€鏌ユ槸鍚︽湁閲嶅鏃堕棿鎴?
                        unique_timestamps = set(timestamps)
                        print(f"鍞竴鏃堕棿鎴虫暟: {len(unique_timestamps)}")
                        
                        if len(timestamps) != len(unique_timestamps):
                            print("鈿狅笍  鍙戠幇閲嶅鏃堕棿鎴筹紒")
                        else:
                            print("鉁?鏃堕棿鎴冲敮涓€鎬ф鏌ラ€氳繃")
                        
                        # 妫€鏌ユ暟鎹畬鏁存€?
                        if len(records) > 1:
                            # 璁＄畻鏃堕棿闂撮殧
                            intervals = []
                            for i in range(1, len(timestamps)):
                                t1 = timestamps[i-1]
                                t2 = timestamps[i]
                                interval = (t2 - t1).total_seconds()
                                intervals.append(interval)
                            
                            if intervals:
                                avg_interval = sum(intervals) / len(intervals)
                                print(f"骞冲潎鏃堕棿闂撮殧: {avg_interval:.2f} 绉?)
                                
                                # 妫€鏌ユ槸鍚︽湁寮傚父澶х殑闂撮殧
                                max_interval = max(intervals)
                                if max_interval > avg_interval * 10:
                                    print(f"鈿狅笍  鍙戠幇寮傚父澶х殑鏃堕棿闂撮殧: {max_interval:.2f} 绉?)
                                else:
                                    print("鉁?鏃堕棿闂撮殧妫€鏌ラ€氳繃")
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
    test_chart_data_integrity()

