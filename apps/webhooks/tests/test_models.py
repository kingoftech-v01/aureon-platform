"""
Tests for webhook models.

Tests cover:
- WebhookEvent creation, status transitions, properties
- WebhookEndpoint creation, delivery recording, success rate
"""

import uuid
import pytest
from django.utils import timezone
from datetime import timedelta

from apps.webhooks.models import WebhookEvent, WebhookEndpoint


# =============================================================================
# WebhookEvent Model Tests
# =============================================================================

@pytest.mark.django_db
class TestWebhookEvent:
    """Tests for the WebhookEvent model."""

    def _create_event(self, **overrides):
        """Helper to create a WebhookEvent with sensible defaults."""
        defaults = {
            'source': WebhookEvent.STRIPE,
            'event_type': 'payment_intent.succeeded',
            'event_id': f'evt_{uuid.uuid4().hex[:24]}',
            'payload': {'type': 'payment_intent.succeeded', 'id': 'evt_123'},
            'headers': {'stripe_signature': 'sig_test'},
            'ip_address': '127.0.0.1',
            'user_agent': 'Stripe/1.0',
        }
        defaults.update(overrides)
        return WebhookEvent.objects.create(**defaults)

    def test_create_webhook_event(self):
        """WebhookEvent should be created with correct default values."""
        event = self._create_event()

        assert event.pk is not None
        assert event.source == WebhookEvent.STRIPE
        assert event.event_type == 'payment_intent.succeeded'
        assert event.status == WebhookEvent.PENDING
        assert event.retry_count == 0
        assert event.max_retries == 3
        assert event.processed_at is None
        assert event.error_message == ''
        assert event.received_at is not None
        assert event.response_code is None
        assert event.response_body is None

    def test_webhook_event_str(self):
        """String representation should include source, type, and status."""
        event = self._create_event()
        result = str(event)

        assert 'stripe' in result
        assert 'payment_intent.succeeded' in result
        assert 'pending' in result

    def test_mark_as_processing(self):
        """mark_as_processing should set status to PROCESSING."""
        event = self._create_event()
        assert event.status == WebhookEvent.PENDING

        event.mark_as_processing()
        event.refresh_from_db()

        assert event.status == WebhookEvent.PROCESSING

    def test_mark_as_processed(self):
        """mark_as_processed should set status, timestamp, and response data."""
        event = self._create_event()
        event.mark_as_processing()

        response_data = {'result': 'success', 'payment_id': 'pay_123'}
        event.mark_as_processed(response_data)
        event.refresh_from_db()

        assert event.status == WebhookEvent.PROCESSED
        assert event.processed_at is not None
        assert event.response_code == 200
        assert event.response_body == response_data

    def test_mark_as_processed_without_response_data(self):
        """mark_as_processed with no response data should still work."""
        event = self._create_event()
        event.mark_as_processed()
        event.refresh_from_db()

        assert event.status == WebhookEvent.PROCESSED
        assert event.processed_at is not None
        assert event.response_code == 200
        assert event.response_body is None

    def test_mark_as_failed(self):
        """mark_as_failed should record error and increment retry count."""
        event = self._create_event()
        event.mark_as_processing()

        event.mark_as_failed('Connection timeout', should_retry=True)
        event.refresh_from_db()

        assert event.status == WebhookEvent.RETRYING
        assert event.error_message == 'Connection timeout'
        assert event.retry_count == 1
        assert event.response_code == 500

    def test_mark_as_failed_no_retry(self):
        """mark_as_failed with should_retry=False should set status to FAILED."""
        event = self._create_event()

        event.mark_as_failed('Permanent error', should_retry=False)
        event.refresh_from_db()

        assert event.status == WebhookEvent.FAILED
        assert event.error_message == 'Permanent error'
        assert event.retry_count == 1

    def test_mark_as_failed_with_retry(self):
        """Multiple failures should increment retry_count and eventually set FAILED."""
        event = self._create_event()

        # Fail 3 times (max_retries default is 3)
        event.mark_as_failed('Error 1', should_retry=True)
        assert event.status == WebhookEvent.RETRYING
        assert event.retry_count == 1

        event.mark_as_failed('Error 2', should_retry=True)
        assert event.status == WebhookEvent.RETRYING
        assert event.retry_count == 2

        event.mark_as_failed('Error 3', should_retry=True)
        # After 3 retries (retry_count == 3, which equals max_retries),
        # status should be FAILED because retry_count >= max_retries
        assert event.status == WebhookEvent.FAILED
        assert event.retry_count == 3

    def test_can_retry(self):
        """can_retry should be True when retries remain and status is FAILED or RETRYING."""
        event = self._create_event()

        # Pending event cannot retry (wrong status)
        assert event.can_retry is False

        # First failure with retry -> RETRYING status, can_retry should be True
        event.mark_as_failed('Error', should_retry=True)
        assert event.can_retry is True

        # Second failure
        event.mark_as_failed('Error', should_retry=True)
        assert event.can_retry is True

        # Third failure -> FAILED, retry_count == max_retries
        event.mark_as_failed('Error', should_retry=True)
        assert event.can_retry is False

    def test_can_retry_after_max_retries(self):
        """can_retry should be False when retry_count >= max_retries."""
        event = self._create_event(max_retries=1)

        event.mark_as_failed('Error', should_retry=True)
        # retry_count is 1, max_retries is 1, so can't retry
        assert event.can_retry is False

    def test_is_stripe_event(self):
        """is_stripe_event should be True for Stripe-sourced events."""
        stripe_event = self._create_event(source=WebhookEvent.STRIPE)
        custom_event = self._create_event(
            source=WebhookEvent.CUSTOM,
            event_id=f'custom_{uuid.uuid4().hex[:12]}',
        )

        assert stripe_event.is_stripe_event is True
        assert custom_event.is_stripe_event is False

    def test_webhook_event_ordering(self):
        """Events should be ordered by -received_at (newest first)."""
        event1 = self._create_event(event_id='evt_order_1')
        event2 = self._create_event(event_id='evt_order_2')

        events = list(WebhookEvent.objects.all())
        assert events[0].event_id == 'evt_order_2'
        assert events[1].event_id == 'evt_order_1'

    def test_webhook_event_unique_event_id(self):
        """event_id should be unique."""
        self._create_event(event_id='evt_unique_test')

        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            self._create_event(event_id='evt_unique_test')

    def test_webhook_event_custom_source(self):
        """Custom webhook events should be created correctly."""
        event = self._create_event(
            source=WebhookEvent.CUSTOM,
            event_type='invoice.created',
            event_id=f'custom_{uuid.uuid4().hex[:12]}',
            payload={'event_type': 'invoice.created', 'invoice_id': '123'},
        )

        assert event.source == WebhookEvent.CUSTOM
        assert event.event_type == 'invoice.created'
        assert event.is_stripe_event is False


