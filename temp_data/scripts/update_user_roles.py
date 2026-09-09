#!/usr/bin/env python
"""
鏇存柊鐢ㄦ埛瑙掕壊鑴氭湰 - 灏嗗尰鐢熻鑹叉敼涓烘櫘閫氱敤鎴?
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

User = get_user_model()

def update_user_roles():
    """鏇存柊鐢ㄦ埛瑙掕壊"""
    print("=== 鏇存柊鐢ㄦ埛瑙掕壊 ===")
    
    # 鏌ユ壘鎵€鏈夊尰鐢熻鑹茬殑鐢ㄦ埛
    doctor_users = User.objects.filter(role='doctor')
    
    if doctor_users.exists():
        print(f"鎵惧埌 {doctor_users.count()} 涓尰鐢熻鑹茬敤鎴凤紝姝ｅ湪鏇存柊...")
        
        for user in doctor_users:
            old_role = user.role
            user.role = 'user'
            user.save()
            print(f"鉁?鐢ㄦ埛 {user.username} 瑙掕壊浠?'{old_role}' 鏇存柊涓?'user'")
    else:
        print("娌℃湁鎵惧埌鍖荤敓瑙掕壊鐨勭敤鎴?)
    
    # 鏄剧ず褰撳墠鎵€鏈夌敤鎴?
    print("\n=== 褰撳墠鐢ㄦ埛鍒楄〃 ===")
    all_users = User.objects.all()
    for user in all_users:
        print(f"  - {user.username} (瑙掕壊: {user.role})")

def main():
    """涓诲嚱鏁?""
    print("鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁?- 鐢ㄦ埛瑙掕壊鏇存柊宸ュ叿")
    print("=" * 50)
    
    update_user_roles()
    
    print("\n=== 鏇存柊瀹屾垚 ===")
    print("鐜板湪绯荤粺鍙敮鎸佺鐞嗗憳鍜屾櫘閫氱敤鎴蜂袱绉嶈鑹?)

if __name__ == "__main__":
    main()

