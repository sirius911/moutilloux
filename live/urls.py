from django.urls import path
from .views import results
from . import views
from . import api_views


urlpatterns = [
    path("", views.home, name="home"),
    path("results/live/", views.results_live_menu, name="results_live_menu"),
    path("results/", results, name="results"),

    # ── API JSON (SPA Vue.js) ──────────────────────────────────────────
    path("api/score_state/", views.score_state, name="score_state"),
    path("api/csrf/", api_views.api_csrf, name="api_csrf"),
    path("api/auth/login/", api_views.api_login, name="api_login"),
    path("api/auth/logout/", api_views.api_logout, name="api_logout"),
    path("api/editions/", api_views.api_editions, name="api_editions"),
    path("api/events/<int:event_id>/players/", api_views.api_event_players, name="api_event_players"),
    path("api/events/<int:event_id>/groups/", api_views.api_event_groups, name="api_event_groups"),
    path("api/events/<int:event_id>/matches/", api_views.api_event_matches, name="api_event_matches"),
    path("api/events/<int:event_id>/bracket/", api_views.api_event_bracket, name="api_event_bracket"),
    path("api/players/", api_views.api_players, name="api_players"),
    path("api/players/create/", api_views.api_player_create, name="api_player_create"),
    path("api/arbitre/matches/", api_views.api_arbitre_matches, name="api_arbitre_matches"),
    path("api/me/", api_views.api_me, name="api_me"),

    # ── API JSON — Phase 2 (inscriptions, mutations) ───────────────────
    path("api/players/<int:player_id>/edit/", api_views.api_player_edit, name="api_player_edit"),
    path("api/events/<int:event_id>/teams/create/", api_views.api_team_create, name="api_team_create"),
    path("api/events/<int:event_id>/registrations/add/", api_views.api_registration_add, name="api_registration_add"),
    path("api/events/<int:event_id>/registrations/add-bulk/", api_views.api_registration_add_bulk, name="api_registration_add_bulk"),
    path("api/events/<int:event_id>/registrations/<int:entry_id>/remove/", api_views.api_registration_remove, name="api_registration_remove"),

    # ── API JSON — Phase 3 (poules, mutations) ─────────────────────────
    path("api/events/<int:event_id>/groups/create/", api_views.api_group_create, name="api_group_create"),
    path("api/events/<int:event_id>/groups/autofill/", api_views.api_groups_autofill, name="api_groups_autofill"),
    path("api/events/<int:event_id>/groups/assign/", api_views.api_group_assign, name="api_group_assign"),
    path("api/events/<int:event_id>/groups/unassign/", api_views.api_group_unassign, name="api_group_unassign"),
    path("api/events/<int:event_id>/matches/generate/", api_views.api_matches_generate, name="api_matches_generate"),

    # ── API JSON — Phase 4 (planning, mutations) ───────────────────────
    path("api/matches/<int:match_id>/edit/", api_views.api_match_edit, name="api_match_edit"),
    path("api/matches/<int:match_id>/feature/", api_views.api_match_feature, name="api_match_feature"),
    path("api/matches/<int:match_id>/start/", api_views.api_match_start, name="api_match_start"),

    # ── API JSON — Phase 5 (live, lecture d'un match) ──────────────────
    path("api/matches/<int:match_id>/", api_views.api_match_detail, name="api_match_detail"),

    # ── API JSON — Phase 7 (bracket, mutations) ────────────────────────
    path("api/events/<int:event_id>/bracket/create/", api_views.api_bracket_create, name="api_bracket_create"),
    path("api/matches/<int:match_id>/bracket-labels/", api_views.api_bracket_labels, name="api_bracket_labels"),
    path("api/events/<int:event_id>/bracket/assign/", api_views.api_bracket_assign, name="api_bracket_assign"),
    path("api/events/<int:event_id>/bracket/clear/", api_views.api_bracket_clear, name="api_bracket_clear"),

    # ── API JSON — Phase 9 (configuration : éditions, catégories, courts, épreuves) ──
    path("api/categories/", api_views.api_categories, name="api_categories"),
    path("api/courts/", api_views.api_courts, name="api_courts"),
    # Éditions
    path("api/editions/create/", api_views.api_edition_create, name="api_edition_create"),
    path("api/editions/<int:edition_id>/edit/", api_views.api_edition_edit, name="api_edition_edit"),
    path("api/editions/<int:edition_id>/activate/", api_views.api_edition_activate, name="api_edition_activate"),
    path("api/editions/<int:edition_id>/delete/", api_views.api_edition_delete, name="api_edition_delete"),
    # Catégories
    path("api/categories/create/", api_views.api_category_create, name="api_category_create"),
    path("api/categories/<int:category_id>/edit/", api_views.api_category_edit, name="api_category_edit"),
    path("api/categories/<int:category_id>/delete/", api_views.api_category_delete, name="api_category_delete"),
    # Courts
    path("api/courts/create/", api_views.api_court_create, name="api_court_create"),
    path("api/courts/<int:court_id>/edit/", api_views.api_court_edit, name="api_court_edit"),
    path("api/courts/<int:court_id>/delete/", api_views.api_court_delete, name="api_court_delete"),
    # Épreuves
    path("api/editions/<int:edition_id>/events/create/", api_views.api_event_create, name="api_event_create"),
    path("api/events/<int:event_id>/edit/", api_views.api_event_edit, name="api_event_edit"),
    path("api/events/<int:event_id>/delete/", api_views.api_event_delete, name="api_event_delete"),
    path("api/events/<int:event_id>/start/", api_views.api_event_start, name="api_event_start"),
    path("api/events/<int:event_id>/close/", api_views.api_event_close, name="api_event_close"),
    path("api/events/<int:event_id>/reopen/", api_views.api_event_reopen, name="api_event_reopen"),

    # ── API JSON — Sprint 12 (ajustements en cours de jeu) ───────────────────
    path("api/entries/<int:entry_id>/withdraw/", api_views.api_entry_withdraw, name="api_entry_withdraw"),
    path("api/events/<int:event_id>/entries/late/", api_views.api_entry_add_late, name="api_entry_add_late"),
    path("api/entries/<int:entry_id>/replace/", api_views.api_entry_replace, name="api_entry_replace"),

    # ── API JSON — Sprint 07 (calendrier : journées et pauses) ────────────────
    # PlayDay
    path("api/editions/<int:edition_id>/play-days/", api_views.api_play_days_list, name="api_play_days_list"),
    path("api/editions/<int:edition_id>/play-days/create/", api_views.api_play_day_create, name="api_play_day_create"),
    path("api/play-days/<int:play_day_id>/edit/", api_views.api_play_day_edit, name="api_play_day_edit"),
    path("api/play-days/<int:play_day_id>/delete/", api_views.api_play_day_delete, name="api_play_day_delete"),
    # Break
    path("api/play-days/<int:play_day_id>/breaks/", api_views.api_breaks_list, name="api_breaks_list"),
    path("api/play-days/<int:play_day_id>/breaks/create/", api_views.api_break_create, name="api_break_create"),
    path("api/breaks/<int:break_id>/edit/", api_views.api_break_edit, name="api_break_edit"),
    path("api/breaks/<int:break_id>/delete/", api_views.api_break_delete, name="api_break_delete"),
    # Packer calendrier + mutations calendrier
    path("api/editions/<int:edition_id>/calendar/", api_views.api_edition_calendar, name="api_edition_calendar"),
    path("api/editions/<int:edition_id>/calendar/reorder/", api_views.api_calendar_reorder, name="api_calendar_reorder"),
    path("api/events/<int:event_id>/matches/auto-arrange/", api_views.api_matches_auto_arrange, name="api_matches_auto_arrange"),
    # TV : prochains matchs (lecture publique)
    path("api/tv/upcoming/", api_views.api_tv_upcoming, name="api_tv_upcoming"),
    # TV : état chaud unifié (sprint 22)
    path("api/tv/state/", api_views.api_tv_state, name="api_tv_state"),
    # TV : contenu froid du carousel (sprint 22)
    path("api/tv/idle/", api_views.api_tv_idle, name="api_tv_idle"),

    path("results/poules/", views.results_poules, name="results_poules"),
    path("results/poules/start/", views.results_poules_start, name="results_poules_start"),
    path("results/poules/<int:event_id>/", views.results_poules_event, name="results_poules_event"),
    path("results/final/start/", views.results_final_start, name="results_final_start"),
    path("results/final/<int:event_id>/", views.results_final_event, name="results_final_event"),
    path("results/mix/start/", views.results_mix_start, name="results_mix_start"),
    path("results/mix/<int:event_id>/", views.results_mix_event, name="results_mix_event"),
]
