#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁?- 瓒呯骇绠＄悊鍛樺垱寤哄伐鍏?

杩欎釜鑴氭湰鐢ㄤ簬鍦ㄦ柊鐢佃剳涓婂畨瑁呯郴缁熷悗鍒涘缓绗竴涓鐞嗗憳璐︽埛銆?
鏀寔浜や簰寮忚緭鍏ュ拰蹇€熷垱寤轰袱绉嶆ā寮忋€?

浣跨敤鏂规硶锛?
    python create_superuser.py              # 浜や簰寮忓垱寤?
    python create_superuser.py --quick      # 蹇€熷垱寤猴紙浣跨敤榛樿瀵嗙爜锛?
"""

import os
import sys
import django
import getpass
import re

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

User = get_user_model()


def print_banner():
    """鎵撳嵃妯箙"""
    print("=" * 70)
    print(" " * 15 + "鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁?)
    print(" " * 20 + "绠＄悊鍛樿处鎴峰垱寤哄伐鍏?)
    print("=" * 70)
    print()


def validate_username(username):
    """楠岃瘉鐢ㄦ埛鍚嶆牸寮?""
    if not username:
        return False, "鐢ㄦ埛鍚嶄笉鑳戒负绌?
    
    if len(username) < 3:
        return False, "鐢ㄦ埛鍚嶈嚦灏戦渶瑕?涓瓧绗?
    
    if len(username) > 150:
        return False, "鐢ㄦ埛鍚嶄笉鑳借秴杩?50涓瓧绗?
    
    # 妫€鏌ユ槸鍚﹀彧鍖呭惈瀛楁瘝銆佹暟瀛椼€佷笅鍒掔嚎銆佽繛瀛楃
    if not re.match(r'^[\w.-]+$', username):
        return False, "鐢ㄦ埛鍚嶅彧鑳藉寘鍚瓧姣嶃€佹暟瀛椼€佷笅鍒掔嚎銆佽繛瀛楃鍜岀偣鍙?
    
    # 妫€鏌ョ敤鎴峰悕鏄惁宸插瓨鍦?
    if User.objects.filter(username=username).exists():
        return False, f"鐢ㄦ埛鍚?'{username}' 宸茶鍗犵敤"
    
    return True, ""


def validate_email_address(email):
    """楠岃瘉閭鏍煎紡"""
    if not email:
        return True, ""  # 閭鍙€?
    
    try:
        validate_email(email)
        return True, ""
    except ValidationError:
        return False, "閭鏍煎紡涓嶆纭?


