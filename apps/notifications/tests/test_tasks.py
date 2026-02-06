"""Tests for notifications Celery tasks."""

import uuid
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from django.utils import timezone
from datetime import timedelta, date
from apps.notifications.models import Notification, NotificationTemplate
from apps.notifications.tasks import (
    send_pending_notifications,
    send_overdue_invoice_reminders,
    send_upcoming_payment_reminders,
    send_contract_expiring_reminders,
    retry_failed_notifications,
    cleanup_old_notifications,
    send_notification_async,
)


@pytest.mark.django_db
class TestSendPendingNotifications:
    """Tests for send_pending_notifications task."""

    def _create_notification(self, status=Notification.PENDING, channel=NotificationTemplate.EMAIL, **kwargs):
        """Helper to create a notification."""
        defaults = {
            'email': 'test@example.com',
            'subject': 'Test',
            'message_text': 'Test body',
            'channel': channel,
            'status': status,
        }
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)

    @patch('apps.notifications.tasks.EmailService')
    def test_send_pending_email_notifications_success(self, mock_email_service):
        """Test sending pending email notifications successfully."""
        mock_email_service.send_email.return_value = True
        self._create_notification()
        self._create_notification(subject='Second')

        result = send_pending_notifications()

        assert result['sent'] == 2
        assert result['failed'] == 0
        assert mock_email_service.send_email.call_count == 2

    @patch('apps.notifications.tasks.EmailService')
    def test_send_pending_notifications_with_failures(self, mock_email_service):
        """Test sending pending notifications with some failures."""
        mock_email_service.send_email.side_effect = [True, False, True]
        self._create_notification(subject='Notif 1')
        self._create_notification(subject='Notif 2')
        self._create_notification(subject='Notif 3')

        result = send_pending_notifications()

        assert result['sent'] == 2
        assert result['failed'] == 1

    @patch('apps.notifications.tasks.EmailService')
    def test_send_pending_notifications_none_pending(self, mock_email_service):
        """Test when there are no pending notifications."""
        self._create_notification(status=Notification.SENT)

        result = send_pending_notifications()

        assert result['sent'] == 0
        assert result['failed'] == 0
        mock_email_service.send_email.assert_not_called()

    @patch('apps.notifications.tasks.EmailService')
    def test_send_pending_skips_non_email_channels(self, mock_email_service):
        """Test that non-email channels are skipped."""
        self._create_notification(channel=NotificationTemplate.SMS)
        self._create_notification(channel=NotificationTemplate.IN_APP)

        result = send_pending_notifications()

        assert result['sent'] == 0
        assert result['failed'] == 0
        mock_email_service.send_email.assert_not_called()

    @patch('apps.notifications.tasks.EmailService')
    def test_send_pending_notifications_limit(self, mock_email_service):
        """Test that only up to 100 notifications are processed at a time."""
        mock_email_service.send_email.return_value = True
        # Create 105 pending notifications
        for i in range(105):
            self._create_notification(subject=f'Notif {i}')

        result = send_pending_notifications()

        assert result['sent'] == 100
        assert mock_email_service.send_email.call_count == 100

    @patch('apps.notifications.tasks.EmailService')
    def test_send_pending_all_fail(self, mock_email_service):
        """Test when all notifications fail to send."""
        mock_email_service.send_email.return_value = False
        self._create_notification()

        result = send_pending_notifications()

        assert result['sent'] == 0
        assert result['failed'] == 1


