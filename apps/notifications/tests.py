"""
Comprehensive unit tests for notifications app.

Tests notification template rendering, email sending, and scheduled tasks.
"""

import pytest
from unittest.mock import patch, MagicMock, call
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.core import mail
from django.conf import settings
from django.utils import timezone

from .models import Notification, NotificationTemplate
from .services import EmailService, NotificationService
from .tasks import (
    send_pending_notifications,
    send_overdue_invoice_reminders,
    send_upcoming_payment_reminders,
    send_contract_expiring_reminders,
    retry_failed_notifications,
    cleanup_old_notifications,
    send_notification_async
)


class NotificationTemplateModelTests(TestCase):
    """Test NotificationTemplate model methods."""

    def setUp(self):
        """Set up test data."""
        self.template = NotificationTemplate.objects.create(
            name='Test Invoice Template',
            template_type=NotificationTemplate.INVOICE_CREATED,
            channel=NotificationTemplate.EMAIL,
            subject='Invoice {{invoice_number}} Created',
            body_text='Hello {{client_name}}, your invoice {{invoice_number}} for {{amount}} is ready.',
            body_html='<p>Hello {{client_name}}, your invoice {{invoice_number}} for {{amount}} is ready.</p>',
            is_active=True
        )

    def test_template_creation(self):
        """Test that notification template is created correctly."""
        self.assertEqual(self.template.template_type, NotificationTemplate.INVOICE_CREATED)
        self.assertEqual(self.template.channel, NotificationTemplate.EMAIL)
        self.assertTrue(self.template.is_active)

    def test_template_render_with_context(self):
        """Test template rendering with context variables."""
        context = {
            'client_name': 'John Doe',
            'invoice_number': 'INV-001',
            'amount': '$500.00'
        }

        rendered = self.template.render(context)

        self.assertEqual(rendered['subject'], 'Invoice INV-001 Created')
        self.assertIn('John Doe', rendered['body_text'])
        self.assertIn('INV-001', rendered['body_text'])
        self.assertIn('$500.00', rendered['body_text'])
        self.assertIn('John Doe', rendered['body_html'])

    def test_template_render_with_missing_variables(self):
        """Test template rendering with missing context variables."""
        context = {
            'client_name': 'John Doe'
            # Missing invoice_number and amount
        }

        rendered = self.template.render(context)

        # Missing variables should remain as placeholders
        self.assertIn('{{invoice_number}}', rendered['subject'])
        self.assertIn('{{amount}}', rendered['body_text'])

    def test_template_render_empty_html(self):
        """Test template rendering when HTML body is empty."""
        self.template.body_html = ''
        self.template.save()

        context = {'client_name': 'Test User'}
        rendered = self.template.render(context)

        self.assertIsNone(rendered['body_html'])


class NotificationModelTests(TestCase):
    """Test Notification model methods."""

    def setUp(self):
        """Set up test data."""
        from apps.accounts.models import User

        self.user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.notification = Notification.objects.create(
            user=self.user,
            email='test@example.com',
            subject='Test Notification',
            message_text='This is a test notification.',
            channel=NotificationTemplate.EMAIL,
            status=Notification.PENDING
        )

    def test_notification_creation(self):
        """Test that notification is created correctly."""
        self.assertEqual(self.notification.status, Notification.PENDING)
        self.assertEqual(self.notification.channel, NotificationTemplate.EMAIL)
        self.assertEqual(self.notification.retry_count, 0)

    def test_mark_as_sent(self):
        """Test marking notification as sent."""
        external_id = 'msg_123456'
        self.notification.mark_as_sent(external_id)
        self.notification.refresh_from_db()

        self.assertEqual(self.notification.status, Notification.SENT)
        self.assertEqual(self.notification.external_id, external_id)
        self.assertIsNotNone(self.notification.sent_at)

    def test_mark_as_delivered(self):
        """Test marking notification as delivered."""
        self.notification.mark_as_delivered()
        self.notification.refresh_from_db()

        self.assertEqual(self.notification.status, Notification.DELIVERED)
        self.assertIsNotNone(self.notification.delivered_at)

    def test_mark_as_read(self):
        """Test marking notification as read."""
        self.notification.mark_as_read()
        self.notification.refresh_from_db()

        self.assertEqual(self.notification.status, Notification.READ)
        self.assertIsNotNone(self.notification.read_at)
        self.assertTrue(self.notification.is_read)

    def test_mark_as_failed(self):
        """Test marking notification as failed."""
        error_msg = 'SMTP connection failed'
        self.notification.mark_as_failed(error_msg)
        self.notification.refresh_from_db()

        self.assertEqual(self.notification.status, Notification.FAILED)
        self.assertEqual(self.notification.error_message, error_msg)
        self.assertEqual(self.notification.retry_count, 1)
        self.assertIsNotNone(self.notification.failed_at)

    def test_recipient_property_with_user(self):
        """Test recipient property when user is set."""
        self.assertEqual(self.notification.recipient, 'test@example.com')

    def test_recipient_property_with_email_only(self):
        """Test recipient property when only email is set."""
        notification = Notification.objects.create(
            email='client@example.com',
            subject='Test',
            message_text='Test message',
            channel=NotificationTemplate.EMAIL
        )

        self.assertEqual(notification.recipient, 'client@example.com')

    def test_recipient_property_with_phone_only(self):
        """Test recipient property when only phone is set."""
        notification = Notification.objects.create(
            phone='+1234567890',
            subject='Test',
            message_text='Test SMS',
            channel=NotificationTemplate.SMS
        )

        self.assertEqual(notification.recipient, '+1234567890')


