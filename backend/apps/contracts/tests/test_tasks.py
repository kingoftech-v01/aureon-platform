"""
Tests for contracts Celery tasks.

Tests cover PDF generation, signature sending, and expiration checks.
"""
import pytest
import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, PropertyMock

from django.utils import timezone
from django.core.files.base import ContentFile

from apps.contracts.models import Contract
from apps.contracts.tasks import (
    generate_contract_pdf,
    send_contract_for_signature,
    check_contract_expirations,
)


@pytest.mark.django_db
class TestGenerateContractPdf:
    """Tests for generate_contract_pdf task."""

    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_generates_pdf_and_saves_to_contract(self, mock_doc_cls, contract_fixed):
        """Test that a PDF is generated and saved to the contract's file field."""
        mock_doc = MagicMock()

        def build_effect(elements):
            buf = mock_doc_cls.call_args[0][0]
            buf.write(b'%PDF-1.4 test content')

        mock_doc.build.side_effect = build_effect
        mock_doc_cls.return_value = mock_doc

        result = generate_contract_pdf(str(contract_fixed.id))

        assert result['status'] == 'success'
        assert result['contract_id'] == str(contract_fixed.id)
        assert result['filename'] == f"{contract_fixed.contract_number}.pdf"

        contract_fixed.refresh_from_db()
        assert bool(contract_fixed.contract_file)

    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_includes_contract_details_in_elements(self, mock_doc_cls, contract_fixed):
        """Test that the PDF build includes contract details as elements."""
        mock_doc = MagicMock()
        captured_elements = []

        def build_effect(elements):
            captured_elements.extend(elements)
            buf = mock_doc_cls.call_args[0][0]
            buf.write(b'%PDF-1.4 test')

        mock_doc.build.side_effect = build_effect
        mock_doc_cls.return_value = mock_doc

        generate_contract_pdf(str(contract_fixed.id))

        # Verify that elements were passed to doc.build
        assert len(captured_elements) > 0
        mock_doc.build.assert_called_once()

    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_contract_without_description(self, mock_doc_cls, client_company, admin_user):
        """Test PDF generation for a contract with no description."""
        contract = Contract.objects.create(
            client=client_company,
            title='No Description Contract',
            description='',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.ACTIVE,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            value=Decimal('1000.00'),
            currency='USD',
            owner=admin_user,
        )

        mock_doc = MagicMock()

        def build_effect(elements):
            buf = mock_doc_cls.call_args[0][0]
            buf.write(b'%PDF-1.4 test')

        mock_doc.build.side_effect = build_effect
        mock_doc_cls.return_value = mock_doc

        result = generate_contract_pdf(str(contract.id))
        assert result['status'] == 'success'

    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_contract_without_end_date(self, mock_doc_cls, client_company, admin_user):
        """Test PDF generation for a contract with no end date (ongoing)."""
        contract = Contract.objects.create(
            client=client_company,
            title='Ongoing Contract',
            description='Ongoing services.',
            contract_type=Contract.RETAINER,
            status=Contract.ACTIVE,
            start_date=date.today(),
            end_date=None,
            value=Decimal('2000.00'),
            currency='USD',
            owner=admin_user,
        )

        mock_doc = MagicMock()

        def build_effect(elements):
            buf = mock_doc_cls.call_args[0][0]
            buf.write(b'%PDF-1.4 test')

        mock_doc.build.side_effect = build_effect
        mock_doc_cls.return_value = mock_doc

        result = generate_contract_pdf(str(contract.id))
        assert result['status'] == 'success'

    def test_retries_on_contract_not_found(self):
        """Test that the task raises an exception (triggering retry) when contract does not exist."""
        with pytest.raises(Exception):
            generate_contract_pdf(str(uuid.uuid4()))

    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_retries_on_build_failure(self, mock_doc_cls, contract_fixed):
        """Test that the task raises an exception (triggering retry) when PDF build fails."""
        mock_doc_cls.side_effect = RuntimeError("Build failed")

        with pytest.raises(Exception):
            generate_contract_pdf(str(contract_fixed.id))