@pytest.mark.django_db
class TestSendOverdueInvoiceReminders:
    """Tests for send_overdue_invoice_reminders task."""

    @patch('apps.notifications.tasks.NotificationService')
    def test_send_overdue_reminders(self, mock_service):
        """Test sending reminders for overdue invoices."""
        from apps.invoicing.models import Invoice
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='test@example.com',
            lifecycle_stage=Client.ACTIVE,
        )
        invoice = Invoice.objects.create(
            client=client,
            status=Invoice.SENT,
            issue_date=date.today() - timedelta(days=45),
            due_date=date.today() - timedelta(days=15),
            subtotal=1000,
            total=1000,
        )

        result = send_overdue_invoice_reminders()

        assert result['reminded'] == 1
        mock_service.send_invoice_notification.assert_called_once_with(
            invoice=invoice,
            template_type=NotificationTemplate.INVOICE_OVERDUE,
        )

    @patch('apps.notifications.tasks.NotificationService')
    def test_skip_recently_reminded(self, mock_service):
        """Test that invoices reminded in last 7 days are skipped."""
        from apps.invoicing.models import Invoice
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='test@example.com',
            lifecycle_stage=Client.ACTIVE,
        )
        invoice = Invoice.objects.create(
            client=client,
            status=Invoice.SENT,
            issue_date=date.today() - timedelta(days=45),
            due_date=date.today() - timedelta(days=15),
            subtotal=1000,
            total=1000,
        )

        # Create a recent reminder notification
        template = NotificationTemplate.objects.create(
            name='Overdue',
            template_type=NotificationTemplate.INVOICE_OVERDUE,
            body_text='Overdue',
        )
        Notification.objects.create(
            email='test@example.com',
            subject='Overdue reminder',
            message_text='Your invoice is overdue.',
            template=template,
            related_invoice=invoice,
        )

        result = send_overdue_invoice_reminders()

        assert result['reminded'] == 0
        mock_service.send_invoice_notification.assert_not_called()

    @patch('apps.notifications.tasks.NotificationService')
    def test_no_overdue_invoices(self, mock_service):
        """Test when there are no overdue invoices."""
        result = send_overdue_invoice_reminders()

        assert result['reminded'] == 0
        mock_service.send_invoice_notification.assert_not_called()

    @patch('apps.notifications.tasks.NotificationService')
    def test_skip_draft_invoices(self, mock_service):
        """Test that draft invoices are not considered overdue."""
        from apps.invoicing.models import Invoice
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='test@example.com',
            lifecycle_stage=Client.ACTIVE,
        )
        Invoice.objects.create(
            client=client,
            status=Invoice.DRAFT,
            issue_date=date.today() - timedelta(days=45),
            due_date=date.today() - timedelta(days=15),
            subtotal=1000,
            total=1000,
        )

        result = send_overdue_invoice_reminders()

        assert result['reminded'] == 0

    @patch('apps.notifications.tasks.NotificationService')
    def test_viewed_overdue_invoice(self, mock_service):
        """Test that viewed overdue invoices get reminders."""
        from apps.invoicing.models import Invoice
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='test@example.com',
            lifecycle_stage=Client.ACTIVE,
        )
        Invoice.objects.create(
            client=client,
            status=Invoice.VIEWED,
            issue_date=date.today() - timedelta(days=45),
            due_date=date.today() - timedelta(days=15),
            subtotal=1000,
            total=1000,
        )

        result = send_overdue_invoice_reminders()

        assert result['reminded'] == 1


@pytest.mark.django_db
class TestSendUpcomingPaymentReminders:
    """Tests for send_upcoming_payment_reminders task."""

    @patch('apps.notifications.tasks.NotificationService')
    def test_send_upcoming_reminders(self, mock_service):
        """Test sending reminders for invoices due in 3 days."""
        from apps.invoicing.models import Invoice
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='test@example.com',
            lifecycle_stage=Client.ACTIVE,
        )
        invoice = Invoice.objects.create(
            client=client,
            status=Invoice.SENT,
            issue_date=date.today() - timedelta(days=27),
            due_date=(timezone.now() + timedelta(days=3)).date(),
            subtotal=1000,
            total=1000,
        )

        result = send_upcoming_payment_reminders()

        assert result['reminded'] == 1
        mock_service.send_invoice_notification.assert_called_once_with(
            invoice=invoice,
            template_type=NotificationTemplate.REMINDER_PAYMENT_DUE,
        )

    @patch('apps.notifications.tasks.NotificationService')
    def test_skip_already_reminded(self, mock_service):
        """Test that invoices already reminded are skipped."""
        from apps.invoicing.models import Invoice
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='test@example.com',
            lifecycle_stage=Client.ACTIVE,
        )
        invoice = Invoice.objects.create(
            client=client,
            status=Invoice.SENT,
            issue_date=date.today() - timedelta(days=27),
            due_date=(timezone.now() + timedelta(days=3)).date(),
            subtotal=1000,
            total=1000,
        )

        template = NotificationTemplate.objects.create(
            name='Payment Due',
            template_type=NotificationTemplate.REMINDER_PAYMENT_DUE,
            body_text='Payment due',
        )
        Notification.objects.create(
            email='test@example.com',
            subject='Payment due reminder',
            message_text='Payment due soon.',
            template=template,
            related_invoice=invoice,
        )

        result = send_upcoming_payment_reminders()

        assert result['reminded'] == 0

    @patch('apps.notifications.tasks.NotificationService')
    def test_no_upcoming_invoices(self, mock_service):
        """Test when there are no upcoming invoices."""
        result = send_upcoming_payment_reminders()

        assert result['reminded'] == 0

    @patch('apps.notifications.tasks.NotificationService')
    def test_skip_paid_invoices(self, mock_service):
        """Test that already paid invoices are not reminded."""
        from apps.invoicing.models import Invoice
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='test@example.com',
            lifecycle_stage=Client.ACTIVE,
        )
        Invoice.objects.create(
            client=client,
            status=Invoice.PAID,
            issue_date=date.today() - timedelta(days=27),
            due_date=(timezone.now() + timedelta(days=3)).date(),
            subtotal=1000,
            total=1000,
        )

        result = send_upcoming_payment_reminders()

        assert result['reminded'] == 0


