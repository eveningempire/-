"""
Custom user model for the PHM platform.

We extend Django's AbstractUser to add a ``role`` field which allows us
to differentiate between ordinary users, doctors, administrators and
other roles that might be required by the platform.
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    """Extends Django's AbstractUser with a role field."""

    class Role(models.TextChoices):
        ADMIN = "admin", "绠＄悊鍛?
        USER = "user", "鏅€氱敤鎴?

    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.USER,
        help_text="Role of the user for permission management",
    )

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"


class UserAccessRecord(models.Model):
    """鐢ㄦ埛璁块棶璁板綍"""
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='access_records',
        verbose_name="鐢ㄦ埛"
    )
    access_time = models.DateTimeField(auto_now_add=True, verbose_name="璁块棶鏃堕棿")
    page_visited = models.CharField(max_length=100, verbose_name="璁块棶椤甸潰")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP鍦板潃")
    user_agent = models.TextField(blank=True, verbose_name="鐢ㄦ埛浠ｇ悊")
    session_key = models.CharField(max_length=40, blank=True, verbose_name="浼氳瘽瀵嗛挜")
    device_info = models.JSONField(default=dict, blank=True, verbose_name="璁惧淇℃伅")
    access_duration = models.IntegerField(default=0, verbose_name="璁块棶鏃堕暱(绉?")
    
    class Meta:
        verbose_name = "鐢ㄦ埛璁块棶璁板綍"
        verbose_name_plural = "鐢ㄦ埛璁块棶璁板綍"
        ordering = ['-access_time']
        indexes = [
            models.Index(fields=['-access_time']),
            models.Index(fields=['user', '-access_time']),
            models.Index(fields=['page_visited']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.page_visited} - {self.access_time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def duration_display(self):
        """鏍煎紡鍖栨樉绀鸿闂椂闀?""
        if self.access_duration <= 0:
            return "鏈煡"
        
        hours = self.access_duration // 3600
        minutes = (self.access_duration % 3600) // 60
        seconds = self.access_duration % 60
        
        if hours > 0:
            return f"{hours}灏忔椂{minutes}鍒嗛挓"
        elif minutes > 0:
            return f"{minutes}鍒嗛挓{seconds}绉?
        else:
            return f"{seconds}绉?