# =============================================================================
# WebhookEndpoint Model Tests
# =============================================================================

@pytest.mark.django_db
class TestWebhookEndpoint:
    """Tests for the WebhookEndpoint model."""

    def _create_endpoint(self, **overrides):
        """Helper to create a WebhookEndpoint with sensible defaults."""
        defaults = {
            'url': 'https://example.com/webhook',
            'secret_key': 'test-secret-key-123',
            'event_types': ['invoice.created', 'payment.succeeded'],
            'is_active': True,
        }
        defaults.update(overrides)
        return WebhookEndpoint.objects.create(**defaults)

    def test_webhook_endpoint_create(self):
        """WebhookEndpoint should be created with correct default values."""
        endpoint = self._create_endpoint()

        assert endpoint.pk is not None
        assert endpoint.url == 'https://example.com/webhook'
        assert endpoint.secret_key == 'test-secret-key-123'
        assert endpoint.event_types == ['invoice.created', 'payment.succeeded']
        assert endpoint.is_active is True
        assert endpoint.timeout == 30
        assert endpoint.max_retries == 3
        assert endpoint.retry_delay == 60
        assert endpoint.total_deliveries == 0
        assert endpoint.successful_deliveries == 0
        assert endpoint.failed_deliveries == 0
        assert endpoint.last_delivery_at is None
        assert endpoint.last_success_at is None

    def test_webhook_endpoint_str(self):
        """String representation should include URL and event count."""
        endpoint = self._create_endpoint()
        result = str(endpoint)

        assert 'https://example.com/webhook' in result
        assert '2 events' in result

    def test_webhook_endpoint_record_delivery_success(self):
        """record_delivery(success=True) should increment delivery counters."""
        endpoint = self._create_endpoint()

        endpoint.record_delivery(success=True)
        endpoint.refresh_from_db()

        assert endpoint.total_deliveries == 1
        assert endpoint.successful_deliveries == 1
        assert endpoint.failed_deliveries == 0
        assert endpoint.last_delivery_at is not None
        assert endpoint.last_success_at is not None

    def test_webhook_endpoint_record_delivery_failure(self):
        """record_delivery(success=False) should increment failure counter."""
        endpoint = self._create_endpoint()

        endpoint.record_delivery(success=False)
        endpoint.refresh_from_db()

        assert endpoint.total_deliveries == 1
        assert endpoint.successful_deliveries == 0
        assert endpoint.failed_deliveries == 1
        assert endpoint.last_delivery_at is not None
        assert endpoint.last_success_at is None

    def test_webhook_endpoint_record_delivery(self):
        """Multiple deliveries should accumulate correctly."""
        endpoint = self._create_endpoint()

        endpoint.record_delivery(success=True)
        endpoint.record_delivery(success=True)
        endpoint.record_delivery(success=False)
        endpoint.refresh_from_db()

        assert endpoint.total_deliveries == 3
        assert endpoint.successful_deliveries == 2
        assert endpoint.failed_deliveries == 1

    def test_webhook_endpoint_success_rate(self):
        """success_rate should return percentage of successful deliveries."""
        endpoint = self._create_endpoint()

        # No deliveries -> 0%
        assert endpoint.success_rate == 0

        # 2 success, 1 failure -> 66.67%
        endpoint.record_delivery(success=True)
        endpoint.record_delivery(success=True)
        endpoint.record_delivery(success=False)
        endpoint.refresh_from_db()

        assert abs(endpoint.success_rate - 66.666666) < 0.01

    def test_webhook_endpoint_success_rate_all_successful(self):
        """100% success rate when all deliveries succeed."""
        endpoint = self._create_endpoint()
        endpoint.record_delivery(success=True)
        endpoint.record_delivery(success=True)
        endpoint.refresh_from_db()

        assert endpoint.success_rate == 100

    def test_webhook_endpoint_success_rate_all_failed(self):
        """0% success rate when all deliveries fail."""
        endpoint = self._create_endpoint()
        endpoint.record_delivery(success=False)
        endpoint.record_delivery(success=False)
        endpoint.refresh_from_db()

        assert endpoint.success_rate == 0

    def test_webhook_endpoint_uuid_primary_key(self):
        """Endpoint should use UUID as primary key."""
        endpoint = self._create_endpoint()
        assert isinstance(endpoint.id, uuid.UUID)

    def test_webhook_endpoint_ordering(self):
        """Endpoints should be ordered by -created_at (newest first)."""
        ep1 = self._create_endpoint(url='https://example.com/1')
        ep2 = self._create_endpoint(url='https://example.com/2')

        endpoints = list(WebhookEndpoint.objects.all())
        assert endpoints[0].url == 'https://example.com/2'
        assert endpoints[1].url == 'https://example.com/1'

    def test_webhook_endpoint_custom_headers(self):
        """Endpoint should store custom headers."""
        endpoint = self._create_endpoint(
            headers={'Authorization': 'Bearer token', 'X-Custom': 'value'}
        )

        assert endpoint.headers['Authorization'] == 'Bearer token'
        assert endpoint.headers['X-Custom'] == 'value'

    def test_webhook_endpoint_inactive(self):
        """Inactive endpoints should be creatable and queryable."""
        endpoint = self._create_endpoint(is_active=False)

        assert endpoint.is_active is False
        assert WebhookEndpoint.objects.filter(is_active=False).count() == 1
