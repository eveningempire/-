from django.urls import path

from . import views

urlpatterns = [
    path("status/", views.status, name="platform-health-status"),
    path("evaluate/", views.evaluate, name="platform-health-evaluate"),
    path("batch/", views.batch, name="platform-health-batch"),
    path("summary/", views.summary, name="platform-health-summary"),
    path("reset/", views.reset, name="platform-health-reset"),
]
