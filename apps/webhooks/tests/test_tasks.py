"""
Tests for webhooks Celery tasks.

Covers:
- process_stripe_webhook: async processing, retries, error handling
- retry_failed_webhooks: periodic retry of failed events
- cleanup_old_webhooks: old event cleanup
- send_outgoing_webhook: outgoing webhook delivery, HMAC signing
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import timedelta
from django.utils import timezone

from apps.webhooks.tasks import (
    process_stripe_webhook,
    retry_failed_webhooks,
    cleanup_old_webhooks,
    send_outgoing_webhook,
)
from apps.webhooks.models import WebhookEvent, WebhookEndpoint


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def webhook_event(db):
    """Create a pending webhook event."""
    return WebhookEvent.objects.create(
        source=WebhookEvent.STRIPE,
        event_type='payment_intent.succeeded',
        event_id=f'evt_{uuid.uuid4().hex[:24]}',
        status=WebhookEvent.PENDING,
        payload={
            'id': 'evt_test',
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_test', 'amount': 5000, 'currency': 'usd'}},
        },
    )


@pytest.fixture
def failed_webhook_event(db):
    """Create a failed webhook event eligible for retry."""
    return WebhookEvent.objects.create(
        source=WebhookEvent.STRIPE,
        event_type='payment_intent.succeeded',
        event_id=f'evt_fail_{uuid.uuid4().hex[:20]}',
        status=WebhookEvent.FAILED,
        payload={'id': 'evt_fail', 'type': 'payment_intent.succeeded', 'data': {'object': {}}},
        retry_count=1,
        max_retries=3,
    )


@pytest.fixture
def processed_webhook_old(db):
    """Create an old processed webhook event (>90 days)."""
    event = WebhookEvent.objects.create(
        source=WebhookEvent.STRIPE,
        event_type='charge.succeeded',
        event_id=f'evt_old_{uuid.uuid4().hex[:20]}',
        status=WebhookEvent.PROCESSED,
        payload={'id': 'evt_old', 'type': 'charge.succeeded', 'data': {'object': {}}},
    )
    # Manually set received_at to >90 days ago
    WebhookEvent.objects.filter(pk=event.pk).update(
        received_at=timezone.now() - timedelta(days=100)
    )
    return event


@pytest.fixture
def webhook_endpoint(db):
    """Create an active webhook endpoint."""
    return WebhookEndpoint.objects.create(
        url='https://hooks.example.com/receive',
        secret_key='test-secret-key-12345',
        event_types=['invoice.created', 'payment.succeeded'],
        is_active=True,
        headers={'X-Custom': 'value'},
        timeout=10,
    )


# ---------------------------------------------------------------------------
# process_stripe_webhook
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProcessStripeWebhook:

    @patch('apps.webhooks.tasks.StripeWebhookHandler')
    def test_successful_processing(self, MockHandler, webhook_event):
        mock_handler = MagicMock()
        mock_handler.handle.return_value = {'status': 'processed'}
        MockHandler.return_value = mock_handler

        result = process_stripe_webhook(webhook_event.id)

        assert result == {'status': 'processed'}
        webhook_event.refresh_from_db()
        assert webhook_event.status == WebhookEvent.PROCESSED
        assert webhook_event.processed_at is not None

    def test_event_not_found(self):
        fake_id = uuid.uuid4()
        result = process_stripe_webhook(fake_id)
        assert result == {'error': 'WebhookEvent not found'}

    @patch('apps.webhooks.tasks.StripeWebhookHandler')
    def test_processing_sets_status_to_processing(self, MockHandler, webhook_event):
        """Should mark event as 'processing' before handling."""
        def check_status(payload):
            webhook_event.refresh_from_db()
            assert webhook_event.status == WebhookEvent.PROCESSING
            handler = MagicMock()
            handler.handle.return_value = {'status': 'ok'}
            return handler

        MockHandler.side_effect = check_status
        process_stripe_webhook(webhook_event.id)

    @patch('apps.webhooks.tasks.StripeWebhookHandler')
    def test_error_with_retry_available(self, MockHandler, webhook_event):
        """Should retry on failure when retries remain."""
        MockHandler.return_value.handle.side_effect = ValueError('boom')

        # process_stripe_webhook is a bound task; call it correctly
        task = process_stripe_webhook
        with pytest.raises(Exception):
            task(webhook_event.id)

        webhook_event.refresh_from_db()
        assert webhook_event.status in [WebhookEvent.RETRYING, WebhookEvent.FAILED]
        assert webhook_event.retry_count >= 1

    @patch('apps.webhooks.tasks.StripeWebhookHandler')
    def test_error_no_retry_when_max_reached(self, MockHandler, webhook_event):
        """Should mark as failed when max retries exceeded."""
        MockHandler.return_value.handle.side_effect = ValueError('boom')
        webhook_event.retry_count = 3
        webhook_event.max_retries = 3
        webhook_event.save()

        result = process_stripe_webhook(webhook_event.id)

        assert 'error' in result
        webhook_event.refresh_from_db()
        assert webhook_event.status == WebhookEvent.FAILED


# ---------------------------------------------------------------------------
# retry_failed_webhooks
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRetryFailedWebhooks:

    @patch('apps.webhooks.tasks.process_stripe_webhook')
    def test_retries_failed_stripe_events(self, mock_task, failed_webhook_event):
        result = retry_failed_webhooks()

        mock_task.delay.assert_called_once_with(failed_webhook_event.id)
        assert result['retried'] >= 1

    @patch('apps.webhooks.tasks.process_stripe_webhook')
    def test_skips_non_stripe_events(self, mock_task, db):
        WebhookEvent.objects.create(
            source=WebhookEvent.CUSTOM,
            event_type='custom.event',
            event_id=f'custom_{uuid.uuid4().hex[:20]}',
            status=WebhookEvent.FAILED,
            payload={'data': 'test'},
            retry_count=0,
            max_retries=3,
        )
        result = retry_failed_webhooks()
        mock_task.delay.assert_not_called()

    @patch('apps.webhooks.tasks.process_stripe_webhook')
    def test_skips_events_at_max_retries(self, mock_task, db):
        WebhookEvent.objects.create(
            source=WebhookEvent.STRIPE,
            event_type='payment_intent.failed',
            event_id=f'evt_maxed_{uuid.uuid4().hex[:18]}',
            status=WebhookEvent.FAILED,
            payload={'data': 'test'},
            retry_count=3,
            max_retries=3,
        )
        result = retry_failed_webhooks()
        mock_task.delay.assert_not_called()

    @patch('apps.webhooks.tasks.process_stripe_webhook')
    def test_returns_timestamp(self, mock_task, db):
        result = retry_failed_webhooks()
        assert 'timestamp' in result
        assert 'retried' in result


# ---------------------------------------------------------------------------
# cleanup_old_webhooks
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCleanupOldWebhooks:

    def test_deletes_old_processed_events(self, processed_webhook_old):
        result = cleanup_old_webhooks()
        assert result['deleted'] >= 1
        assert not WebhookEvent.objects.filter(pk=processed_webhook_old.pk).exists()

    def test_keeps_recent_processed_events(self, webhook_event):
        webhook_event.status = WebhookEvent.PROCESSED
        webhook_event.save()

        result = cleanup_old_webhooks()
        assert WebhookEvent.objects.filter(pk=webhook_event.pk).exists()

    def test_keeps_old_failed_events(self, db):
        event = WebhookEvent.objects.create(
            source=WebhookEvent.STRIPE,
            event_type='charge.failed',
            event_id=f'evt_oldfail_{uuid.uuid4().hex[:16]}',
            status=WebhookEvent.FAILED,
            payload={'data': 'fail'},
        )
        WebhookEvent.objects.filter(pk=event.pk).update(
            received_at=timezone.now() - timedelta(days=120)
        )

        result = cleanup_old_webhooks()
        assert WebhookEvent.objects.filter(pk=event.pk).exists()

    def test_returns_cutoff_date(self):
        result = cleanup_old_webhooks()
        assert 'cutoff_date' in result
        assert 'deleted' in result


# ---------------------------------------------------------------------------
# send_outgoing_webhook
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSendOutgoingWebhook:

    def test_endpoint_not_found(self):
        result = send_outgoing_webhook(uuid.uuid4(), 'test.event', {'key': 'val'})
        assert result == {'error': 'Endpoint not found'}

    def test_inactive_endpoint_not_found(self, webhook_endpoint):
        webhook_endpoint.is_active = False
        webhook_endpoint.save()
        result = send_outgoing_webhook(webhook_endpoint.id, 'test.event', {'key': 'val'})
        assert result == {'error': 'Endpoint not found'}

    def test_event_type_not_subscribed(self, webhook_endpoint):
        result = send_outgoing_webhook(
            webhook_endpoint.id,
            'unsubscribed.event',
            {'data': 'test'}
        )
        assert 'skipped' in result

    @patch('apps.webhooks.tasks.requests.post')
    def test_successful_delivery(self, mock_post, webhook_endpoint):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = send_outgoing_webhook(
            webhook_endpoint.id,
            'payment.succeeded',
            {'amount': 100}
        )

        assert result['delivered'] is True
        assert result['status_code'] == 200
        mock_post.assert_called_once()

        # Verify HMAC signature was set
        call_kwargs = mock_post.call_args
        headers = call_kwargs[1]['headers'] if 'headers' in call_kwargs[1] else call_kwargs.kwargs['headers']
        assert 'X-Webhook-Signature' in headers
        assert 'X-Event-Type' in headers

        webhook_endpoint.refresh_from_db()
        assert webhook_endpoint.total_deliveries == 1
        assert webhook_endpoint.successful_deliveries == 1

    @patch('apps.webhooks.tasks.requests.post')
    def test_delivery_non_success_status(self, mock_post, webhook_endpoint):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        result = send_outgoing_webhook(
            webhook_endpoint.id,
            'payment.succeeded',
            {'amount': 100}
        )

        assert result['delivered'] is False
        assert result['status_code'] == 500

        webhook_endpoint.refresh_from_db()
        assert webhook_endpoint.failed_deliveries == 1

    @patch('apps.webhooks.tasks.requests.post')
    def test_delivery_accepted_status_codes(self, mock_post, webhook_endpoint):
        """201, 202, and 204 should count as success."""
        for status_code in [201, 202, 204]:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_post.return_value = mock_response

            result = send_outgoing_webhook(
                webhook_endpoint.id,
                'invoice.created',
                {'invoice_id': 'inv_test'}
            )
            assert result['delivered'] is True

    @patch('apps.webhooks.tasks.requests.post')
    def test_request_exception(self, mock_post, webhook_endpoint):
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError('connection refused')

        result = send_outgoing_webhook(
            webhook_endpoint.id,
            'payment.succeeded',
            {'amount': 100}
        )

        assert result['delivered'] is False
        assert 'error' in result

        webhook_endpoint.refresh_from_db()
        assert webhook_endpoint.failed_deliveries == 1

    @patch('apps.webhooks.tasks.requests.post')
    def test_custom_headers_included(self, mock_post, webhook_endpoint):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        send_outgoing_webhook(
            webhook_endpoint.id,
            'payment.succeeded',
            {'data': 'test'}
        )

        call_kwargs = mock_post.call_args
        headers = call_kwargs[1]['headers'] if 'headers' in call_kwargs[1] else call_kwargs.kwargs['headers']
        assert headers.get('X-Custom') == 'value'

    @patch('apps.webhooks.tasks.requests.post')
    def test_timeout_passed(self, mock_post, webhook_endpoint):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        send_outgoing_webhook(
            webhook_endpoint.id,
            'payment.succeeded',
            {'data': 'test'}
        )

        call_kwargs = mock_post.call_args
        assert call_kwargs[1].get('timeout') == webhook_endpoint.timeout or \
               call_kwargs.kwargs.get('timeout') == webhook_endpoint.timeout
