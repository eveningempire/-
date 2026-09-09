#!/usr/bin/env python
"""
璋冭瘯鐢ㄦ埛鏉冮檺闂
"""

import os
import sys
import django

# 璁剧疆Django鐜 - 淇璺緞闂
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
import logging

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

User = get_user_model()

def debug_user_permissions():
    """璋冭瘯鐢ㄦ埛鏉冮檺"""
    print("=" * 60)
    print("璋冭瘯鐢ㄦ埛鏉冮檺闂")
    print("=" * 60)
    
    # 妫€鏌ユ墍鏈夌敤鎴?
    users = User.objects.all()
    print(f"\n褰撳墠绯荤粺涓殑鐢ㄦ埛鏁伴噺: {users.count()}")
    
    for user in users:
        print(f"\n鐢ㄦ埛: {user.username}")
        print(f"  ID: {user.id}")
        print(f"  瑙掕壊: {user.role}")
        print(f"  鏄惁婵€娲? {user.is_active}")
        print(f"  鏄惁璁よ瘉: {user.is_authenticated}")
        print(f"  鏄惁瓒呯骇鐢ㄦ埛: {user.is_superuser}")
        print(f"  鏄惁鍛樺伐: {user.is_staff}")
    
    # 妫€鏌ョ鐞嗗憳鐢ㄦ埛
    admin_users = User.objects.filter(role='admin')
    print(f"\n绠＄悊鍛樼敤鎴锋暟閲? {admin_users.count()}")
    
    for admin in admin_users:
        print(f"  绠＄悊鍛? {admin.username} (ID: {admin.id})")
    
    # 妫€鏌ユ櫘閫氱敤鎴?
    normal_users = User.objects.filter(role='user')
    print(f"\n鏅€氱敤鎴锋暟閲? {normal_users.count()}")
    
    for user in normal_users:
        print(f"  鏅€氱敤鎴? {user.username} (ID: {user.id})")

if __name__ == '__main__':
    debug_user_permissions()

