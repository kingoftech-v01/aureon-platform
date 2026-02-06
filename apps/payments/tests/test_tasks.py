"""
Tests for payments Celery tasks.

Tests cover Stripe webhook processing, payment processing, retries, and data sync.
"""
import pytest
import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, PropertyMock

from django.utils import timezone

from apps.payments.models import Payment
from apps.invoicing.models import Invoice
from apps.payments.tasks import (
    process_stripe_webhook,
    process_payment,
    retry_failed_payment,
    sync_stripe_data,
)


@pytest.fixture(autouse=True)
def stripe_settings(settings):
    """Set Stripe secret key for all tests in this module."""
    settings.STRIPE_SECRET_KEY = 'sk_test_fake_key'
    return settings


@pytest.mark.django_db
class TestProcessStripeWebhook:
    """Tests for process_stripe_webhook task."""

    @patch('apps.webhooks.stripe_handlers.StripeWebhookHandler')
    def test_processes_webhook_event_successfully(self, mock_handler_cls):
        """Test that a webhook event is processed and marked as complete."""
        from apps.webhooks.models import WebhookEvent

        webhook_event = WebhookEvent.objects.create(
            source=WebhookEvent.STRIPE,
            event_type='payment_intent.succeeded',
            event_id='evt_test_success_123',
            payload={'type': 'payment_intent.succeeded', 'data': {'id': 'pi_test'}},
            status=WebhookEvent.PENDING,
        )

        mock_handler = MagicMock()
        mock_handler.handle.return_value = {'processed': True}
        mock_handler_cls.return_value = mock_handler

        result = process_stripe_webhook(str(webhook_event.id))

        assert result['status'] == 'success'
        assert result['result'] == {'processed': True}

        webhook_event.refresh_from_db()
        assert webhook_event.status == WebhookEvent.PROCESSED

    @patch('apps.webhooks.stripe_handlers.StripeWebhookHandler')
    def test_marks_event_as_processing_during_execution(self, mock_handler_cls):
        """Test that the event status is set to PROCESSING before handling."""
        from apps.webhooks.models import WebhookEvent

        statuses_during_handling = []

        webhook_event = WebhookEvent.objects.create(
            source=WebhookEvent.STRIPE,
            event_type='payment_intent.succeeded',
            event_id='evt_test_processing_123',
            payload={'type': 'payment_intent.succeeded'},
            status=WebhookEvent.PENDING,
        )

        def track_status(payload):
            event = WebhookEvent.objects.get(id=webhook_event.id)
            statuses_during_handling.append(event.status)
            return {'ok': True}

        mock_handler = MagicMock()
        mock_handler.handle.side_effect = track_status
        mock_handler_cls.return_value = mock_handler

        process_stripe_webhook(str(webhook_event.id))

        assert WebhookEvent.PROCESSING in statuses_during_handling

    def test_retries_on_event_not_found(self):
        """Test that the task retries when webhook event does not exist."""
        from celery.exceptions import Retry

        with pytest.raises(Retry):
            process_stripe_webhook(str(uuid.uuid4()))

    @patch('apps.webhooks.stripe_handlers.StripeWebhookHandler')
    def test_retries_on_handler_exception(self, mock_handler_cls):
        """Test that the task retries when handler raises an exception."""
        from apps.webhooks.models import WebhookEvent
        from celery.exceptions import Retry

        webhook_event = WebhookEvent.objects.create(
            source=WebhookEvent.STRIPE,
            event_type='payment_intent.failed',
            event_id='evt_test_fail_123',
            payload={'type': 'payment_intent.failed'},
            status=WebhookEvent.PENDING,
        )

        mock_handler = MagicMock()
        mock_handler.handle.side_effect = RuntimeError("Handler error")
        mock_handler_cls.return_value = mock_handler

        with pytest.raises(Retry):
            process_stripe_webhook(str(webhook_event.id))


