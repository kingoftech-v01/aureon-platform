"""
Tests for integration models.

Tests cover:
- Integration creation and defaults
- String representation
- is_connected property
- needs_reauth property
- IntegrationSyncLog creation
"""

import uuid
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.integrations.models import Integration, IntegrationSyncLog


@pytest.mark.django_db
class TestIntegration:
    """Tests for the Integration model."""

    def _create_integration(self, **overrides):
        """Helper to create an Integration with sensible defaults."""
        defaults = {
            'name': 'Test QuickBooks',
            'service_type': Integration.QUICKBOOKS,
            'status': Integration.INACTIVE,
            'config': {'api_url': 'https://api.quickbooks.com'},
        }
        defaults.update(overrides)
        return Integration.objects.create(**defaults)

    def test_create_integration(self):
        """Integration should be created with correct defaults."""
        integration = self._create_integration()

        assert integration.pk is not None
        assert isinstance(integration.id, uuid.UUID)
        assert integration.name == 'Test QuickBooks'
        assert integration.service_type == Integration.QUICKBOOKS
        assert integration.status == Integration.INACTIVE
        assert integration.config == {'api_url': 'https://api.quickbooks.com'}
        assert integration.access_token == ''
        assert integration.refresh_token == ''
        assert integration.token_expires_at is None
        assert integration.sync_enabled is True
        assert integration.sync_interval_minutes == 60
        assert integration.last_sync_at is None
        assert integration.last_sync_status == ''
        assert integration.last_sync_error == ''
        assert integration.webhook_url == ''
        assert integration.webhook_secret == ''
        assert integration.metadata == {}
        assert integration.created_at is not None
        assert integration.updated_at is not None

    def test_integration_str(self):
        """String representation should include name and service type display."""
        integration = self._create_integration(
            name='My Xero',
            service_type=Integration.XERO,
        )
        result = str(integration)

        assert 'My Xero' in result
        assert 'Xero' in result

    def test_integration_str_custom(self):
        """Custom integration type should show correct display name."""
        integration = self._create_integration(
            name='Custom API',
            service_type=Integration.CUSTOM,
        )
        result = str(integration)

        assert 'Custom API' in result
        assert 'Custom Integration' in result

    def test_is_connected_true(self):
        """is_connected should be True when status is ACTIVE and access_token is set."""
        integration = self._create_integration(
            status=Integration.ACTIVE,
            access_token='some-token-value',
        )

        assert integration.is_connected is True

    def test_is_connected_false_inactive(self):
        """is_connected should be False when status is INACTIVE."""
        integration = self._create_integration(
            status=Integration.INACTIVE,
            access_token='some-token-value',
        )

        assert integration.is_connected is False

    def test_is_connected_false_no_token(self):
        """is_connected should be False when access_token is empty."""
        integration = self._create_integration(
            status=Integration.ACTIVE,
            access_token='',
        )

        assert integration.is_connected is False

    def test_is_connected_false_error_status(self):
        """is_connected should be False when status is ERROR."""
        integration = self._create_integration(
            status=Integration.ERROR,
            access_token='token',
        )

        assert integration.is_connected is False

    def test_needs_reauth_true(self):
        """needs_reauth should be True when token has expired."""
        integration = self._create_integration(
            access_token='expired-token',
            token_expires_at=timezone.now() - timedelta(hours=1),
        )

        assert integration.needs_reauth is True

    def test_needs_reauth_false_not_expired(self):
        """needs_reauth should be False when token has not expired."""
        integration = self._create_integration(
            access_token='valid-token',
            token_expires_at=timezone.now() + timedelta(hours=1),
        )

        assert integration.needs_reauth is False

    def test_needs_reauth_false_no_expiry(self):
        """needs_reauth should be False when token_expires_at is None."""
        integration = self._create_integration(
            access_token='permanent-token',
            token_expires_at=None,
        )

        assert integration.needs_reauth is False

    def test_needs_reauth_at_exact_expiry(self):
        """needs_reauth should be True when token expires exactly now."""
        now = timezone.now()
        integration = self._create_integration(
            access_token='token',
            token_expires_at=now,
        )

        # timezone.now() >= token_expires_at should be True
        assert integration.needs_reauth is True

    def test_all_service_types(self):
        """All service type choices should be valid."""
        for value, _ in Integration.SERVICE_CHOICES:
            integration = self._create_integration(
                name=f'Test {value}',
                service_type=value,
            )
            assert integration.service_type == value

    def test_all_status_choices(self):
        """All status choices should be valid."""
        for value, _ in Integration.STATUS_CHOICES:
            integration = self._create_integration(
                name=f'Status {value}',
                status=value,
            )
            assert integration.status == value

    def test_integration_ordering(self):
        """Integrations should be ordered by -created_at."""
        int1 = self._create_integration(name='First')
        int2 = self._create_integration(name='Second')

        integrations = list(Integration.objects.all())
        assert integrations[0].name == 'Second'
        assert integrations[1].name == 'First'

    def test_integration_with_oauth_tokens(self):
        """Integration should store OAuth tokens."""
        integration = self._create_integration(
            access_token='access_xyz',
            refresh_token='refresh_xyz',
            token_expires_at=timezone.now() + timedelta(hours=2),
        )

        assert integration.access_token == 'access_xyz'
        assert integration.refresh_token == 'refresh_xyz'
        assert integration.token_expires_at is not None

    def test_integration_with_webhook_config(self):
        """Integration should store webhook configuration."""
        integration = self._create_integration(
            webhook_url='https://example.com/webhook',
            webhook_secret='whsec_test123',
        )

        assert integration.webhook_url == 'https://example.com/webhook'
        assert integration.webhook_secret == 'whsec_test123'

    def test_integration_metadata(self):
        """Integration should store JSON metadata."""
        meta = {'region': 'us-east', 'tier': 'premium'}
        integration = self._create_integration(metadata=meta)
        integration.refresh_from_db()

        assert integration.metadata == meta


