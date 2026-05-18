from django.contrib import admin
from .models import Category, Event, Entry, Group, GroupMembership, GroupStanding


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "mode")
    list_filter = ("mode",)
    search_fields = ("name",)


class EntryInline(admin.TabularInline):
    model = Entry
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("edition", "category", "group_size_default", "qualified_per_group")
    list_filter = ("edition", "category")
    inlines = [EntryInline]


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("event", "player", "team", "seed_hint", "created_at")
    list_filter = ("event",)
    search_fields = ("player__last_name", "team__name")


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("event", "name")
    list_filter = ("event",)
    inlines = [GroupMembershipInline]


@admin.register(GroupStanding)
class GroupStandingAdmin(admin.ModelAdmin):
    list_display = ("group", "entry", "rank", "points", "wins", "losses", "games_won", "games_lost")
    list_filter = ("group",)
