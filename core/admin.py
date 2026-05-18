from django.contrib import admin
from .models import TournamentEdition, Player, Team


@admin.register(TournamentEdition)
class TournamentEditionAdmin(admin.ModelAdmin):
    list_display = ("year", "name", "is_active", "start_dt", "end_dt")
    list_filter = ("is_active",)
    search_fields = ("name", "year")


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "gender", "birth_year", "license_number")
    search_fields = ("last_name", "first_name", "license_number")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "player1", "player2")
    search_fields = ("name", "player1__last_name", "player2__last_name")
