#子路由
from django.urls import path
from algorithm.views import *
from . import views

urlpatterns = [
    #urls的写法
    path('configuration/', algorithm_configuration, name='configuration'),
    path('para_csv/', load_paracsv, name='para_csv'),
    path('anomaly/', anomaly_detection, name='anomaly'),
    path('diagnosis/', fault_diagnosis, name='diagnosis'),
    path('gradientboost/', gradient_boost, name='gradientboost'),
    path('hier14/', hier14_diagnosis, name='hier14'),
    path('component_eval/', component_eval, name='component_eval'),
    path('subsystem_eval/', subsystem_eval, name='subsystem_eval'),
    path('system_eval/', system_eval, name='system_eval'),
    path('troubleshoot/', troubleshoot, name='troubleshoot'),
    path('fmeca/', fmeca, name='fmeca'),
    path('editfmeca/', editfmeca, name='editfmeca'),
    path('inituser/', inituser, name='inituser'),
    path('edituser/', edituser, name='edituser'),
    path('adduser/', adduser, name='adduser'),
    path('deleteuser/', deleteuser, name='deleteuser'),
    path('loginuser/', loginuser, name='loginuser'),
    path('currentuser/', currentuser, name='currentuser'),
    path('currentrole/', currentrole, name='currentrole'),
    path('maxuserid/', maxuserid, name='maxuserid'),
    path('searchid/', searchid, name='searchid'),
]
    