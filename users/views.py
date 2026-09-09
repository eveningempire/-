# phm_backend/users/views.py
from __future__ import annotations

import logging
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.decorators import action

from .serializers import UserSerializer, RegisterSerializer, UserAccessRecordSerializer, CurrentUserSerializer
from .models import UserAccessRecord

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomIsAuthenticated(BasePermission):
    """鑷畾涔夎璇佹潈闄愮被"""
    def has_permission(self, request, view):
        logger.debug(f"鏉冮檺妫€鏌?- has_permission: 鐢ㄦ埛={request.user}, 璁よ瘉鐘舵€?{request.user.is_authenticated}")
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """瀵硅薄绾у埆鐨勬潈闄愭鏌?""
        user = request.user
        logger.debug(f"鏉冮檺妫€鏌?- has_object_permission: 鐢ㄦ埛={user.username}, 瑙掕壊={user.role}, 瀵硅薄={obj}")
        
        # 绠＄悊鍛樺彲浠ユ搷浣滄墍鏈夊璞?        if user.role == User.Role.ADMIN:
            logger.debug(f"绠＄悊鍛樻潈闄愰€氳繃: {user.username}")
            return True
        
        # 鏅€氱敤鎴峰彧鑳芥煡鐪嬪叾浠栨櫘閫氱敤鎴?        if user.role == User.Role.USER:
            if hasattr(obj, 'role'):
                result = obj.role == User.Role.USER
                logger.debug(f"鏅€氱敤鎴锋潈闄愭鏌? {result}")
                return result
        
        logger.debug(f"鏉冮檺妫€鏌ュけ璐? 鐢ㄦ埛={user.username}, 瑙掕壊={user.role}")
        return False


class UserViewSet(viewsets.ModelViewSet):
    """鐢ㄦ埛绠＄悊瑙嗗浘闆?""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [CustomIsAuthenticated]  # 闇€瑕佺櫥褰曟墠鑳借闂?    
    def get_queryset(self):
        """鏍规嵁鐢ㄦ埛瑙掕壊杩斿洖涓嶅悓鐨勬煡璇㈤泦"""
        user = self.request.user
        
        if user.role == User.Role.ADMIN:
            # 绠＄悊鍛樺彲浠ョ湅鍒版墍鏈夌敤鎴?            return User.objects.all().select_related()
        elif user.role == User.Role.USER:
            # 鏅€氱敤鎴峰彧鑳界湅鍒板叾浠栨櫘閫氱敤鎴?            return User.objects.filter(role=User.Role.USER).select_related()
        else:
            # 鍏朵粬鎯呭喌鏃犳潈闄?            return User.objects.none()
    
    def perform_create(self, serializer):
        """鍒涘缓鐢ㄦ埛鏃剁殑鏉冮檺妫€鏌?""
        if self.request.user.role != User.Role.ADMIN:
            raise PermissionError("鍙湁绠＄悊鍛樺彲浠ュ垱寤虹敤鎴?)
        serializer.save()
    
    def perform_update(self, serializer):
        """鏇存柊鐢ㄦ埛鏃剁殑鏉冮檺妫€鏌?""
        if self.request.user.role != User.Role.ADMIN:
            raise PermissionError("鍙湁绠＄悊鍛樺彲浠ョ紪杈戠敤鎴?)
        serializer.save()
    
    def perform_destroy(self, instance):
        """鍒犻櫎鐢ㄦ埛鏃剁殑鏉冮檺妫€鏌?""
        user = self.request.user
        logger.debug(f"鎵ц鍒犻櫎鎿嶄綔 - 鐢ㄦ埛: {user.username}, 瑙掕壊: {user.role}, 鐩爣鐢ㄦ埛: {instance.username}, 鐩爣瑙掕壊: {instance.role}")
        
        if user.role != User.Role.ADMIN:
            logger.warning(f"鏉冮檺鎷掔粷 - 闈炵鐞嗗憳鐢ㄦ埛灏濊瘯鍒犻櫎: {user.username}")
            raise PermissionError("鍙湁绠＄悊鍛樺彲浠ュ垹闄ょ敤鎴?)
        
        if instance.role == User.Role.ADMIN:
            logger.warning(f"鏉冮檺鎷掔粷 - 灏濊瘯鍒犻櫎绠＄悊鍛樿处鎴? {instance.username}")
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("涓嶈兘鍒犻櫎绠＄悊鍛樿处鎴?)
        
        logger.info(f"鍒犻櫎鐢ㄦ埛鎴愬姛: {instance.username} (鐢?{user.username} 鎵ц)")
        instance.delete()

    def get_object(self):
        """鑾峰彇瀵硅薄锛屽浜庡垹闄ゆ搷浣滈渶瑕佽幏鍙栨纭殑鐢ㄦ埛瀵硅薄"""
        if self.action == 'me':
            # 瀵逛簬me鎿嶄綔锛岃繑鍥炲綋鍓嶇敤鎴?            return self.request.user
        else:
            # 瀵逛簬鍏朵粬鎿嶄綔锛屼娇鐢ㄩ粯璁ょ殑get_object閫昏緫
            return super().get_object()

    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """鐢ㄦ埛娉ㄥ唽"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class UserAccessRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """鐢ㄦ埛璁块棶璁板綍绠＄悊"""
    serializer_class = UserAccessRecordSerializer
    permission_classes = [CustomIsAuthenticated]
    
    def get_queryset(self):
        """鏍规嵁鐢ㄦ埛鏉冮檺杩斿洖涓嶅悓鐨勬煡璇㈤泦"""
        user = self.request.user
        
        # 绠＄悊鍛樺彲浠ユ煡鐪嬫墍鏈夎褰曪紝鏅€氱敤鎴峰彧鑳芥煡鐪嬭嚜宸辩殑璁板綍
        if user.role == User.Role.ADMIN:
            queryset = UserAccessRecord.objects.all()
        else:
            queryset = UserAccessRecord.objects.filter(user=user)
        
        return queryset.select_related('user').order_by('-access_time')
    
    @action(detail=True, methods=['delete'])
    def delete_record(self, request, pk=None):
        """鍒犻櫎鍗曟潯璁块棶璁板綍"""
        try:
            record = self.get_object()
            record.delete()
            return Response({"message": "璁块棶璁板綍宸插垹闄?}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """娓呯┖鎵€鏈夎闂褰?""
        try:
            user = request.user
            if user.role == User.Role.ADMIN:
                # 绠＄悊鍛樺彲浠ユ竻绌烘墍鏈夎褰?                UserAccessRecord.objects.all().delete()
                message = "鎵€鏈夎闂褰曞凡娓呯┖"
            else:
                # 鏅€氱敤鎴峰彧鑳芥竻绌鸿嚜宸辩殑璁板綍
                UserAccessRecord.objects.filter(user=user).delete()
                message = "鎮ㄧ殑璁块棶璁板綍宸叉竻绌?
            
            return Response({"message": message}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def record_access(self, request):
        """璁板綍鐢ㄦ埛璁块棶"""
        try:
            user = request.user
            page_visited = request.data.get('page', '鏈煡椤甸潰')
            
            # 鑾峰彇瀹㈡埛绔疘P
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # 鑾峰彇鐢ㄦ埛浠ｇ悊
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # 鍒涘缓璁块棶璁板綍
            UserAccessRecord.objects.create(
                user=user,
                page_visited=page_visited,
                ip_address=ip_address,
                user_agent=user_agent,
                session_key=request.session.session_key,
                device_info=self._parse_device_info(user_agent),
                access_duration=0  # 鍒濆涓?锛屽悗缁彲浠ユ洿鏂?            )
            
            return Response({"message": "璁块棶璁板綍宸插垱寤?}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
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


@method_decorator(csrf_exempt, name="dispatch")  # 寮€鍙戦樁娈碉細鍏?CSRF锛岄厤鍚?Session 鐧婚檰
class LoginView(APIView):
    """琛ㄥ崟鐧诲綍锛堝墠绔互 application/x-www-form-urlencoded 鎻愪氦 username/password锛?""
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"鐧诲綍璇锋眰寮€濮?- 鏂规硶: {request.method}, 璺緞: {request.path}")
        logger.info(f"璇锋眰澶? {dict(request.headers)}")
        logger.info(f"璇锋眰鏁版嵁: POST={dict(request.POST)}, DATA={request.data}")
        
        # 鍏煎 form 琛ㄥ崟鍜?JSON
        username = request.POST.get("username") or request.data.get("username")
        password = request.POST.get("password") or request.data.get("password")

        logger.info(f"鎻愬彇鐨勭敤鎴峰悕: {username}")

        if not username or not password:
            logger.warning("鐢ㄦ埛鍚嶆垨瀵嗙爜缂哄け")
            return Response({"detail": "鐢ㄦ埛鍚嶆垨瀵嗙爜缂哄け"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        logger.info(f"璁よ瘉缁撴灉: user={user}, is_active={user.is_active if user else None}")
        
        if user is None or not user.is_active:
            logger.warning(f"璁よ瘉澶辫触: user={user}, is_active={user.is_active if user else None}")
            return Response({"detail": "鐢ㄦ埛鍚嶆垨瀵嗙爜閿欒"}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)  # 鍐欏叆 sessionid cookie
        
        # 鏇存柊鏈€鍚庣櫥褰曟椂闂?        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        logger.info(f"鐧诲綍鎴愬姛: {user.username}, 瑙掕壊: {user.role}")
        
        return Response({
            "detail": "鐧诲綍鎴愬姛", 
            "username": user.get_username(),
            "role": user.role
        })


@method_decorator(csrf_exempt, name="dispatch")  # 寮€鍙戦樁娈碉細鍏?CSRF
class LogoutView(APIView):
    """鐧诲嚭"""
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response({"detail": "宸查€€鍑虹櫥褰?})

