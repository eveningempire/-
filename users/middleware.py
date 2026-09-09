"""
Middleware for recording user access to the PHM platform.
"""

import time
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .models import UserAccessRecord

User = get_user_model()


class AccessRecordMiddleware(MiddlewareMixin):
    """璁板綍鐢ㄦ埛璁块棶鐨勪腑闂翠欢"""
    
    def process_request(self, request):
        """澶勭悊璇锋眰鏃惰褰曡闂俊鎭?""
        # 璁板綍璇锋眰寮€濮嬫椂闂?        request.start_time = time.time()
        
        # 鍙褰曞墠绔〉闈㈢殑璁块棶锛屼笉璁板綍API璇锋眰
        if request.path.startswith('/api/'):
            return None
        
        # 鍙褰旼ET璇锋眰
        if request.method != 'GET':
            return None
        
        # 璺宠繃闈欐€佹枃浠?        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
        
        # 璁板綍璁块棶淇℃伅
        self._record_access(request)
        
        return None
    
    def _record_access(self, request):
        """璁板綍璁块棶淇℃伅"""
        try:
            # 鑾峰彇褰撳墠鐢ㄦ埛锛堝鏋滄湁鐨勮瘽锛?            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated:
                # 濡傛灉娌℃湁鐧诲綍鐢ㄦ埛锛屽垱寤轰竴涓尶鍚嶇敤鎴疯褰?                user, created = User.objects.get_or_create(
                    username='anonymous',
                    defaults={
                        'email': '',
                        'role': User.Role.USER,
                        'is_active': False
                    }
                )
            
            # 鑾峰彇瀹㈡埛绔疘P
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # 鑾峰彇鐢ㄦ埛浠ｇ悊
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # 鑾峰彇璁块棶鐨勯〉闈?            page_visited = request.path
            if page_visited == '/':
                page_visited = '棣栭〉'
            elif page_visited.startswith('/'):
                page_visited = page_visited[1:].replace('-', ' ').title()
            
            # 鍒涘缓璁块棶璁板綍
            UserAccessRecord.objects.create(
                user=user,
                page_visited=page_visited,
                ip_address=ip_address,
                user_agent=user_agent,
                session_key=request.session.session_key if hasattr(request, 'session') and request.session and request.session.session_key else '',
                device_info=self._parse_device_info(user_agent),
                access_duration=0  # 鍒濆涓?
            )
            
        except Exception as e:
            # 璁板綍澶辫触涓嶅簲璇ュ奖鍝嶆甯歌姹?            print(f"璁板綍璁块棶淇℃伅澶辫触: {e}")
    
    def _parse_device_info(self, user_agent):
        """瑙ｆ瀽鐢ㄦ埛浠ｇ悊鑾峰彇璁惧淇℃伅"""
        device_info = {
            'browser': '鏈煡',
            'browser_version': '',
            'os': '鏈煡',
            'os_version': '',
            'device_type': 'desktop'
        }
        
        try:
            user_agent_lower = user_agent.lower()
            
            # 妫€娴嬫祻瑙堝櫒
            if 'chrome' in user_agent_lower:
                device_info['browser'] = 'Chrome'
            elif 'firefox' in user_agent_lower:
                device_info['browser'] = 'Firefox'
            elif 'safari' in user_agent_lower:
                device_info['browser'] = 'Safari'
            elif 'edge' in user_agent_lower:
                device_info['browser'] = 'Edge'
            elif 'opera' in user_agent_lower:
                device_info['browser'] = 'Opera'
            
            # 妫€娴嬫搷浣滅郴缁?            if 'windows' in user_agent_lower:
                device_info['os'] = 'Windows'
            elif 'mac' in user_agent_lower:
                device_info['os'] = 'macOS'
            elif 'linux' in user_agent_lower:
                device_info['os'] = 'Linux'
            elif 'android' in user_agent_lower:
                device_info['os'] = 'Android'
                device_info['device_type'] = 'mobile'
            elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
                device_info['os'] = 'iOS'
                device_info['device_type'] = 'mobile'
            
            # 妫€娴嬭澶囩被鍨?            if 'mobile' in user_agent_lower or 'android' in user_agent_lower or 'iphone' in user_agent_lower:
                device_info['device_type'] = 'mobile'
            elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
                device_info['device_type'] = 'tablet'
            
        except Exception:
            pass
        
        return device_info

