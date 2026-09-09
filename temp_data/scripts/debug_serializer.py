#!/usr/bin/env python
"""
璋冭瘯鐢ㄦ埛搴忓垪鍖栧櫒
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.serializers import UserSerializer

User = get_user_model()

def debug_serializer():
    """璋冭瘯搴忓垪鍖栧櫒"""
    print("=" * 60)
    print("璋冭瘯鐢ㄦ埛搴忓垪鍖栧櫒")
    print("=" * 60)
    
    # 鑾峰彇鎵€鏈夌敤鎴?
    users = User.objects.all()
    print(f"鏁版嵁搴撲腑鐨勭敤鎴锋暟閲? {users.count()}")
    
    for user in users:
        print(f"\n鐢ㄦ埛: {user.username}")
        print(f"  ID: {user.id}")
        print(f"  瑙掕壊: {user.get_role_display()}")
        print(f"  鍒涘缓鏃堕棿: {user.date_joined}")
        print(f"  鏈€鍚庣櫥褰? {user.last_login}")
        
        # 浣跨敤搴忓垪鍖栧櫒
        serializer = UserSerializer(user)
        data = serializer.data
        
        print(f"  搴忓垪鍖栧悗鐨勬暟鎹?")
        print(f"    username: {data.get('username')}")
        print(f"    role: {data.get('role')}")
        print(f"    role_display: {data.get('role_display')}")
        print(f"    date_joined: {data.get('date_joined')}")
        print(f"    last_login: {data.get('last_login')}")
        
        # 妫€鏌ュ瓧娈垫槸鍚﹀瓨鍦?
        if 'last_login' in data:
            print("  鉁?last_login瀛楁鍦ㄥ簭鍒楀寲鏁版嵁涓瓨鍦?)
        else:
            print("  鉂?last_login瀛楁鍦ㄥ簭鍒楀寲鏁版嵁涓己澶?)
    
    print("\n" + "=" * 60)
    print("璋冭瘯瀹屾垚")
    print("=" * 60)

if __name__ == '__main__':
    debug_serializer()

