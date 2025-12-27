"""
Comprehensive unit tests for webhooks app.

Tests Stripe webhook processing, signature verification, and event handlers.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.conf import settings
from django.utils import timezone
import stripe

from .models import WebhookEvent, WebhookEndpoint
from .views import stripe_webhook, process_webhook_sync, generic_webhook
from .stripe_handlers import StripeWebhookHandler


class WebhookEventModelTests(TestCase):
    """Test WebhookEvent model methods."""

    def setUp(self):
        """Set up test data."""
        self.webhook_event = WebhookEvent.objects.create(
            source=WebhookEvent.STRIPE,
            event_type='payment_intent.succeeded',
            event_id='evt_test123',
            payload={'test': 'data'},
            headers={'stripe_signature': 'test_sig'},
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )

    def test_webhook_event_creation(self):
        """Test that webhook event is created correctly."""
        self.assertEqual(self.webhook_event.status, WebhookEvent.PENDING)
        self.assertEqual(self.webhook_event.source, WebhookEvent.STRIPE)
        self.assertEqual(self.webhook_event.event_type, 'payment_intent.succeeded')
        self.assertEqual(self.webhook_event.retry_count, 0)

    def test_mark_as_processing(self):
        """Test marking webhook as processing."""
        self.webhook_event.mark_as_processing()
        self.webhook_event.refresh_from_db()
        self.assertEqual(self.webhook_event.status, WebhookEvent.PROCESSING)

    def test_mark_as_processed(self):
        """Test marking webhook as successfully processed."""
        response_data = {'status': 'success'}
        self.webhook_event.mark_as_processed(response_data)
        self.webhook_event.refresh_from_db()

        self.assertEqual(self.webhook_event.status, WebhookEvent.PROCESSED)
        self.assertEqual(self.webhook_event.response_code, 200)
        self.assertEqual(self.webhook_event.response_body, response_data)
        self.assertIsNotNone(self.webhook_event.processed_at)

    def test_mark_as_failed_with_retry(self):
        """Test marking webhook as failed with retry enabled."""
        error_msg = 'Test error'
        self.webhook_event.mark_as_failed(error_msg, should_retry=True)
        self.webhook_event.refresh_from_db()

        self.assertEqual(self.webhook_event.status, WebhookEvent.RETRYING)
        self.assertEqual(self.webhook_event.error_message, error_msg)
        self.assertEqual(self.webhook_event.retry_count, 1)
        self.assertEqual(self.webhook_event.response_code, 500)

    def test_mark_as_failed_max_retries_exceeded(self):
        """Test marking webhook as failed when max retries exceeded."""
        self.webhook_event.retry_count = 3
        self.webhook_event.save()

        self.webhook_event.mark_as_failed('Max retries', should_retry=True)
        self.webhook_event.refresh_from_db()

        self.assertEqual(self.webhook_event.status, WebhookEvent.FAILED)

    def test_can_retry_property(self):
        """Test can_retry property logic."""
        self.webhook_event.status = WebhookEvent.FAILED
        self.assertTrue(self.webhook_event.can_retry)

        self.webhook_event.retry_count = 5
        self.assertFalse(self.webhook_event.can_retry)

    def test_is_stripe_event_property(self):
        """Test is_stripe_event property."""
        self.assertTrue(self.webhook_event.is_stripe_event)

        custom_event = WebhookEvent.objects.create(
            source=WebhookEvent.CUSTOM,
            event_type='test.event',
            event_id='custom_123',
            payload={}
        )
        self.assertFalse(custom_event.is_stripe_event)


class StripeWebhookSignatureVerificationTests(TestCase):
    """Test Stripe webhook signature verification."""

    def setUp(self):
        """Set up test request factory."""
        self.factory = RequestFactory()

    @patch('stripe.Webhook.construct_event')
    def test_webhook_signature_verification_success(self, mock_construct):
        """Test successful webhook signature verification."""
        # Mock Stripe event
        mock_event = {
            'id': 'evt_test123',
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_123'}}
        }
        mock_construct.return_value = mock_event

        # Create request
        request = self.factory.post(
            '/webhooks/stripe/',
            data=json.dumps(mock_event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        # Call view
        with patch('apps.webhooks.views.process_stripe_webhook') as mock_task:
            mock_task.delay.return_value = None
            response = stripe_webhook(request)

        # Verify
        self.assertEqual(response.status_code, 202)
        mock_construct.assert_called_once()

    @patch('stripe.Webhook.construct_event')
    def test_webhook_signature_verification_invalid_signature(self, mock_construct):
        """Test webhook with invalid signature."""
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            'Invalid signature', 'sig_header'
        )

        request = self.factory.post(
            '/webhooks/stripe/',
            data=b'{"test": "data"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )

        response = stripe_webhook(request)

        self.assertEqual(response.status_code, 400)

    @patch('stripe.Webhook.construct_event')
    def test_webhook_signature_verification_invalid_payload(self, mock_construct):
        """Test webhook with invalid payload."""
        mock_construct.side_effect = ValueError('Invalid payload')

        request = self.factory.post(
            '/webhooks/stripe/',
            data=b'invalid json',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        response = stripe_webhook(request)

        self.assertEqual(response.status_code, 400)


@pytest.mark.django_db
class StripeWebhookHandlerTests(TestCase):
    """Test Stripe webhook event handlers."""

    def setUp(self):
        """Set up test data."""
        from apps.payments.models import Payment
        from apps.invoicing.models import Invoice
        from apps.clients.models import Client
        from apps.tenants.models import Tenant

        # Create test tenant and client
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.client = Client.objects.create(
            tenant=self.tenant,
            email='client@example.com',
            first_name='Test',
            last_name='Client'
        )

    def test_handle_payment_intent_succeeded_new_payment(self):
        """Test handling successful payment intent for new payment."""
        event = {
            'id': 'evt_test123',
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_123456',
                    'amount': 10000,  # $100.00 in cents
                    'currency': 'usd'
                }
            }
        }

        handler = StripeWebhookHandler(event)
        result = handler.handle_payment_intent_succeeded()

        self.assertEqual(result['status'], 'processed')
        self.assertEqual(result['amount'], 100.00)

        from apps.payments.models import Payment
        payment = Payment.objects.get(stripe_payment_intent_id='pi_123456')
        self.assertEqual(payment.status, Payment.SUCCESS)
        self.assertEqual(payment.amount, Decimal('100.00'))

    def test_handle_payment_intent_succeeded_existing_payment(self):
        """Test handling successful payment intent for existing payment."""
        from apps.payments.models import Payment

        # Create existing payment
        payment = Payment.objects.create(
            client=self.client,
            stripe_payment_intent_id='pi_existing',
            amount=Decimal('50.00'),
            currency='USD',
            status=Payment.PENDING
        )

        event = {
            'id': 'evt_test456',
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_existing',
                    'amount': 5000,
                    'currency': 'usd'
                }
            }
        }

        handler = StripeWebhookHandler(event)
        result = handler.handle_payment_intent_succeeded()

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.SUCCESS)

    def test_handle_payment_intent_failed(self):
        """Test handling failed payment intent."""
        from apps.payments.models import Payment

        payment = Payment.objects.create(
            client=self.client,
            stripe_payment_intent_id='pi_failed',
            amount=Decimal('50.00'),
            currency='USD',
            status=Payment.PENDING
        )

        event = {
            'id': 'evt_test789',
            'type': 'payment_intent.payment_failed',
            'data': {
                'object': {
                    'id': 'pi_failed',
                    'last_payment_error': {
                        'message': 'Insufficient funds'
                    }
                }
            }
        }

        handler = StripeWebhookHandler(event)
        result = handler.handle_payment_intent_failed()

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.FAILED)
        self.assertEqual(payment.failure_reason, 'Insufficient funds')

    def test_handle_payment_intent_processing(self):
        """Test handling payment intent in processing state."""
        from apps.payments.models import Payment

        payment = Payment.objects.create(
            client=self.client,
            stripe_payment_intent_id='pi_processing',
            amount=Decimal('50.00'),
            currency='USD',
            status=Payment.PENDING
        )

        event = {
            'id': 'evt_processing',
            'type': 'payment_intent.processing',
            'data': {
                'object': {
                    'id': 'pi_processing'
                }
            }
        }

        handler = StripeWebhookHandler(event)
        result = handler.handle_payment_intent_processing()

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.PROCESSING)

    def test_handle_payment_intent_canceled(self):
        """Test handling canceled payment intent."""
        from apps.payments.models import Payment

        payment = Payment.objects.create(
            client=self.client,
            stripe_payment_intent_id='pi_canceled',
            amount=Decimal('50.00'),
            currency='USD',
            status=Payment.PENDING
        )

        event = {
            'id': 'evt_canceled',
            'type': 'payment_intent.canceled',
            'data': {
                'object': {
                    'id': 'pi_canceled'
                }
            }
        }

        handler = StripeWebhookHandler(event)
        result = handler.handle_payment_intent_canceled()

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.CANCELLED)

    def test_handle_charge_refunded(self):
        """Test handling charge refund."""
        from apps.payments.models import Payment

        payment = Payment.objects.create(
            client=self.client,
            stripe_charge_id='ch_refunded',
            amount=Decimal('100.00'),
            currency='USD',
            status=Payment.SUCCESS
        )

        event = {
            'id': 'evt_refund',
            'type': 'charge.refunded',
            'data': {
                'object': {
                    'id': 'ch_refunded',
                    'amount_refunded': 5000  # $50.00 in cents
                }
            }
        }

        handler = StripeWebhookHandler(event)
        result = handler.handle_charge_refunded()

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.REFUNDED)
        self.assertEqual(payment.refunded_amount, Decimal('50.00'))

    def test_handle_unknown_event_type(self):
        """Test handling unknown event type."""
        event = {
            'id': 'evt_unknown',
            'type': 'unknown.event.type',
            'data': {'object': {}}
        }

        handler = StripeWebhookHandler(event)
        result = handler.handle()

        self.assertEqual(result['status'], 'ignored')
        self.assertIn('No handler', result['message'])


class GenericWebhookTests(TestCase):
    """Test generic webhook endpoint."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.endpoint = WebhookEndpoint.objects.create(
            url='https://example.com/webhook',
            secret_key='test_secret',
            event_types=['invoice.created', 'payment.succeeded'],
            is_active=True
        )

    def test_generic_webhook_success(self):
        """Test successful generic webhook processing."""
        payload = {
            'event_type': 'invoice.created',
            'id': 'custom_123',
            'data': {'invoice_id': 'inv_123'}
        }

        request = self.factory.post(
            f'/webhooks/generic/{self.endpoint.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response = generic_webhook(request, self.endpoint.id)

        self.assertEqual(response.status_code, 200)

        # Verify webhook event was created
        webhook_event = WebhookEvent.objects.filter(
            source=WebhookEvent.CUSTOM,
            event_type='invoice.created'
        ).first()
        self.assertIsNotNone(webhook_event)
        self.assertEqual(webhook_event.status, WebhookEvent.PROCESSED)

    def test_generic_webhook_inactive_endpoint(self):
        """Test generic webhook with inactive endpoint."""
        self.endpoint.is_active = False
        self.endpoint.save()

        request = self.factory.post(
            f'/webhooks/generic/{self.endpoint.id}/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json'
        )

        response = generic_webhook(request, self.endpoint.id)
        self.assertEqual(response.status_code, 404)

    def test_generic_webhook_invalid_json(self):
        """Test generic webhook with invalid JSON."""
        request = self.factory.post(
            f'/webhooks/generic/{self.endpoint.id}/',
            data=b'invalid json',
            content_type='application/json'
        )

        response = generic_webhook(request, self.endpoint.id)
        self.assertEqual(response.status_code, 400)

    def test_generic_webhook_nonexistent_endpoint(self):
        """Test generic webhook with non-existent endpoint."""
        from uuid import uuid4

        request = self.factory.post(
            f'/webhooks/generic/{uuid4()}/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json'
        )

        response = generic_webhook(request, uuid4())
        self.assertEqual(response.status_code, 404)


class WebhookEndpointModelTests(TestCase):
    """Test WebhookEndpoint model methods."""

    def test_webhook_endpoint_creation(self):
        """Test creating webhook endpoint."""
        endpoint = WebhookEndpoint.objects.create(
            url='https://example.com/webhook',
            secret_key='test_secret',
            event_types=['invoice.created'],
            is_active=True
        )

        self.assertEqual(endpoint.total_deliveries, 0)
        self.assertEqual(endpoint.successful_deliveries, 0)
        self.assertEqual(endpoint.failed_deliveries, 0)

    def test_record_successful_delivery(self):
        """Test recording successful webhook delivery."""
        endpoint = WebhookEndpoint.objects.create(
            url='https://example.com/webhook',
            secret_key='test_secret',
            event_types=['invoice.created']
        )

        endpoint.record_delivery(success=True)
        endpoint.refresh_from_db()

        self.assertEqual(endpoint.total_deliveries, 1)
        self.assertEqual(endpoint.successful_deliveries, 1)
        self.assertEqual(endpoint.failed_deliveries, 0)
        self.assertIsNotNone(endpoint.last_delivery_at)
        self.assertIsNotNone(endpoint.last_success_at)

    def test_record_failed_delivery(self):
        """Test recording failed webhook delivery."""
        endpoint = WebhookEndpoint.objects.create(
            url='https://example.com/webhook',
            secret_key='test_secret',
            event_types=['invoice.created']
        )

        endpoint.record_delivery(success=False)
        endpoint.refresh_from_db()

        self.assertEqual(endpoint.total_deliveries, 1)
        self.assertEqual(endpoint.successful_deliveries, 0)
        self.assertEqual(endpoint.failed_deliveries, 1)
        self.assertIsNotNone(endpoint.last_delivery_at)
        self.assertIsNone(endpoint.last_success_at)

    def test_success_rate_calculation(self):
        """Test webhook endpoint success rate calculation."""
        endpoint = WebhookEndpoint.objects.create(
            url='https://example.com/webhook',
            secret_key='test_secret',
            event_types=['invoice.created']
        )

        # No deliveries = 0% success rate
        self.assertEqual(endpoint.success_rate, 0)

        # 3 successful, 1 failed = 75% success rate
        endpoint.record_delivery(success=True)
        endpoint.record_delivery(success=True)
        endpoint.record_delivery(success=True)
        endpoint.record_delivery(success=False)

        self.assertEqual(endpoint.success_rate, 75.0)


class WebhookHealthCheckTests(TestCase):
    """Test webhook health check endpoint."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

    def test_webhook_health_check_healthy(self):
        """Test health check returns healthy status."""
        from .views import webhook_health

        # Create some webhook events
        WebhookEvent.objects.create(
            source=WebhookEvent.STRIPE,
            event_type='test',
            event_id='evt_1',
            payload={},
            status=WebhookEvent.PROCESSED
        )

        request = self.factory.get('/webhooks/health/')
        response = webhook_health(request)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('stats_24h', data)

    @patch('apps.webhooks.views.connection')
    def test_webhook_health_check_unhealthy(self, mock_connection):
        """Test health check returns unhealthy status on database error."""
        from .views import webhook_health

        mock_connection.cursor.side_effect = Exception('Database error')

        request = self.factory.get('/webhooks/health/')
        response = webhook_health(request)

        self.assertEqual(response.status_code, 500)

        data = json.loads(response.content)
        self.assertEqual(data['status'], 'unhealthy')