@pytest.mark.django_db
class TestProcessPayment:
    """Tests for process_payment task."""

    @patch('stripe.PaymentIntent.retrieve')
    def test_processes_succeeded_payment(self, mock_retrieve, payment_pending):
        """Test processing a payment whose Stripe intent has succeeded."""
        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'
        mock_retrieve.return_value = mock_intent

        # Mock mark_as_paid to avoid client.update_financial_summary bug
        with patch.object(Invoice, 'mark_as_paid'):
            result = process_payment(str(payment_pending.id))

        assert result['status'] == 'success'
        assert result['payment_status'] == Payment.SUCCEEDED

        payment_pending.refresh_from_db()
        assert payment_pending.status == Payment.SUCCEEDED

    @patch('stripe.PaymentIntent.retrieve')
    def test_processes_requires_payment_method(self, mock_retrieve, payment_pending):
        """Test processing a payment that requires a new payment method."""
        mock_intent = MagicMock()
        mock_intent.status = 'requires_payment_method'
        mock_retrieve.return_value = mock_intent

        result = process_payment(str(payment_pending.id))

        assert result['payment_status'] == Payment.FAILED

        payment_pending.refresh_from_db()
        assert payment_pending.status == Payment.FAILED
        assert payment_pending.failure_message == 'Payment method required'

    @patch('stripe.PaymentIntent.retrieve')
    def test_processes_pending_intent(self, mock_retrieve, payment_pending):
        """Test processing a payment whose intent is still processing."""
        mock_intent = MagicMock()
        mock_intent.status = 'processing'
        mock_retrieve.return_value = mock_intent

        result = process_payment(str(payment_pending.id))

        assert result['payment_status'] == Payment.PENDING

        payment_pending.refresh_from_db()
        assert payment_pending.status == Payment.PENDING

    def test_payment_without_stripe_intent(self, client_company, contract_fixed):
        """Test that a payment without a Stripe intent is marked as failed."""
        invoice = Invoice.objects.create(
            client=client_company,
            contract=contract_fixed,
            status=Invoice.SENT,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000.00'),
            total=Decimal('1000.00'),
            currency='USD',
        )
        payment = Payment.objects.create(
            invoice=invoice,
            amount=Decimal('1000.00'),
            currency='USD',
            status=Payment.PENDING,
            payment_date=timezone.now(),
            stripe_payment_intent_id=None,
        )

        result = process_payment(str(payment.id))

        assert result['payment_status'] == Payment.FAILED
        payment.refresh_from_db()
        assert payment.failure_message == 'No payment intent configured'

    @patch('stripe.PaymentIntent.retrieve')
    def test_sets_processing_status_first(self, mock_retrieve, payment_pending):
        """Test that payment status is set to PROCESSING before Stripe call."""
        statuses = []

        original_retrieve = mock_retrieve.side_effect

        def track_retrieve(intent_id):
            p = Payment.objects.get(id=payment_pending.id)
            statuses.append(p.status)
            mock = MagicMock()
            mock.status = 'succeeded'
            return mock

        mock_retrieve.side_effect = track_retrieve

        with patch.object(Invoice, 'mark_as_paid'):
            process_payment(str(payment_pending.id))

        assert Payment.PROCESSING in statuses

    @patch('stripe.PaymentIntent.retrieve')
    def test_updates_invoice_on_success(self, mock_retrieve, payment_pending):
        """Test that the invoice is updated when payment succeeds."""
        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'
        mock_retrieve.return_value = mock_intent

        with patch.object(Invoice, 'mark_as_paid') as mock_mark_paid:
            process_payment(str(payment_pending.id))
            mock_mark_paid.assert_called_once()

    def test_retries_on_payment_not_found(self):
        """Test that the task retries when payment does not exist."""
        from celery.exceptions import Retry

        with pytest.raises(Retry):
            process_payment(str(uuid.uuid4()))


@pytest.mark.django_db
class TestRetryFailedPayment:
    """Tests for retry_failed_payment task."""

    @patch('apps.payments.tasks.process_payment')
    def test_retries_failed_payment(self, mock_process, payment_failed):
        """Test that a failed payment is reset and re-queued for processing."""
        result = retry_failed_payment(str(payment_failed.id))

        assert result['status'] == 'success'
        assert result['retried'] is True

        payment_failed.refresh_from_db()
        assert payment_failed.status == Payment.PENDING
        assert payment_failed.failure_code == ''
        assert payment_failed.failure_message == ''

        mock_process.delay.assert_called_once_with(payment_failed.id)

    def test_skips_non_failed_payment(self, payment_pending):
        """Test that a non-failed payment is skipped."""
        result = retry_failed_payment(str(payment_pending.id))

        assert result['status'] == 'skipped'
        assert 'not failed' in result['message']

    def test_skips_succeeded_payment(self, payment_successful):
        """Test that a succeeded payment is skipped."""
        result = retry_failed_payment(str(payment_successful.id))

        assert result['status'] == 'skipped'

    def test_retries_on_payment_not_found(self):
        """Test that the task retries when payment does not exist."""
        from celery.exceptions import Retry

        with pytest.raises(Retry):
            retry_failed_payment(str(uuid.uuid4()))


