"""
Tests for integrations Celery tasks.

Covers the service-based tasks:
- sync_external_service: look up integration, refresh token if needed, sync
- scheduled_sync_all: queue syncs for active integrations past their interval
- refresh_all_tokens: batch OAuth token refresh
- process_integration_webhook: webhook processing with sync log creation
- _process_quickbooks_webhook / _process_xero_webhook / _process_slack_webhook
"""

import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.utils import timezone

from apps.integrations.models import Integration, IntegrationSyncLog
from apps.integrations.tasks import (
    sync_external_service,
    scheduled_sync_all,
    refresh_all_tokens,
    process_integration_webhook,
    _process_quickbooks_webhook,
    _process_xero_webhook,
    _process_slack_webhook,
)


@pytest.fixture
def active_qb(db):
    return Integration.objects.create(
        name='QB Active',
        service_type=Integration.QUICKBOOKS,
        status=Integration.ACTIVE,
        access_token='tok_qb',
        config={'company_id': 'qb_1'},
        sync_enabled=True,
        sync_interval_minutes=60,
    )


@pytest.fixture
def active_xero(db):
    return Integration.objects.create(
        name='Xero Active',
        service_type=Integration.XERO,
        status=Integration.ACTIVE,
        access_token='tok_xero',
        config={'tenant_id': 'xero_1'},
        sync_enabled=True,
        sync_interval_minutes=30,
        last_sync_at=timezone.now() - timedelta(hours=2),
    )


@pytest.fixture
def inactive_integration(db):
    return Integration.objects.create(
        name='Inactive',
        service_type=Integration.SLACK,
        status=Integration.INACTIVE,
    )


@pytest.fixture
def expiring_token_integration(db):
    return Integration.objects.create(
        name='Expiring',
        service_type=Integration.QUICKBOOKS,
        status=Integration.ACTIVE,
        access_token='tok_old',
        refresh_token='ref_old',
        token_expires_at=timezone.now() - timedelta(hours=1),
        config={'company_id': 'qb_exp'},
    )


# ---------------------------------------------------------------------------
# sync_external_service
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSyncExternalService:

    @patch('apps.integrations.services.get_service')
    def test_sync_by_integration_id(self, mock_get_service, active_qb):
        mock_log = MagicMock(records_synced=10, duration_ms=500)
        mock_service = MagicMock()
        mock_service.sync.return_value = mock_log
        mock_get_service.return_value = mock_service

        # Integration doesn't need reauth
        active_qb.token_expires_at = None
        active_qb.save()

        result = sync_external_service(
            'quickbooks',
            {'integration_id': str(active_qb.id), 'sync_type': 'full'},
        )

        assert result['status'] == 'success'
        assert result['records_synced'] == 10
        mock_service.sync.assert_called_once_with(sync_type='full')

    @patch('apps.integrations.services.get_service')
    def test_sync_by_service_type_fallback(self, mock_get_service, active_qb):
        mock_log = MagicMock(records_synced=5, duration_ms=200)
        mock_service = MagicMock()
        mock_service.sync.return_value = mock_log
        mock_get_service.return_value = mock_service

        active_qb.token_expires_at = None
        active_qb.save()

        result = sync_external_service('quickbooks', {'sync_type': 'incremental'})

        assert result['status'] == 'success'
        mock_service.sync.assert_called_once_with(sync_type='incremental')

    def test_no_active_integration_skips(self, inactive_integration):
        result = sync_external_service(
            'slack', {'sync_type': 'full'},
        )

        assert result['status'] == 'skipped'

    @patch('apps.integrations.services.get_service')
    def test_refreshes_token_if_needed(self, mock_get_service, expiring_token_integration):
        mock_log = MagicMock(records_synced=1, duration_ms=100)
        mock_service = MagicMock()
        mock_service.sync.return_value = mock_log
        mock_get_service.return_value = mock_service

        result = sync_external_service(
            'quickbooks',
            {'integration_id': str(expiring_token_integration.id)},
        )

        assert result['status'] == 'success'
        mock_service.refresh_token.assert_called_once()

    @patch('apps.integrations.services.get_service')
    def test_retries_on_exception(self, mock_get_service, active_qb):
        mock_get_service.side_effect = Exception('boom')

        with pytest.raises(Exception, match='boom'):
            sync_external_service(
                'quickbooks',
                {'integration_id': str(active_qb.id)},
            )


