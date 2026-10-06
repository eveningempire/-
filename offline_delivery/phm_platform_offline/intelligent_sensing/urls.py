"""
URL configuration for the Intelligent Sensing module.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('prediction-results/', views.get_prediction_results, name='prediction_results'),
    path('coupling-layers/', views.get_coupling_layers, name='coupling_layers'),
    # Undersampling API endpoints
    path('undersampling/random-sampling/', views.get_random_sampling_data, name='random_sampling_data'),
    path('undersampling/reconstruction/', views.get_undersampling_reconstruction_data, name='undersampling_reconstruction_data'),
    path('undersampling/limited-sensing/', views.get_limited_sensing_data, name='limited_sensing_data'),
    path('undersampling/online-learning/', views.get_online_learning_data, name='online_learning_data'),
]