@pytest.mark.django_db
class TestSendContractExpiringReminders:
    """Tests for send_contract_expiring_reminders task."""

    @patch('apps.notifications.tasks.NotificationService')
    def test_send_expiring_reminders(self, mock_service):
        """Test sending reminders for contracts expiring in 30 days."""
        from apps.contracts.models import Contract
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='test@example.com',
            lifecycle_stage=Client.ACTIVE,
        )
        contract = Contract.objects.create(
            client=client,
            title='Test Contract',
            description='Test contract description',
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=335),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            value=10000,
        )

        result = send_contract_expiring_reminders()

        assert result['reminded'] == 1
        mock_service.send_contract_notification.assert_called_once_with(
            contract=contract,
            template_type=NotificationTemplate.CONTRACT_EXPIRING,
        )

    @patch('apps.notifications.tasks.NotificationService')
    def test_skip_already_reminded_contracts(self, mock_service):
        """Test that contracts already reminded are skipped."""
        from apps.contracts.models import Contract
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='test@example.com',
            lifecycle_stage=Client.ACTIVE,
        )
        contract = Contract.objects.create(
            client=client,
            title='Test Contract',
            description='Test contract',
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=335),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            value=10000,
        )

        template = NotificationTemplate.objects.create(
            name='Contract Expiring',
            template_type=NotificationTemplate.CONTRACT_EXPIRING,
            body_text='Contract expiring',
        )
        Notification.objects.create(
            email='test@example.com',
            subject='Contract expiring',
            message_text='Your contract is expiring.',
            template=template,
            related_contract=contract,
        )

        result = send_contract_expiring_reminders()

        assert result['reminded'] == 0

    @patch('apps.notifications.tasks.NotificationService')
    def test_no_expiring_contracts(self, mock_service):
        """Test when there are no expiring contracts."""
        result = send_contract_expiring_reminders()

        assert result['reminded'] == 0

    @patch('apps.notifications.tasks.NotificationService')
    def test_skip_non_active_contracts(self, mock_service):
        """Test that non-active contracts are not reminded."""
        from apps.contracts.models import Contract
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='test@example.com',
            lifecycle_stage=Client.ACTIVE,
        )
        Contract.objects.create(
            client=client,
            title='Draft Contract',
            description='Draft',
            status=Contract.DRAFT,
            start_date=date.today(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            value=5000,
        )

        result = send_contract_expiring_reminders()

        assert result['reminded'] == 0


@pytest.mark.django_db
class TestRetryFailedNotifications:
    """Tests for retry_failed_notifications task."""

    def _create_notification(self, status=Notification.FAILED, retry_count=0, **kwargs):
        defaults = {
            'email': 'test@example.com',
            'subject': 'Test',
            'message_text': 'Test body',
            'channel': NotificationTemplate.EMAIL,
            'status': status,
            'retry_count': retry_count,
        }
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)

    @patch('apps.notifications.tasks.EmailService')
    def test_retry_failed_notifications_success(self, mock_email_service):
        """Test retrying failed notifications successfully."""
        mock_email_service.send_email.return_value = True
        self._create_notification(retry_count=1)

        result = retry_failed_notifications()

        assert result['retried'] == 1

    @patch('apps.notifications.tasks.EmailService')
    def test_skip_notifications_at_max_retries(self, mock_email_service):
        """Test that notifications with retry_count >= 3 are skipped."""
        self._create_notification(retry_count=3)
        self._create_notification(retry_count=5)

        result = retry_failed_notifications()

        assert result['retried'] == 0
        mock_email_service.send_email.assert_not_called()

    @patch('apps.notifications.tasks.EmailService')
    def test_retry_limit_50(self, mock_email_service):
        """Test that only up to 50 failed notifications are retried."""
        mock_email_service.send_email.return_value = True
        for i in range(55):
            self._create_notification(subject=f'Failed {i}', retry_count=1)

        result = retry_failed_notifications()

        assert result['retried'] == 50

    @patch('apps.notifications.tasks.EmailService')
    def test_retry_non_email_channels_skipped(self, mock_email_service):
        """Test that non-email failed notifications are skipped."""
        self._create_notification(channel=NotificationTemplate.SMS, retry_count=1)

        result = retry_failed_notifications()

        assert result['retried'] == 0

    @patch('apps.notifications.tasks.EmailService')
    def test_retry_fails_again(self, mock_email_service):
        """Test when retry also fails."""
        mock_email_service.send_email.return_value = False
        self._create_notification(retry_count=1)

        result = retry_failed_notifications()

        assert result['retried'] == 0