# ---------------------------------------------------------------------------
# scheduled_sync_all
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestScheduledSyncAll:

    @patch('apps.integrations.tasks.sync_external_service')
    def test_queues_due_integrations(self, mock_sync, active_xero):
        """Xero integration last synced 2h ago with 30min interval: should be queued."""
        result = scheduled_sync_all()

        assert result['status'] == 'success'
        assert result['queued'] >= 1
        mock_sync.delay.assert_called()

    @patch('apps.integrations.tasks.sync_external_service')
    def test_skips_recently_synced(self, mock_sync, db):
        Integration.objects.create(
            name='Recent',
            service_type=Integration.SLACK,
            status=Integration.ACTIVE,
            access_token='tok',
            sync_enabled=True,
            sync_interval_minutes=60,
            last_sync_at=timezone.now() - timedelta(minutes=10),
            config={'channel': '#test'},
        )

        result = scheduled_sync_all()

        assert result['queued'] == 0
        mock_sync.delay.assert_not_called()

    @patch('apps.integrations.tasks.sync_external_service')
    def test_skips_inactive(self, mock_sync, inactive_integration):
        result = scheduled_sync_all()

        assert result['queued'] == 0

    @patch('apps.integrations.tasks.sync_external_service')
    def test_queues_never_synced(self, mock_sync, active_qb):
        """Integration with no last_sync_at should always be queued."""
        active_qb.last_sync_at = None
        active_qb.save()

        result = scheduled_sync_all()

        assert result['queued'] >= 1

    def test_retries_on_exception(self):
        with patch('apps.integrations.models.Integration.objects') as mock_objs:
            mock_objs.filter.side_effect = Exception('DB error')

            with pytest.raises(Exception, match='DB error'):
                scheduled_sync_all()


# ---------------------------------------------------------------------------
# refresh_all_tokens
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRefreshAllTokens:

    @patch('apps.integrations.services.get_service')
    def test_refreshes_expired_tokens(self, mock_get_service, expiring_token_integration):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        result = refresh_all_tokens()

        assert result['status'] == 'success'
        assert result['refreshed'] >= 1
        mock_service.refresh_token.assert_called()

    @patch('apps.integrations.services.get_service')
    def test_skips_non_expired(self, mock_get_service, db):
        Integration.objects.create(
            name='Fresh',
            service_type=Integration.XERO,
            status=Integration.ACTIVE,
            access_token='tok',
            token_expires_at=timezone.now() + timedelta(hours=2),
            config={'tenant_id': 't1'},
        )

        result = refresh_all_tokens()

        assert result['refreshed'] == 0

    @patch('apps.integrations.services.get_service')
    def test_counts_failures(self, mock_get_service, expiring_token_integration):
        mock_service = MagicMock()
        mock_service.refresh_token.side_effect = Exception('Token error')
        mock_get_service.return_value = mock_service

        result = refresh_all_tokens()

        assert result['failed'] >= 1

    def test_retries_on_top_level_exception(self):
        with patch('apps.integrations.models.Integration.objects') as mock_objs:
            mock_objs.filter.side_effect = Exception('DB down')

            with pytest.raises(Exception, match='DB down'):
                refresh_all_tokens()


