#!/usr/bin/env python
"""
娴嬭瘯鐢ㄦ埛API杩斿洖鐨勬暟鎹?
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

def test_user_api():
    """娴嬭瘯鐢ㄦ埛API"""
    print("=" * 60)
    print("娴嬭瘯鐢ㄦ埛API杩斿洖鐨勬暟鎹?)
    print("=" * 60)
    
    # 鍒涘缓浼氳瘽
    session = requests.Session()
    
    # 鍏堢櫥褰?
    login_url = 'http://localhost:8000/api/v1/users/login/'
    login_data = {
        'username': 'admin',
        'password': 'admin123456'
    }
    
    try:
        print("1. 鐧诲綍...")
        login_response = session.post(login_url, json=login_data)
        print(f"鐧诲綍鐘舵€佺爜: {login_response.status_code}")
        
        if login_response.status_code == 200:
            print("鉁?鐧诲綍鎴愬姛")
            
            # 娴嬭瘯鑾峰彇鐢ㄦ埛鍒楄〃
            users_url = 'http://localhost:8000/api/v1/users/users/'
            print("\n2. 鑾峰彇鐢ㄦ埛鍒楄〃...")
            
            users_response = session.get(users_url)
            print(f"鐢ㄦ埛鍒楄〃API鍝嶅簲鐘舵€佺爜: {users_response.status_code}")
            
            if users_response.status_code == 200:
                users = users_response.json()
                print(f"杩斿洖鐨勭敤鎴锋暟閲? {len(users)}")
                
                for user in users:
                    print(f"\n鐢ㄦ埛: {user.get('username')}")
                    print(f"  ID: {user.get('id')}")
                    print(f"  瑙掕壊: {user.get('role_display')}")
                    print(f"  鍒涘缓鏃堕棿: {user.get('date_joined')}")
                    print(f"  鏈€鍚庣櫥褰? {user.get('last_login')}")
                    
                    # 妫€鏌ast_login瀛楁鏄惁瀛樺湪
                    if 'last_login' in user:
                        print("  鉁?last_login瀛楁瀛樺湪")
                    else:
                        print("  鉂?last_login瀛楁缂哄け")
            else:
                print(f"鐢ㄦ埛鍒楄〃API璇锋眰澶辫触: {users_response.text}")
        else:
            print(f"鐧诲綍澶辫触: {login_response.text}")
            
    except Exception as e:
        print(f"璇锋眰澶辫触: {e}")
    
    print("\n" + "=" * 60)
    print("娴嬭瘯瀹屾垚")
    print("=" * 60)

if __name__ == '__main__':
    test_user_api()

