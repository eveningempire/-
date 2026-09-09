#!/usr/bin/env python
"""
娴嬭瘯鐧诲綍鍜屾潈闄愬姛鑳?
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

def test_login_and_permissions():
    """娴嬭瘯鐧诲綍鍜屾潈闄愬姛鑳?""
    print("=== 鐧诲綍鍜屾潈闄愭祴璇?===")
    
    # 妫€鏌ョ鐞嗗憳鐢ㄦ埛
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        print("鉂?娌℃湁鎵惧埌绠＄悊鍛樼敤鎴?)
        print("璇疯繍琛?python scripts/create_admin.py 鍒涘缓绠＄悊鍛樿处鎴?)
        return
    
    print(f"鉁?鎵惧埌绠＄悊鍛樼敤鎴? {admin_user.username}")
    
    # 鍒涘缓娴嬭瘯瀹㈡埛绔?
    client = Client()
    
    # 娴嬭瘯鐧诲綍
    print("\n1. 娴嬭瘯绠＄悊鍛樼櫥褰?..")
    login_response = client.post('/api/v1/users/login/', {
        'username': admin_user.username,
        'password': 'admin123456'
    })
    
    print(f"   鐧诲綍鐘舵€佺爜: {login_response.status_code}")
    if login_response.status_code == 200:
        print("   鉁?绠＄悊鍛樼櫥褰曟垚鍔?)
        print(f"   杩斿洖鏁版嵁: {login_response.json()}")
    else:
        print(f"   鉂?绠＄悊鍛樼櫥褰曞け璐? {login_response.content}")
        return
    
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
    
    # 娴嬭瘯鏅€氱敤鎴风櫥褰?
    print("\n3. 娴嬭瘯鏅€氱敤鎴风櫥褰?..")
    user_user = User.objects.filter(role='user').first()
    if user_user:
        user_login_response = client.post('/api/v1/users/login/', {
            'username': user_user.username,
            'password': 'user123'
        })
        
        print(f"   鏅€氱敤鎴风櫥褰曠姸鎬佺爜: {user_login_response.status_code}")
        if user_login_response.status_code == 200:
            print("   鉁?鏅€氱敤鎴风櫥褰曟垚鍔?)
            print(f"   杩斿洖鏁版嵁: {user_login_response.json()}")
        else:
            print(f"   鉂?鏅€氱敤鎴风櫥褰曞け璐? {user_login_response.content}")
    else:
        print("   鈿狅笍  娌℃湁鎵惧埌鏅€氱敤鎴疯繘琛屾祴璇?)

def main():
    """涓诲嚱鏁?""
    print("鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁?- 鐧诲綍鍜屾潈闄愭祴璇?)
    print("=" * 50)
    
    test_login_and_permissions()
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")

if __name__ == "__main__":
    main()

