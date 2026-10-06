"""
Serializers for the users application.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserAccessRecord

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'role_display', 'is_active', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']


class RegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'first_name', 'last_name', 'role']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("密码不匹配")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserAccessRecordSerializer(serializers.ModelSerializer):
    """用户访问记录序列化器"""
    
    username = serializers.CharField(source='user.username', read_only=True)
    user_role = serializers.CharField(source='user.get_role_display', read_only=True)
    duration_display = serializers.CharField(read_only=True)
    access_time_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAccessRecord
        fields = [
            'id', 'username', 'user_role', 'access_time', 'access_time_formatted',
            'page_visited', 'ip_address', 'user_agent', 'session_key',
            'device_info', 'access_duration', 'duration_display'
        ]
        read_only_fields = ['id', 'access_time', 'username', 'user_role', 'duration_display']
    
    def get_access_time_formatted(self, obj):
        return obj.access_time.strftime('%Y-%m-%d %H:%M:%S') if obj.access_time else ''


class CurrentUserSerializer(serializers.ModelSerializer):
    """当前用户信息序列化器"""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    recent_access = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'role_display', 'recent_access']
    
    def get_recent_access(self, obj):
        """获取最近的访问记录"""
        recent_records = obj.access_records.all()[:5]  # 最近5条
        return UserAccessRecordSerializer(recent_records, many=True).data