class EmailServiceTests(TestCase):
    """Test EmailService functionality."""

    def setUp(self):
        """Set up test data."""
        self.notification = Notification.objects.create(
            email='recipient@example.com',
            subject='Test Email',
            message_text='Plain text message',
            message_html='<p>HTML message</p>',
            channel=NotificationTemplate.EMAIL,
            status=Notification.PENDING
        )

    def test_send_email_success(self):
        """Test successful email sending."""
        success = EmailService.send_email(self.notification)

        self.assertTrue(success)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.status, Notification.SENT)

        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, 'Test Email')
        self.assertEqual(sent_email.to, ['recipient@example.com'])
        self.assertIn('Plain text message', sent_email.body)

    def test_send_email_with_html_alternative(self):
        """Test sending email with HTML alternative."""
        EmailService.send_email(self.notification)

        sent_email = mail.outbox[0]
        # Check that HTML alternative exists
        self.assertEqual(len(sent_email.alternatives), 1)
        html_content, content_type = sent_email.alternatives[0]
        self.assertEqual(content_type, 'text/html')
        self.assertIn('<p>HTML message</p>', html_content)

    def test_send_email_without_html(self):
        """Test sending email without HTML alternative."""
        self.notification.message_html = ''
        self.notification.save()

        EmailService.send_email(self.notification)

        sent_email = mail.outbox[0]
        self.assertEqual(len(sent_email.alternatives), 0)

    @patch('apps.notifications.services.EmailMultiAlternatives.send')
    def test_send_email_failure(self, mock_send):
        """Test email sending failure handling."""
        mock_send.side_effect = Exception('SMTP error')

        success = EmailService.send_email(self.notification)

        self.assertFalse(success)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.status, Notification.FAILED)
        self.assertIn('SMTP error', self.notification.error_message)


