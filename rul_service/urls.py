from django.urls import path
from . import views
urlpatterns=[path('status/',views.status),path('predict/',views.predict),path('demo/',views.demo)]
