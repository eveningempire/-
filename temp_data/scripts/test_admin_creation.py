#!/usr/bin/env python
"""
娴嬭瘯绠＄悊鍛樺垱寤哄姛鑳?
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

def test_admin_creation():
    """娴嬭瘯绠＄悊鍛樺垱寤哄姛鑳?""
    print("=== 娴嬭瘯绠＄悊鍛樺垱寤哄姛鑳?===")
    
    # 娓呯悊娴嬭瘯鐢ㄦ埛锛堝鏋滃瓨鍦級
    test_username = 'test_admin'
    if User.objects.filter(username=test_username).exists():
        User.objects.filter(username=test_username).delete()
        print(f"娓呯悊浜嗗凡瀛樺湪鐨勬祴璇曠敤鎴? {test_username}")
    
    # 娴嬭瘯1: 浣跨敤create_user鏂规硶鍒涘缓绠＄悊鍛?
    print("\n1. 娴嬭瘯 create_user 鏂规硶鍒涘缓绠＄悊鍛?..")
    try:
        admin_user = User.objects.create_user(
            username=test_username,
            email='test_admin@example.com',
            password='test123456',
            first_name='娴嬭瘯绠＄悊鍛?,
            role='admin',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        
        print(f"鉁?绠＄悊鍛樺垱寤烘垚鍔?")
        print(f"   鐢ㄦ埛鍚? {admin_user.username}")
        print(f"   瑙掕壊: {admin_user.role}")
        print(f"   瑙掕壊鏄剧ず: {admin_user.get_role_display()}")
        print(f"   鏄惁涓鸿秴绾х敤鎴? {admin_user.is_superuser}")
        print(f"   鏄惁涓哄憳宸? {admin_user.is_staff}")
        
        # 楠岃瘉瑙掕壊鏄惁姝ｇ‘
        if admin_user.role == 'admin':
            print("鉁?瑙掕壊璁剧疆姝ｇ‘")
        else:
            print(f"鉂?瑙掕壊璁剧疆閿欒锛屾湡鏈? admin, 瀹為檯: {admin_user.role}")
        
        # 娓呯悊娴嬭瘯鐢ㄦ埛
        admin_user.delete()
        print("鉁?娴嬭瘯鐢ㄦ埛宸叉竻鐞?)
        
    except Exception as e:
        print(f"鉂?鍒涘缓绠＄悊鍛樺け璐? {e}")
        return False
    
    # 娴嬭瘯2: 浣跨敤create_superuser鏂规硶鍒涘缓绠＄悊鍛?
    print("\n2. 娴嬭瘯 create_superuser 鏂规硶鍒涘缓绠＄悊鍛?..")
    try:
        admin_user = User.objects.create_superuser(
            username=test_username,
            email='test_admin@example.com',
            password='test123456',
            role='admin'
        )
        
        print(f"鉁?瓒呯骇鐢ㄦ埛鍒涘缓鎴愬姛!")
        print(f"   鐢ㄦ埛鍚? {admin_user.username}")
        print(f"   瑙掕壊: {admin_user.role}")
        print(f"   瑙掕壊鏄剧ず: {admin_user.get_role_display()}")
        print(f"   鏄惁涓鸿秴绾х敤鎴? {admin_user.is_superuser}")
        print(f"   鏄惁涓哄憳宸? {admin_user.is_staff}")
        
        # 楠岃瘉瑙掕壊鏄惁姝ｇ‘
        if admin_user.role == 'admin':
            print("鉁?瑙掕壊璁剧疆姝ｇ‘")
        else:
            print(f"鉂?瑙掕壊璁剧疆閿欒锛屾湡鏈? admin, 瀹為檯: {admin_user.role}")
        
        # 娓呯悊娴嬭瘯鐢ㄦ埛
        admin_user.delete()
        print("鉁?娴嬭瘯鐢ㄦ埛宸叉竻鐞?)
        
    except Exception as e:
        print(f"鉂?鍒涘缓瓒呯骇鐢ㄦ埛澶辫触: {e}")
        return False
    
    # 娴嬭瘯3: 妫€鏌ヨ鑹查€夋嫨
    print("\n3. 娴嬭瘯瑙掕壊閫夋嫨...")
    print(f"鍙敤瑙掕壊: {[choice[0] for choice in CustomUser.Role.choices]}")
    print(f"绠＄悊鍛樿鑹插€? {CustomUser.Role.ADMIN}")
    print(f"鏅€氱敤鎴疯鑹插€? {CustomUser.Role.USER}")
    
    return True

def check_existing_admins():
    """妫€鏌ョ幇鏈夌殑绠＄悊鍛樼敤鎴?""
    print("\n=== 妫€鏌ョ幇鏈夌鐞嗗憳 ===")
    
    admin_users = User.objects.filter(role='admin')
    if admin_users.exists():
        print(f"鎵惧埌 {admin_users.count()} 涓鐞嗗憳鐢ㄦ埛:")
        for user in admin_users:
            print(f"  - {user.username} ({user.email}) - 瑙掕壊: {user.get_role_display()}")
    else:
        print("鉂?娌℃湁鎵惧埌绠＄悊鍛樼敤鎴?)
    
    # 妫€鏌ユ墍鏈夎秴绾х敤鎴?
    superusers = User.objects.filter(is_superuser=True)
    print(f"\n鎵惧埌 {superusers.count()} 涓秴绾х敤鎴?")
    for user in superusers:
        print(f"  - {user.username} - 瑙掕壊: {user.role} ({user.get_role_display()})")
        if user.role != 'admin':
            print(f"    鈿狅笍  瓒呯骇鐢ㄦ埛 {user.username} 鐨勮鑹蹭笉鏄?'admin'锛岃€屾槸 '{user.role}'")

if __name__ == '__main__':
    print("PHM骞冲彴绠＄悊鍛樺垱寤哄姛鑳芥祴璇?)
    print("=" * 50)
    
    # 妫€鏌ョ幇鏈夌鐞嗗憳
    check_existing_admins()
    
    # 娴嬭瘯绠＄悊鍛樺垱寤?
    success = test_admin_creation()
    
    print(f"\n" + "=" * 50)
    if success:
        print("鉁?鎵€鏈夋祴璇曢€氳繃锛佺鐞嗗憳鍒涘缓鍔熻兘姝ｅ父")
    else:
        print("鉂?娴嬭瘯澶辫触锛佺鐞嗗憳鍒涘缓鍔熻兘瀛樺湪闂")
    print("=" * 50)

