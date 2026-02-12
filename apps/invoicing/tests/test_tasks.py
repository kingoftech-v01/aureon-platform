"""
Tests for invoicing Celery tasks.

Tests cover PDF generation, email sending, recurring invoices, and payment reminders.
"""
import pytest
import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.utils import timezone

from apps.contracts.models import Contract
from apps.invoicing.models import Invoice
from apps.invoicing.tasks import (
    generate_invoice,
    send_invoice_email,
    generate_recurring_invoices,
    send_payment_reminders,
)


@pytest.mark.django_db
class TestGenerateInvoicePdf:
    """Tests for generate_invoice (PDF generation) task."""

    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_generates_pdf_and_saves_to_invoice(self, mock_doc_cls, invoice_draft, invoice_item):
        """Test that a PDF is generated and saved to the invoice's file field."""
        mock_doc = MagicMock()

        def build_effect(elements):
            buf = mock_doc_cls.call_args[0][0]
            buf.write(b'%PDF-1.4 invoice content')

        mock_doc.build.side_effect = build_effect
        mock_doc_cls.return_value = mock_doc

        result = generate_invoice(str(invoice_draft.id))

        assert result['status'] == 'success'
        assert result['invoice_id'] == str(invoice_draft.id)
        assert result['filename'] == f"{invoice_draft.invoice_number}.pdf"

        invoice_draft.refresh_from_db()
        assert bool(invoice_draft.pdf_file)

    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_generates_pdf_with_notes_and_terms(self, mock_doc_cls, invoice_draft, invoice_item):
        """Test PDF generation includes notes and terms sections."""
        mock_doc = MagicMock()
        captured_elements = []

        def build_effect(elements):
            captured_elements.extend(elements)
            buf = mock_doc_cls.call_args[0][0]
            buf.write(b'%PDF-1.4 test')

        mock_doc.build.side_effect = build_effect
        mock_doc_cls.return_value = mock_doc

        result = generate_invoice(str(invoice_draft.id))
        assert result['status'] == 'success'
        assert len(captured_elements) > 0

    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_generates_pdf_without_notes(self, mock_doc_cls, client_company, contract_fixed):
        """Test PDF generation for invoice without notes or terms."""
        invoice = Invoice.objects.create(
            client=client_company,
            contract=contract_fixed,
            status=Invoice.DRAFT,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000.00'),
            tax_rate=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
            total=Decimal('1000.00'),
            currency='USD',
            notes='',
            terms='',
        )

        mock_doc = MagicMock()

        def build_effect(elements):
            buf = mock_doc_cls.call_args[0][0]
            buf.write(b'%PDF-1.4 test')

        mock_doc.build.side_effect = build_effect
        mock_doc_cls.return_value = mock_doc

        result = generate_invoice(str(invoice.id))
        assert result['status'] == 'success'

    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_generates_pdf_with_discount(self, mock_doc_cls, client_company, contract_fixed):
        """Test PDF generation for invoice with discount."""
        invoice = Invoice.objects.create(
            client=client_company,
            contract=contract_fixed,
            status=Invoice.DRAFT,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000.00'),
            tax_rate=Decimal('10.00'),
            tax_amount=Decimal('100.00'),
            discount_amount=Decimal('50.00'),
            total=Decimal('1050.00'),
            paid_amount=Decimal('500.00'),
            currency='USD',
        )

        mock_doc = MagicMock()

        def build_effect(elements):
            buf = mock_doc_cls.call_args[0][0]
            buf.write(b'%PDF-1.4 test')

        mock_doc.build.side_effect = build_effect
        mock_doc_cls.return_value = mock_doc

        result = generate_invoice(str(invoice.id))
        assert result['status'] == 'success'

    def test_retries_on_invoice_not_found(self):
        """Test that the task raises an exception (triggering retry) when invoice does not exist."""
        with pytest.raises(Exception):
            generate_invoice(str(uuid.uuid4()))