@pytest.mark.django_db
class TestIntegrationSyncLog:
    """Tests for the IntegrationSyncLog model."""

    @pytest.fixture
    def integration(self, db):
        """Create an integration for sync log tests."""
        return Integration.objects.create(
            name='Sync Test Integration',
            service_type=Integration.XERO,
            status=Integration.ACTIVE,
            access_token='token',
        )

    def test_sync_log_creation(self, integration):
        """Sync log should be created with correct values."""
        log = IntegrationSyncLog.objects.create(
            integration=integration,
            status='completed',
            records_synced=42,
            duration_ms=1500,
        )

        assert log.pk is not None
        assert isinstance(log.id, uuid.UUID)
        assert log.integration == integration
        assert log.status == 'completed'
        assert log.records_synced == 42
        assert log.duration_ms == 1500
        assert log.errors == []
        assert log.metadata == {}
        assert log.started_at is not None
        assert log.completed_at is None

    def test_sync_log_str(self, integration):
        """String representation should include integration name and timestamp."""
        log = IntegrationSyncLog.objects.create(
            integration=integration,
            status='running',
        )
        result = str(log)

        assert 'Sync Test Integration' in result
        assert 'sync at' in result

    def test_sync_log_with_errors(self, integration):
        """Sync log should store error details."""
        errors = [
            {'field': 'amount', 'message': 'Invalid format'},
            {'field': 'date', 'message': 'Out of range'},
        ]
        log = IntegrationSyncLog.objects.create(
            integration=integration,
            status='failed',
            records_synced=10,
            errors=errors,
        )
        log.refresh_from_db()

        assert log.errors == errors
        assert len(log.errors) == 2

    def test_sync_log_with_metadata(self, integration):
        """Sync log should store arbitrary metadata."""
        meta = {'batch_id': 'b123', 'page': 3}
        log = IntegrationSyncLog.objects.create(
            integration=integration,
            status='completed',
            metadata=meta,
        )
        log.refresh_from_db()

        assert log.metadata == meta

    def test_sync_log_with_completed_at(self, integration):
        """Sync log completed_at should be settable."""
        now = timezone.now()
        log = IntegrationSyncLog.objects.create(
            integration=integration,
            status='completed',
            completed_at=now,
            duration_ms=500,
        )

        assert log.completed_at == now

    def test_sync_log_ordering(self, integration):
        """Sync logs should be ordered by -started_at (newest first)."""
        log1 = IntegrationSyncLog.objects.create(
            integration=integration,
            status='completed',
            records_synced=10,
        )
        log2 = IntegrationSyncLog.objects.create(
            integration=integration,
            status='completed',
            records_synced=20,
        )

        logs = list(IntegrationSyncLog.objects.all())
        assert logs[0].records_synced == 20
        assert logs[1].records_synced == 10

    def test_sync_log_cascade_delete(self, integration):
        """Deleting integration should cascade-delete its sync logs."""
        IntegrationSyncLog.objects.create(
            integration=integration,
            status='completed',
        )
        IntegrationSyncLog.objects.create(
            integration=integration,
            status='failed',
        )

        assert IntegrationSyncLog.objects.count() == 2

        integration.delete()

        assert IntegrationSyncLog.objects.count() == 0

    def test_sync_log_related_name(self, integration):
        """Integration should have sync_logs reverse relation."""
        IntegrationSyncLog.objects.create(
            integration=integration,
            status='completed',
            records_synced=5,
        )

        assert integration.sync_logs.count() == 1
        assert integration.sync_logs.first().records_synced == 5
