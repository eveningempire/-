#!/usr/bin/env python
"""
娴嬭瘯鐧诲綍鍔熻兘
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
import json

User = get_user_model()

def test_login():
    """娴嬭瘯鐧诲綍鍔熻兘"""
    print("=" * 60)
    print("娴嬭瘯鐧诲綍鍔熻兘")
    print("=" * 60)
    
    # 鍒涘缓娴嬭瘯瀹㈡埛绔?
    client = Client()
    
    # 鑾峰彇绠＄悊鍛樼敤鎴?
    admin_user = User.objects.get(username='admin')
    print(f"绠＄悊鍛樼敤鎴? {admin_user.username} (ID: {admin_user.id})")
    
    # 娴嬭瘯鐧诲綍
    print("\n1. 娴嬭瘯绠＄悊鍛樼櫥褰?..")
    login_data = {
        'username': 'admin',
        'password': 'admin123456'
    }
    
    print(f"鐧诲綍鏁版嵁: {login_data}")
    login_response = client.post('/api/v1/users/login/', login_data)
    
    print(f"鐧诲綍鐘舵€佺爜: {login_response.status_code}")
    print(f"鍝嶅簲鍐呭: {login_response.content}")
    
    if login_response.status_code == 200:
        print("鉁?鐧诲綍鎴愬姛")
        response_data = login_response.json()
        print(f"   鐢ㄦ埛鍚? {response_data.get('username')}")
        print(f"   瑙掕壊: {response_data.get('role')}")
        
        # 娴嬭瘯鑾峰彇褰撳墠鐢ㄦ埛淇℃伅
        print("\n2. 娴嬭瘯鑾峰彇褰撳墠鐢ㄦ埛淇℃伅...")
        me_response = client.get('/api/v1/users/users/me/')
        print(f"鑾峰彇鐢ㄦ埛淇℃伅鐘舵€佺爜: {me_response.status_code}")
        
        if me_response.status_code == 200:
            user_data = me_response.json()
            print(f"鉁?鐢ㄦ埛淇℃伅鑾峰彇鎴愬姛")
            print(f"   鐢ㄦ埛鍚? {user_data.get('username')}")
            print(f"   瑙掕壊: {user_data.get('role')}")
        else:
            print(f"鉂?鑾峰彇鐢ㄦ埛淇℃伅澶辫触: {me_response.content}")
            
    else:
        print("鉂?鐧诲綍澶辫触")
        try:
            error_data = login_response.json()
            print(f"   閿欒淇℃伅: {error_data}")
        except:
            print(f"   閿欒鍐呭: {login_response.content}")

if __name__ == '__main__':
    test_login()

