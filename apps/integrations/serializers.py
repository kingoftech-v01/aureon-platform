"""Integration serializers."""

from rest_framework import serializers
from .models import Integration, IntegrationSyncLog


class IntegrationSerializer(serializers.ModelSerializer):
    is_connected = serializers.ReadOnlyField()
    needs_reauth = serializers.ReadOnlyField()

    class Meta:
        model = Integration
        fields = [
            'id', 'name', 'service_type', 'status', 'config',
            'sync_enabled', 'sync_interval_minutes', 'last_sync_at',
            'last_sync_status', 'is_connected', 'needs_reauth',
            'webhook_url', 'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'last_sync_at', 'last_sync_status', 'created_at', 'updated_at']
        extra_kwargs = {
            'config': {'write_only': False},
        }


class IntegrationSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationSyncLog
        fields = ['id', 'integration', 'status', 'records_synced', 'errors', 'duration_ms', 'started_at', 'completed_at']
        read_only_fields = ['id', 'started_at']
