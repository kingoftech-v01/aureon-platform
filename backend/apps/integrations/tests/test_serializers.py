"""
Tests for integrations serializers.

Covers:
- IntegrationSerializer: all fields, read-only fields, computed properties
- IntegrationSyncLogSerializer: all fields, read-only fields
"""

import pytest
from datetime import timedelta
from django.utils import timezone

from apps.integrations.models import Integration, IntegrationSyncLog
from apps.integrations.serializers import IntegrationSerializer, IntegrationSyncLogSerializer


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
