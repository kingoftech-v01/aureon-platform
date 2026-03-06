"""Celery tasks for scheduled notifications and reminders."""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Notification, NotificationTemplate
from .services import NotificationService

logger = logging.getLogger(__name__)


@shared_task
def send_pending_notifications():
    """
    Send pending notifications.

    This task runs periodically to send queued notifications.
    """
    from .services import EmailService

    pending = Notification.objects.filter(
        status=Notification.PENDING
    ).order_by('created_at')[:100]  # Process up to 100 at a time

    sent_count = 0
    failed_count = 0

    for notification in pending:
        if notification.channel == NotificationTemplate.EMAIL:
            success = EmailService.send_email(notification)
            if success:
                sent_count += 1
            else:
                failed_count += 1

    logger.info(f"Sent {sent_count} notifications, {failed_count} failed")

    return {
        'sent': sent_count,
        'failed': failed_count
    }


@shared_task
def send_overdue_invoice_reminders():
    """
    Send reminders for overdue invoices.

    Checks for overdue invoices and sends reminder emails.
    """
    from apps.invoicing.models import Invoice

    # Get overdue invoices that haven't been reminded in last 7 days
    overdue_invoices = Invoice.objects.filter(
        status__in=[Invoice.SENT, Invoice.VIEWED],
        due_date__lt=timezone.now().date()
    )

    reminded_count = 0

    for invoice in overdue_invoices:
        # Check if we've sent a reminder in the last 7 days
        recent_reminder = Notification.objects.filter(
            related_invoice=invoice,
            template__template_type=NotificationTemplate.INVOICE_OVERDUE,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).exists()

        if not recent_reminder:
            NotificationService.send_invoice_notification(
                invoice=invoice,
                template_type=NotificationTemplate.INVOICE_OVERDUE
            )
            reminded_count += 1

    logger.info(f"Sent {reminded_count} overdue invoice reminders")

    return {
        'reminded': reminded_count
    }


@shared_task
def send_upcoming_payment_reminders():
    """
    Send reminders for invoices due soon.

    Sends reminders 3 days before invoice due date.
    """
    from apps.invoicing.models import Invoice

    # Get invoices due in 3 days
    reminder_date = (timezone.now() + timedelta(days=3)).date()

    upcoming_invoices = Invoice.objects.filter(
        status__in=[Invoice.SENT, Invoice.VIEWED],
        due_date=reminder_date
    )

    reminded_count = 0

    for invoice in upcoming_invoices:
        # Check if we've already sent a reminder for this invoice
        existing_reminder = Notification.objects.filter(
            related_invoice=invoice,
            template__template_type=NotificationTemplate.REMINDER_PAYMENT_DUE
        ).exists()

        if not existing_reminder:
            NotificationService.send_invoice_notification(
                invoice=invoice,
                template_type=NotificationTemplate.REMINDER_PAYMENT_DUE
            )
            reminded_count += 1

    logger.info(f"Sent {reminded_count} upcoming payment reminders")

    return {
        'reminded': reminded_count
    }


@shared_task
def send_contract_expiring_reminders():
    """
    Send reminders for contracts expiring soon.

    Sends reminders 30 days before contract expiration.
    """
    from apps.contracts.models import Contract

    # Get contracts expiring in 30 days
    reminder_date = (timezone.now() + timedelta(days=30)).date()

    expiring_contracts = Contract.objects.filter(
        status=Contract.ACTIVE,
        end_date=reminder_date
    )

    reminded_count = 0

    for contract in expiring_contracts:
        # Check if we've already sent a reminder for this contract
        existing_reminder = Notification.objects.filter(
            related_contract=contract,
            template__template_type=NotificationTemplate.CONTRACT_EXPIRING
        ).exists()

        if not existing_reminder:
            NotificationService.send_contract_notification(
                contract=contract,
                template_type=NotificationTemplate.CONTRACT_EXPIRING
            )
            reminded_count += 1

    logger.info(f"Sent {reminded_count} contract expiring reminders")

    return {
        'reminded': reminded_count
    }


@shared_task
def retry_failed_notifications():
    """
    Retry failed notifications.

    Attempts to resend notifications that failed on first attempt.
    """
    from .services import EmailService

    failed = Notification.objects.filter(
        status=Notification.FAILED,
        retry_count__lt=3
    ).order_by('failed_at')[:50]  # Retry up to 50 at a time

    retried_count = 0

    for notification in failed:
        if notification.channel == NotificationTemplate.EMAIL:
            success = EmailService.send_email(notification)
            if success:
                retried_count += 1

    logger.info(f"Retried {retried_count} failed notifications")

    return {
        'retried': retried_count
    }


@shared_task
def cleanup_old_notifications():
    """
    Clean up old read and delivered notifications.

    Deletes notifications older than 90 days that have been read or delivered.
    """
    cutoff_date = timezone.now() - timedelta(days=90)

    deleted_count, _ = Notification.objects.filter(
        status__in=[Notification.READ, Notification.DELIVERED],
        created_at__lt=cutoff_date
    ).delete()

    logger.info(f"Cleaned up {deleted_count} old notifications")

    return {
        'deleted': deleted_count
    }


@shared_task
def send_notification_async(notification_id):
    """
    Send a single notification asynchronously.

    Args:
        notification_id: UUID of notification to send

    Returns:
        dict: Send result
    """
    from .services import EmailService

    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return {'error': 'Notification not found'}

    if notification.channel == NotificationTemplate.EMAIL:
        success = EmailService.send_email(notification)
        return {
            'sent': success,
            'notification_id': str(notification_id)
        }

    return {'error': 'Unsupported channel'}