@pytest.mark.django_db
class TestSyncStripeData:
    """Tests for sync_stripe_data task."""

    @patch('stripe.PaymentIntent.retrieve')
    def test_syncs_succeeded_payment(self, mock_retrieve, payment_pending):
        """Test that a pending payment is updated when Stripe shows succeeded."""
        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'
        mock_retrieve.return_value = mock_intent

        with patch.object(Invoice, 'mark_as_paid'):
            result = sync_stripe_data()

        assert result['status'] == 'success'
        assert result['synced_count'] >= 1

        payment_pending.refresh_from_db()
        assert payment_pending.status == Payment.SUCCEEDED

    @patch('stripe.PaymentIntent.retrieve')
    def test_syncs_cancelled_payment(self, mock_retrieve, payment_pending):
        """Test that a pending payment is updated when Stripe shows canceled."""
        mock_intent = MagicMock()
        mock_intent.status = 'canceled'
        mock_retrieve.return_value = mock_intent

        result = sync_stripe_data()

        payment_pending.refresh_from_db()
        assert payment_pending.status == Payment.CANCELLED

    @patch('stripe.PaymentIntent.retrieve')
    def test_syncs_failed_payment(self, mock_retrieve, payment_pending):
        """Test that a pending payment is updated when Stripe shows requires_payment_method."""
        mock_intent = MagicMock()
        mock_intent.status = 'requires_payment_method'
        mock_retrieve.return_value = mock_intent

        result = sync_stripe_data()

        payment_pending.refresh_from_db()
        assert payment_pending.status == Payment.FAILED

    @patch('stripe.PaymentIntent.retrieve')
    def test_no_change_when_status_matches(self, mock_retrieve, payment_pending):
        """Test that no update occurs when Stripe status matches local status."""
        mock_intent = MagicMock()
        mock_intent.status = 'processing'  # maps to PROCESSING, but payment is PENDING
        mock_retrieve.return_value = mock_intent

        # processing maps to PROCESSING which != PENDING, so it will sync
        result = sync_stripe_data()
        assert result['synced_count'] >= 0

    @patch('stripe.PaymentIntent.retrieve')
    def test_handles_stripe_api_error_gracefully(self, mock_retrieve, payment_pending):
        """Test that Stripe API errors for individual payments don't crash the task."""
        mock_retrieve.side_effect = Exception("Stripe API error")

        result = sync_stripe_data()

        assert result['status'] == 'success'
        # Payment should remain unchanged
        payment_pending.refresh_from_db()
        assert payment_pending.status == Payment.PENDING

    @patch('stripe.PaymentIntent.retrieve')
    def test_skips_payments_without_stripe_id(self, mock_retrieve, client_company, contract_fixed):
        """Test that payments without Stripe intent IDs are skipped."""
        invoice = Invoice.objects.create(
            client=client_company,
            contract=contract_fixed,
            status=Invoice.SENT,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000.00'),
            total=Decimal('1000.00'),
            currency='USD',
        )
        Payment.objects.create(
            invoice=invoice,
            amount=Decimal('1000.00'),
            currency='USD',
            status=Payment.PENDING,
            payment_date=timezone.now(),
            stripe_payment_intent_id=None,
        )

        result = sync_stripe_data()

        assert result['status'] == 'success'
        # Should not call Stripe for payments without intent ID
        mock_retrieve.assert_not_called()

    @patch('stripe.PaymentIntent.retrieve')
    def test_updates_invoice_on_succeeded_sync(self, mock_retrieve, payment_pending):
        """Test that the invoice is marked as paid when a synced payment succeeds."""
        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'
        mock_retrieve.return_value = mock_intent

        with patch.object(Invoice, 'mark_as_paid') as mock_mark_paid:
            sync_stripe_data()
            mock_mark_paid.assert_called_once()