def validate_password(password):
    """楠岃瘉瀵嗙爜寮哄害"""
    if not password:
        return False, "瀵嗙爜涓嶈兘涓虹┖"
    
    if len(password) < 6:
        return False, "瀵嗙爜鑷冲皯闇€瑕?涓瓧绗?
    
    # 寤鸿鍖呭惈鏁板瓧鍜屽瓧姣?
    has_digit = any(c.isdigit() for c in password)
    has_alpha = any(c.isalpha() for c in password)
    
    if not (has_digit and has_alpha):
        print("  鈿狅笍  寤鸿瀵嗙爜鍚屾椂鍖呭惈瀛楁瘝鍜屾暟瀛楋紝浠ユ彁楂樺畨鍏ㄦ€?)
    
    return True, ""


def interactive_create_admin():
    """浜や簰寮忓垱寤虹鐞嗗憳"""
    print("馃摑 璇疯緭鍏ョ鐞嗗憳璐︽埛淇℃伅锛?)
    print()
    
    # 杈撳叆鐢ㄦ埛鍚?
    while True:
        username = input("鐢ㄦ埛鍚? ").strip()
        is_valid, error_msg = validate_username(username)
        if is_valid:
            break
        else:
            print(f"  鉂?{error_msg}")
            print()
    
    # 杈撳叆閭
    while True:
        email = input("閭 (鍙€夛紝鐩存帴鍥炶溅璺宠繃): ").strip()
        is_valid, error_msg = validate_email_address(email)
        if is_valid:
            break
        else:
            print(f"  鉂?{error_msg}")
            print()
    
    # 杈撳叆瀵嗙爜
    while True:
        password = getpass.getpass("瀵嗙爜 (杈撳叆鏃朵笉鏄剧ず): ")
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            print(f"  鉂?{error_msg}")
            print()
            continue
        
        password_confirm = getpass.getpass("纭瀵嗙爜: ")
        if password == password_confirm:
            break
        else:
            print("  鉂?涓ゆ杈撳叆鐨勫瘑鐮佷笉涓€鑷达紝璇烽噸鏂拌緭鍏?)
            print()
    
    # 杈撳叆濮撳悕
    first_name = input("濮撳悕 (鍙€夛紝鐩存帴鍥炶溅璺宠繃): ").strip()
    
    return {
        'username': username,
        'email': email or f'{username}@cmg-platform.local',
        'password': password,
        'first_name': first_name or '绯荤粺绠＄悊鍛?
    }


def quick_create_admin():
    """蹇€熷垱寤洪粯璁ょ鐞嗗憳"""
    print("馃殌 蹇€熷垱寤烘ā寮忥細浣跨敤榛樿绠＄悊鍛樿处鎴?)
    print()
    
    default_username = 'admin'
    default_password = 'admin123456'
    
    # 妫€鏌ラ粯璁ょ敤鎴峰悕鏄惁宸插瓨鍦?
    if User.objects.filter(username=default_username).exists():
        print(f"鉂?鐢ㄦ埛鍚?'{default_username}' 宸插瓨鍦?)
        print("   璇蜂娇鐢ㄤ氦浜掓ā寮忓垱寤烘柊璐︽埛锛歱ython create_superuser.py")
        return None
    
    print(f"  鐢ㄦ埛鍚? {default_username}")
    print(f"  瀵嗙爜: {default_password}")
    print(f"  閭: admin@cmg-platform.local")
    print(f"  濮撳悕: 绯荤粺绠＄悊鍛?)
    print()
    
    confirm = input("纭鍒涘缓? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', '鏄?]:
        print("鉂?宸插彇娑堝垱寤?)
        return None
    
    return {
        'username': default_username,
        'email': 'admin@cmg-platform.local',
        'password': default_password,
        'first_name': '绯荤粺绠＄悊鍛?
    }


def create_superuser(user_data):
    """鍒涘缓瓒呯骇绠＄悊鍛樿处鎴?""
    try:
        print()
        print("鈴?姝ｅ湪鍒涘缓绠＄悊鍛樿处鎴?..")
        
        admin_user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            role='admin',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        
        print()
        print("=" * 70)
        print(" " * 25 + "鉁?鍒涘缓鎴愬姛锛?)
        print("=" * 70)
        print()
        print("馃搵 璐︽埛淇℃伅锛?)
        print(f"   鐢ㄦ埛鍚? {user_data['username']}")
        print(f"   瀵嗙爜: {user_data['password']}")
        print(f"   閭: {user_data['email']}")
        print(f"   濮撳悕: {user_data['first_name']}")
        print(f"   瑙掕壊: 瓒呯骇绠＄悊鍛?)
        print()
        print("鈿狅笍  閲嶈鎻愮ず锛?)
        print("   1. 璇峰Ε鍠勪繚绠′笂杩扮櫥褰曞嚟鎹?)
        print("   2. 棣栨鐧诲綍鍚庯紝璇风珛鍗充慨鏀瑰瘑鐮?)
        print("   3. 寤鸿璁剧疆鏇村鏉傜殑瀵嗙爜浠ユ彁楂樺畨鍏ㄦ€?)
        print()
        print(f"馃寪 鐜板湪鍙互璁块棶绯荤粺骞朵娇鐢ㄤ笂杩板嚟鎹櫥褰曪細")
        print(f"   http://localhost:8000")
        print()
        
        return True
        
    except Exception as e:
        print()
        print(f"鉂?鍒涘缓绠＄悊鍛樿处鎴峰け璐? {e}")
        print()
        return False


def check_existing_admins():
    """妫€鏌ユ槸鍚﹀凡瀛樺湪绠＄悊鍛?""
    admin_count = User.objects.filter(role='admin').count()
    
    if admin_count > 0:
        print("鈩癸笍  绯荤粺涓凡瀛樺湪绠＄悊鍛樿处鎴凤細")
        print()
        
        admins = User.objects.filter(role='admin').values(
            'username', 'email', 'first_name', 'is_active', 'last_login'
        )
        
        for i, admin in enumerate(admins, 1):
            print(f"   {i}. 鐢ㄦ埛鍚? {admin['username']}")
            print(f"      閭: {admin['email']}")
            print(f"      濮撳悕: {admin['first_name']}")
            print(f"      鐘舵€? {'婵€娲? if admin['is_active'] else '绂佺敤'}")
            last_login = admin['last_login'].strftime('%Y-%m-%d %H:%M:%S') if admin['last_login'] else '浠庢湭鐧诲綍'
            print(f"      鏈€鍚庣櫥褰? {last_login}")
            print()
        
        confirm = input("鏄惁浠嶈鍒涘缓鏂扮殑绠＄悊鍛樿处鎴? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '鏄?]:
            print("鉂?宸插彇娑堝垱寤?)
            return False
        print()
    
    return True


def main():
    """涓诲嚱鏁?""
    print_banner()
    
    # 妫€鏌ュ懡浠よ鍙傛暟
    quick_mode = '--quick' in sys.argv or '-q' in sys.argv
    
    # 妫€鏌ユ槸鍚﹀凡瀛樺湪绠＄悊鍛?
    if not check_existing_admins():
        return
    
    # 鑾峰彇鐢ㄦ埛鏁版嵁
    if quick_mode:
        user_data = quick_create_admin()
    else:
        user_data = interactive_create_admin()
    
    # 濡傛灉鐢ㄦ埛鍙栨秷锛岄€€鍑?
    if user_data is None:
        return
    
    # 鍒涘缓绠＄悊鍛?
    success = create_superuser(user_data)
    
    if success:
        print("=" * 70)
        print(" " * 20 + "馃帀 璐︽埛鍒涘缓瀹屾垚锛?)
        print("=" * 70)
    else:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("鈿狅笍  鎿嶄綔宸茶鐢ㄦ埛涓柇")
        sys.exit(0)
    except Exception as e:
        print()
        print(f"鉂?鍙戠敓閿欒: {e}")
        sys.exit(1)