@pytest.mark.django_db
class NotificationServiceTests(TestCase):
    """Test NotificationService functionality."""

    def setUp(self):
        """Set up test data."""
        from apps.tenants.models import Tenant
        from apps.clients.models import Client

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

        self.template = NotificationTemplate.objects.create(
            name='Invoice Created',
            template_type=NotificationTemplate.INVOICE_CREATED,
            channel=NotificationTemplate.EMAIL,
            subject='Invoice {{invoice_number}} Created',
            body_text='Your invoice {{invoice_number}} for {{amount}} is ready.',
            is_active=True
        )

    def test_send_notification_success(self):
        """Test sending notification with template."""
        context = {
            'invoice_number': 'INV-001',
            'amount': '$500.00'
        }

        notification = NotificationService.send_notification(
            template_type=NotificationTemplate.INVOICE_CREATED,
            recipient_email='client@example.com',
            context=context
        )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.subject, 'Invoice INV-001 Created')
        self.assertIn('INV-001', notification.message_text)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_notification_template_not_found(self):
        """Test sending notification with non-existent template."""
        notification = NotificationService.send_notification(
            template_type='non_existent_template',
            recipient_email='test@example.com',
            context={}
        )

        self.assertIsNone(notification)

    def test_send_notification_inactive_template(self):
        """Test sending notification with inactive template."""
        self.template.is_active = False
        self.template.save()

        notification = NotificationService.send_notification(
            template_type=NotificationTemplate.INVOICE_CREATED,
            recipient_email='test@example.com',
            context={}
        )

        self.assertIsNone(notification)

    def test_send_invoice_notification(self):
        """Test sending invoice-related notification."""
        from apps.invoicing.models import Invoice
        from datetime import date

        invoice = Invoice.objects.create(
            tenant=self.tenant,
            client=self.client,
            invoice_number='INV-001',
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('500.00'),
            tax=Decimal('50.00'),
            total=Decimal('550.00'),
            currency='USD'
        )

        with patch.object(settings, 'SITE_NAME', 'Test Company'):
            notification = NotificationService.send_invoice_notification(
                invoice=invoice,
                template_type=NotificationTemplate.INVOICE_CREATED
            )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.email, 'client@example.com')
        self.assertEqual(notification.related_invoice, invoice)

    def test_send_payment_receipt(self):
        """Test sending payment receipt notification."""
        from apps.payments.models import Payment
        from apps.invoicing.models import Invoice
        from datetime import date

        invoice = Invoice.objects.create(
            tenant=self.tenant,
            client=self.client,
            invoice_number='INV-002',
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            total=Decimal('1000.00'),
            currency='USD'
        )

        payment = Payment.objects.create(
            client=self.client,
            invoice=invoice,
            amount=Decimal('1000.00'),
            currency='USD',
            status='success',
            payment_method='card',
            payment_date=date.today()
        )

        # Create receipt template
        NotificationTemplate.objects.create(
            name='Payment Receipt',
            template_type=NotificationTemplate.PAYMENT_RECEIPT,
            channel=NotificationTemplate.EMAIL,
            subject='Payment Receipt',
            body_text='Receipt for {{amount}}',
            is_active=True
        )

        with patch.object(settings, 'SITE_NAME', 'Test Company'):
            notification = NotificationService.send_payment_receipt(payment)

        self.assertIsNotNone(notification)
        self.assertEqual(notification.related_payment, payment)


