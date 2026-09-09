#!/usr/bin/env python
"""
閲嶇疆鐢ㄦ埛瀵嗙爜鑴氭湰
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

def reset_user_passwords():
    """閲嶇疆鐢ㄦ埛瀵嗙爜"""
    print("=== 閲嶇疆鐢ㄦ埛瀵嗙爜 ===")
    
    # 閲嶇疆绠＄悊鍛樺瘑鐮?
    admin_user = User.objects.filter(role='admin').first()
    if admin_user:
        admin_user.set_password('admin123456')
        admin_user.save()
        print(f"鉁?閲嶇疆绠＄悊鍛樺瘑鐮? {admin_user.username} -> admin123456")
    
    # 閲嶇疆鏅€氱敤鎴峰瘑鐮?
    user_users = User.objects.filter(role='user')
    for user in user_users:
        user.set_password('user123')
        user.save()
        print(f"鉁?閲嶇疆鏅€氱敤鎴峰瘑鐮? {user.username} -> user123")
    
    print(f"\n鎬诲叡閲嶇疆浜?{user_users.count() + 1} 涓敤鎴风殑瀵嗙爜")
    
    # 鏄剧ず鎵€鏈夌敤鎴?
    print("\n=== 褰撳墠鐢ㄦ埛鍒楄〃 ===")
    all_users = User.objects.all()
    for user in all_users:
        print(f"  - {user.username} (瑙掕壊: {user.role}, 鐘舵€? {'鍚敤' if user.is_active else '绂佺敤'})")

def main():
    """涓诲嚱鏁?""
    print("鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁?- 鐢ㄦ埛瀵嗙爜閲嶇疆宸ュ叿")
    print("=" * 50)
    
    reset_user_passwords()
    
    print("\n=== 閲嶇疆瀹屾垚 ===")
    print("鐜板湪鍙互浣跨敤浠ヤ笅瀵嗙爜鐧诲綍锛?)
    print("- 绠＄悊鍛? admin / admin123456")
    print("- 鏅€氱敤鎴? [鐢ㄦ埛鍚峕 / user123")

if __name__ == "__main__":
    main()

