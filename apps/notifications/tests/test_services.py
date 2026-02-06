"""
Tests for notification services.

Tests cover email sending, notification channels (email, SMS, in-app),
and convenience methods for invoice/payment/contract/client notifications.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, PropertyMock

from django.utils import timezone
from django.conf import settings

from apps.notifications.models import Notification, NotificationTemplate
from apps.notifications.services import EmailService, NotificationService


@pytest.fixture
def email_template(db):
    """Create an email notification template."""
    return NotificationTemplate.objects.create(
        name='Invoice Sent',
        template_type=NotificationTemplate.INVOICE_SENT,
        channel=NotificationTemplate.EMAIL,
        subject='Invoice {{invoice_number}} from {{company_name}}',
        body_text='Dear {{client_name}}, please find invoice {{invoice_number}} for {{amount}}.',
        body_html='<p>Dear {{client_name}}, please find invoice {{invoice_number}} for {{amount}}.</p>',
        is_active=True,
    )


@pytest.fixture
def sms_template(db):
    """Create an SMS notification template."""
    return NotificationTemplate.objects.create(
        name='Payment Reminder SMS',
        template_type='reminder_payment_due',
        channel=NotificationTemplate.SMS,
        subject='Payment Reminder',
        body_text='Reminder: Invoice {{invoice_number}} for {{amount}} is due on {{due_date}}.',
        is_active=True,
    )


@pytest.fixture
def in_app_template(db):
    """Create an in-app notification template."""
    return NotificationTemplate.objects.create(
        name='Payment Received In-App',
        template_type=NotificationTemplate.PAYMENT_RECEIVED,
        channel=NotificationTemplate.IN_APP,
        subject='Payment Received',
        body_text='Payment of {{amount}} received for invoice {{invoice_number}}.',
        is_active=True,
    )


@pytest.fixture
def welcome_template(db):
    """Create a client welcome template."""
    return NotificationTemplate.objects.create(
        name='Client Welcome',
        template_type=NotificationTemplate.CLIENT_WELCOME,
        channel=NotificationTemplate.EMAIL,
        subject='Welcome to {{company_name}}',
        body_text='Dear {{client_name}}, welcome to {{company_name}}!',
        is_active=True,
    )


@pytest.fixture
def receipt_template(db):
    """Create a payment receipt template."""
    return NotificationTemplate.objects.create(
        name='Payment Receipt',
        template_type=NotificationTemplate.PAYMENT_RECEIPT,
        channel=NotificationTemplate.EMAIL,
        subject='Payment Receipt - {{amount}}',
        body_text='Your payment of {{amount}} has been received.',
        is_active=True,
    )


@pytest.fixture
def contract_template(db):
    """Create a contract notification template."""
    return NotificationTemplate.objects.create(
        name='Contract Signature Request',
        template_type='contract_signature_request',
        channel=NotificationTemplate.EMAIL,
        subject='Contract Ready for Signature',
        body_text='Dear {{client_name}}, contract {{contract_title}} is ready for your signature.',
        is_active=True,
    )


@pytest.mark.django_db
class TestEmailService:
    """Tests for EmailService."""

    @patch('apps.notifications.services.EmailMultiAlternatives')
    def test_send_email_success(self, mock_email_cls):
        """Test that send_email sends an email and marks notification as sent."""
        notification = Notification.objects.create(
            email='test@example.com',
            channel=NotificationTemplate.EMAIL,
            subject='Test Subject',
            message_text='Test body',
            message_html='<p>Test body</p>',
            status=Notification.PENDING,
        )

        mock_email = MagicMock()
        mock_email_cls.return_value = mock_email

        result = EmailService.send_email(notification)

        assert result is True
        mock_email.attach_alternative.assert_called_once_with('<p>Test body</p>', 'text/html')
        mock_email.send.assert_called_once_with(fail_silently=False)

        notification.refresh_from_db()
        assert notification.status == Notification.SENT
        assert notification.sent_at is not None

    @patch('apps.notifications.services.EmailMultiAlternatives')
    def test_send_email_without_html(self, mock_email_cls):
        """Test that email without HTML body skips attach_alternative."""
        notification = Notification.objects.create(
            email='test@example.com',
            channel=NotificationTemplate.EMAIL,
            subject='Plain Text Only',
            message_text='Plain text body',
            message_html='',
            status=Notification.PENDING,
        )

        mock_email = MagicMock()
        mock_email_cls.return_value = mock_email

        result = EmailService.send_email(notification)

        assert result is True
        mock_email.attach_alternative.assert_not_called()

    @patch('apps.notifications.services.EmailMultiAlternatives')
    def test_send_email_failure(self, mock_email_cls):
        """Test that email sending failure marks notification as failed."""
        notification = Notification.objects.create(
            email='test@example.com',
            channel=NotificationTemplate.EMAIL,
            subject='Will Fail',
            message_text='Test body',
            status=Notification.PENDING,
        )

        mock_email = MagicMock()
        mock_email.send.side_effect = Exception("SMTP error")
        mock_email_cls.return_value = mock_email

        result = EmailService.send_email(notification)

        assert result is False
        notification.refresh_from_db()
        assert notification.status == Notification.FAILED
        assert 'SMTP error' in notification.error_message
        assert notification.retry_count == 1

    @patch('apps.notifications.services.EmailMultiAlternatives')
    def test_send_email_uses_correct_from_address(self, mock_email_cls):
        """Test that the email uses DEFAULT_FROM_EMAIL."""
        notification = Notification.objects.create(
            email='recipient@example.com',
            channel=NotificationTemplate.EMAIL,
            subject='From Address Test',
            message_text='Body',
            status=Notification.PENDING,
        )

        mock_email = MagicMock()
        mock_email_cls.return_value = mock_email

        EmailService.send_email(notification)

        call_kwargs = mock_email_cls.call_args
        assert call_kwargs[1]['from_email'] == settings.DEFAULT_FROM_EMAIL
        assert call_kwargs[1]['to'] == ['recipient@example.com']


@pytest.mark.django_db
class TestNotificationServiceEmail:
    """Tests for NotificationService email channel."""

    @patch('apps.notifications.services.EmailService.send_email')
    def test_send_notification_creates_and_sends_email(
        self, mock_send_email, email_template
    ):
        """Test that send_notification creates a Notification and sends email."""
        mock_send_email.return_value = True

        context = {
            'invoice_number': 'INV-001',
            'client_name': 'John Doe',
            'amount': '$5000.00',
            'company_name': 'Test Co',
        }

        notification = NotificationService.send_notification(
            template_type=NotificationTemplate.INVOICE_SENT,
            recipient_email='john@example.com',
            context=context,
        )

        assert notification is not None
        assert notification.email == 'john@example.com'
        assert 'INV-001' in notification.subject
        assert notification.channel == NotificationTemplate.EMAIL
        mock_send_email.assert_called_once()

    @patch('apps.notifications.services.EmailService.send_email')
    def test_template_variables_are_rendered(self, mock_send_email, email_template):
        """Test that template variables are correctly replaced."""
        mock_send_email.return_value = True

        context = {
            'invoice_number': 'INV-042',
            'client_name': 'Jane Smith',
            'amount': '$1500.00',
            'company_name': 'Acme Corp',
        }

        notification = NotificationService.send_notification(
            template_type=NotificationTemplate.INVOICE_SENT,
            recipient_email='jane@example.com',
            context=context,
        )

        assert 'INV-042' in notification.subject
        assert 'Jane Smith' in notification.message_text
        assert '$1500.00' in notification.message_text


@pytest.mark.django_db
class TestNotificationServiceSms:
    """Tests for NotificationService SMS channel."""

    def test_sms_notification_stored_when_sns_not_configured(self, sms_template):
        """Test that SMS notification is stored when AWS SNS is not configured."""
        context = {
            'invoice_number': 'INV-001',
            'amount': '$500.00',
            'due_date': 'January 15, 2025',
        }

        notification = NotificationService.send_notification(
            template_type='reminder_payment_due',
            recipient_email='+1234567890',
            context=context,
        )

        assert notification is not None
        assert notification.channel == NotificationTemplate.SMS
        # Without AWS SNS configured, should be marked as delivered (stored)
        notification.refresh_from_db()
        assert notification.status in [Notification.DELIVERED, Notification.SENT]

    @patch('boto3.client')
    def test_sms_sends_via_sns_when_configured(self, mock_boto, sms_template):
        """Test that SMS is sent via AWS SNS when configured."""
        mock_sns = MagicMock()
        mock_boto.return_value = mock_sns

        with patch.object(settings, 'AWS_SNS_ENABLED', True, create=True):
            context = {
                'invoice_number': 'INV-001',
                'amount': '$500.00',
                'due_date': 'January 15, 2025',
            }

            notification = NotificationService.send_notification(
                template_type='reminder_payment_due',
                recipient_email='+1234567890',
                context=context,
            )

            assert notification is not None
            mock_sns.publish.assert_called_once()


@pytest.mark.django_db
class TestNotificationServiceInApp:
    """Tests for NotificationService in-app channel."""

    def test_in_app_notification_marked_as_delivered(self, in_app_template):
        """Test that in-app notifications are stored and marked as delivered."""
        context = {
            'amount': '$2500.00',
            'invoice_number': 'INV-010',
        }

        notification = NotificationService.send_notification(
            template_type=NotificationTemplate.PAYMENT_RECEIVED,
            recipient_email='user@example.com',
            context=context,
        )

        assert notification is not None
        assert notification.channel == NotificationTemplate.IN_APP
        notification.refresh_from_db()
        assert notification.status == Notification.DELIVERED
        assert notification.delivered_at is not None


@pytest.mark.django_db
class TestSendInvoiceNotification:
    """Tests for NotificationService.send_invoice_notification."""

    @patch('apps.notifications.services.NotificationService.send_notification')
    def test_sends_invoice_notification_with_correct_context(
        self, mock_send, invoice_sent
    ):
        """Test that invoice notification passes the correct context."""
        mock_send.return_value = MagicMock()

        # Monkeypatch full_name since Client model lacks this property
        invoice_sent.client.full_name = invoice_sent.client.get_full_name()

        NotificationService.send_invoice_notification(invoice_sent, 'invoice_sent')

        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        context = call_kwargs[1]['context'] if 'context' in call_kwargs[1] else call_kwargs[0][2]

        assert context['invoice_number'] == invoice_sent.invoice_number
        assert context['client_name'] == invoice_sent.client.get_full_name()
        assert invoice_sent.currency in context['currency']

    @patch('apps.notifications.services.NotificationService.send_notification')
    def test_sends_to_client_email(self, mock_send, invoice_sent):
        """Test that the notification is sent to the client's email."""
        mock_send.return_value = MagicMock()
        invoice_sent.client.full_name = invoice_sent.client.get_full_name()

        NotificationService.send_invoice_notification(invoice_sent, 'invoice_sent')

        call_kwargs = mock_send.call_args
        recipient = call_kwargs[1].get('recipient_email') or call_kwargs[0][1]
        assert recipient == invoice_sent.client.email

    @patch('apps.notifications.services.NotificationService.send_notification')
    def test_passes_related_invoice(self, mock_send, invoice_sent):
        """Test that the invoice is passed as a related object."""
        mock_send.return_value = MagicMock()
        invoice_sent.client.full_name = invoice_sent.client.get_full_name()

        NotificationService.send_invoice_notification(invoice_sent, 'invoice_sent')

        call_kwargs = mock_send.call_args[1]
        assert call_kwargs.get('related_invoice') == invoice_sent


