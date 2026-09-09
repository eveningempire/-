#!/usr/bin/env python
"""
娴嬭瘯鍓嶇鍜屽悗绔殑閫氫俊
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

def test_communication():
    """娴嬭瘯鍓嶇鍜屽悗绔殑閫氫俊"""
    print("=" * 60)
    print("娴嬭瘯鍓嶇鍜屽悗绔殑閫氫俊")
    print("=" * 60)
    
    # 鍒涘缓娴嬭瘯瀹㈡埛绔?
    client = Client()
    
    # 鑾峰彇绠＄悊鍛樼敤鎴?
    admin_user = User.objects.get(username='admin')
    print(f"绠＄悊鍛樼敤鎴? {admin_user.username} (ID: {admin_user.id})")
    
    # 鍏堢櫥褰曠鐞嗗憳
    print("\n1. 绠＄悊鍛樼櫥褰?..")
    login_response = client.post('/api/v1/users/login/', {
        'username': 'admin',
        'password': 'admin123456'
    })
    
    if login_response.status_code != 200:
        print(f"鉂?绠＄悊鍛樼櫥褰曞け璐? {login_response.status_code}")
        return
    
    print("鉁?绠＄悊鍛樼櫥褰曟垚鍔?)
    
    # 娴嬭瘯鑾峰彇褰撳墠鐢ㄦ埛淇℃伅
    print("\n2. 娴嬭瘯鑾峰彇褰撳墠鐢ㄦ埛淇℃伅...")
    me_response = client.get('/api/v1/users/users/me/')
    print(f"鑾峰彇鐢ㄦ埛淇℃伅鐘舵€佺爜: {me_response.status_code}")
    
    if me_response.status_code == 200:
        user_data = me_response.json()
        print(f"鉁?鐢ㄦ埛淇℃伅鑾峰彇鎴愬姛")
        print(f"   鐢ㄦ埛鍚? {user_data.get('username')}")
        print(f"   瑙掕壊: {user_data.get('role')}")
        print(f"   鏄惁婵€娲? {user_data.get('is_active')}")
    else:
        print(f"鉂?鑾峰彇鐢ㄦ埛淇℃伅澶辫触: {me_response.content}")
    
    # 娴嬭瘯鑾峰彇鐢ㄦ埛鍒楄〃
    print("\n3. 娴嬭瘯鑾峰彇鐢ㄦ埛鍒楄〃...")
    users_response = client.get('/api/v1/users/users/')
    print(f"鑾峰彇鐢ㄦ埛鍒楄〃鐘舵€佺爜: {users_response.status_code}")
    
    if users_response.status_code == 200:
        users_data = users_response.json()
        print(f"鉁?鐢ㄦ埛鍒楄〃鑾峰彇鎴愬姛锛屽叡 {len(users_data)} 涓敤鎴?)
        for user in users_data:
            print(f"   - {user.get('username')} (瑙掕壊: {user.get('role')})")
    else:
        print(f"鉂?鑾峰彇鐢ㄦ埛鍒楄〃澶辫触: {users_response.content}")
    
    # 娴嬭瘯鍒犻櫎鐢ㄦ埛锛堝鏋滆繕鏈夋櫘閫氱敤鎴风殑璇濓級
    normal_users = User.objects.filter(role='user').exclude(username='anonymous')
    if normal_users.exists():
        test_user = normal_users.first()
        print(f"\n4. 娴嬭瘯鍒犻櫎鐢ㄦ埛: {test_user.username}")
        
        delete_response = client.delete(f'/api/v1/users/users/{test_user.id}/')
        print(f"鍒犻櫎鐢ㄦ埛鐘舵€佺爜: {delete_response.status_code}")
        
        if delete_response.status_code == 204:
            print("鉁?鐢ㄦ埛鍒犻櫎鎴愬姛")
        else:
            print(f"鉂?鐢ㄦ埛鍒犻櫎澶辫触: {delete_response.content}")

if __name__ == '__main__':
    test_communication()

