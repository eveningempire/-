from django.urls import path
from . import views

urlpatterns = [
    path("status/", views.status, name="fault-diagnosis-status"),
    path("predict/", views.predict, name="fault-diagnosis-predict"),
    path("simulate-inject/", views.simulate_inject, name="matlab-simulate-inject"),
]