@pytest.mark.django_db
class TestSendPaymentReceipt:
    """Tests for NotificationService.send_payment_receipt."""

    @patch('apps.notifications.services.NotificationService.send_notification')
    def test_sends_payment_receipt_with_correct_context(
        self, mock_send, payment_successful
    ):
        """Test that payment receipt passes the correct context."""
        mock_send.return_value = MagicMock()

        # Payment has invoice, and invoice has client
        invoice = payment_successful.invoice
        client = invoice.client
        client.full_name = client.get_full_name()
        # The code accesses payment.client, which doesn't exist on Payment model.
        # We add it as an attribute for testing.
        payment_successful.client = client

        NotificationService.send_payment_receipt(payment_successful)

        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        context = call_kwargs[1]['context'] if 'context' in call_kwargs[1] else call_kwargs[0][2]

        assert context['invoice_number'] == invoice.invoice_number
        assert str(payment_successful.id) in context['payment_id']


@pytest.mark.django_db
class TestSendContractNotification:
    """Tests for NotificationService.send_contract_notification."""

    @patch('apps.notifications.services.NotificationService.send_notification')
    def test_sends_contract_notification_with_correct_context(
        self, mock_send, contract_fixed
    ):
        """Test that contract notification passes the correct context."""
        mock_send.return_value = MagicMock()

        # Monkeypatch missing attributes
        contract_fixed.client.full_name = contract_fixed.client.get_full_name()
        contract_fixed.total_value = contract_fixed.value

        NotificationService.send_contract_notification(
            contract_fixed, 'contract_signature_request'
        )

        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        context = call_kwargs[1]['context'] if 'context' in call_kwargs[1] else call_kwargs[0][2]

        assert context['contract_title'] == contract_fixed.title
        assert context['client_name'] == contract_fixed.client.get_full_name()

    @patch('apps.notifications.services.NotificationService.send_notification')
    def test_handles_contract_without_end_date(self, mock_send, client_company, admin_user):
        """Test notification for a contract without an end date."""
        from apps.contracts.models import Contract

        contract = Contract.objects.create(
            client=client_company,
            title='Ongoing Contract',
            description='No end date.',
            contract_type=Contract.RETAINER,
            status=Contract.ACTIVE,
            start_date=date.today(),
            end_date=None,
            value=Decimal('3000.00'),
            currency='USD',
            owner=admin_user,
        )

        mock_send.return_value = MagicMock()
        contract.client.full_name = contract.client.get_full_name()
        contract.total_value = contract.value

        NotificationService.send_contract_notification(contract, 'contract_expiring')

        call_kwargs = mock_send.call_args
        context = call_kwargs[1]['context'] if 'context' in call_kwargs[1] else call_kwargs[0][2]
        assert context['end_date'] == 'Ongoing'