@pytest.mark.django_db
class TestSendContractForSignature:
    """Tests for send_contract_for_signature task."""

    @patch('apps.contracts.tasks.generate_contract_pdf')
    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_sends_contract_and_updates_status(
        self, mock_notify, mock_gen_pdf, contract_draft
    ):
        """Test that a draft contract is updated to pending and notification sent."""
        result = send_contract_for_signature(str(contract_draft.id))

        assert result['status'] == 'success'
        contract_draft.refresh_from_db()
        assert contract_draft.status == Contract.PENDING
        mock_notify.assert_called_once_with(contract_draft, 'contract_signature_request')

    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_does_not_change_non_draft_status(self, mock_notify, contract_fixed):
        """Test that an active contract's status is not changed to pending."""
        contract_fixed.contract_file.save('test.pdf', ContentFile(b'pdf'), save=True)

        result = send_contract_for_signature(str(contract_fixed.id))
        assert result['status'] == 'success'

        contract_fixed.refresh_from_db()
        assert contract_fixed.status == Contract.ACTIVE

    @patch('apps.contracts.tasks.generate_contract_pdf')
    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_generates_pdf_if_no_file(
        self, mock_notify, mock_gen_pdf, contract_draft
    ):
        """Test that PDF is generated when the contract has no file."""
        assert not contract_draft.contract_file
        send_contract_for_signature(str(contract_draft.id))
        mock_gen_pdf.assert_called_once_with(str(contract_draft.id))

    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_skips_pdf_generation_if_file_exists(self, mock_notify, contract_fixed):
        """Test that PDF generation is skipped when file already exists."""
        contract_fixed.contract_file.save('existing.pdf', ContentFile(b'pdf'), save=True)

        with patch('apps.contracts.tasks.generate_contract_pdf') as mock_gen_pdf:
            send_contract_for_signature(str(contract_fixed.id))
            mock_gen_pdf.assert_not_called()

    @patch('apps.contracts.tasks.generate_contract_pdf')
    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_handles_notification_failure_gracefully(
        self, mock_notify, mock_gen_pdf, contract_draft
    ):
        """Test that notification failure does not crash the task."""
        mock_notify.side_effect = Exception("Notification failed")

        result = send_contract_for_signature(str(contract_draft.id))
        assert result['status'] == 'success'

    def test_retries_on_contract_not_found(self):
        """Test that the task raises an exception (triggering retry) when contract does not exist."""
        with pytest.raises(Exception):
            send_contract_for_signature(str(uuid.uuid4()))


@pytest.mark.django_db
class TestCheckContractExpirations:
    """Tests for check_contract_expirations task."""

    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_notifies_contracts_expiring_within_30_days(
        self, mock_notify, client_company, admin_user
    ):
        """Test that contracts expiring within 30 days trigger notifications."""
        Contract.objects.create(
            client=client_company,
            title='Expiring Soon',
            description='Test',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=15),
            value=Decimal('5000.00'),
            currency='USD',
            owner=admin_user,
        )

        result = check_contract_expirations()

        assert result['status'] == 'success'
        assert result['expiring_notified'] >= 1
        mock_notify.assert_called()

    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_does_not_notify_contracts_expiring_after_30_days(
        self, mock_notify, client_company, admin_user
    ):
        """Test that contracts expiring after 30 days are not notified."""
        Contract.objects.create(
            client=client_company,
            title='Far Future Contract',
            description='Test',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=90),
            value=Decimal('5000.00'),
            currency='USD',
            owner=admin_user,
        )

        result = check_contract_expirations()

        assert result['expiring_notified'] == 0

    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_updates_expired_contracts_to_completed(
        self, mock_notify, client_company, admin_user
    ):
        """Test that expired active contracts are marked as completed."""
        contract = Contract.objects.create(
            client=client_company,
            title='Expired Contract',
            description='Test',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=120),
            end_date=date.today() - timedelta(days=1),
            value=Decimal('5000.00'),
            currency='USD',
            owner=admin_user,
        )

        result = check_contract_expirations()

        contract.refresh_from_db()
        assert contract.status == Contract.COMPLETED
        assert result['expired_updated'] >= 1

    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_ignores_non_active_contracts(self, mock_notify, client_company, admin_user):
        """Test that draft/pending contracts are not processed."""
        Contract.objects.create(
            client=client_company,
            title='Draft Contract',
            description='Test',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.DRAFT,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=15),
            value=Decimal('5000.00'),
            currency='USD',
            owner=admin_user,
        )

        result = check_contract_expirations()
        assert result['expiring_notified'] == 0
        assert result['expired_updated'] == 0

    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_handles_notification_failure_gracefully(
        self, mock_notify, client_company, admin_user
    ):
        """Test that notification failure for one contract does not stop the loop."""
        mock_notify.side_effect = Exception("Notification failed")

        Contract.objects.create(
            client=client_company,
            title='Expiring Contract',
            description='Test',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=15),
            value=Decimal('5000.00'),
            currency='USD',
            owner=admin_user,
        )

        result = check_contract_expirations()

        assert result['status'] == 'success'
        # Notification failed so count is 0, but task didn't crash
        assert result['expiring_notified'] == 0

    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_multiple_expiring_contracts(
        self, mock_notify, client_company, admin_user
    ):
        """Test that multiple expiring contracts are all notified."""
        for i in range(3):
            Contract.objects.create(
                client=client_company,
                title=f'Expiring Contract {i}',
                description='Test',
                contract_type=Contract.FIXED_PRICE,
                status=Contract.ACTIVE,
                start_date=date.today() - timedelta(days=60),
                end_date=date.today() + timedelta(days=10 + i),
                value=Decimal('5000.00'),
                currency='USD',
                owner=admin_user,
            )

        result = check_contract_expirations()

        assert result['expiring_notified'] == 3
        assert mock_notify.call_count == 3

    @patch('apps.notifications.services.NotificationService.send_contract_notification')
    def test_contract_expiring_today_included(
        self, mock_notify, client_company, admin_user
    ):
        """Test that a contract expiring today is included as expiring."""
        Contract.objects.create(
            client=client_company,
            title='Expiring Today',
            description='Test',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today(),
            value=Decimal('5000.00'),
            currency='USD',
            owner=admin_user,
        )

        result = check_contract_expirations()

        assert result['expiring_notified'] >= 1
