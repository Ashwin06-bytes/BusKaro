from django.contrib import admin
from .models import SourceProvider, SearchLog

@admin.register(SourceProvider)
class SourceProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'is_active', 'is_dummy', 'last_synced_at')
    list_filter = ('is_active', 'is_dummy')
    search_fields = ('name', 'display_name')

@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination', 'travel_date', 'results_count', 'created_at')
    list_filter = ('travel_date', 'created_at')
    search_fields = ('origin', 'destination')