@pytest.mark.django_db
class TestCleanupOldNotifications:
    """Tests for cleanup_old_notifications task."""

    def _create_notification(self, status=Notification.READ, days_old=100, **kwargs):
        defaults = {
            'email': 'test@example.com',
            'subject': 'Test',
            'message_text': 'Test body',
            'status': status,
        }
        defaults.update(kwargs)
        notification = Notification.objects.create(**defaults)
        # Update created_at to simulate age
        Notification.objects.filter(pk=notification.pk).update(
            created_at=timezone.now() - timedelta(days=days_old)
        )
        return notification

    def test_cleanup_old_read_notifications(self):
        """Test cleaning up old read notifications."""
        self._create_notification(status=Notification.READ, days_old=100)
        self._create_notification(status=Notification.READ, days_old=95)

        result = cleanup_old_notifications()

        assert result['deleted'] == 2
        assert Notification.objects.count() == 0

    def test_cleanup_old_delivered_notifications(self):
        """Test cleaning up old delivered notifications."""
        self._create_notification(status=Notification.DELIVERED, days_old=100)

        result = cleanup_old_notifications()

        assert result['deleted'] == 1

    def test_skip_recent_notifications(self):
        """Test that recent notifications are not cleaned up."""
        self._create_notification(status=Notification.READ, days_old=30)
        self._create_notification(status=Notification.DELIVERED, days_old=50)

        result = cleanup_old_notifications()

        assert result['deleted'] == 0
        assert Notification.objects.count() == 2

    def test_skip_pending_notifications(self):
        """Test that pending notifications are never cleaned up."""
        self._create_notification(status=Notification.PENDING, days_old=100)

        result = cleanup_old_notifications()

        assert result['deleted'] == 0

    def test_skip_failed_notifications(self):
        """Test that failed notifications are not cleaned up."""
        self._create_notification(status=Notification.FAILED, days_old=100)

        result = cleanup_old_notifications()

        assert result['deleted'] == 0

    def test_skip_sent_notifications(self):
        """Test that sent notifications are not cleaned up."""
        self._create_notification(status=Notification.SENT, days_old=100)

        result = cleanup_old_notifications()

        assert result['deleted'] == 0

    def test_mixed_statuses_and_ages(self):
        """Test cleanup with mix of statuses and ages."""
        # Should be deleted
        self._create_notification(status=Notification.READ, days_old=100)
        self._create_notification(status=Notification.DELIVERED, days_old=95)
        # Should be kept
        self._create_notification(status=Notification.READ, days_old=10)
        self._create_notification(status=Notification.PENDING, days_old=100)
        self._create_notification(status=Notification.FAILED, days_old=100)

        result = cleanup_old_notifications()

        assert result['deleted'] == 2
        assert Notification.objects.count() == 3

    def test_cleanup_no_notifications(self):
        """Test cleanup when there are no notifications."""
        result = cleanup_old_notifications()

        assert result['deleted'] == 0


@pytest.mark.django_db
class TestSendNotificationAsync:
    """Tests for send_notification_async task."""

    def _create_notification(self, **kwargs):
        defaults = {
            'email': 'test@example.com',
            'subject': 'Test',
            'message_text': 'Test body',
            'channel': NotificationTemplate.EMAIL,
            'status': Notification.PENDING,
        }
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)

    @patch('apps.notifications.tasks.EmailService')
    def test_send_async_success(self, mock_email_service):
        """Test sending a notification asynchronously."""
        mock_email_service.send_email.return_value = True
        notification = self._create_notification()

        result = send_notification_async(str(notification.id))

        assert result['sent'] is True
        assert result['notification_id'] == str(notification.id)

    @patch('apps.notifications.tasks.EmailService')
    def test_send_async_failure(self, mock_email_service):
        """Test handling send failure."""
        mock_email_service.send_email.return_value = False
        notification = self._create_notification()

        result = send_notification_async(str(notification.id))

        assert result['sent'] is False

    def test_send_async_not_found(self):
        """Test sending a notification that does not exist."""
        fake_id = str(uuid.uuid4())

        result = send_notification_async(fake_id)

        assert result['error'] == 'Notification not found'

    @patch('apps.notifications.tasks.EmailService')
    def test_send_async_unsupported_channel(self, mock_email_service):
        """Test sending notification with unsupported channel."""
        notification = self._create_notification(channel=NotificationTemplate.SMS)

        result = send_notification_async(str(notification.id))

        assert result['error'] == 'Unsupported channel'
        mock_email_service.send_email.assert_not_called()

    @patch('apps.notifications.tasks.EmailService')
    def test_send_async_in_app_unsupported(self, mock_email_service):
        """Test sending notification with in_app channel returns unsupported."""
        notification = self._create_notification(channel=NotificationTemplate.IN_APP)

        result = send_notification_async(str(notification.id))

        assert result['error'] == 'Unsupported channel'