class NotificationTasksTests(TestCase):
    """Test notification scheduled tasks."""

    def setUp(self):
        """Set up test data."""
        from apps.tenants.models import Tenant
        from apps.clients.models import Client

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

    def test_send_pending_notifications_task(self):
        """Test sending pending notifications task."""
        # Create pending notifications
        for i in range(5):
            Notification.objects.create(
                email=f'test{i}@example.com',
                subject=f'Test {i}',
                message_text='Test message',
                channel=NotificationTemplate.EMAIL,
                status=Notification.PENDING
            )

        result = send_pending_notifications()

        self.assertEqual(result['sent'], 5)
        self.assertEqual(result['failed'], 0)
        self.assertEqual(len(mail.outbox), 5)

    def test_send_pending_notifications_with_failures(self):
        """Test sending pending notifications with some failures."""
        # Create notifications
        for i in range(3):
            Notification.objects.create(
                email=f'test{i}@example.com',
                subject=f'Test {i}',
                message_text='Test message',
                channel=NotificationTemplate.EMAIL,
                status=Notification.PENDING
            )

        with patch('apps.notifications.services.EmailService.send_email') as mock_send:
            # First two succeed, third fails
            mock_send.side_effect = [True, True, False]
            result = send_pending_notifications()

        self.assertEqual(result['sent'], 2)
        self.assertEqual(result['failed'], 1)

    @pytest.mark.django_db
    def test_send_overdue_invoice_reminders_task(self):
        """Test sending overdue invoice reminders."""
        from apps.invoicing.models import Invoice
        from datetime import date

        # Create overdue invoice
        overdue_invoice = Invoice.objects.create(
            tenant=self.tenant,
            client=self.client,
            invoice_number='INV-OVERDUE',
            issue_date=date.today() - timedelta(days=40),
            due_date=date.today() - timedelta(days=10),
            total=Decimal('500.00'),
            currency='USD',
            status=Invoice.SENT
        )

        # Create template
        NotificationTemplate.objects.create(
            name='Invoice Overdue',
            template_type=NotificationTemplate.INVOICE_OVERDUE,
            channel=NotificationTemplate.EMAIL,
            subject='Invoice Overdue',
            body_text='Your invoice {{invoice_number}} is overdue.',
            is_active=True
        )

        with patch.object(settings, 'SITE_NAME', 'Test Company'):
            result = send_overdue_invoice_reminders()

        self.assertEqual(result['reminded'], 1)

    @pytest.mark.django_db
    def test_send_overdue_invoice_reminders_skip_recent(self):
        """Test that overdue reminders skip recently reminded invoices."""
        from apps.invoicing.models import Invoice
        from datetime import date

        # Create overdue invoice
        overdue_invoice = Invoice.objects.create(
            tenant=self.tenant,
            client=self.client,
            invoice_number='INV-OVERDUE-2',
            issue_date=date.today() - timedelta(days=40),
            due_date=date.today() - timedelta(days=10),
            total=Decimal('500.00'),
            currency='USD',
            status=Invoice.SENT
        )

        template = NotificationTemplate.objects.create(
            name='Invoice Overdue',
            template_type=NotificationTemplate.INVOICE_OVERDUE,
            channel=NotificationTemplate.EMAIL,
            subject='Invoice Overdue',
            body_text='Overdue',
            is_active=True
        )

        # Create recent reminder
        Notification.objects.create(
            email=self.client.email,
            template=template,
            subject='Test',
            message_text='Test',
            channel=NotificationTemplate.EMAIL,
            related_invoice=overdue_invoice,
            created_at=timezone.now() - timedelta(days=3)
        )

        result = send_overdue_invoice_reminders()

        # Should skip because reminder was sent within last 7 days
        self.assertEqual(result['reminded'], 0)

    @pytest.mark.django_db
    def test_send_upcoming_payment_reminders_task(self):
        """Test sending upcoming payment reminders."""
        from apps.invoicing.models import Invoice
        from datetime import date

        # Create invoice due in 3 days
        upcoming_invoice = Invoice.objects.create(
            tenant=self.tenant,
            client=self.client,
            invoice_number='INV-UPCOMING',
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=3),
            total=Decimal('500.00'),
            currency='USD',
            status=Invoice.SENT
        )

        # Create template
        NotificationTemplate.objects.create(
            name='Payment Reminder',
            template_type=NotificationTemplate.REMINDER_PAYMENT_DUE,
            channel=NotificationTemplate.EMAIL,
            subject='Payment Due Soon',
            body_text='Your invoice {{invoice_number}} is due soon.',
            is_active=True
        )

        with patch.object(settings, 'SITE_NAME', 'Test Company'):
            result = send_upcoming_payment_reminders()

        self.assertEqual(result['reminded'], 1)

    def test_retry_failed_notifications_task(self):
        """Test retrying failed notifications."""
        # Create failed notifications
        for i in range(3):
            Notification.objects.create(
                email=f'test{i}@example.com',
                subject=f'Test {i}',
                message_text='Test message',
                channel=NotificationTemplate.EMAIL,
                status=Notification.FAILED,
                retry_count=1
            )

        result = retry_failed_notifications()

        self.assertEqual(result['retried'], 3)
        self.assertEqual(len(mail.outbox), 3)

    def test_retry_failed_notifications_max_retries(self):
        """Test that notifications with max retries are skipped."""
        # Create notification with max retries
        Notification.objects.create(
            email='test@example.com',
            subject='Test',
            message_text='Test message',
            channel=NotificationTemplate.EMAIL,
            status=Notification.FAILED,
            retry_count=5  # Exceeds max
        )

        result = retry_failed_notifications()

        self.assertEqual(result['retried'], 0)

    def test_cleanup_old_notifications_task(self):
        """Test cleaning up old notifications."""
        # Create old read notification
        old_notification = Notification.objects.create(
            email='old@example.com',
            subject='Old',
            message_text='Old message',
            channel=NotificationTemplate.EMAIL,
            status=Notification.READ
        )
        # Manually set old created_at
        old_notification.created_at = timezone.now() - timedelta(days=100)
        old_notification.save()

        # Create recent notification
        recent_notification = Notification.objects.create(
            email='recent@example.com',
            subject='Recent',
            message_text='Recent message',
            channel=NotificationTemplate.EMAIL,
            status=Notification.READ
        )

        result = cleanup_old_notifications()

        self.assertEqual(result['deleted'], 1)
        # Recent notification should still exist
        self.assertTrue(Notification.objects.filter(id=recent_notification.id).exists())
        # Old notification should be deleted
        self.assertFalse(Notification.objects.filter(id=old_notification.id).exists())

    def test_send_notification_async_task(self):
        """Test sending single notification asynchronously."""
        notification = Notification.objects.create(
            email='async@example.com',
            subject='Async Test',
            message_text='Async message',
            channel=NotificationTemplate.EMAIL,
            status=Notification.PENDING
        )

        result = send_notification_async(notification.id)

        self.assertTrue(result['sent'])
        self.assertEqual(result['notification_id'], str(notification.id))
        self.assertEqual(len(mail.outbox), 1)

    def test_send_notification_async_not_found(self):
        """Test async send with non-existent notification."""
        from uuid import uuid4

        result = send_notification_async(uuid4())

        self.assertIn('error', result)
        self.assertEqual(result['error'], 'Notification not found')
