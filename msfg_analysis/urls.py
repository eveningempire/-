"""
MSFG分析URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'msfg-definitions', views.MSFGDefinitionViewSet)
router.register(r'nodes', views.MSFGNodeViewSet)
router.register(r'edges', views.MSFGEdgeViewSet)
router.register(r'results', views.MSFGAnalysisResultViewSet)
router.register(r'editor', views.MSFGEditorView, basename='msfg-editor')
router.register(r'testpoint-mappings', views.TestPointRuleMappingViewSet)
router.register(r'testpoint-rules', views.TestPointRuleViewSet)
router.register(r'component-mappings', views.TestPointComponentMappingViewSet)
router.register(r'fault-component-mappings', views.FaultComponentMappingViewSet)
router.register(r'testpoint-fault-mappings', views.TestPointFaultMappingViewSet, basename='testpoint-fault-mappings')

app_name = 'msfg_analysis'

urlpatterns = [
    path('', include(router.urls)),
    path('component-mappings-ui/', views.component_mappings_view, name='component_mappings_ui'),
    path('inspect/', views.msfg_inspect_view, name='msfg_inspect_ui'),
    # 简洁别名：用于结构检查与预览（可选直达）
    path('definitions/<int:pk>/graph-inspect/', views.MSFGDefinitionViewSet.as_view({'get': 'graph_inspect'}), name='msfg_graph_inspect'),
    path('definitions/<int:pk>/analysis/preview/', views.MSFGDefinitionViewSet.as_view({'post': 'analysis_preview'}), name='msfg_analysis_preview'),
]