@pytest.mark.django_db
class TestSendInvoiceEmail:
    """Tests for send_invoice_email task."""

    @patch('apps.notifications.services.NotificationService.send_invoice_notification')
    def test_sends_email_and_marks_as_sent(self, mock_notify, invoice_draft):
        """Test that email is sent and invoice status becomes SENT."""
        # Give the invoice a PDF file so PDF generation is skipped
        from django.core.files.base import ContentFile
        invoice_draft.pdf_file.save('test.pdf', ContentFile(b'pdf'), save=True)

        result = send_invoice_email(str(invoice_draft.id))

        assert result['status'] == 'success'
        mock_notify.assert_called_once_with(invoice_draft, 'invoice_sent')
        invoice_draft.refresh_from_db()
        assert invoice_draft.status == Invoice.SENT

    @patch('apps.invoicing.tasks.generate_invoice')
    @patch('apps.notifications.services.NotificationService.send_invoice_notification')
    def test_generates_pdf_if_not_exists(self, mock_notify, mock_gen_pdf, invoice_draft):
        """Test that PDF is generated when invoice has no file."""
        assert not invoice_draft.pdf_file
        send_invoice_email(str(invoice_draft.id))
        mock_gen_pdf.assert_called_once_with(str(invoice_draft.id))

    @patch('apps.notifications.services.NotificationService.send_invoice_notification')
    def test_marks_draft_invoice_as_sent(self, mock_notify, invoice_draft):
        """Test that a draft invoice is marked as sent after email is sent."""
        from django.core.files.base import ContentFile
        invoice_draft.pdf_file.save('test.pdf', ContentFile(b'pdf'), save=True)

        assert invoice_draft.status == Invoice.DRAFT
        send_invoice_email(str(invoice_draft.id))

        invoice_draft.refresh_from_db()
        assert invoice_draft.status == Invoice.SENT
        assert invoice_draft.sent_at is not None

    def test_retries_on_invoice_not_found(self):
        """Test that the task raises an exception (triggering retry) when invoice does not exist."""
        with pytest.raises(Exception):
            send_invoice_email(str(uuid.uuid4()))


@pytest.mark.django_db
class TestGenerateRecurringInvoices:
    """Tests for generate_recurring_invoices task."""

    def test_generates_invoice_for_monthly_contract_without_prior_invoice(
        self, client_company, admin_user
    ):
        """Test that a monthly retainer contract without existing invoices gets one."""
        contract = Contract.objects.create(
            client=client_company,
            title='Monthly Retainer',
            description='Monthly consulting services.',
            contract_type=Contract.RETAINER,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=335),
            value=Decimal('3000.00'),
            currency='USD',
            invoice_schedule='monthly',
            owner=admin_user,
        )

        initial_count = Invoice.objects.filter(contract=contract).count()
        result = generate_recurring_invoices()

        assert result['status'] == 'success'
        assert result['invoices_generated'] >= 1
        assert Invoice.objects.filter(contract=contract).count() > initial_count

    def test_generates_invoice_for_weekly_schedule(self, client_company, admin_user):
        """Test that a weekly contract generates invoices when due."""
        contract = Contract.objects.create(
            client=client_company,
            title='Weekly Milestone',
            description='Weekly deliverables.',
            contract_type=Contract.MILESTONE,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=335),
            value=Decimal('1000.00'),
            currency='USD',
            invoice_schedule='weekly',
            owner=admin_user,
        )

        result = generate_recurring_invoices()

        assert result['status'] == 'success'
        assert result['invoices_generated'] >= 1

    def test_skips_contract_with_recent_monthly_invoice(self, client_company, admin_user):
        """Test that a contract with a recent invoice does not generate a duplicate."""
        contract = Contract.objects.create(
            client=client_company,
            title='Monthly Retainer',
            description='Monthly.',
            contract_type=Contract.RETAINER,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=60),
            value=Decimal('3000.00'),
            currency='USD',
            invoice_schedule='monthly',
            owner=admin_user,
        )

        # Create a recent invoice for this month
        Invoice.objects.create(
            client=client_company,
            contract=contract,
            status=Invoice.DRAFT,
            issue_date=date.today() - timedelta(days=5),
            due_date=date.today() + timedelta(days=25),
            subtotal=Decimal('3000.00'),
            total=Decimal('3000.00'),
            currency='USD',
        )

        result = generate_recurring_invoices()

        # Should not generate another invoice for the same month
        invoice_count = Invoice.objects.filter(contract=contract).count()
        assert invoice_count == 1

    def test_skips_inactive_contracts(self, client_company, admin_user):
        """Test that inactive contracts do not generate invoices."""
        Contract.objects.create(
            client=client_company,
            title='Inactive Retainer',
            description='Inactive.',
            contract_type=Contract.RETAINER,
            status=Contract.DRAFT,
            start_date=date.today(),
            value=Decimal('3000.00'),
            currency='USD',
            invoice_schedule='monthly',
            owner=admin_user,
        )

        result = generate_recurring_invoices()

        assert result['invoices_generated'] == 0

    def test_skips_contracts_without_schedule(self, contract_fixed):
        """Test that contracts without an invoice schedule are skipped."""
        # contract_fixed has invoice_schedule='Upon milestone completion'
        # which is not 'monthly' or 'weekly', and it's FIXED_PRICE not RETAINER/MILESTONE
        result = generate_recurring_invoices()

        assert result['status'] == 'success'

    def test_generated_invoice_has_correct_values(self, client_company, admin_user):
        """Test that the generated invoice has the correct amount and dates."""
        contract = Contract.objects.create(
            client=client_company,
            title='Monthly Retainer',
            description='Test.',
            contract_type=Contract.RETAINER,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=30),
            value=Decimal('5000.00'),
            currency='EUR',
            invoice_schedule='monthly',
            owner=admin_user,
        )

        generate_recurring_invoices()

        invoice = Invoice.objects.filter(contract=contract).first()
        assert invoice is not None
        assert invoice.subtotal == Decimal('5000.00')
        assert invoice.total == Decimal('5000.00')
        assert invoice.currency == 'EUR'
        assert invoice.client == client_company
        assert invoice.status == Invoice.DRAFT
        assert invoice.issue_date == date.today()
        assert invoice.due_date == date.today() + timedelta(days=30)


