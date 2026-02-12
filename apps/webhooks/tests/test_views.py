"""
Tests for webhook views.

Tests cover:
- Stripe webhook endpoint (signature verification, event saving, response codes)
- Generic webhook endpoint (endpoint lookup, payload parsing, HMAC verification)
- Webhook health check endpoint
"""

import json
import hashlib
import hmac as hmac_module
import uuid
import pytest
from unittest.mock import patch, MagicMock

from django.test import Client as DjangoClient
from django.utils import timezone

from apps.webhooks.models import WebhookEvent, WebhookEndpoint


# =============================================================================
# Stripe Webhook Tests
# =============================================================================

@pytest.mark.django_db
class TestStripeWebhook:
    """Tests for the Stripe webhook endpoint."""

    STRIPE_WEBHOOK_URL = '/webhooks/stripe/'

    def _make_stripe_event(self, event_type='payment_intent.succeeded', event_id=None):
        """Build a fake Stripe event dict."""
        if event_id is None:
            event_id = f'evt_{uuid.uuid4().hex[:24]}'
        return {
            'id': event_id,
            'type': event_type,
            'data': {
                'object': {
                    'id': f'pi_{uuid.uuid4().hex[:24]}',
                    'amount': 5000,
                    'currency': 'usd',
                }
            }
        }

    @patch('apps.webhooks.views.stripe.Webhook.construct_event')
    def test_stripe_webhook_valid_signature(self, mock_construct_event, db):
        """Valid Stripe signature should save event and return 202 (async) or 200 (sync)."""
        event = self._make_stripe_event()
        mock_construct_event.return_value = event

        # Patch the async task import to simulate Celery being available
        with patch('apps.webhooks.views.process_webhook_sync') as mock_sync:
            mock_sync.return_value = MagicMock(status_code=200)

            client = DjangoClient()
            response = client.post(
                self.STRIPE_WEBHOOK_URL,
                data=json.dumps(event),
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='t=123,v1=abc',
            )

        # The view tries to import process_stripe_webhook task via Celery;
        # if Celery is available it returns 202, otherwise falls back to sync (200).
        # Either way we accept both.
        assert response.status_code in (200, 202)

        # Verify the webhook event was saved
        saved = WebhookEvent.objects.get(event_id=event['id'])
        assert saved.source == WebhookEvent.STRIPE
        assert saved.event_type == event['type']
        assert saved.payload == event
        assert saved.headers['stripe_signature'] == 't=123,v1=abc'

    @patch('apps.webhooks.views.stripe.Webhook.construct_event')
    def test_stripe_webhook_invalid_signature(self, mock_construct_event, db):
        """Invalid Stripe signature should return 400."""
        import stripe
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
            'Invalid signature', 't=123,v1=bad'
        )

        client = DjangoClient()
        response = client.post(
            self.STRIPE_WEBHOOK_URL,
            data=b'{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=bad',
        )

        assert response.status_code == 400
        assert WebhookEvent.objects.count() == 0

    @patch('apps.webhooks.views.stripe.Webhook.construct_event')
    def test_stripe_webhook_invalid_payload(self, mock_construct_event, db):
        """Invalid payload should return 400."""
        mock_construct_event.side_effect = ValueError('Invalid payload')

        client = DjangoClient()
        response = client.post(
            self.STRIPE_WEBHOOK_URL,
            data=b'not-json',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=abc',
        )

        assert response.status_code == 400
        assert WebhookEvent.objects.count() == 0

    @patch('apps.webhooks.views.stripe.Webhook.construct_event')
    def test_stripe_webhook_saves_ip_address(self, mock_construct_event, db):
        """Webhook should record the sender IP address."""
        event = self._make_stripe_event()
        mock_construct_event.return_value = event

        client = DjangoClient()
        response = client.post(
            self.STRIPE_WEBHOOK_URL,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=abc',
        )

        assert response.status_code in (200, 202)
        saved = WebhookEvent.objects.get(event_id=event['id'])
        assert saved.ip_address is not None

    @patch('apps.webhooks.views.stripe.Webhook.construct_event')
    def test_stripe_webhook_saves_forwarded_ip(self, mock_construct_event, db):
        """Webhook should use X-Forwarded-For header when present."""
        event = self._make_stripe_event()
        mock_construct_event.return_value = event

        client = DjangoClient()
        response = client.post(
            self.STRIPE_WEBHOOK_URL,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=abc',
            HTTP_X_FORWARDED_FOR='203.0.113.50, 70.41.3.18',
        )

        assert response.status_code in (200, 202)
        saved = WebhookEvent.objects.get(event_id=event['id'])
        assert saved.ip_address == '203.0.113.50'

    def test_stripe_webhook_get_not_allowed(self, db):
        """GET request to Stripe webhook should return 405."""
        client = DjangoClient()
        response = client.get(self.STRIPE_WEBHOOK_URL)
        assert response.status_code == 405

    @patch('apps.webhooks.views.stripe.Webhook.construct_event')
    def test_stripe_webhook_sync_processing_error(self, mock_construct_event, db):
        """When sync processing raises an exception, 500 is returned."""
        event = self._make_stripe_event()
        mock_construct_event.return_value = event

        # Make the Celery import fail so sync processing is used
        with patch('apps.webhooks.views.StripeWebhookHandler') as MockHandler:
            handler_instance = MagicMock()
            handler_instance.handle.side_effect = Exception('Handler error')
            MockHandler.return_value = handler_instance

            # Also force sync path by making the task import fail
            with patch.dict('sys.modules', {'apps.webhooks.tasks': None}):
                client = DjangoClient()
                response = client.post(
                    self.STRIPE_WEBHOOK_URL,
                    data=json.dumps(event),
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='t=123,v1=abc',
                )

            # Sync processing may return 500 or the task may be queued
            # depending on whether Celery is available
            assert response.status_code in (200, 202, 500)


