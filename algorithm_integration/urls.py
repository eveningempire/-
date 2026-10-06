from django.urls import path
from . import views
from . import plugin_views

urlpatterns = [
    path("summary/", views.summary),
    path("fmeca/", views.fmeca),
    path("components/", views.components),
    path("components/<str:code>/", views.component_detail),
    path("assets/", views.assets),
    path("parameters/batch/", views.parameter_batch),
    path("algorithms/", plugin_views.algorithms),
    path("algorithms/import/", plugin_views.import_algorithm),
    path("algorithms/<str:key>/", plugin_views.algorithm_detail),
    path("algorithms/<str:key>/run/", plugin_views.algorithm_run),
    path("algorithms/<str:key>/batch-run/", plugin_views.algorithm_batch_run),
]
