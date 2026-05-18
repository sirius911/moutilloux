from django.urls import path
from .views import results
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("results/live/", views.results_live_menu, name="results_live_menu"),
    path("results/", results, name="results"),
    path("api/score_state/", views.score_state, name="score_state"),
    path("results/poules/", views.results_poules, name="results_poules"),
    path("results/poules/start/", views.results_poules_start, name="results_poules_start"),
    path("results/poules/<int:event_id>/", views.results_poules_event, name="results_poules_event"),
    path("results/final/start/", views.results_final_start, name="results_final_start"),
    path("results/final/<int:event_id>/", views.results_final_event, name="results_final_event"),
    path("results/mix/start/", views.results_mix_start, name="results_mix_start"),
    path("results/mix/<int:event_id>/", views.results_mix_event, name="results_mix_event"),
]