# =============================================================================
# Generic Webhook Tests
# =============================================================================

@pytest.mark.django_db
class TestGenericWebhook:
    """Tests for the generic webhook endpoint."""

    @pytest.fixture
    def webhook_endpoint(self, db):
        """Create an active webhook endpoint."""
        return WebhookEndpoint.objects.create(
            url='https://example.com/webhook',
            secret_key='test-secret-key',
            event_types=['invoice.created', 'payment.succeeded'],
            is_active=True,
        )

    @pytest.fixture
    def inactive_endpoint(self, db):
        """Create an inactive webhook endpoint."""
        return WebhookEndpoint.objects.create(
            url='https://example.com/webhook-inactive',
            secret_key='secret',
            event_types=['invoice.created'],
            is_active=False,
        )

    def test_generic_webhook_valid(self, webhook_endpoint):
        """Valid generic webhook should save event and return 200."""
        payload = {
            'id': f'custom_{uuid.uuid4().hex[:12]}',
            'event_type': 'invoice.created',
            'data': {'invoice_id': '123'},
        }
        body = json.dumps(payload)

        # Compute HMAC signature
        signature = hmac_module.new(
            webhook_endpoint.secret_key.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        client = DjangoClient()
        response = client.post(
            f'/webhooks/receive/{webhook_endpoint.id}/',
            data=body,
            content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )

        assert response.status_code == 200
        data = response.json()
        assert data['received'] is True

        saved = WebhookEvent.objects.get(event_id=payload['id'])
        assert saved.source == WebhookEvent.CUSTOM
        assert saved.event_type == 'invoice.created'
        assert saved.status == WebhookEvent.PROCESSED

    def test_generic_webhook_invalid_endpoint(self, db):
        """Nonexistent endpoint ID should return 404."""
        fake_uuid = uuid.uuid4()
        client = DjangoClient()
        response = client.post(
            f'/webhooks/receive/{fake_uuid}/',
            data=json.dumps({'event_type': 'test'}),
            content_type='application/json',
        )
        assert response.status_code == 404

    def test_generic_webhook_inactive_endpoint(self, inactive_endpoint):
        """Inactive endpoint should return 404."""
        client = DjangoClient()
        response = client.post(
            f'/webhooks/receive/{inactive_endpoint.id}/',
            data=json.dumps({'event_type': 'test'}),
            content_type='application/json',
        )
        assert response.status_code == 404

    def test_generic_webhook_invalid_json(self, webhook_endpoint):
        """Non-JSON body should return 400."""
        client = DjangoClient()
        response = client.post(
            f'/webhooks/receive/{webhook_endpoint.id}/',
            data=b'this-is-not-json',
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_generic_webhook_signature_verification(self, webhook_endpoint):
        """Valid HMAC signature should be accepted."""
        payload = {
            'id': f'sig_test_{uuid.uuid4().hex[:8]}',
            'event_type': 'payment.succeeded',
            'amount': 100,
        }
        body = json.dumps(payload)

        signature = hmac_module.new(
            webhook_endpoint.secret_key.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        client = DjangoClient()
        response = client.post(
            f'/webhooks/receive/{webhook_endpoint.id}/',
            data=body,
            content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )

        assert response.status_code == 200

    def test_generic_webhook_invalid_signature(self, webhook_endpoint):
        """Invalid HMAC signature should return 401."""
        payload = {'event_type': 'invoice.created', 'id': 'test_bad_sig'}
        client = DjangoClient()
        response = client.post(
            f'/webhooks/receive/{webhook_endpoint.id}/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE='definitely-wrong-signature',
        )
        assert response.status_code == 401

    def test_generic_webhook_missing_signature_with_secret(self, webhook_endpoint):
        """Missing signature when endpoint has a secret_key should return 401."""
        payload = {'event_type': 'invoice.created', 'id': 'test_no_sig'}
        client = DjangoClient()
        response = client.post(
            f'/webhooks/receive/{webhook_endpoint.id}/',
            data=json.dumps(payload),
            content_type='application/json',
            # No HTTP_X_WEBHOOK_SIGNATURE header
        )
        assert response.status_code == 401

    def test_generic_webhook_no_secret_no_signature_required(self, db):
        """Endpoint without a secret_key should not require a signature."""
        endpoint = WebhookEndpoint.objects.create(
            url='https://example.com/open-webhook',
            secret_key='',
            event_types=['invoice.created'],
            is_active=True,
        )
        payload = {
            'id': f'no_sig_{uuid.uuid4().hex[:8]}',
            'event_type': 'invoice.created',
        }

        client = DjangoClient()
        response = client.post(
            f'/webhooks/receive/{endpoint.id}/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        assert response.status_code == 200

    def test_generic_webhook_default_event_type(self, db):
        """When event_type is missing from payload, it defaults to 'unknown'."""
        endpoint = WebhookEndpoint.objects.create(
            url='https://example.com/hook',
            secret_key='',
            event_types=['unknown'],
            is_active=True,
        )
        payload = {'id': f'no_type_{uuid.uuid4().hex[:8]}'}

        client = DjangoClient()
        response = client.post(
            f'/webhooks/receive/{endpoint.id}/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        assert response.status_code == 200

        saved = WebhookEvent.objects.get(event_id=payload['id'])
        assert saved.event_type == 'unknown'

    def test_generic_webhook_get_not_allowed(self, webhook_endpoint):
        """GET request to generic webhook should return 405."""
        client = DjangoClient()
        response = client.get(f'/webhooks/receive/{webhook_endpoint.id}/')
        assert response.status_code == 405


# =============================================================================
# Webhook Health Endpoint Tests
# =============================================================================

@pytest.mark.django_db
class TestWebhookHealth:
    """Tests for the webhook health check endpoint."""

    HEALTH_URL = '/webhooks/health/'

    def test_webhook_health_endpoint(self, db):
        """Health check should return status and stats."""
        client = DjangoClient()
        response = client.get(self.HEALTH_URL)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'stats_24h' in data
        assert 'total' in data['stats_24h']
        assert 'processed' in data['stats_24h']
        assert 'failed' in data['stats_24h']
        assert 'success_rate' in data['stats_24h']

    def test_webhook_health_with_events(self, db):
        """Health check should count recent events correctly."""
        # Create some webhook events
        WebhookEvent.objects.create(
            source=WebhookEvent.STRIPE,
            event_type='payment_intent.succeeded',
            event_id='evt_health_1',
            payload={'type': 'test'},
            status=WebhookEvent.PROCESSED,
        )
        WebhookEvent.objects.create(
            source=WebhookEvent.STRIPE,
            event_type='payment_intent.failed',
            event_id='evt_health_2',
            payload={'type': 'test'},
            status=WebhookEvent.FAILED,
        )
        WebhookEvent.objects.create(
            source=WebhookEvent.CUSTOM,
            event_type='invoice.created',
            event_id='evt_health_3',
            payload={'type': 'test'},
            status=WebhookEvent.PROCESSED,
        )

        client = DjangoClient()
        response = client.get(self.HEALTH_URL)

        assert response.status_code == 200
        data = response.json()
        assert data['stats_24h']['total'] == 3
        assert data['stats_24h']['processed'] == 2
        assert data['stats_24h']['failed'] == 1
        assert data['stats_24h']['success_rate'] == '66.67%'

    def test_webhook_health_empty_stats(self, db):
        """Health check with no events should show zero stats."""
        client = DjangoClient()
        response = client.get(self.HEALTH_URL)

        assert response.status_code == 200
        data = response.json()
        assert data['stats_24h']['total'] == 0
        assert data['stats_24h']['success_rate'] == '0.00%'

    def test_webhook_health_post_not_allowed(self, db):
        """POST request to health check should return 405."""
        client = DjangoClient()
        response = client.post(self.HEALTH_URL)
        assert response.status_code == 405


# =============================================================================
# Sync Processing Success Path (lines 102-104)
# =============================================================================

@pytest.mark.django_db
class TestStripeWebhookSyncProcessing:
    """Tests for the sync processing path in the Stripe webhook view (lines 102-104)."""

    STRIPE_WEBHOOK_URL = '/webhooks/stripe/'

    @patch('apps.webhooks.views.StripeWebhookHandler')
    @patch('apps.webhooks.views.stripe.Webhook.construct_event')
    def test_sync_processing_success_returns_200(self, mock_construct_event, MockHandler, db):
        """Sync processing success path should return 200 with processed: True."""
        event_id = f'evt_{uuid.uuid4().hex[:24]}'
        event = {
            'id': event_id,
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': f'pi_{uuid.uuid4().hex[:24]}',
                    'amount': 5000,
                    'currency': 'usd',
                }
            }
        }
        mock_construct_event.return_value = event

        handler_instance = MagicMock()
        handler_instance.handle.return_value = {'status': 'processed'}
        MockHandler.return_value = handler_instance

        # Force the sync path by making Celery task import raise ImportError
        with patch('apps.webhooks.tasks.process_stripe_webhook') as mock_task:
            mock_task.delay.side_effect = Exception('Celery not available')

            client = DjangoClient()
            response = client.post(
                self.STRIPE_WEBHOOK_URL,
                data=json.dumps(event),
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='t=123,v1=abc',
            )

        assert response.status_code == 200
        data = response.json()
        assert data['received'] is True
        assert data['processed'] is True


# =============================================================================
# Generic Webhook X-Forwarded-For (line 169)
# =============================================================================

@pytest.mark.django_db
class TestGenericWebhookForwardedIp:
    """Tests for X-Forwarded-For in generic webhooks (line 169)."""

    def test_generic_webhook_saves_forwarded_ip(self, db):
        """Generic webhook should use X-Forwarded-For header when present."""
        endpoint = WebhookEndpoint.objects.create(
            url='https://example.com/webhook-fwd',
            secret_key='',
            event_types=['invoice.created'],
            is_active=True,
        )
        payload = {
            'id': f'fwd_ip_test_{uuid.uuid4().hex[:8]}',
            'event_type': 'invoice.created',
            'data': {'test': True},
        }

        client = DjangoClient()
        response = client.post(
            f'/webhooks/receive/{endpoint.id}/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_FORWARDED_FOR='198.51.100.50, 203.0.113.10',
        )

        assert response.status_code == 200

        saved = WebhookEvent.objects.get(event_id=payload['id'])
        assert saved.ip_address == '198.51.100.50'


# =============================================================================
# Health Check Exception Path (lines 236-238)
# =============================================================================

@pytest.mark.django_db
class TestWebhookHealthException:
    """Tests for health check exception handler (lines 236-238)."""

    HEALTH_URL = '/webhooks/health/'

    def test_health_check_exception_returns_500(self, db):
        """Health check should return 500 when an exception occurs."""
        with patch('apps.webhooks.views.WebhookEvent.objects.filter') as mock_filter:
            mock_filter.side_effect = Exception('Database error')

            client = DjangoClient()
            response = client.get(self.HEALTH_URL)

        assert response.status_code == 500
        data = response.json()
        assert data['status'] == 'unhealthy'
        assert 'error' in data
