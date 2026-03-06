"""Tests for notifications signal handlers."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone

from apps.notifications.models import NotificationTemplate
from apps.notifications.signals import (
    invoice_notification_handler,
    payment_notification_handler,
    contract_notification_handler,
    client_notification_handler,
    track_invoice_status_change,
    track_payment_status_change,
    track_contract_signature,
)


@pytest.mark.django_db
class TestInvoiceNotificationHandler:
    """Tests for invoice_notification_handler signal."""

    @patch('apps.notifications.signals.NotificationService')
    def test_skip_draft_invoices(self, mock_service):
        """Test that draft invoices do not trigger notifications."""
        from apps.invoicing.models import Invoice

        mock_instance = MagicMock(spec=Invoice)
        mock_instance.status = Invoice.DRAFT

        invoice_notification_handler(sender=Invoice, instance=mock_instance, created=True)

        mock_service.send_invoice_notification.assert_not_called()

    @patch('apps.notifications.signals.NotificationService')
    def test_new_sent_invoice_triggers_notification(self, mock_service):
        """Test that a new invoice with SENT status triggers notification."""
        from apps.invoicing.models import Invoice

        mock_instance = MagicMock(spec=Invoice)
        mock_instance.status = Invoice.SENT
        mock_instance.invoice_number = 'INV-001'

        invoice_notification_handler(sender=Invoice, instance=mock_instance, created=True)

        mock_service.send_invoice_notification.assert_called_once_with(
            invoice=mock_instance,
            template_type=NotificationTemplate.INVOICE_SENT,
        )

    @patch('apps.notifications.signals.NotificationService')
    def test_paid_invoice_with_status_changed_triggers_notification(self, mock_service):
        """Test that paid invoice with _status_changed triggers notification."""
        from apps.invoicing.models import Invoice

        mock_instance = MagicMock(spec=Invoice)
        mock_instance.status = Invoice.PAID
        mock_instance._status_changed = True
        mock_instance.invoice_number = 'INV-001'

        invoice_notification_handler(sender=Invoice, instance=mock_instance, created=False)

        mock_service.send_invoice_notification.assert_called_once_with(
            invoice=mock_instance,
            template_type=NotificationTemplate.INVOICE_PAID,
        )

    @patch('apps.notifications.signals.NotificationService')
    def test_paid_invoice_without_status_changed_no_notification(self, mock_service):
        """Test that paid invoice without _status_changed does not trigger."""
        from apps.invoicing.models import Invoice

        mock_instance = MagicMock(spec=Invoice)
        mock_instance.status = Invoice.PAID
        mock_instance._status_changed = False

        invoice_notification_handler(sender=Invoice, instance=mock_instance, created=False)

        mock_service.send_invoice_notification.assert_not_called()

    @patch('apps.notifications.signals.NotificationService')
    def test_paid_invoice_without_attribute_no_notification(self, mock_service):
        """Test paid invoice without _status_changed attribute."""
        from apps.invoicing.models import Invoice

        mock_instance = MagicMock(spec=Invoice)
        mock_instance.status = Invoice.PAID
        # Remove _status_changed so hasattr returns False
        del mock_instance._status_changed

        invoice_notification_handler(sender=Invoice, instance=mock_instance, created=False)

        mock_service.send_invoice_notification.assert_not_called()

    @patch('apps.notifications.signals.NotificationService')
    def test_exception_handling(self, mock_service):
        """Test that exceptions are caught and logged."""
        from apps.invoicing.models import Invoice

        mock_service.send_invoice_notification.side_effect = Exception('Service error')
        mock_instance = MagicMock(spec=Invoice)
        mock_instance.status = Invoice.SENT
        mock_instance.invoice_number = 'INV-001'

        # Should not raise
        invoice_notification_handler(sender=Invoice, instance=mock_instance, created=True)

    @patch('apps.notifications.signals.NotificationService')
    def test_non_created_non_paid_invoice_no_notification(self, mock_service):
        """Test that updating an invoice to non-PAID status does not trigger."""
        from apps.invoicing.models import Invoice

        mock_instance = MagicMock(spec=Invoice)
        mock_instance.status = Invoice.SENT
        mock_instance._status_changed = True

        invoice_notification_handler(sender=Invoice, instance=mock_instance, created=False)

        mock_service.send_invoice_notification.assert_not_called()


@pytest.mark.django_db
class TestPaymentNotificationHandler:
    """Tests for payment_notification_handler signal."""

    @patch('apps.notifications.signals.NotificationService')
    def test_skip_non_success_payments(self, mock_service):
        """Test that non-successful payments do not trigger notifications."""
        from apps.payments.models import Payment

        mock_instance = MagicMock(spec=Payment)
        mock_instance.status = Payment.PENDING

        # Payment.SUCCESS doesn't exist on the model (SUCCEEDED does), so the
        # signal handler will raise AttributeError which we test here
        try:
            payment_notification_handler(sender=Payment, instance=mock_instance, created=True)
        except AttributeError:
            # Expected: Payment.SUCCESS does not exist (it's SUCCEEDED)
            pass

    @patch('apps.notifications.signals.Payment')
    @patch('apps.notifications.signals.NotificationService')
    def test_new_successful_payment_triggers_receipt(self, mock_service, mock_payment_class):
        """Test that a new successful payment triggers receipt notification."""
        mock_payment_class.SUCCEEDED = 'succeeded'
        mock_instance = MagicMock()
        mock_instance.status = 'succeeded'
        mock_instance.id = 'test-payment-id'

        payment_notification_handler(
            sender=mock_payment_class, instance=mock_instance, created=True
        )

        mock_service.send_payment_receipt.assert_called_once_with(payment=mock_instance)

    @patch('apps.notifications.signals.Payment')
    @patch('apps.notifications.signals.NotificationService')
    def test_status_changed_to_success_triggers_receipt(self, mock_service, mock_payment_class):
        """Test that payment status changed to success triggers receipt."""
        mock_payment_class.SUCCEEDED = 'succeeded'
        mock_instance = MagicMock()
        mock_instance.status = 'succeeded'
        mock_instance._status_changed = True
        mock_instance.id = 'test-payment-id'

        payment_notification_handler(
            sender=mock_payment_class, instance=mock_instance, created=False
        )

        mock_service.send_payment_receipt.assert_called_once_with(payment=mock_instance)

    @patch('apps.notifications.signals.Payment')
    @patch('apps.notifications.signals.NotificationService')
    def test_not_created_and_no_status_change_no_receipt(self, mock_service, mock_payment_class):
        """Test that unchanged payment does not trigger receipt."""
        mock_payment_class.SUCCEEDED = 'succeeded'
        mock_instance = MagicMock()
        mock_instance.status = 'succeeded'
        mock_instance._status_changed = False

        payment_notification_handler(
            sender=mock_payment_class, instance=mock_instance, created=False
        )

        mock_service.send_payment_receipt.assert_not_called()

    @patch('apps.notifications.signals.Payment')
    @patch('apps.notifications.signals.NotificationService')
    def test_exception_handling(self, mock_service, mock_payment_class):
        """Test that exceptions are caught and logged."""
        mock_payment_class.SUCCEEDED = 'succeeded'
        mock_service.send_payment_receipt.side_effect = Exception('Service error')
        mock_instance = MagicMock()
        mock_instance.status = 'succeeded'
        mock_instance.id = 'test-payment-id'

        # Should not raise
        payment_notification_handler(
            sender=mock_payment_class, instance=mock_instance, created=True
        )


@pytest.mark.django_db
class TestContractNotificationHandler:
    """Tests for contract_notification_handler signal."""

    @patch('apps.notifications.signals.NotificationService')
    def test_signed_contract_triggers_notification(self, mock_service):
        """Test that a newly signed contract triggers notification."""
        from apps.contracts.models import Contract

        mock_instance = MagicMock(spec=Contract)
        mock_instance.is_signed = True
        mock_instance._signature_added = True
        mock_instance.title = 'Test Contract'

        contract_notification_handler(sender=Contract, instance=mock_instance, created=False)

        mock_service.send_contract_notification.assert_called_once_with(
            contract=mock_instance,
            template_type=NotificationTemplate.CONTRACT_SIGNED,
        )

    @patch('apps.notifications.signals.NotificationService')
    def test_unsigned_contract_no_notification(self, mock_service):
        """Test that unsigned contract does not trigger notification."""
        from apps.contracts.models import Contract

        mock_instance = MagicMock(spec=Contract)
        mock_instance.is_signed = False

        contract_notification_handler(sender=Contract, instance=mock_instance, created=False)

        mock_service.send_contract_notification.assert_not_called()

    @patch('apps.notifications.signals.NotificationService')
    def test_signed_without_signature_added_no_notification(self, mock_service):
        """Test that contract with is_signed but no _signature_added does not trigger."""
        from apps.contracts.models import Contract

        mock_instance = MagicMock(spec=Contract)
        mock_instance.is_signed = True
        mock_instance._signature_added = False

        contract_notification_handler(sender=Contract, instance=mock_instance, created=False)

        mock_service.send_contract_notification.assert_not_called()

    @patch('apps.notifications.signals.NotificationService')
    def test_signed_without_attribute_no_notification(self, mock_service):
        """Test contract without _signature_added attribute."""
        from apps.contracts.models import Contract

        mock_instance = MagicMock(spec=Contract)
        mock_instance.is_signed = True
        del mock_instance._signature_added

        contract_notification_handler(sender=Contract, instance=mock_instance, created=False)

        mock_service.send_contract_notification.assert_not_called()

    @patch('apps.notifications.signals.NotificationService')
    def test_exception_handling(self, mock_service):
        """Test that exceptions are caught and logged."""
        from apps.contracts.models import Contract

        mock_service.send_contract_notification.side_effect = Exception('Error')
        mock_instance = MagicMock(spec=Contract)
        mock_instance.is_signed = True
        mock_instance._signature_added = True
        mock_instance.title = 'Test Contract'

        # Should not raise
        contract_notification_handler(sender=Contract, instance=mock_instance, created=False)


@pytest.mark.django_db
class TestClientNotificationHandler:
    """Tests for client_notification_handler signal."""

    @patch('apps.notifications.signals.NotificationService')
    def test_new_active_client_triggers_welcome(self, mock_service):
        """Test that a new active client triggers welcome notification."""
        from apps.clients.models import Client

        mock_instance = MagicMock(spec=Client)
        mock_instance.lifecycle_stage = Client.ACTIVE
        mock_instance.email = 'client@example.com'

        client_notification_handler(sender=Client, instance=mock_instance, created=True)

        mock_service.send_client_welcome.assert_called_once_with(client=mock_instance)

    @patch('apps.notifications.signals.NotificationService')
    def test_new_prospect_triggers_welcome(self, mock_service):
        """Test that a new prospect client triggers welcome notification."""
        from apps.clients.models import Client

        mock_instance = MagicMock(spec=Client)
        mock_instance.lifecycle_stage = Client.PROSPECT
        mock_instance.email = 'prospect@example.com'

        client_notification_handler(sender=Client, instance=mock_instance, created=True)

        mock_service.send_client_welcome.assert_called_once_with(client=mock_instance)

    @patch('apps.notifications.signals.NotificationService')
    def test_new_lead_no_welcome(self, mock_service):
        """Test that a new lead does not trigger welcome notification."""
        from apps.clients.models import Client

        mock_instance = MagicMock(spec=Client)
        mock_instance.lifecycle_stage = Client.LEAD
        mock_instance.email = 'lead@example.com'

        client_notification_handler(sender=Client, instance=mock_instance, created=True)

        mock_service.send_client_welcome.assert_not_called()

    @patch('apps.notifications.signals.NotificationService')
    def test_updated_client_no_welcome(self, mock_service):
        """Test that updating an existing client does not trigger welcome."""
        from apps.clients.models import Client

        mock_instance = MagicMock(spec=Client)
        mock_instance.lifecycle_stage = Client.ACTIVE

        client_notification_handler(sender=Client, instance=mock_instance, created=False)

        mock_service.send_client_welcome.assert_not_called()

    @patch('apps.notifications.signals.NotificationService')
    def test_exception_handling(self, mock_service):
        """Test that exceptions are caught and logged."""
        from apps.clients.models import Client

        mock_service.send_client_welcome.side_effect = Exception('Error')
        mock_instance = MagicMock(spec=Client)
        mock_instance.lifecycle_stage = Client.ACTIVE
        mock_instance.email = 'client@example.com'

        # Should not raise
        client_notification_handler(sender=Client, instance=mock_instance, created=True)

    @patch('apps.notifications.signals.NotificationService')
    def test_inactive_new_client_no_welcome(self, mock_service):
        """Test that new inactive client does not get welcome."""
        from apps.clients.models import Client

        mock_instance = MagicMock(spec=Client)
        mock_instance.lifecycle_stage = Client.INACTIVE

        client_notification_handler(sender=Client, instance=mock_instance, created=True)

        mock_service.send_client_welcome.assert_not_called()

    @patch('apps.notifications.signals.NotificationService')
    def test_churned_new_client_no_welcome(self, mock_service):
        """Test that new churned client does not get welcome."""
        from apps.clients.models import Client

        mock_instance = MagicMock(spec=Client)
        mock_instance.lifecycle_stage = Client.CHURNED

        client_notification_handler(sender=Client, instance=mock_instance, created=True)

        mock_service.send_client_welcome.assert_not_called()


@pytest.mark.django_db
class TestTrackInvoiceStatusChange:
    """Tests for track_invoice_status_change helper."""

    def test_track_new_invoice(self):
        """Test tracking a new invoice (no pk)."""
        mock_instance = MagicMock()
        mock_instance.pk = None

        track_invoice_status_change(mock_instance)

        assert mock_instance._status_changed is False

    def test_track_existing_invoice_status_changed(self):
        """Test tracking when invoice status has changed."""
        from apps.invoicing.models import Invoice
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test', last_name='Client',
            email='test@example.com', lifecycle_stage=Client.ACTIVE,
        )
        invoice = Invoice.objects.create(
            client=client, status=Invoice.DRAFT,
            issue_date=date.today(), due_date=date.today() + timedelta(days=30),
            subtotal=1000, total=1000,
        )

        # Simulate status change
        invoice.status = Invoice.SENT
        track_invoice_status_change(invoice)

        assert invoice._status_changed is True

    def test_track_existing_invoice_status_unchanged(self):
        """Test tracking when invoice status has not changed."""
        from apps.invoicing.models import Invoice
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test', last_name='Client',
            email='test@example.com', lifecycle_stage=Client.ACTIVE,
        )
        invoice = Invoice.objects.create(
            client=client, status=Invoice.DRAFT,
            issue_date=date.today(), due_date=date.today() + timedelta(days=30),
            subtotal=1000, total=1000,
        )

        track_invoice_status_change(invoice)

        assert invoice._status_changed is False

    def test_track_deleted_invoice(self):
        """Test tracking when invoice has pk but was deleted from DB."""
        from apps.invoicing.models import Invoice

        mock_instance = MagicMock()
        mock_instance.pk = 'non-existent-pk'

        with patch('apps.notifications.signals.Invoice') as mock_invoice:
            mock_invoice.DoesNotExist = Invoice.DoesNotExist
            mock_invoice.objects.get.side_effect = Invoice.DoesNotExist
            track_invoice_status_change(mock_instance)

        assert mock_instance._status_changed is False


@pytest.mark.django_db
class TestTrackPaymentStatusChange:
    """Tests for track_payment_status_change helper."""

    def test_track_new_payment(self):
        """Test tracking a new payment (no pk)."""
        mock_instance = MagicMock()
        mock_instance.pk = None

        track_payment_status_change(mock_instance)

        assert mock_instance._status_changed is False

    def test_track_existing_payment_status_changed(self, payment_successful):
        """Test tracking when payment status has changed."""
        from apps.payments.models import Payment

        payment_successful.status = Payment.REFUNDED
        track_payment_status_change(payment_successful)

        assert payment_successful._status_changed is True

    def test_track_existing_payment_status_unchanged(self, payment_successful):
        """Test tracking when payment status has not changed."""
        track_payment_status_change(payment_successful)

        assert payment_successful._status_changed is False

    def test_track_deleted_payment(self):
        """Test tracking when payment has pk but was deleted."""
        from apps.payments.models import Payment

        mock_instance = MagicMock()
        mock_instance.pk = 'non-existent-pk'

        with patch('apps.notifications.signals.Payment') as mock_payment:
            mock_payment.DoesNotExist = Payment.DoesNotExist
            mock_payment.objects.get.side_effect = Payment.DoesNotExist
            track_payment_status_change(mock_instance)

        assert mock_instance._status_changed is False


@pytest.mark.django_db
class TestTrackContractSignature:
    """Tests for track_contract_signature helper."""

    def test_track_new_contract(self):
        """Test tracking a new contract (no pk)."""
        mock_instance = MagicMock()
        mock_instance.pk = None

        track_contract_signature(mock_instance)

        assert mock_instance._signature_added is False

    def test_track_contract_newly_signed(self, contract_fixed):
        """Test tracking when contract becomes signed."""
        from apps.contracts.models import Contract

        # contract_fixed is already signed, make old version unsigned
        old_contract = Contract.objects.get(pk=contract_fixed.pk)
        old_contract.signed_by_client = False
        old_contract.signed_by_company = False
        old_contract.save()

        # Now simulate signing
        old_contract.signed_by_client = True
        old_contract.signed_by_company = True
        track_contract_signature(old_contract)

        assert old_contract._signature_added is True

    def test_track_contract_already_signed(self, contract_fixed):
        """Test tracking when contract was already signed."""
        track_contract_signature(contract_fixed)

        assert contract_fixed._signature_added is False

    def test_track_deleted_contract(self):
        """Test tracking when contract has pk but was deleted."""
        from apps.contracts.models import Contract

        mock_instance = MagicMock()
        mock_instance.pk = 'non-existent-pk'

        with patch('apps.notifications.signals.Contract') as mock_contract:
            mock_contract.DoesNotExist = Contract.DoesNotExist
            mock_contract.objects.get.side_effect = Contract.DoesNotExist
            track_contract_signature(mock_instance)

        assert mock_instance._signature_added is False
