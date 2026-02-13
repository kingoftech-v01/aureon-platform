"""Integration serializers for Aureon SaaS Platform."""

from rest_framework import serializers
from .models import Integration, IntegrationSyncLog


class IntegrationSerializer(serializers.ModelSerializer):
    """Standard integration serializer for list views."""

    is_connected = serializers.ReadOnlyField()
    needs_reauth = serializers.ReadOnlyField()
    service_type_display = serializers.CharField(
        source='get_service_type_display', read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )

    class Meta:
        model = Integration
        fields = [
            'id', 'name', 'service_type', 'service_type_display',
            'status', 'status_display', 'config',
            'sync_enabled', 'sync_interval_minutes',
            'last_sync_at', 'last_sync_status', 'last_sync_error',
            'is_connected', 'needs_reauth',
            'webhook_url', 'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'last_sync_at', 'last_sync_status',
            'last_sync_error', 'created_at', 'updated_at',
        ]


class IntegrationDetailSerializer(IntegrationSerializer):
    """Detailed integration serializer with recent sync logs."""

    recent_sync_logs = serializers.SerializerMethodField()
    total_syncs = serializers.SerializerMethodField()
    successful_syncs = serializers.SerializerMethodField()

    class Meta(IntegrationSerializer.Meta):
        fields = IntegrationSerializer.Meta.fields + [
            'recent_sync_logs', 'total_syncs', 'successful_syncs',
        ]

    def get_recent_sync_logs(self, obj):
        logs = obj.sync_logs.order_by('-started_at')[:10]
        return IntegrationSyncLogSerializer(logs, many=True).data

    def get_total_syncs(self, obj):
        return obj.sync_logs.count()

    def get_successful_syncs(self, obj):
        return obj.sync_logs.filter(status='success').count()


class IntegrationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating integrations with validation."""

    class Meta:
        model = Integration
        fields = [
            'id', 'name', 'service_type', 'config', 'sync_enabled',
            'sync_interval_minutes', 'webhook_url', 'metadata',
        ]
        read_only_fields = ['id']

    REQUIRED_CONFIG_FIELDS = {
        'quickbooks': ['company_id'],
        'xero': ['tenant_id'],
        'google_calendar': [],
        'outlook': [],
        'slack': ['channel'],
    }

    def validate(self, data):
        service_type = data.get(
            'service_type',
            getattr(self.instance, 'service_type', None),
        )
        config = data.get(
            'config',
            getattr(self.instance, 'config', {}),
        )

        required = self.REQUIRED_CONFIG_FIELDS.get(service_type, [])
        missing = [f for f in required if not config.get(f)]
        if missing:
            raise serializers.ValidationError({
                'config': f"Missing required config fields for {service_type}: {', '.join(missing)}",
            })

        interval = data.get('sync_interval_minutes', 60)
        if interval < 5:
            raise serializers.ValidationError({
                'sync_interval_minutes': 'Sync interval must be at least 5 minutes.',
            })

        return data


class IntegrationSyncLogSerializer(serializers.ModelSerializer):
    """Sync log serializer."""

    class Meta:
        model = IntegrationSyncLog
        fields = [
            'id', 'integration', 'status', 'records_synced',
            'errors', 'duration_ms', 'metadata',
            'started_at', 'completed_at',
        ]
        read_only_fields = ['id', 'started_at']


class IntegrationStatsSerializer(serializers.Serializer):
    """Aggregated integration statistics."""

    total_integrations = serializers.IntegerField()
    active_integrations = serializers.IntegerField()
    inactive_integrations = serializers.IntegerField()
    error_integrations = serializers.IntegerField()
    integrations_by_service = serializers.DictField(child=serializers.IntegerField())
    syncs_last_24h = serializers.IntegerField()
    successful_syncs_last_24h = serializers.IntegerField()
    failed_syncs_last_24h = serializers.IntegerField()
    records_synced_last_24h = serializers.IntegerField()
    avg_sync_duration_ms = serializers.IntegerField()
