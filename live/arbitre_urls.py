from django.urls import path
from . import referee_views

urlpatterns = [
    path("", referee_views.referee_home, name="referee_home"),
    path("match/<int:match_id>/", referee_views.referee_match, name="referee_match"),
    path("match/<int:match_id>/action/", referee_views.referee_action, name="referee_action"),
]
