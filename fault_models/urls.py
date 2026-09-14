from rest_framework.routers import DefaultRouter
from .views import Tree,Fmeca
r=DefaultRouter(); r.register('fault-trees',Tree); r.register('fmeca',Fmeca); urlpatterns=r.urls
