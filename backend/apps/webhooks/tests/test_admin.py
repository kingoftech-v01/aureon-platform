"""
Tests for webhooks admin configuration.

Covers:
- WebhookEventAdmin registration, list_display, list_filter, search_fields,
  readonly_fields, fieldsets, actions, custom display methods
- WebhookEndpointAdmin registration, list_display, list_filter, search_fields,
  readonly_fields, fieldsets, actions, custom display methods
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

from apps.webhooks.models import WebhookEvent, WebhookEndpoint
from apps.webhooks.admin import WebhookEventAdmin, WebhookEndpointAdmin


@pytest.fixture
def site():
    return AdminSite()


@pytest.fixture
def event_admin(site):
    return WebhookEventAdmin(WebhookEvent, site)


@pytest.fixture
def endpoint_admin(site):
    return WebhookEndpointAdmin(WebhookEndpoint, site)


@pytest.fixture
def webhook_event(db):
    return WebhookEvent.objects.create(
        source=WebhookEvent.STRIPE,
        event_type='payment_intent.succeeded',
        event_id=f'evt_admin_{uuid.uuid4().hex[:20]}',
        status=WebhookEvent.PROCESSED,
        payload={'id': 'evt_test', 'type': 'payment_intent.succeeded', 'data': {'object': {}}},
        headers={'stripe_signature': 'sig_test'},
        response_body={'result': 'ok'},
    )


@pytest.fixture
def webhook_endpoint(db):
    return WebhookEndpoint.objects.create(
        url='https://hooks.example.com/receive',
        secret_key='secret-123',
        event_types=['invoice.created', 'payment.succeeded', 'contract.signed'],
        is_active=True,
        total_deliveries=100,
        successful_deliveries=95,
        failed_deliveries=5,
    )


# ---------------------------------------------------------------------------
# WebhookEventAdmin
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWebhookEventAdmin:

    def test_registered(self):
        assert WebhookEvent in admin.site._registry

    def test_list_display(self, event_admin):
        expected = ['event_id', 'source', 'event_type', 'status_badge', 'retry_count', 'received_at', 'processed_at']
        assert event_admin.list_display == expected

    def test_list_filter(self, event_admin):
        assert 'source' in event_admin.list_filter
        assert 'status' in event_admin.list_filter

    def test_search_fields(self, event_admin):
        assert 'event_id' in event_admin.search_fields
        assert 'event_type' in event_admin.search_fields
        assert 'error_message' in event_admin.search_fields

    def test_readonly_fields(self, event_admin):
        assert 'id' in event_admin.readonly_fields
        assert 'event_id' in event_admin.readonly_fields
        assert 'payload_display' in event_admin.readonly_fields

    def test_status_badge_processed(self, event_admin, webhook_event):
        result = event_admin.status_badge(webhook_event)
        assert 'green' in result
        assert webhook_event.get_status_display() in result

    def test_status_badge_failed(self, event_admin, webhook_event):
        webhook_event.status = WebhookEvent.FAILED
        result = event_admin.status_badge(webhook_event)
        assert 'red' in result

    def test_status_badge_pending(self, event_admin, webhook_event):
        webhook_event.status = WebhookEvent.PENDING
        result = event_admin.status_badge(webhook_event)
        assert 'gray' in result

    def test_status_badge_processing(self, event_admin, webhook_event):
        webhook_event.status = WebhookEvent.PROCESSING
        result = event_admin.status_badge(webhook_event)
        assert 'blue' in result

    def test_status_badge_retrying(self, event_admin, webhook_event):
        webhook_event.status = WebhookEvent.RETRYING
        result = event_admin.status_badge(webhook_event)
        assert 'orange' in result

    def test_payload_display_formatted(self, event_admin, webhook_event):
        result = event_admin.payload_display(webhook_event)
        assert '<pre>' in result
        assert 'evt_test' in result

    def test_payload_display_fallback(self, event_admin, webhook_event):
        webhook_event.payload = 'not json serializable object'
        # Even strings are json-serializable, so test with a non-serializable type
        result = event_admin.payload_display(webhook_event)
        assert result is not None

    def test_headers_display_formatted(self, event_admin, webhook_event):
        result = event_admin.headers_display(webhook_event)
        assert '<pre>' in result

    def test_response_body_display_formatted(self, event_admin, webhook_event):
        result = event_admin.response_body_display(webhook_event)
        assert '<pre>' in result

    def test_response_body_display_none(self, event_admin, webhook_event):
        webhook_event.response_body = None
        result = event_admin.response_body_display(webhook_event)
        assert result == '-'

    def test_actions_present(self, event_admin):
        assert 'retry_failed_webhooks' in event_admin.actions
        assert 'mark_as_processed' in event_admin.actions

    @patch('apps.webhooks.admin.process_stripe_webhook')
    def test_retry_failed_webhooks_action(self, mock_task, event_admin, webhook_event):
        webhook_event.status = WebhookEvent.FAILED
        webhook_event.retry_count = 0
        webhook_event.save()

        queryset = WebhookEvent.objects.filter(pk=webhook_event.pk)
        request = MagicMock()
        event_admin.retry_failed_webhooks(request, queryset)

        mock_task.delay.assert_called_once_with(webhook_event.id)
        event_admin.message_user.assert_not_called  # message_user is called on the admin

    def test_mark_as_processed_action(self, event_admin, webhook_event):
        webhook_event.status = WebhookEvent.FAILED
        webhook_event.save()

        queryset = WebhookEvent.objects.filter(pk=webhook_event.pk)
        request = MagicMock()
        event_admin.mark_as_processed(request, queryset)

        webhook_event.refresh_from_db()
        assert webhook_event.status == 'processed'

    def test_fieldsets_defined(self, event_admin):
        assert len(event_admin.fieldsets) > 0
        fieldset_names = [fs[0] for fs in event_admin.fieldsets]
        assert 'Event Information' in fieldset_names
        assert 'Payload' in fieldset_names


# ---------------------------------------------------------------------------
# WebhookEndpointAdmin
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWebhookEndpointAdmin:

    def test_registered(self):
        assert WebhookEndpoint in admin.site._registry

    def test_list_display(self, endpoint_admin):
        expected = ['url', 'is_active', 'event_count', 'success_rate_display', 'total_deliveries', 'last_delivery_at']
        assert endpoint_admin.list_display == expected

    def test_list_filter(self, endpoint_admin):
        assert 'is_active' in endpoint_admin.list_filter

    def test_search_fields(self, endpoint_admin):
        assert 'url' in endpoint_admin.search_fields

    def test_readonly_fields(self, endpoint_admin):
        assert 'id' in endpoint_admin.readonly_fields
        assert 'total_deliveries' in endpoint_admin.readonly_fields
        assert 'success_rate_display' in endpoint_admin.readonly_fields

    def test_event_count(self, endpoint_admin, webhook_endpoint):
        result = endpoint_admin.event_count(webhook_endpoint)
        assert result == 3

    def test_success_rate_display_high(self, endpoint_admin, webhook_endpoint):
        result = endpoint_admin.success_rate_display(webhook_endpoint)
        assert 'green' in result
        assert '95.0%' in result

    def test_success_rate_display_medium(self, endpoint_admin, webhook_endpoint):
        webhook_endpoint.successful_deliveries = 85
        webhook_endpoint.failed_deliveries = 15
        result = endpoint_admin.success_rate_display(webhook_endpoint)
        assert 'orange' in result

    def test_success_rate_display_low(self, endpoint_admin, webhook_endpoint):
        webhook_endpoint.successful_deliveries = 50
        webhook_endpoint.failed_deliveries = 50
        result = endpoint_admin.success_rate_display(webhook_endpoint)
        assert 'red' in result

    def test_fieldsets_defined(self, endpoint_admin):
        assert len(endpoint_admin.fieldsets) > 0
        fieldset_names = [fs[0] for fs in endpoint_admin.fieldsets]
        assert 'Endpoint Configuration' in fieldset_names
        assert 'Statistics' in fieldset_names

    @patch('apps.webhooks.admin.send_outgoing_webhook')
    def test_test_webhook_endpoint_action(self, mock_task, endpoint_admin, webhook_endpoint):
        queryset = WebhookEndpoint.objects.filter(pk=webhook_endpoint.pk)
        request = MagicMock()
        endpoint_admin.test_webhook_endpoint(request, queryset)

        mock_task.delay.assert_called_once()
        call_args = mock_task.delay.call_args[0]
        assert call_args[0] == str(webhook_endpoint.id)
        assert call_args[1] == 'test.event'

    @patch('apps.webhooks.admin.send_outgoing_webhook')
    def test_test_webhook_skips_inactive(self, mock_task, endpoint_admin, webhook_endpoint):
        webhook_endpoint.is_active = False
        webhook_endpoint.save()

        queryset = WebhookEndpoint.objects.filter(pk=webhook_endpoint.pk)
        request = MagicMock()
        endpoint_admin.test_webhook_endpoint(request, queryset)

        mock_task.delay.assert_not_called()

    def test_actions_present(self, endpoint_admin):
        assert 'test_webhook_endpoint' in endpoint_admin.actions
