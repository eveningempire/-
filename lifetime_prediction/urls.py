"""
寿命预测模块的URL配置

定义寿命预测功能的API路由。
"""

from django.urls import path
from . import views

app_name = 'lifetime_prediction'

urlpatterns = [
    # 获取可用的算法列表
    path('algorithms/', views.get_available_algorithms, name='available_algorithms'),
    
    # 获取可用的CMG列表
    path('cmgs/', views.get_available_cmgs, name='available_cmgs'),
    
    # 获取预测摘要信息
    path('summary/<int:cmg_id>/', views.get_prediction_summary, name='prediction_summary'),
    
    # 执行寿命预测
    path('predict/', views.predict_lifetime, name='predict_lifetime'),
    
    # 模型微调（增量学习）
    path('finetune/', views.finetune_model, name='finetune_model'),
    
    # 获取遥测数据（调试用）
    path('telemetry/<int:cmg_id>/', views.get_telemetry_data, name='telemetry_data'),
    
    # 健康检查
    path('health/', views.health_check, name='health_check'),
]
