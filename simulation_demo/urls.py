from django.urls import path
from . import views
urlpatterns = [path('sample/', views.sample),path('run/', views.run),path('tasks/<str:task_id>/', views.task),path('workflows/', views.workflows),path('workflows/<uuid:task_id>/', views.workflow_detail),path('workflows/<uuid:task_id>/generate/', views.workflow_generate),path('workflows/<uuid:task_id>/samples/', views.workflow_sample)]