@pytest.mark.django_db
class TestSendPaymentReminders:
    """Tests for send_payment_reminders task."""

    @patch('apps.notifications.services.NotificationService.send_invoice_notification')
    def test_sends_reminders_for_overdue_invoices(
        self, mock_notify, client_company, contract_fixed
    ):
        """Test that reminders are sent for invoices past their due date."""
        invoice = Invoice.objects.create(
            client=client_company,
            contract=contract_fixed,
            status=Invoice.SENT,
            issue_date=date.today() - timedelta(days=45),
            due_date=date.today() - timedelta(days=15),
            subtotal=Decimal('5000.00'),
            total=Decimal('5000.00'),
            currency='USD',
        )

        result = send_payment_reminders()

        assert result['status'] == 'success'
        assert result['reminders_sent'] >= 1
        mock_notify.assert_called()

    @patch('apps.notifications.services.NotificationService.send_invoice_notification')
    def test_marks_invoices_as_overdue(
        self, mock_notify, client_company
    ):
        """Test that sent invoices past due date are marked as OVERDUE."""
        invoice = Invoice.objects.create(
            client=client_company,
            status=Invoice.SENT,
            issue_date=date.today() - timedelta(days=45),
            due_date=date.today() - timedelta(days=15),
            subtotal=Decimal('2000.00'),
            total=Decimal('2000.00'),
            currency='USD',
        )

        send_payment_reminders()

        invoice.refresh_from_db()
        assert invoice.status == Invoice.OVERDUE

    @patch('apps.notifications.services.NotificationService.send_invoice_notification')
    def test_handles_partially_paid_overdue(
        self, mock_notify, client_company
    ):
        """Test that partially paid overdue invoices also get reminders."""
        invoice = Invoice.objects.create(
            client=client_company,
            status=Invoice.PARTIALLY_PAID,
            issue_date=date.today() - timedelta(days=45),
            due_date=date.today() - timedelta(days=15),
            subtotal=Decimal('5000.00'),
            total=Decimal('5000.00'),
            paid_amount=Decimal('2000.00'),
            currency='USD',
        )

        result = send_payment_reminders()

        assert result['reminders_sent'] >= 1

    @patch('apps.notifications.services.NotificationService.send_invoice_notification')
    def test_does_not_remind_paid_invoices(self, mock_notify, invoice_paid):
        """Test that paid invoices do not receive reminders."""
        result = send_payment_reminders()

        assert result['reminders_sent'] == 0

    @patch('apps.notifications.services.NotificationService.send_invoice_notification')
    def test_does_not_remind_non_overdue_invoices(self, mock_notify, invoice_sent):
        """Test that invoices not yet due are not reminded."""
        result = send_payment_reminders()

        assert result['reminders_sent'] == 0

    @patch('apps.notifications.services.NotificationService.send_invoice_notification')
    def test_handles_notification_failure_gracefully(
        self, mock_notify, client_company
    ):
        """Test that notification failure for one invoice does not crash the task."""
        mock_notify.side_effect = Exception("Email failed")

        Invoice.objects.create(
            client=client_company,
            status=Invoice.SENT,
            issue_date=date.today() - timedelta(days=45),
            due_date=date.today() - timedelta(days=15),
            subtotal=Decimal('1000.00'),
            total=Decimal('1000.00'),
            currency='USD',
        )

        result = send_payment_reminders()

        assert result['status'] == 'success'
        assert result['reminders_sent'] == 0

    @patch('apps.notifications.services.NotificationService.send_invoice_notification')
    def test_multiple_overdue_invoices(
        self, mock_notify, client_company
    ):
        """Test that multiple overdue invoices each get a reminder."""
        for i in range(3):
            Invoice.objects.create(
                client=client_company,
                status=Invoice.SENT,
                issue_date=date.today() - timedelta(days=45 + i),
                due_date=date.today() - timedelta(days=15 + i),
                subtotal=Decimal('1000.00'),
                total=Decimal('1000.00'),
                currency='USD',
            )

        # Reset mock to clear calls from post_save signal during invoice creation
        mock_notify.reset_mock()

        result = send_payment_reminders()

        assert result['reminders_sent'] == 3
        assert mock_notify.call_count == 3


