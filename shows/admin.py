# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.contrib import admin
from django.db.models import Count

from .models import Genre, Show, ShowRequest, WatchEntry

admin.site.site_header = 'TV Show Tracker Admin'
admin.site.site_title = 'TV Show Tracker Admin'
admin.site.index_title = 'Manage the catalog and watchlists'


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'show_total']
    search_fields = ['name']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(show_total=Count('shows'))

    @admin.display(description='Shows', ordering='show_total')
    def show_total(self, obj):
        return obj.show_total


class WatchEntryInline(admin.TabularInline):
    """Lists who is tracking a show. New entries are added from the Watch entries page."""

    model = WatchEntry
    extra = 0
    fields = ['user', 'status', 'episodes_watched', 'rating']
    autocomplete_fields = ['user']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ['title', 'genre', 'network', 'premiere_year', 'season_count', 'episode_count']
    list_filter = ['genre', 'network']
    list_select_related = ['genre']
    search_fields = ['title', 'network']
    readonly_fields = ['created_at']
    inlines = [WatchEntryInline]
    fieldsets = [
        (None, {'fields': ['title', 'genre', 'network', 'description']}),
        ('Run', {'fields': ['premiere_year', 'season_count', 'episode_count']}),
        ('Record info', {'classes': ['collapse'], 'fields': ['created_at']}),
    ]


@admin.register(WatchEntry)
class WatchEntryAdmin(admin.ModelAdmin):
    list_display = ['show', 'user', 'status', 'episodes_watched', 'rating', 'updated_at']
    list_filter = ['status', 'show__genre']
    list_select_related = ['show', 'user']
    search_fields = ['show__title', 'user__username']
    autocomplete_fields = ['user', 'show']
    readonly_fields = ['updated_at']
    fieldsets = [
        (None, {'fields': ['user', 'show']}),
        ('Progress', {'fields': ['status', 'episodes_watched', 'rating']}),
        ('Notes', {'fields': ['notes', 'updated_at']}),
    ]


@admin.register(ShowRequest)
class ShowRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'network', 'requested_by', 'status', 'created_at']
    list_editable = ['status']
    list_filter = ['status']
    list_select_related = ['requested_by']
    search_fields = ['title', 'network', 'requested_by__username']
    autocomplete_fields = ['requested_by']
    readonly_fields = ['created_at']
    fieldsets = [
        (None, {'fields': ['title', 'network', 'note']}),
        ('Review', {'fields': ['requested_by', 'status', 'created_at']}),
    ]
