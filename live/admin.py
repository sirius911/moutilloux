from django.contrib import admin
from .models import Court, Match, PlayDay, Break


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "event", "stage", "status", "is_featured",
        "scheduled_time", "court", "order_index",
        "side_a", "side_b",
        "sets_a", "sets_b", "games_a", "games_b",
    )
    list_filter = ("event", "stage", "status", "is_featured", "court")
    search_fields = ("side_a__player__last_name",
                     "side_b__player__last_name",
                     "side_a__team__name",
                     "side_b__team__name")
    ordering = ("event", "scheduled_time", "order_index")


@admin.register(PlayDay)
class PlayDayAdmin(admin.ModelAdmin):
    list_display = ("edition", "date", "start_time", "target_end_time")
    list_filter = ("edition",)
    ordering = ("edition", "date")


@admin.register(Break)
class BreakAdmin(admin.ModelAdmin):
    list_display = ("play_day", "order_index", "label", "duration_min")
    list_filter = ("play_day__edition",)
    ordering = ("play_day", "order_index")
