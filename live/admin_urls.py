from django.urls import path
from . import admin_views


urlpatterns = [
    path("panel/", admin_views.panel_home, name="panel_home"),
    path("panel/select/", admin_views.panel_select, name="panel_select"),
    path("panel/event/<int:event_id>/", admin_views.panel_event, name="panel_event"),

    # actions
    path("panel/event/<int:event_id>/player/create/", admin_views.player_create, name="panel_player_create"),
    path("panel/event/<int:event_id>/team/create/", admin_views.team_create, name="panel_team_create"),

    path("panel/event/<int:event_id>/group/create/", admin_views.group_create, name="panel_group_create"),
    path("panel/event/<int:event_id>/group/fill/", admin_views.group_fill, name="panel_group_fill"),
    path("panel/event/<int:event_id>/matches/generate-groups/", admin_views.generate_group_matches,
         name="panel_generate_group_matches"),

    path("panel/event/<int:event_id>/match/<int:match_id>/edit/", admin_views.match_edit, name="panel_match_edit"),
    path("panel/event/<int:event_id>/match/<int:match_id>/feature/", admin_views.match_feature,
         name="panel_match_feature"),
    path("panel/event/<int:event_id>/entry/add-player/", admin_views.entry_add_player, name="panel_entry_add_player"),
    path("panel/event/<int:event_id>/entry/add-players/", admin_views.entry_add_players,
         name="panel_entry_add_players"),
    path("panel/event/<int:event_id>/entry/<int:entry_id>/remove/",
         admin_views.entry_remove,
         name="panel_entry_remove",),
    path("panel/event/<int:event_id>/players/", admin_views.panel_players, name="panel_players"),
    path("panel/event/<int:event_id>/groups/", admin_views.panel_groups, name="panel_groups"),
    path("panel/event/<int:event_id>/matches/", admin_views.panel_matches, name="panel_matches"),
    path("panel/event/<int:event_id>/final/", admin_views.panel_final, name="panel_final"),
    path("panel/event/<int:event_id>/final/create/", admin_views.panel_final_create, name="panel_final_create"),
    path("panel/event/<int:event_id>/final/assign/", admin_views.panel_final_assign, name="panel_final_assign"),
    path("panel/event/<int:event_id>/final/clear/", admin_views.panel_final_clear, name="panel_final_clear"),
    path(
        "panel/event/<int:event_id>/final/<int:match_id>/labels/",
        admin_views.panel_final_label_update,
        name="panel_final_label_update",
    ),
    path("panel/event/<int:event_id>/player/<int:player_id>/edit/", admin_views.player_edit, name="panel_player_edit"),
    path("panel/event/<int:event_id>/groups/assign/", admin_views.group_assign, name="panel_group_assign"),
    path("panel/event/<int:event_id>/groups/unassign/", admin_views.group_unassign, name="panel_group_unassign"),

]