# ---------------------------------------------------------------------------
# process_integration_webhook
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProcessIntegrationWebhook:

    def test_quickbooks_webhook(self, active_qb):
        payload = {
            'eventNotifications': [{
                'dataChangeEvent': {
                    'entities': [{'name': 'Invoice', 'id': '123', 'operation': 'Create'}]
                }
            }]
        }
        result = process_integration_webhook('quickbooks', payload)

        assert result['status'] == 'success'
        assert IntegrationSyncLog.objects.filter(integration=active_qb).exists()

    def test_xero_webhook(self, active_xero):
        payload = {
            'events': [
                {'resourceId': 'r1', 'eventCategory': 'INVOICE', 'eventType': 'UPDATE'},
            ]
        }
        result = process_integration_webhook('xero', payload)

        assert result['status'] == 'success'

    def test_slack_webhook(self, db):
        slack = Integration.objects.create(
            name='Slack',
            service_type=Integration.SLACK,
            status=Integration.ACTIVE,
            access_token='tok_slack',
            config={'channel': '#test'},
        )
        payload = {'type': 'event_callback', 'event': {'type': 'message'}}
        result = process_integration_webhook('slack', payload)

        assert result['status'] == 'success'

    def test_no_active_integration_skips(self, inactive_integration):
        result = process_integration_webhook('slack', {})

        assert result['status'] == 'skipped'

    def test_unknown_integration_type(self, db):
        result = process_integration_webhook('unknown_service', {})

        assert result['status'] == 'skipped'

    def test_unhandled_type_creates_skipped_log(self, db):
        custom = Integration.objects.create(
            name='Custom',
            service_type=Integration.CUSTOM,
            status=Integration.ACTIVE,
            access_token='tok_custom',
        )
        result = process_integration_webhook('custom', {'data': 'test'})

        assert result['status'] == 'success'
        log = IntegrationSyncLog.objects.filter(integration=custom).first()
        assert log is not None
        assert log.status == 'skipped'

    def test_retries_on_exception(self):
        with patch('apps.integrations.models.Integration.objects') as mock_objs:
            mock_objs.filter.side_effect = RuntimeError('DB crash')

            with pytest.raises(RuntimeError):
                process_integration_webhook('quickbooks', {})


# ---------------------------------------------------------------------------
# Webhook processors
# ---------------------------------------------------------------------------

class TestProcessQuickbooksWebhook:

    def test_extracts_entities(self):
        payload = {
            'eventNotifications': [{
                'dataChangeEvent': {
                    'entities': [
                        {'name': 'Invoice', 'id': '1', 'operation': 'Create'},
                        {'name': 'Customer', 'id': '2', 'operation': 'Update'},
                    ]
                }
            }]
        }
        result = _process_quickbooks_webhook(payload)

        assert result['processed'] is True
        assert result['records_processed'] == 2
        assert len(result['entities']) == 2

    def test_empty_notifications(self):
        result = _process_quickbooks_webhook({'eventNotifications': []})

        assert result['processed'] is True
        assert result['records_processed'] == 0

    def test_missing_key(self):
        result = _process_quickbooks_webhook({})

        assert result['processed'] is True
        assert result['records_processed'] == 0


class TestProcessXeroWebhook:

    def test_extracts_events(self):
        payload = {
            'events': [
                {'resourceId': 'r1', 'eventCategory': 'INVOICE', 'eventType': 'UPDATE'},
                {'resourceId': 'r2', 'eventCategory': 'PAYMENT', 'eventType': 'CREATE'},
            ]
        }
        result = _process_xero_webhook(payload)

        assert result['processed'] is True
        assert result['records_processed'] == 2

    def test_empty_events(self):
        result = _process_xero_webhook({'events': []})

        assert result['processed'] is True
        assert result['records_processed'] == 0

    def test_missing_key(self):
        result = _process_xero_webhook({})

        assert result['processed'] is True
        assert result['records_processed'] == 0


class TestProcessSlackWebhook:

    def test_processes_event(self):
        payload = {'type': 'event_callback'}
        result = _process_slack_webhook(payload)

        assert result['processed'] is True
        assert result['records_processed'] == 1
        assert result['event_type'] == 'event_callback'

    def test_unknown_type(self):
        result = _process_slack_webhook({})

        assert result['processed'] is True
        assert result['event_type'] == 'unknown'
