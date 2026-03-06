"""
Tests for integrations Celery tasks.

Covers:
- sync_external_service: service routing, QuickBooks sync, Xero sync, unknown service
- _sync_quickbooks / _sync_xero: API calls, missing config
- process_integration_webhook: QuickBooks webhook, Xero webhook, unknown
- _process_quickbooks_webhook / _process_xero_webhook: payload parsing
"""

import pytest
from unittest.mock import patch, MagicMock
from django.test import override_settings

from apps.integrations.tasks import (
    sync_external_service,
    process_integration_webhook,
    _sync_quickbooks,
    _sync_xero,
    _process_quickbooks_webhook,
    _process_xero_webhook,
)


# ---------------------------------------------------------------------------
# sync_external_service
# ---------------------------------------------------------------------------

class TestSyncExternalService:

    @patch('apps.integrations.tasks._sync_quickbooks')
    def test_routes_to_quickbooks(self, mock_qb):
        mock_qb.return_value = {'synced': True}
        result = sync_external_service('quickbooks', {'invoice_id': '123'})

        assert result['status'] == 'success'
        assert result['service'] == 'quickbooks'
        mock_qb.assert_called_once_with({'invoice_id': '123'})

    @patch('apps.integrations.tasks._sync_xero')
    def test_routes_to_xero(self, mock_xero):
        mock_xero.return_value = {'synced': True}
        result = sync_external_service('xero', {'data': 'test'})

        assert result['status'] == 'success'
        assert result['service'] == 'xero'
        mock_xero.assert_called_once_with({'data': 'test'})

    def test_unknown_service(self):
        result = sync_external_service('unknown_service', {})

        assert result['status'] == 'success'
        assert result['result']['synced'] is False
        assert 'not configured' in result['result']['message']

    @patch('apps.integrations.tasks._sync_quickbooks')
    def test_retries_on_exception(self, mock_qb):
        mock_qb.side_effect = ConnectionError('network error')

        with pytest.raises(Exception):
            sync_external_service('quickbooks', {})


# ---------------------------------------------------------------------------
# _sync_quickbooks
# ---------------------------------------------------------------------------

class TestSyncQuickbooks:

    @override_settings(QUICKBOOKS_API_URL=None, QUICKBOOKS_API_TOKEN=None)
    def test_not_configured(self):
        result = _sync_quickbooks({'data': 'test'})
        assert result['synced'] is False
        assert 'not configured' in result['message']

    @override_settings(QUICKBOOKS_API_URL='https://qb.api/v3', QUICKBOOKS_API_TOKEN='tok_123')
    def test_successful_sync(self):
        import requests as req_module
        mock_response = MagicMock()
        mock_response.json.return_value = {'status': 'ok'}
        mock_response.raise_for_status = MagicMock()

        with patch.object(req_module, 'post', return_value=mock_response) as mock_post:
            result = _sync_quickbooks({'invoice': 'inv_1'})

        assert result['synced'] is True
        assert result['response'] == {'status': 'ok'}
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert 'Bearer tok_123' in str(call_args)

    @override_settings(QUICKBOOKS_API_URL='https://qb.api/v3', QUICKBOOKS_API_TOKEN='tok_123')
    def test_api_error_raises(self):
        import requests as req_module
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req_module.exceptions.HTTPError('500')

        with patch.object(req_module, 'post', return_value=mock_response):
            with pytest.raises(req_module.exceptions.HTTPError):
                _sync_quickbooks({'data': 'test'})

    @override_settings(QUICKBOOKS_API_URL='https://qb.api/v3', QUICKBOOKS_API_TOKEN=None)
    def test_missing_token(self):
        result = _sync_quickbooks({'data': 'test'})
        assert result['synced'] is False


# ---------------------------------------------------------------------------
# _sync_xero
# ---------------------------------------------------------------------------

