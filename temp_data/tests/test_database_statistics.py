#!/usr/bin/env python
"""
娴嬭瘯鏁版嵁搴撶粺璁￠€昏緫鐨勬纭€?
楠岃瘉鏁版嵁瀵煎叆銆佸垹闄ゃ€佹娴嬪悗缁熻淇℃伅鐨勫噯纭€?
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

def test_database_statistics():
    """娴嬭瘯鏁版嵁搴撶粺璁￠€昏緫"""
    print("=== 娴嬭瘯鏁版嵁搴撶粺璁￠€昏緫 ===")
    
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
                
                # 娴嬭瘯1: 妫€鏌ュ垵濮嬬粺璁′俊鎭?
                print("\n1. 妫€鏌ュ垵濮嬬粺璁′俊鎭?..")
                response = client.get(f'/api/v1/data/data/statistics/?cmg_id={cmg_id}&refresh=true')
                if response.status_code == 200:
                    stats = response.json()
                    print(f"  缁熻淇℃伅: {stats}")
                    
                    # 娴嬭瘯2: 妫€鏌ユ暟鎹鏁?
                    print("\n2. 妫€鏌ユ暟鎹鏁?..")
                    response = client.get(f'/api/v1/data/data/count/?cmg_id={cmg_id}')
                    if response.status_code == 200:
                        count_data = response.json()
                        data_count = count_data.get('count', 0)
                        print(f"  鏁版嵁鎬绘暟: {data_count}")
                        
                        # 楠岃瘉缁熻淇℃伅涓殑璁℃暟鏄惁涓庡疄闄呮暟鎹竴鑷?
                        stats_count = stats.get('statistics', {}).get('cmg_data', {}).get('count', 0)
                        if data_count == stats_count:
                            print("  鉁?鏁版嵁璁℃暟涓€鑷?)
                        else:
                            print(f"  鈿狅笍  鏁版嵁璁℃暟涓嶄竴鑷? 瀹為檯={data_count}, 缁熻={stats_count}")
                    
                    # 娴嬭瘯3: 妫€鏌MS妫€娴嬬粨鏋滆鏁?
                    print("\n3. 妫€鏌MS妫€娴嬬粨鏋滆鏁?..")
                    response = client.get(f'/health/ims-results/?cmg_id={cmg_id}&limit=1000')
                    if response.status_code == 200:
                        ims_data = response.json()
                        if 'results' in ims_data:
                            ims_count = len(ims_data['results'])
                        else:
                            ims_count = len(ims_data) if isinstance(ims_data, list) else 0
                        print(f"  IMS缁撴灉鏁? {ims_count}")
                        
                        # 楠岃瘉缁熻淇℃伅涓殑IMS璁℃暟
                        stats_ims_count = stats.get('statistics', {}).get('ims_results', {}).get('count', 0)
                        if ims_count == stats_ims_count:
                            print("  鉁?IMS璁℃暟涓€鑷?)
                        else:
                            print(f"  鈿狅笍  IMS璁℃暟涓嶄竴鑷? 瀹為檯={ims_count}, 缁熻={stats_ims_count}")
                    
                    # 娴嬭瘯4: 妫€鏌ヨ鍒欐娴嬬粨鏋滆鏁?
                    print("\n4. 妫€鏌ヨ鍒欐娴嬬粨鏋滆鏁?..")
                    response = client.get(f'/rules/results/?cmg_id={cmg_id}&limit=1000')
                    if response.status_code == 200:
                        rule_data = response.json()
                        if 'results' in rule_data:
                            rule_count = len(rule_data['results'])
                        else:
                            rule_count = len(rule_data) if isinstance(rule_data, list) else 0
                        print(f"  瑙勫垯缁撴灉鏁? {rule_count}")
                        
                        # 楠岃瘉缁熻淇℃伅涓殑瑙勫垯璁℃暟
                        stats_rule_count = stats.get('statistics', {}).get('rule_results', {}).get('count', 0)
                        if rule_count == stats_rule_count:
                            print("  鉁?瑙勫垯璁℃暟涓€鑷?)
                        else:
                            print(f"  鈿狅笍  瑙勫垯璁℃暟涓嶄竴鑷? 瀹為檯={rule_count}, 缁熻={stats_rule_count}")
                    
                    # 娴嬭瘯5: 妫€鏌SFG妫€娴嬬粨鏋滆鏁?
                    print("\n5. 妫€鏌SFG妫€娴嬬粨鏋滆鏁?..")
                    response = client.get(f'/msfg/results/?cmg_id={cmg_id}&limit=1000')
                    if response.status_code == 200:
                        msfg_data = response.json()
                        if 'results' in msfg_data:
                            msfg_count = len(msfg_data['results'])
                        else:
                            msfg_count = len(msfg_data) if isinstance(msfg_data, list) else 0
                        print(f"  MSFG缁撴灉鏁? {msfg_count}")
                        
                        # 楠岃瘉缁熻淇℃伅涓殑MSFG璁℃暟
                        stats_msfg_count = stats.get('statistics', {}).get('msfg_results', {}).get('count', 0)
                        if msfg_count == stats_msfg_count:
                            print("  鉁?MSFG璁℃暟涓€鑷?)
                        else:
                            print(f"  鈿狅笍  MSFG璁℃暟涓嶄竴鑷? 瀹為檯={msfg_count}, 缁熻={stats_msfg_count}")
                    
                    # 娴嬭瘯6: 妫€鏌ュ紓甯稿抚璁℃暟
                    print("\n6. 妫€鏌ュ紓甯稿抚璁℃暟...")
                    response = client.get(f'/health/ims-results/anomaly-data/?cmg_id={cmg_id}&anomaly_only=true&limit=1000')
                    if response.status_code == 200:
                        anomaly_data = response.json()
                        anomaly_count = len(anomaly_data) if isinstance(anomaly_data, list) else 0
                        print(f"  寮傚父甯ф暟: {anomaly_count}")
                        
                        # 楠岃瘉缁熻淇℃伅涓殑寮傚父甯ц鏁?
                        stats_anomaly_count = stats.get('statistics', {}).get('anomaly_frames', {}).get('count', 0)
                        if anomaly_count == stats_anomaly_count:
                            print("  鉁?寮傚父甯ц鏁颁竴鑷?)
                        else:
                            print(f"  鈿狅笍  寮傚父甯ц鏁颁笉涓€鑷? 瀹為檯={anomaly_count}, 缁熻={stats_anomaly_count}")
                    
                    # 娴嬭瘯7: 娴嬭瘯鍒锋柊鍔熻兘
                    print("\n7. 娴嬭瘯缁熻淇℃伅鍒锋柊鍔熻兘...")
                    response = client.get(f'/api/v1/data/data/statistics/?cmg_id={cmg_id}&refresh=true')
                    if response.status_code == 200:
                        refresh_stats = response.json()
                        if refresh_stats.get('refreshed'):
                            print("  鉁?缁熻淇℃伅鍒锋柊鎴愬姛")
                        else:
                            print("  鈿狅笍  缁熻淇℃伅鍒锋柊澶辫触")
                    else:
                        print("  鉂?缁熻淇℃伅鍒锋柊API璋冪敤澶辫触")
                        
                else:
                    print(f"缁熻淇℃伅API璋冪敤澶辫触: {response.status_code}")
            else:
                print("娌℃湁鎵惧埌PHM")
        else:
            print(f"PHM鏌ヨ澶辫触: {response.status_code}")
    except Exception as e:
        print(f"娴嬭瘯杩囩▼涓嚭鐜伴敊璇? {e}")
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")

if __name__ == '__main__':
    test_database_statistics()

