#!/usr/bin/env python
"""
娴嬭瘯鐢ㄦ埛绠＄悊鍔熻兘
"""

import os
import sys
import django
import requests

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def test_user_management():
    """娴嬭瘯鐢ㄦ埛绠＄悊鍔熻兘"""
    print("=== 鐢ㄦ埛绠＄悊鍔熻兘娴嬭瘯 ===")
    
    # 妫€鏌ュ綋鍓嶇敤鎴?
    print(f"褰撳墠鐢ㄦ埛鎬绘暟: {User.objects.count()}")
    
    # 鏄剧ず鎵€鏈夌敤鎴?
    print("\n褰撳墠鐢ㄦ埛鍒楄〃:")
    for user in User.objects.all():
        print(f"  - {user.username} (瑙掕壊: {user.role}, 鐘舵€? {'鍚敤' if user.is_active else '绂佺敤'})")
    
    # 妫€鏌ユ槸鍚︽湁绠＄悊鍛樿处鎴?
    admin_users = User.objects.filter(role='admin')
    if admin_users.exists():
        print(f"\n鉁?鎵惧埌 {admin_users.count()} 涓鐞嗗憳璐︽埛")
        for admin in admin_users:
            print(f"   绠＄悊鍛? {admin.username}")
    else:
        print("\n鉂?娌℃湁鎵惧埌绠＄悊鍛樿处鎴?)
        print("璇疯繍琛?python scripts/create_admin.py 鍒涘缓绠＄悊鍛樿处鎴?)
    
    # 妫€鏌ユ櫘閫氱敤鎴?
    user_users = User.objects.filter(role='user')
    if user_users.exists():
        print(f"\n鉁?鎵惧埌 {user_users.count()} 涓櫘閫氱敤鎴疯处鎴?)
        for user in user_users:
            print(f"   鏅€氱敤鎴? {user.username}")
    else:
        print("\n鈿狅笍  娌℃湁鎵惧埌鏅€氱敤鎴疯处鎴?)
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")

def test_api_endpoints():
    """娴嬭瘯API绔偣"""
    print("\n=== API绔偣娴嬭瘯 ===")
    
    base_url = "http://127.0.0.1:8000"
    
    # 娴嬭瘯鐧诲綍API
    print("1. 娴嬭瘯鐧诲綍API...")
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123456'
        }
        response = requests.post(f"{base_url}/api/v1/users/login/", data=login_data)
        print(f"   鐧诲綍鐘舵€佺爜: {response.status_code}")
        if response.status_code == 200:
            print("   鉁?鐧诲綍API姝ｅ父")
        else:
            print(f"   鉂?鐧诲綍澶辫触: {response.text}")
    except Exception as e:
        print(f"   鉂?鐧诲綍API閿欒: {e}")
    
    # 娴嬭瘯鐢ㄦ埛鍒楄〃API锛堥渶瑕佺櫥褰曪級
    print("\n2. 娴嬭瘯鐢ㄦ埛鍒楄〃API...")
    try:
        # 鍏堢櫥褰曡幏鍙杝ession
        session = requests.Session()
        login_response = session.post(f"{base_url}/api/v1/users/login/", data=login_data)
        
        if login_response.status_code == 200:
            # 鑾峰彇鐢ㄦ埛鍒楄〃
            users_response = session.get(f"{base_url}/api/v1/users/users/")
            print(f"   鐢ㄦ埛鍒楄〃鐘舵€佺爜: {users_response.status_code}")
            if users_response.status_code == 200:
                users_data = users_response.json()
                print(f"   鉁?鐢ㄦ埛鍒楄〃API姝ｅ父锛岃繑鍥?{len(users_data)} 涓敤鎴?)
            else:
                print(f"   鉂?鐢ㄦ埛鍒楄〃澶辫触: {users_response.text}")
        else:
            print("   鉂?鏃犳硶鐧诲綍锛岃烦杩囩敤鎴峰垪琛ㄦ祴璇?)
    except Exception as e:
        print(f"   鉂?鐢ㄦ埛鍒楄〃API閿欒: {e}")

def main():
    """涓诲嚱鏁?""
    print("鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁?- 鐢ㄦ埛绠＄悊鍔熻兘娴嬭瘯")
    print("=" * 50)
    
    test_user_management()
    test_api_endpoints()
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")
    print("濡傛灉鎵€鏈夋祴璇曢兘閫氳繃锛岃鏄庣敤鎴风鐞嗗姛鑳芥甯稿伐浣?)

if __name__ == "__main__":
    main()

