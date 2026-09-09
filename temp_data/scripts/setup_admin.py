#!/usr/bin/env python
"""
PHM骞冲彴绠＄悊鍛樿处鍙峰揩閫熻缃剼鏈?

鏈剼鏈敤浜庡揩閫熷垱寤烘垨鏇存柊绠＄悊鍛樿处鍙凤紝閫傜敤浜庡凡鏈夋暟鎹簱鐨勬儏鍐点€?
"""

import os
import sys
import getpass
from pathlib import Path

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')

import django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def print_header(title):
    """鎵撳嵃鏍囬"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def get_user_input(prompt, default=None, password=False):
    """鑾峰彇鐢ㄦ埛杈撳叆"""
    if password:
        while True:
            value = getpass.getpass(prompt)
            if value:
                return value
            elif default:
                return default
            else:
                print("鉂?瀵嗙爜涓嶈兘涓虹┖锛岃閲嶆柊杈撳叆")
    else:
        value = input(prompt).strip()
        return value if value else default

def create_admin_user():
    """鍒涘缓绠＄悊鍛樿处鍙?""
    print_header("PHM骞冲彴绠＄悊鍛樿处鍙疯缃?)
    
    print("馃懁 璇疯緭鍏ョ鐞嗗憳璐﹀彿淇℃伅:")
    
    # 鑾峰彇鐢ㄦ埛鍚?
    username = get_user_input("鐢ㄦ埛鍚?(榛樿: admin): ", "admin")
    
    # 鑾峰彇閭
    email = get_user_input("閭: ")
    if not email:
        print("鉂?閭涓嶈兘涓虹┖")
        return False
    
    # 鑾峰彇瀵嗙爜
    password = get_user_input("瀵嗙爜: ", password=True)
    if not password:
        print("鉂?瀵嗙爜涓嶈兘涓虹┖")
        return False
    
    # 纭瀵嗙爜
    confirm_password = get_user_input("纭瀵嗙爜: ", password=True)
    if password != confirm_password:
        print("鉂?涓ゆ杈撳叆鐨勫瘑鐮佷笉涓€鑷?)
        return False
    
    print(f"\n馃搵 璐﹀彿淇℃伅:")
    print(f"   鐢ㄦ埛鍚? {username}")
    print(f"   閭: {email}")
    print(f"   瀵嗙爜: {'*' * len(password)}")
    
    # 纭鍒涘缓
    confirm = input("\n鏄惁鍒涘缓姝ょ鐞嗗憳璐﹀彿? (Y/n): ").strip().lower()
    if confirm in ['n', 'no']:
        print("鉂?鍙栨秷鍒涘缓")
        return False
    
    try:
        # 妫€鏌ョ敤鎴锋槸鍚﹀凡瀛樺湪
        if User.objects.filter(username=username).exists():
            print(f"\n鈿狅笍  鐢ㄦ埛 {username} 宸插瓨鍦紝灏嗘洿鏂颁负绠＄悊鍛?)
            user = User.objects.get(username=username)
            user.email = email
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.role = 'admin'
            user.save()
            print("鉁?鐢ㄦ埛鏉冮檺宸叉洿鏂颁负绠＄悊鍛?)
        else:
            # 鍒涘缓鏂扮鐞嗗憳鐢ㄦ埛
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='admin'
            )
            print("鉁?绠＄悊鍛樿处鍙峰垱寤烘垚鍔?)
        
        print(f"\n馃懁 绠＄悊鍛樹俊鎭?")
        print(f"   鐢ㄦ埛鍚? {user.username}")
        print(f"   閭: {user.email}")
        print(f"   瑙掕壊: {user.get_role_display()}")
        print(f"   瓒呯骇鐢ㄦ埛: {'鏄? if user.is_superuser else '鍚?}")
        print(f"   鍛樺伐鐘舵€? {'鏄? if user.is_staff else '鍚?}")
        
        print(f"\n馃敆 璁块棶鍦板潃:")
        print(f"   绠＄悊鍚庡彴: http://localhost:8000/admin/")
        print(f"   鍓嶇鐣岄潰: http://localhost:3000")
        print(f"   API鎺ュ彛: http://localhost:8000/api/v1/")
        
        return True
        
    except Exception as e:
        print(f"鉂?鍒涘缓绠＄悊鍛樿处鍙峰け璐? {e}")
        return False

def list_users():
    """鍒楀嚭鎵€鏈夌敤鎴?""
    print_header("鐢ㄦ埛鍒楄〃")
    
    users = User.objects.all()
    if not users:
        print("馃摥 鏆傛棤鐢ㄦ埛")
        return
    
    print(f"馃搳 鍏辨壘鍒?{users.count()} 涓敤鎴?\n")
    
    for i, user in enumerate(users, 1):
        print(f"{i:2d}. {user.username}")
        print(f"    閭: {user.email}")
        print(f"    瑙掕壊: {user.get_role_display()}")
        print(f"    瓒呯骇鐢ㄦ埛: {'鏄? if user.is_superuser else '鍚?}")
        print(f"    鍛樺伐鐘舵€? {'鏄? if user.is_staff else '鍚?}")
        print(f"    鏈€鍚庣櫥褰? {user.last_login or '浠庢湭鐧诲綍'}")
        print()

def reset_password():
    """閲嶇疆鐢ㄦ埛瀵嗙爜"""
    print_header("閲嶇疆鐢ㄦ埛瀵嗙爜")
    
    # 鍒楀嚭鎵€鏈夌敤鎴?
    users = User.objects.all()
    if not users:
        print("馃摥 鏆傛棤鐢ㄦ埛")
        return False
    
    print("璇烽€夋嫨瑕侀噸缃瘑鐮佺殑鐢ㄦ埛:")
    for i, user in enumerate(users, 1):
        print(f"{i}. {user.username} ({user.email})")
    
    try:
        choice = int(input("\n璇疯緭鍏ョ敤鎴风紪鍙? ")) - 1
        if choice < 0 or choice >= len(users):
            print("鉂?鏃犳晥鐨勭敤鎴风紪鍙?)
            return False
        
        user = users[choice]
        print(f"\n閲嶇疆鐢ㄦ埛 {user.username} 鐨勫瘑鐮?)
        
        # 鑾峰彇鏂板瘑鐮?
        password = get_user_input("鏂板瘑鐮? ", password=True)
        if not password:
            print("鉂?瀵嗙爜涓嶈兘涓虹┖")
            return False
        
        confirm_password = get_user_input("纭鏂板瘑鐮? ", password=True)
        if password != confirm_password:
            print("鉂?涓ゆ杈撳叆鐨勫瘑鐮佷笉涓€鑷?)
            return False
        
        # 鏇存柊瀵嗙爜
        user.set_password(password)
        user.save()
        print(f"鉁?鐢ㄦ埛 {user.username} 鐨勫瘑鐮佸凡閲嶇疆")
        return True
        
    except ValueError:
        print("鉂?璇疯緭鍏ユ湁鏁堢殑鏁板瓧")
        return False
    except Exception as e:
        print(f"鉂?閲嶇疆瀵嗙爜澶辫触: {e}")
        return False

def interactive_menu():
    """浜や簰寮忚彍鍗?""
    while True:
        print_header("PHM骞冲彴鐢ㄦ埛绠＄悊")
        
        print("璇烽€夋嫨瑕佹墽琛岀殑鎿嶄綔:")
        print("1. 鍒涘缓绠＄悊鍛樿处鍙?)
        print("2. 鏌ョ湅鐢ㄦ埛鍒楄〃")
        print("3. 閲嶇疆鐢ㄦ埛瀵嗙爜")
        print("0. 閫€鍑?)
        
        choice = input("\n璇疯緭鍏ラ€夋嫨 (0-3): ").strip()
        
        if choice == '0':
            print("馃憢 鍐嶈!")
            break
        elif choice == '1':
            create_admin_user()
        elif choice == '2':
            list_users()
        elif choice == '3':
            reset_password()
        else:
            print("鉂?鏃犳晥閫夋嫨锛岃閲嶆柊杈撳叆")
        
        input("\n鎸夊洖杞﹂敭缁х画...")

def main():
    """涓诲嚱鏁?""
    import argparse
    
    parser = argparse.ArgumentParser(description="PHM骞冲彴绠＄悊鍛樿处鍙疯缃伐鍏?)
    parser.add_argument('--create', action='store_true', help='鍒涘缓绠＄悊鍛樿处鍙?)
    parser.add_argument('--list', action='store_true', help='鏌ョ湅鐢ㄦ埛鍒楄〃')
    parser.add_argument('--reset', action='store_true', help='閲嶇疆鐢ㄦ埛瀵嗙爜')
    parser.add_argument('--interactive', action='store_true', help='浜や簰寮忚彍鍗?)
    
    args = parser.parse_args()
    
    if args.create:
        create_admin_user()
    elif args.list:
        list_users()
    elif args.reset:
        reset_password()
    elif args.interactive:
        interactive_menu()
    else:
        # 榛樿鏄剧ず甯姪
        parser.print_help()

if __name__ == '__main__':
    main()

