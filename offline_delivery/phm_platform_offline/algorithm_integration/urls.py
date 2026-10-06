from django.urls import path
from . import views

urlpatterns = [
    path("summary/", views.summary),
    path("fmeca/", views.fmeca),
    path("components/", views.components),
    path("components/<str:code>/", views.component_detail),
    path("assets/", views.assets),
]
