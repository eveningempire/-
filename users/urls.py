"""
URL configuration for the users app.

Defines RESTful API endpoints for user management, authentication and
access records. The endpoints are registered under the /api/v1/users/
prefix in the project level URL conf.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    RegisterViewSet,
    UserAccessRecordViewSet,
    LoginView,
    LogoutView,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"register", RegisterViewSet, basename="register")
router.register(r"access-records", UserAccessRecordViewSet, basename="access-records")

urlpatterns = [
    # 登录登出端点
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
] + router.urls