class TestSyncXero:

    @override_settings(XERO_API_URL=None, XERO_API_TOKEN=None)
    def test_not_configured(self):
        result = _sync_xero({'data': 'test'})
        assert result['synced'] is False
        assert 'not configured' in result['message']

    @override_settings(XERO_API_URL='https://xero.api/2.0', XERO_API_TOKEN='xero_tok')
    def test_successful_sync(self):
        import requests as req_module
        mock_response = MagicMock()
        mock_response.json.return_value = {'contacts': []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(req_module, 'post', return_value=mock_response) as mock_post:
            result = _sync_xero({'contact': 'c_1'})

        assert result['synced'] is True
        mock_post.assert_called_once()

    @override_settings(XERO_API_URL='https://xero.api/2.0', XERO_API_TOKEN='xero_tok')
    def test_api_error_raises(self):
        import requests as req_module
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req_module.exceptions.HTTPError('401')

        with patch.object(req_module, 'post', return_value=mock_response):
            with pytest.raises(req_module.exceptions.HTTPError):
                _sync_xero({'data': 'test'})

    @override_settings(XERO_API_URL=None, XERO_API_TOKEN='tok')
    def test_missing_url(self):
        result = _sync_xero({'data': 'test'})
        assert result['synced'] is False


# ---------------------------------------------------------------------------
# process_integration_webhook
# ---------------------------------------------------------------------------

class TestProcessIntegrationWebhook:

    @patch('apps.integrations.tasks._process_quickbooks_webhook')
    def test_routes_to_quickbooks(self, mock_handler):
        mock_handler.return_value = {'processed': True, 'event_type': 'Invoice'}
        result = process_integration_webhook('quickbooks', {'eventNotifications': []})

        assert result['status'] == 'success'
        assert result['integration'] == 'quickbooks'
        mock_handler.assert_called_once()

    @patch('apps.integrations.tasks._process_xero_webhook')
    def test_routes_to_xero(self, mock_handler):
        mock_handler.return_value = {'processed': True, 'events_count': 3}
        result = process_integration_webhook('xero', {'events': [1, 2, 3]})

        assert result['status'] == 'success'
        assert result['integration'] == 'xero'

    def test_unknown_integration(self):
        result = process_integration_webhook('unknown', {})

        assert result['status'] == 'success'
        assert result['result']['processed'] is False

    @patch('apps.integrations.tasks._process_quickbooks_webhook')
    def test_retries_on_exception(self, mock_handler):
        mock_handler.side_effect = RuntimeError('processing error')

        with pytest.raises(Exception):
            process_integration_webhook('quickbooks', {})


# ---------------------------------------------------------------------------
# _process_quickbooks_webhook
# ---------------------------------------------------------------------------

class TestProcessQuickbooksWebhook:

    def test_extracts_event_type(self):
        payload = {
            'eventNotifications': [{
                'dataChangeEvent': {
                    'entities': [{'name': 'Invoice', 'id': '123'}]
                }
            }]
        }
        result = _process_quickbooks_webhook(payload)
        assert result['processed'] is True
        assert result['event_type'] == 'Invoice'

    def test_missing_event_data(self):
        result = _process_quickbooks_webhook({})
        assert result['processed'] is True
        assert result['event_type'] == 'unknown'

    def test_empty_notifications_raises_index_error(self):
        """Empty eventNotifications list triggers IndexError in source (known bug)."""
        with pytest.raises(IndexError):
            _process_quickbooks_webhook({'eventNotifications': []})


# ---------------------------------------------------------------------------
# _process_xero_webhook
# ---------------------------------------------------------------------------

class TestProcessXeroWebhook:

    def test_counts_events(self):
        payload = {'events': [{'id': 1}, {'id': 2}, {'id': 3}]}
        result = _process_xero_webhook(payload)
        assert result['processed'] is True
        assert result['events_count'] == 3

    def test_empty_events(self):
        result = _process_xero_webhook({'events': []})
        assert result['processed'] is True
        assert result['events_count'] == 0

    def test_missing_events_key(self):
        result = _process_xero_webhook({})
        assert result['processed'] is True
        assert result['events_count'] == 0
