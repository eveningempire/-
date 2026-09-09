#!/usr/bin/env python
"""
娴嬭瘯鐢ㄦ埛鍒楄〃鍔犺浇鍔熻兘
"""

import os
import sys
import django

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

def test_user_list():
    """娴嬭瘯鐢ㄦ埛鍒楄〃鍔犺浇鍔熻兘"""
    print("=== 鐢ㄦ埛鍒楄〃鍔犺浇娴嬭瘯 ===")
    
    # 妫€鏌ョ鐞嗗憳鐢ㄦ埛
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        print("鉂?娌℃湁鎵惧埌绠＄悊鍛樼敤鎴?)
        return
    
    print(f"鉁?鎵惧埌绠＄悊鍛樼敤鎴? {admin_user.username}")
    
    # 鍒涘缓娴嬭瘯瀹㈡埛绔?
    client = Client()
    
    # 鍏堢櫥褰曠鐞嗗憳
    print("\n1. 绠＄悊鍛樼櫥褰?..")
    login_response = client.post('/api/v1/users/login/', {
        'username': admin_user.username,
        'password': 'admin123456'
    })
    
    if login_response.status_code != 200:
        print(f"鉂?绠＄悊鍛樼櫥褰曞け璐? {login_response.content}")
        return
    
    print("鉁?绠＄悊鍛樼櫥褰曟垚鍔?)
    
    # 娴嬭瘯鐢ㄦ埛鍒楄〃璁块棶
    print("\n2. 娴嬭瘯鐢ㄦ埛鍒楄〃璁块棶...")
    users_response = client.get('/api/v1/users/users/')
    print(f"   鐢ㄦ埛鍒楄〃鐘舵€佺爜: {users_response.status_code}")
    
    if users_response.status_code == 200:
        users_data = users_response.json()
        print(f"   鉁?鐢ㄦ埛鍒楄〃璁块棶鎴愬姛锛岃繑鍥?{len(users_data)} 涓敤鎴?)
        for user in users_data:
            print(f"     - {user['username']} (瑙掕壊: {user['role']})")
    else:
        print(f"   鉂?鐢ㄦ埛鍒楄〃璁块棶澶辫触: {users_response.content}")

def main():
    """涓诲嚱鏁?""
    print("鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁?- 鐢ㄦ埛鍒楄〃鍔犺浇娴嬭瘯")
    print("=" * 50)
    
    test_user_list()
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")

if __name__ == "__main__":
    main()

