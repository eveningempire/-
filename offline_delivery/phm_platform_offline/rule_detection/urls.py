"""
规则检测URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'faults', views.FaultDefinitionViewSet)
router.register(r'rules', views.RuleDefinitionViewSet)
router.register(r'results', views.RuleDetectionResultViewSet)
router.register(r'components', views.ComponentDefinitionViewSet)
router.register(r'editor', views.RuleEditorView, basename='rule-editor')
router.register(r'health', views.HealthViewSet, basename='health')

app_name = 'rule_detection'

urlpatterns = [
    path('', include(router.urls)),
]
