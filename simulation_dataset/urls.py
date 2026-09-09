from django.urls import path
from . import views
urlpatterns = [path("catalog/", views.catalog), path("files/<str:category>/", views.files), path("preview/", views.preview)]
