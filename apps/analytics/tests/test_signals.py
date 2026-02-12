"""
Tests for analytics signal handlers.

Tests verify that model save signals trigger activity logging.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.utils import timezone

from apps.analytics.models import ActivityLog


@pytest.mark.django_db
class TestContractCreationSignal:
    """Tests for the contract post_save signal handler."""

    def test_logs_activity_on_contract_creation(self, client_company, admin_user):
        """Test that creating a contract logs a 'contract_created' activity."""
        from apps.contracts.models import Contract

        initial_count = ActivityLog.objects.filter(activity_type='contract_created').count()

        Contract.objects.create(
            client=client_company,
            title='Signal Test Contract',
            description='Testing signal.',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.DRAFT,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            value=Decimal('1000.00'),
            currency='USD',
            owner=admin_user,
        )

        new_count = ActivityLog.objects.filter(activity_type='contract_created').count()
        assert new_count == initial_count + 1

    def test_contract_creation_log_has_description(self, client_company, admin_user):
        """Test that the contract creation activity log includes the contract number."""
        from apps.contracts.models import Contract

        contract = Contract.objects.create(
            client=client_company,
            title='Signal Description Test',
            description='Testing.',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.DRAFT,
            start_date=date.today(),
            value=Decimal('1000.00'),
            currency='USD',
            owner=admin_user,
        )

        activity = ActivityLog.objects.filter(
            activity_type='contract_created'
        ).order_by('-created_at').first()

        assert contract.contract_number in activity.description

    def test_contract_update_does_not_log_creation(self, contract_fixed):
        """Test that updating a contract does not log a 'contract_created' activity."""
        initial_count = ActivityLog.objects.filter(activity_type='contract_created').count()

        contract_fixed.title = 'Updated Title'
        contract_fixed.save()

        new_count = ActivityLog.objects.filter(activity_type='contract_created').count()
        assert new_count == initial_count

    def test_signed_contract_update_logs_signed_activity(self, contract_fixed):
        """Test that a signed active contract logs a 'contract_signed' activity."""
        # contract_fixed is already ACTIVE and signed
        initial_count = ActivityLog.objects.filter(activity_type='contract_signed').count()

        # Trigger a save on the already signed contract
        contract_fixed.notes = 'Updated notes'
        contract_fixed.save()

        new_count = ActivityLog.objects.filter(activity_type='contract_signed').count()
        assert new_count == initial_count + 1


@pytest.mark.django_db
class TestInvoiceCreationSignal:
    """Tests for the invoice post_save signal handler."""

    def test_logs_activity_on_invoice_creation(self, client_company, contract_fixed):
        """Test that creating an invoice logs an 'invoice_created' activity."""
        from apps.invoicing.models import Invoice

        initial_count = ActivityLog.objects.filter(activity_type='invoice_created').count()

        Invoice.objects.create(
            client=client_company,
            contract=contract_fixed,
            status=Invoice.DRAFT,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000.00'),
            total=Decimal('1000.00'),
            currency='USD',
        )

        new_count = ActivityLog.objects.filter(activity_type='invoice_created').count()
        assert new_count == initial_count + 1

    def test_invoice_creation_log_contains_invoice_number(
        self, client_company, contract_fixed
    ):
        """Test that the activity log description includes the invoice number."""
        from apps.invoicing.models import Invoice

        invoice = Invoice.objects.create(
            client=client_company,
            contract=contract_fixed,
            status=Invoice.DRAFT,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('500.00'),
            total=Decimal('500.00'),
            currency='USD',
        )

        activity = ActivityLog.objects.filter(
            activity_type='invoice_created'
        ).order_by('-created_at').first()

        assert invoice.invoice_number in activity.description

    def test_paid_invoice_update_logs_paid_activity(self, invoice_draft):
        """Test that marking an invoice as paid logs an 'invoice_paid' activity."""
        from apps.invoicing.models import Invoice

        initial_count = ActivityLog.objects.filter(activity_type='invoice_paid').count()

        invoice_draft.status = 'paid'
        invoice_draft.save()

        new_count = ActivityLog.objects.filter(activity_type='invoice_paid').count()
        assert new_count == initial_count + 1

    def test_non_paid_update_does_not_log_paid(self, invoice_draft):
        """Test that a non-paid status update does not log 'invoice_paid'."""
        initial_count = ActivityLog.objects.filter(activity_type='invoice_paid').count()

        invoice_draft.status = 'sent'
        invoice_draft.save()

        new_count = ActivityLog.objects.filter(activity_type='invoice_paid').count()
        assert new_count == initial_count


@pytest.mark.django_db
class TestPaymentActivitySignal:
    """Tests for the payment post_save signal handler."""

    def test_logs_activity_on_succeeded_payment(self, invoice_sent):
        """Test that a succeeded payment logs a 'payment_received' activity."""
        from apps.payments.models import Payment

        initial_count = ActivityLog.objects.filter(activity_type='payment_received').count()

        Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('8100.00'),
            currency='USD',
            payment_method=Payment.CARD,
            status='succeeded',
            payment_date=timezone.now(),
        )

        new_count = ActivityLog.objects.filter(activity_type='payment_received').count()
        assert new_count == initial_count + 1

    def test_does_not_log_for_pending_payment(self, invoice_sent):
        """Test that a pending payment does not log 'payment_received'."""
        from apps.payments.models import Payment

        initial_count = ActivityLog.objects.filter(activity_type='payment_received').count()

        Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('100.00'),
            currency='USD',
            payment_method=Payment.CARD,
            status=Payment.PENDING,
            payment_date=timezone.now(),
        )

        new_count = ActivityLog.objects.filter(activity_type='payment_received').count()
        assert new_count == initial_count

    def test_does_not_log_for_failed_payment(self, invoice_sent):
        """Test that a failed payment does not log 'payment_received'."""
        from apps.payments.models import Payment

        initial_count = ActivityLog.objects.filter(activity_type='payment_received').count()

        Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('100.00'),
            currency='USD',
            payment_method=Payment.CARD,
            status=Payment.FAILED,
            payment_date=timezone.now(),
        )

        new_count = ActivityLog.objects.filter(activity_type='payment_received').count()
        assert new_count == initial_count

    def test_payment_received_log_includes_amount(self, invoice_sent):
        """Test that the activity log for payment includes the amount."""
        from apps.payments.models import Payment

        Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('9999.99'),
            currency='EUR',
            payment_method=Payment.CARD,
            status='succeeded',
            payment_date=timezone.now(),
        )

        activity = ActivityLog.objects.filter(
            activity_type='payment_received'
        ).order_by('-created_at').first()

        assert '9999.99' in activity.description
        assert 'EUR' in activity.description


# =============================================================================
# Exception Handling Tests (covers lines 25-26, 44-45, 58-59)
# =============================================================================

@pytest.mark.django_db
class TestContractSignalExceptionHandling:
    """Tests for exception handling in the contract post_save signal (lines 25-26)."""

    def test_contract_signal_handles_activity_logger_exception(self, client_company, admin_user):
        """When ActivityLogger.log_activity raises, the signal should not propagate the error."""
        from apps.contracts.models import Contract

        with patch(
            'apps.analytics.services.ActivityLogger.log_activity',
            side_effect=Exception('Logger service unavailable'),
        ):
            # Creating a contract should succeed even if the signal handler fails
            contract = Contract.objects.create(
                client=client_company,
                title='Signal Exception Test Contract',
                description='Testing.',
                contract_type=Contract.FIXED_PRICE,
                status=Contract.DRAFT,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                value=Decimal('1000.00'),
                currency='USD',
                owner=admin_user,
            )

        assert contract.pk is not None


@pytest.mark.django_db
class TestInvoiceSignalExceptionHandling:
    """Tests for exception handling in the invoice post_save signal (lines 44-45)."""

    def test_invoice_signal_handles_activity_logger_exception(self, client_company, contract_fixed):
        """When ActivityLogger.log_activity raises, the signal should not propagate the error."""
        from apps.invoicing.models import Invoice

        with patch(
            'apps.analytics.services.ActivityLogger.log_activity',
            side_effect=Exception('Logger service unavailable'),
        ):
            invoice = Invoice.objects.create(
                client=client_company,
                contract=contract_fixed,
                status=Invoice.DRAFT,
                issue_date=date.today(),
                due_date=date.today() + timedelta(days=30),
                subtotal=Decimal('1000.00'),
                total=Decimal('1000.00'),
                currency='USD',
            )

        assert invoice.pk is not None

    def test_invoice_paid_signal_handles_activity_logger_exception(self, invoice_draft):
        """When ActivityLogger raises on invoice paid update, the signal should not propagate."""
        with patch(
            'apps.analytics.services.ActivityLogger.log_activity',
            side_effect=Exception('Logger service unavailable'),
        ):
            invoice_draft.status = 'paid'
            invoice_draft.save()

        invoice_draft.refresh_from_db()
        assert invoice_draft.status == 'paid'


@pytest.mark.django_db
class TestPaymentSignalExceptionHandling:
    """Tests for exception handling in the payment post_save signal (lines 58-59)."""

    def test_payment_signal_handles_activity_logger_exception(self, invoice_sent):
        """When ActivityLogger.log_activity raises, the signal should not propagate the error."""
        from apps.payments.models import Payment

        with patch(
            'apps.analytics.services.ActivityLogger.log_activity',
            side_effect=Exception('Logger service unavailable'),
        ):
            payment = Payment.objects.create(
                invoice=invoice_sent,
                amount=Decimal('100.00'),
                currency='USD',
                payment_method=Payment.CARD,
                status='succeeded',
                payment_date=timezone.now(),
            )

        assert payment.pk is not None
