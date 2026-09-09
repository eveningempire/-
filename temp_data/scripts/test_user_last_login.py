#!/usr/bin/env python
"""
娴嬭瘯鐢ㄦ埛鏈€鍚庣櫥褰曟椂闂村瓧娈?
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def test_user_last_login():
    """娴嬭瘯鐢ㄦ埛鏈€鍚庣櫥褰曟椂闂?""
    print("=" * 60)
    print("娴嬭瘯鐢ㄦ埛鏈€鍚庣櫥褰曟椂闂?)
    print("=" * 60)
    
    # 鑾峰彇鎵€鏈夌敤鎴?
    users = User.objects.all()
    print(f"绯荤粺涓殑鐢ㄦ埛鏁伴噺: {users.count()}")
    
    for user in users:
        print(f"\n鐢ㄦ埛: {user.username}")
        print(f"  ID: {user.id}")
        print(f"  瑙掕壊: {user.get_role_display()}")
        print(f"  鍒涘缓鏃堕棿: {user.date_joined}")
        print(f"  鏈€鍚庣櫥褰? {user.last_login}")
        
        if user.last_login:
            # 璁＄畻鏃堕棿宸?
            time_diff = timezone.now() - user.last_login
            print(f"  璺濈鐜板湪: {time_diff}")
            
            # 鏍煎紡鍖栨樉绀?
            if time_diff.days > 0:
                print(f"  鏄剧ず鏍煎紡: {time_diff.days}澶╁墠")
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                print(f"  鏄剧ず鏍煎紡: {hours}灏忔椂鍓?)
            elif time_diff.seconds > 60:
                minutes = time_diff.seconds // 60
                print(f"  鏄剧ず鏍煎紡: {minutes}鍒嗛挓鍓?)
            else:
                print(f"  鏄剧ず鏍煎紡: 鍒氬垰")
        else:
            print("  鏄剧ず鏍煎紡: 浠庢湭鐧诲綍")
    
    print("\n" + "=" * 60)
    print("娴嬭瘯瀹屾垚")
    print("=" * 60)

if __name__ == '__main__':
    test_user_last_login()

