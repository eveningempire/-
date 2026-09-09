#!/usr/bin/env python3
"""
娴嬭瘯瀵垮懡棰勬祴绠楁硶鎵╁睍鍔熻兘
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

# 娴嬭瘯API绔偣
BASE_URL = 'http://localhost:8000/api/v1/lifetime'

def test_get_algorithms():
    """娴嬭瘯鑾峰彇绠楁硶鍒楄〃API"""
    print("馃敩 娴嬭瘯鑾峰彇绠楁硶鍒楄〃...")
    try:
        response = requests.get(f'{BASE_URL}/algorithms/')
        if response.status_code == 200:
            data = response.json()
            print(f"鉁?鎴愬姛鑾峰彇绠楁硶鍒楄〃锛屽叡 {data.get('count', 0)} 涓畻娉?")
            for algo in data.get('data', []):
                print(f"   - {algo['key']}: {algo['name']}")
                print(f"     鎻忚堪: {algo['description']}")
        else:
            print(f"鉂?鑾峰彇绠楁硶鍒楄〃澶辫触: {response.status_code}")
            print(f"   鍝嶅簲: {response.text}")
    except Exception as e:
        print(f"鉂?鑾峰彇绠楁硶鍒楄〃寮傚父: {str(e)}")

def test_get_cmgs():
    """娴嬭瘯鑾峰彇PHM鍒楄〃API"""
    print("\n馃敩 娴嬭瘯鑾峰彇PHM鍒楄〃...")
    try:
        response = requests.get(f'{BASE_URL}/cmgs/')
        if response.status_code == 200:
            data = response.json()
            cmgs = data.get('data', [])
            print(f"鉁?鎴愬姛鑾峰彇PHM鍒楄〃锛屽叡 {len(cmgs)} 涓狢MG:")
            for cmg in cmgs[:3]:  # 鍙樉绀哄墠3涓?
                print(f"   - {cmg['cmg_id']}: {cmg['name']} ({cmg['model_name']})")
            return cmgs
        else:
            print(f"鉂?鑾峰彇PHM鍒楄〃澶辫触: {response.status_code}")
            return []
    except Exception as e:
        print(f"鉂?鑾峰彇PHM鍒楄〃寮傚父: {str(e)}")
        return []

def test_algorithm_prediction(cmg_id, algorithm='strategy0'):
    """娴嬭瘯鐗瑰畾绠楁硶鐨勯娴嬪姛鑳?""
    print(f"\n馃敩 娴嬭瘯绠楁硶 {algorithm} 鐨勯娴嬪姛鑳?..")
    try:
        request_data = {
            'cmg_id': cmg_id,
            'design_life': 10,
            'start_time': '2020/01/01 01:01:01',
            'algorithm': algorithm
        }
        
        response = requests.post(f'{BASE_URL}/predict/', json=request_data)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                result = data.get('data', {})
                print(f"鉁?{algorithm} 棰勬祴鎴愬姛:")
                print(f"   - RUL鍊? {result.get('rul_value', 0)} 灏忔椂")
                print(f"   - 浣跨敤绠楁硶: {result.get('algorithm_name', 'Unknown')}")
                print(f"   - 棰勬祴鏃堕棿: {result.get('prediction_time', 'Unknown')}")
                print(f"   - 鍋ュ悍搴忓垪闀垮害: {len(result.get('hi_sequence', []))}")
                return True
            else:
                print(f"鉂?{algorithm} 棰勬祴澶辫触: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"鉂?{algorithm} 棰勬祴璇锋眰澶辫触: {response.status_code}")
            print(f"   鍝嶅簲: {response.text}")
            return False
    except Exception as e:
        print(f"鉂?{algorithm} 棰勬祴寮傚父: {str(e)}")
        return False

def test_all_algorithms():
    """娴嬭瘯鎵€鏈夌畻娉?""
    print("\n馃殌 寮€濮嬫祴璇曟墍鏈夌畻娉曠殑鍔熻兘...")
    
    # 鑾峰彇PHM鍒楄〃
    cmgs = test_get_cmgs()
    if not cmgs:
        print("鉂?鏃犳硶鑾峰彇PHM鍒楄〃锛屽仠姝㈡祴璇?)
        return
    
    # 浣跨敤绗竴涓狢MG杩涜娴嬭瘯
    test_cmg = cmgs[0]
    print(f"\n馃搳 浣跨敤PHM '{test_cmg['cmg_id']}' 杩涜娴嬭瘯")
    
    # 娴嬭瘯鎵€鏈夌畻娉?
    algorithms = ['strategy0', 'strategy1', 'strategy2', 'strategy3']
    success_count = 0
    
    for algorithm in algorithms:
        if test_algorithm_prediction(test_cmg['cmg_id'], algorithm):
            success_count += 1
    
    print(f"\n馃搱 娴嬭瘯缁撴灉鎬荤粨:")
    print(f"   - 娴嬭瘯绠楁硶鏁? {len(algorithms)}")
    print(f"   - 鎴愬姛绠楁硶鏁? {success_count}")
    print(f"   - 鎴愬姛鐜? {success_count/len(algorithms)*100:.1f}%")
    
    if success_count == len(algorithms):
        print("馃帀 鎵€鏈夌畻娉曟祴璇曢€氳繃锛?)
    else:
        print("鈿狅笍  閮ㄥ垎绠楁硶娴嬭瘯澶辫触锛岃妫€鏌ユ棩蹇?)

def main():
    """涓绘祴璇曞嚱鏁?""
    print("馃敡 瀵垮懡棰勬祴绠楁硶鎵╁睍鍔熻兘娴嬭瘯")
    print("=" * 50)
    
    # 娴嬭瘯鑾峰彇绠楁硶鍒楄〃
    test_get_algorithms()
    
    # 娴嬭瘯鎵€鏈夌畻娉曠殑棰勬祴鍔熻兘
    test_all_algorithms()
    
    print("\n鉁?娴嬭瘯瀹屾垚锛?)

if __name__ == '__main__':
    main()

