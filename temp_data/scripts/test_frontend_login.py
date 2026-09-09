#!/usr/bin/env python
"""
妯℃嫙鍓嶇鐧诲綍璇锋眰娴嬭瘯
"""

import os
import sys
import django
import requests
import json

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

def test_frontend_login():
    """妯℃嫙鍓嶇鐧诲綍璇锋眰"""
    print("=" * 60)
    print("妯℃嫙鍓嶇鐧诲綍璇锋眰娴嬭瘯")
    print("=" * 60)
    
    # 妯℃嫙鍓嶇璇锋眰
    url = 'http://localhost:8000/api/v1/users/login/'
    
    # 娴嬭瘯JSON鏍煎紡
    print("\n1. 娴嬭瘯JSON鏍煎紡鐧诲綍璇锋眰...")
    headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    data = {
        'username': 'admin',
        'password': 'admin123456'
    }
    
    print(f"璇锋眰URL: {url}")
    print(f"璇锋眰澶? {headers}")
    print(f"璇锋眰鏁版嵁: {data}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"鍝嶅簲鐘舵€佺爜: {response.status_code}")
        print(f"鍝嶅簲澶? {dict(response.headers)}")
        print(f"鍝嶅簲鍐呭: {response.text}")
        
        if response.status_code == 200:
            print("鉁?JSON鏍煎紡鐧诲綍鎴愬姛")
        else:
            print("鉂?JSON鏍煎紡鐧诲綍澶辫触")
            
    except Exception as e:
        print(f"鉂?璇锋眰澶辫触: {e}")
    
    # 娴嬭瘯FormData鏍煎紡
    print("\n2. 娴嬭瘯FormData鏍煎紡鐧诲綍璇锋眰...")
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    data = {
        'username': 'admin',
        'password': 'admin123456'
    }
    
    print(f"璇锋眰URL: {url}")
    print(f"璇锋眰澶? {headers}")
    print(f"璇锋眰鏁版嵁: {data}")
    
    try:
        response = requests.post(url, data=data, headers=headers)
        print(f"鍝嶅簲鐘舵€佺爜: {response.status_code}")
        print(f"鍝嶅簲澶? {dict(response.headers)}")
        print(f"鍝嶅簲鍐呭: {response.text}")
        
        if response.status_code == 200:
            print("鉁?FormData鏍煎紡鐧诲綍鎴愬姛")
        else:
            print("鉂?FormData鏍煎紡鐧诲綍澶辫触")
            
    except Exception as e:
        print(f"鉂?璇锋眰澶辫触: {e}")

if __name__ == '__main__':
    test_frontend_login()

