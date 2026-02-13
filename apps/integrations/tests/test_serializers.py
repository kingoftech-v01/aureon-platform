"""
Tests for integrations serializers.

Covers:
- IntegrationSerializer: all fields, read-only fields, computed properties
- IntegrationDetailSerializer: recent_sync_logs, total_syncs, successful_syncs
- IntegrationCreateUpdateSerializer: validation, required config fields
- IntegrationSyncLogSerializer: all fields, read-only fields
- IntegrationStatsSerializer: aggregated metrics
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from apps.integrations.models import Integration, IntegrationSyncLog
from apps.integrations.serializers import (
    IntegrationSerializer,
    IntegrationDetailSerializer,
    IntegrationCreateUpdateSerializer,
    IntegrationSyncLogSerializer,
    IntegrationStatsSerializer,
)


@pytest.fixture
def active_integration(db):
    return Integration.objects.create(
        name='QuickBooks Test',
        service_type=Integration.QUICKBOOKS,
        status=Integration.ACTIVE,
        config={'company_id': 'qb_123'},
        access_token='token_abc',
        refresh_token='refresh_xyz',
        token_expires_at=timezone.now() + timedelta(hours=1),
        sync_enabled=True,
        sync_interval_minutes=30,
        webhook_url='https://hooks.example.com/qb',
        metadata={'version': '3.0'},
    )


@pytest.fixture
def inactive_integration(db):
    return Integration.objects.create(
        name='Xero Disconnected',
        service_type=Integration.XERO,
        status=Integration.INACTIVE,
        config={},
        access_token='',
        sync_enabled=False,
    )


@pytest.fixture
def expired_integration(db):
    return Integration.objects.create(
        name='Expired Token',
        service_type=Integration.QUICKBOOKS,
        status=Integration.ACTIVE,
        access_token='expired_token',
        token_expires_at=timezone.now() - timedelta(hours=1),
    )


@pytest.fixture
def sync_log(db, active_integration):
    return IntegrationSyncLog.objects.create(
        integration=active_integration,
        status='success',
        records_synced=42,
        errors=[],
        duration_ms=1234,
        completed_at=timezone.now(),
    )


# ---------------------------------------------------------------------------
# IntegrationSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestIntegrationSerializer:

    def test_serializes_all_expected_fields(self, active_integration):
        serializer = IntegrationSerializer(active_integration)
        data = serializer.data
        expected_fields = [
            'id', 'name', 'service_type', 'status', 'config',
            'sync_enabled', 'sync_interval_minutes', 'last_sync_at',
            'last_sync_status', 'is_connected', 'needs_reauth',
            'webhook_url', 'metadata', 'created_at', 'updated_at',
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_read_only_fields(self):
        meta = IntegrationSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'status' in meta.read_only_fields
        assert 'last_sync_at' in meta.read_only_fields
        assert 'last_sync_status' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields
        assert 'updated_at' in meta.read_only_fields

    def test_is_connected_active_with_token(self, active_integration):
        serializer = IntegrationSerializer(active_integration)
        assert serializer.data['is_connected'] is True

    def test_is_connected_inactive(self, inactive_integration):
        serializer = IntegrationSerializer(inactive_integration)
        assert serializer.data['is_connected'] is False

    def test_needs_reauth_false_when_not_expired(self, active_integration):
        serializer = IntegrationSerializer(active_integration)
        assert serializer.data['needs_reauth'] is False

    def test_needs_reauth_true_when_expired(self, expired_integration):
        serializer = IntegrationSerializer(expired_integration)
        assert serializer.data['needs_reauth'] is True

    def test_needs_reauth_false_when_no_expiry(self, inactive_integration):
        serializer = IntegrationSerializer(inactive_integration)
        assert serializer.data['needs_reauth'] is False

    def test_config_is_serialized(self, active_integration):
        serializer = IntegrationSerializer(active_integration)
        assert serializer.data['config'] == {'company_id': 'qb_123'}

    def test_metadata_serialized(self, active_integration):
        serializer = IntegrationSerializer(active_integration)
        assert serializer.data['metadata'] == {'version': '3.0'}

    def test_name_serialized(self, active_integration):
        serializer = IntegrationSerializer(active_integration)
        assert serializer.data['name'] == 'QuickBooks Test'

    def test_service_type_serialized(self, active_integration):
        serializer = IntegrationSerializer(active_integration)
        assert serializer.data['service_type'] == 'quickbooks'

    def test_model_is_integration(self):
        assert IntegrationSerializer.Meta.model is Integration


# ---------------------------------------------------------------------------
# IntegrationSyncLogSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestIntegrationSyncLogSerializer:

    def test_serializes_all_expected_fields(self, sync_log):
        serializer = IntegrationSyncLogSerializer(sync_log)
        data = serializer.data
        expected = ['id', 'integration', 'status', 'records_synced', 'errors', 'duration_ms', 'started_at', 'completed_at']
        for field in expected:
            assert field in data, f"Missing field: {field}"

    def test_read_only_fields(self):
        meta = IntegrationSyncLogSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'started_at' in meta.read_only_fields

    def test_records_synced(self, sync_log):
        serializer = IntegrationSyncLogSerializer(sync_log)
        assert serializer.data['records_synced'] == 42

    def test_duration_ms(self, sync_log):
        serializer = IntegrationSyncLogSerializer(sync_log)
        assert serializer.data['duration_ms'] == 1234

    def test_status_serialized(self, sync_log):
        serializer = IntegrationSyncLogSerializer(sync_log)
        assert serializer.data['status'] == 'success'

    def test_model_is_sync_log(self):
        assert IntegrationSyncLogSerializer.Meta.model is IntegrationSyncLog


# ---------------------------------------------------------------------------
# IntegrationDetailSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestIntegrationDetailSerializer:

    def test_includes_recent_sync_logs(self, active_integration, sync_log):
        data = IntegrationDetailSerializer(active_integration).data
        assert 'recent_sync_logs' in data
        assert len(data['recent_sync_logs']) == 1

    def test_total_syncs(self, active_integration, sync_log):
        data = IntegrationDetailSerializer(active_integration).data
        assert data['total_syncs'] == 1

    def test_successful_syncs(self, active_integration, sync_log):
        data = IntegrationDetailSerializer(active_integration).data
        assert data['successful_syncs'] == 1

    def test_empty_sync_logs(self, active_integration):
        IntegrationSyncLog.objects.filter(integration=active_integration).delete()
        data = IntegrationDetailSerializer(active_integration).data
        assert data['recent_sync_logs'] == []
        assert data['total_syncs'] == 0
        assert data['successful_syncs'] == 0

    def test_inherits_base_fields(self, active_integration):
        data = IntegrationDetailSerializer(active_integration).data
        assert 'name' in data
        assert 'service_type' in data
        assert 'is_connected' in data

    def test_recent_sync_logs_limit(self, active_integration):
        for i in range(15):
            IntegrationSyncLog.objects.create(
                integration=active_integration,
                status='success' if i % 2 == 0 else 'error',
                records_synced=i,
            )
        data = IntegrationDetailSerializer(active_integration).data
        assert len(data['recent_sync_logs']) <= 10

    def test_service_type_display(self, active_integration):
        data = IntegrationDetailSerializer(active_integration).data
        assert 'service_type_display' in data

    def test_status_display(self, active_integration):
        data = IntegrationDetailSerializer(active_integration).data
        assert 'status_display' in data


# ---------------------------------------------------------------------------
# IntegrationCreateUpdateSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestIntegrationCreateUpdateSerializer:

    def test_valid_quickbooks(self):
        data = {
            'name': 'QB Test',
            'service_type': 'quickbooks',
            'config': {'company_id': 'qb_1'},
            'sync_interval_minutes': 60,
        }
        serializer = IntegrationCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_missing_required_config(self):
        data = {
            'name': 'QB Missing',
            'service_type': 'quickbooks',
            'config': {},
            'sync_interval_minutes': 60,
        }
        serializer = IntegrationCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'config' in serializer.errors

    def test_xero_requires_tenant_id(self):
        data = {
            'name': 'Xero Missing',
            'service_type': 'xero',
            'config': {},
            'sync_interval_minutes': 30,
        }
        serializer = IntegrationCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'config' in serializer.errors

    def test_slack_requires_channel(self):
        data = {
            'name': 'Slack Missing',
            'service_type': 'slack',
            'config': {},
            'sync_interval_minutes': 15,
        }
        serializer = IntegrationCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'config' in serializer.errors

    def test_google_calendar_no_required_config(self):
        data = {
            'name': 'GCal',
            'service_type': 'google_calendar',
            'config': {},
            'sync_interval_minutes': 60,
        }
        serializer = IntegrationCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_outlook_no_required_config(self):
        data = {
            'name': 'Outlook',
            'service_type': 'outlook',
            'config': {},
            'sync_interval_minutes': 60,
        }
        serializer = IntegrationCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_sync_interval_minimum(self):
        data = {
            'name': 'Too Fast',
            'service_type': 'google_calendar',
            'config': {},
            'sync_interval_minutes': 2,
        }
        serializer = IntegrationCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'sync_interval_minutes' in serializer.errors

    def test_sync_interval_boundary(self):
        data = {
            'name': 'Just Right',
            'service_type': 'google_calendar',
            'config': {},
            'sync_interval_minutes': 5,
        }
        serializer = IntegrationCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_update_existing_uses_instance_service_type(self, active_integration):
        data = {
            'name': 'Updated Name',
            'config': {'company_id': 'updated'},
            'sync_interval_minutes': 90,
        }
        serializer = IntegrationCreateUpdateSerializer(
            active_integration, data=data, partial=True,
        )
        assert serializer.is_valid(), serializer.errors


# ---------------------------------------------------------------------------
# IntegrationStatsSerializer
# ---------------------------------------------------------------------------

class TestIntegrationStatsSerializer:

    def test_serializes_all_fields(self):
        data = {
            'total_integrations': 10,
            'active_integrations': 7,
            'inactive_integrations': 2,
            'error_integrations': 1,
            'integrations_by_service': {'quickbooks': 3, 'xero': 4, 'slack': 3},
            'syncs_last_24h': 50,
            'successful_syncs_last_24h': 45,
            'failed_syncs_last_24h': 5,
            'records_synced_last_24h': 1200,
            'avg_sync_duration_ms': 350,
        }
        serializer = IntegrationStatsSerializer(data)
        for key in data:
            assert key in serializer.data

    def test_zero_stats(self):
        data = {
            'total_integrations': 0,
            'active_integrations': 0,
            'inactive_integrations': 0,
            'error_integrations': 0,
            'integrations_by_service': {},
            'syncs_last_24h': 0,
            'successful_syncs_last_24h': 0,
            'failed_syncs_last_24h': 0,
            'records_synced_last_24h': 0,
            'avg_sync_duration_ms': 0,
        }
        serializer = IntegrationStatsSerializer(data)
        assert serializer.data['total_integrations'] == 0