# ============================================================================
# Coverage Tests for Recurring Invoice Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestRecurringInvoiceCoverage:
    """Tests to cover remaining uncovered branches in tasks.py."""

    def test_monthly_schedule_december_wrap_around(self, client_company, admin_user):
        """Test monthly schedule wraps from December to January of next year."""
        contract = Contract.objects.create(
            client=client_company,
            title='Monthly December Contract',
            description='Monthly retainer starting in December.',
            contract_type=Contract.RETAINER,
            status=Contract.ACTIVE,
            start_date=date(2025, 11, 1),
            end_date=date(2026, 12, 31),
            value=Decimal('2000.00'),
            currency='USD',
            invoice_schedule='monthly',
            owner=admin_user,
        )

        # Create an invoice in December - the next one should be January
        Invoice.objects.create(
            client=client_company,
            contract=contract,
            status=Invoice.DRAFT,
            issue_date=date(2025, 12, 15),
            due_date=date(2026, 1, 15),
            subtotal=Decimal('2000.00'),
            total=Decimal('2000.00'),
            currency='USD',
        )

        result = generate_recurring_invoices()

        assert result['status'] == 'success'
        # The next invoice should be generated since today (2026-02) >= January 2026
        assert result['invoices_generated'] >= 1

    def test_weekly_schedule_with_existing_recent_invoice(self, client_company, admin_user):
        """Test weekly schedule skips when recent invoice exists."""
        contract = Contract.objects.create(
            client=client_company,
            title='Weekly Contract',
            description='Weekly deliverables.',
            contract_type=Contract.MILESTONE,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=300),
            value=Decimal('500.00'),
            currency='USD',
            invoice_schedule='weekly',
            owner=admin_user,
        )

        # Create an invoice from 3 days ago (less than 7 days, so weekly should skip)
        Invoice.objects.create(
            client=client_company,
            contract=contract,
            status=Invoice.DRAFT,
            issue_date=date.today() - timedelta(days=3),
            due_date=date.today() + timedelta(days=27),
            subtotal=Decimal('500.00'),
            total=Decimal('500.00'),
            currency='USD',
        )

        result = generate_recurring_invoices()

        # Should not generate another invoice since less than 7 days passed
        assert result['status'] == 'success'
        invoice_count = Invoice.objects.filter(contract=contract).count()
        assert invoice_count == 1

    def test_weekly_schedule_with_old_invoice_generates_new(self, client_company, admin_user):
        """Test weekly schedule generates new invoice when last one is old enough."""
        contract = Contract.objects.create(
            client=client_company,
            title='Weekly Contract Old',
            description='Weekly deliverables with old invoice.',
            contract_type=Contract.MILESTONE,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=300),
            value=Decimal('500.00'),
            currency='USD',
            invoice_schedule='weekly',
            owner=admin_user,
        )

        # Create an invoice from 10 days ago (more than 7 days, so weekly should trigger)
        Invoice.objects.create(
            client=client_company,
            contract=contract,
            status=Invoice.DRAFT,
            issue_date=date.today() - timedelta(days=10),
            due_date=date.today() + timedelta(days=20),
            subtotal=Decimal('500.00'),
            total=Decimal('500.00'),
            currency='USD',
        )

        result = generate_recurring_invoices()

        assert result['status'] == 'success'
        assert result['invoices_generated'] >= 1
        invoice_count = Invoice.objects.filter(contract=contract).count()
        assert invoice_count == 2


# =============================================================================
# Retry Exception Tests (covers lines 216-218, 258-260)
# =============================================================================

@pytest.mark.django_db
class TestGenerateRecurringInvoicesRetry:
    """Tests for retry behavior of generate_recurring_invoices (lines 216-218)."""

    def test_retries_on_exception(self):
        """Task should retry when a top-level exception occurs."""
        with patch('apps.contracts.models.Contract.objects') as mock_objects:
            mock_objects.filter.side_effect = Exception('DB connection lost')

            with pytest.raises(Exception, match='DB connection lost'):
                generate_recurring_invoices()


@pytest.mark.django_db
class TestSendPaymentRemindersRetry:
    """Tests for retry behavior of send_payment_reminders (lines 258-260)."""

    def test_retries_on_exception(self):
        """Task should retry when a top-level exception occurs."""
        with patch('apps.invoicing.models.Invoice.objects') as mock_objects:
            mock_objects.filter.side_effect = Exception('DB connection lost')

            with pytest.raises(Exception, match='DB connection lost'):
                send_payment_reminders()
