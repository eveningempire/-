#!/usr/bin/env python
"""
鍒涘缓绠＄悊鍛樿处鎴疯剼鏈?
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
from users.models import CustomUser

User = get_user_model()

def create_admin_user():
    """鍒涘缓绠＄悊鍛樼敤鎴?""
    print("=== 鍒涘缓绠＄悊鍛樿处鎴?===")
    
    # 妫€鏌ユ槸鍚﹀凡瀛樺湪绠＄悊鍛?
    if User.objects.filter(role='admin').exists():
        print("宸插瓨鍦ㄧ鐞嗗憳璐︽埛锛岃烦杩囧垱寤?)
        return
    
    # 鍒涘缓绠＄悊鍛樿处鎴?
    admin_username = 'admin'
    admin_password = 'admin123456'
    admin_email = 'admin@cmg.com'
    
    try:
        admin_user = User.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            first_name='绯荤粺绠＄悊鍛?,
            role='admin',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        
        print(f"鉁?绠＄悊鍛樿处鎴峰垱寤烘垚鍔燂紒")
        print(f"   鐢ㄦ埛鍚? {admin_username}")
        print(f"   瀵嗙爜: {admin_password}")
        print(f"   閭: {admin_email}")
        print(f"   瑙掕壊: 绠＄悊鍛?)
        print("\n璇蜂娇鐢ㄤ互涓婂嚟鎹櫥褰曠郴缁燂紝骞剁珛鍗充慨鏀瑰瘑鐮侊紒")
        
    except Exception as e:
        print(f"鉂?鍒涘缓绠＄悊鍛樿处鎴峰け璐? {e}")
        return False
    
    return True

def create_test_users():
    """鍒涘缓娴嬭瘯鐢ㄦ埛"""
    print("\n=== 鍒涘缓娴嬭瘯鐢ㄦ埛 ===")
    
    test_users = [
        {
            'username': 'user1',
            'password': 'user123',
            'email': 'user1@cmg.com',
            'first_name': '鏉庣敤鎴?,
            'role': 'user'
        },
        {
            'username': 'user2',
            'password': 'user123',
            'email': 'user2@cmg.com',
            'first_name': '鐜嬬敤鎴?,
            'role': 'user'
        }
    ]
    
    for user_data in test_users:
        try:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    role=user_data['role'],
                    is_active=True
                )
                print(f"鉁?鍒涘缓鐢ㄦ埛: {user_data['username']} ({user_data['role']})")
            else:
                print(f"鈿狅笍  鐢ㄦ埛宸插瓨鍦? {user_data['username']}")
        except Exception as e:
            print(f"鉂?鍒涘缓鐢ㄦ埛澶辫触 {user_data['username']}: {e}")

def main():
    """涓诲嚱鏁?""
    print("鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁?- 鐢ㄦ埛璐︽埛鍒涘缓宸ュ叿")
    print("=" * 50)
    
    # 鍒涘缓绠＄悊鍛?
    if create_admin_user():
        # 鍒涘缓娴嬭瘯鐢ㄦ埛
        create_test_users()
    
    print("\n=== 瀹屾垚 ===")
    print("鐜板湪鍙互浣跨敤鍒涘缓鐨勮处鎴风櫥褰曠郴缁熶簡锛?)

if __name__ == "__main__":
    main()