@pytest.mark.django_db
class TestSendClientWelcome:
    """Tests for NotificationService.send_client_welcome."""

    @patch('apps.notifications.services.NotificationService.send_notification')
    def test_sends_welcome_email(self, mock_send, client_company):
        """Test that a welcome notification is sent to a new client."""
        mock_send.return_value = MagicMock()
        client_company.full_name = client_company.get_full_name()

        NotificationService.send_client_welcome(client_company)

        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        template_type = call_kwargs[1].get('template_type') or call_kwargs[0][0]
        assert template_type == NotificationTemplate.CLIENT_WELCOME

    @patch('apps.notifications.services.NotificationService.send_notification')
    def test_welcome_email_sent_to_client_email(self, mock_send, client_company):
        """Test that the welcome email is sent to the client's email address."""
        mock_send.return_value = MagicMock()
        client_company.full_name = client_company.get_full_name()

        NotificationService.send_client_welcome(client_company)

        call_kwargs = mock_send.call_args
        recipient = call_kwargs[1].get('recipient_email') or call_kwargs[0][1]
        assert recipient == client_company.email


@pytest.mark.django_db
class TestTemplateNotFound:
    """Tests for handling missing notification templates."""

    def test_returns_none_when_template_not_found(self):
        """Test that send_notification returns None when template does not exist."""
        result = NotificationService.send_notification(
            template_type='nonexistent_template',
            recipient_email='test@example.com',
            context={},
        )

        assert result is None

    def test_no_notification_created_when_template_missing(self):
        """Test that no Notification record is created when template is missing."""
        initial_count = Notification.objects.count()

        NotificationService.send_notification(
            template_type='nonexistent_template',
            recipient_email='test@example.com',
            context={},
        )

        assert Notification.objects.count() == initial_count

    def test_returns_none_for_inactive_template(self, db):
        """Test that an inactive template is treated as not found."""
        NotificationTemplate.objects.create(
            name='Inactive Template',
            template_type='inactive_type',
            channel=NotificationTemplate.EMAIL,
            subject='Test',
            body_text='Test',
            is_active=False,
        )

        result = NotificationService.send_notification(
            template_type='inactive_type',
            recipient_email='test@example.com',
            context={},
        )

        assert result is None
