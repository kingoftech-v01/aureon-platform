"""Integration admin configuration."""

from django.contrib import admin
from .models import Integration, IntegrationSyncLog


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'status', 'sync_enabled', 'last_sync_at', 'created_at']
    list_filter = ['service_type', 'status', 'sync_enabled']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(IntegrationSyncLog)
class IntegrationSyncLogAdmin(admin.ModelAdmin):
    list_display = ['integration', 'status', 'records_synced', 'duration_ms', 'started_at']
    list_filter = ['status']
    readonly_fields = ['id', 'started_at']
