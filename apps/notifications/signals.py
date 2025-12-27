"""Signal handlers for automatic notification triggers."""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.invoicing.models import Invoice
from apps.payments.models import Payment
from apps.contracts.models import Contract
from apps.clients.models import Client
from .models import NotificationTemplate
from .services import NotificationService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Invoice)
def invoice_notification_handler(sender, instance, created, **kwargs):
    """
    Send notifications when invoice status changes.

    Args:
        sender: Invoice model
        instance: Invoice instance
        created: Whether this is a new invoice
    """
    # Don't send notifications for draft invoices
    if instance.status == Invoice.DRAFT:
        return

    try:
        # New invoice sent to client
        if created and instance.status == Invoice.SENT:
            NotificationService.send_invoice_notification(
                invoice=instance,
                template_type=NotificationTemplate.INVOICE_SENT
            )
            logger.info(f"Sent invoice notification for {instance.invoice_number}")

        # Invoice paid
        elif instance.status == Invoice.PAID and hasattr(instance, '_status_changed'):
            if instance._status_changed:
                NotificationService.send_invoice_notification(
                    invoice=instance,
                    template_type=NotificationTemplate.INVOICE_PAID
                )
                logger.info(f"Sent payment confirmation for {instance.invoice_number}")

    except Exception as e:
        logger.error(f"Failed to send invoice notification: {str(e)}", exc_info=True)


@receiver(post_save, sender=Payment)
def payment_notification_handler(sender, instance, created, **kwargs):
    """
    Send notifications when payment is received.

    Args:
        sender: Payment model
        instance: Payment instance
        created: Whether this is a new payment
    """
    # Only send for successful payments
    if instance.status != Payment.SUCCESS:
        return

    try:
        # New successful payment - send receipt
        if created or (hasattr(instance, '_status_changed') and instance._status_changed):
            NotificationService.send_payment_receipt(payment=instance)
            logger.info(f"Sent payment receipt for payment {instance.id}")

    except Exception as e:
        logger.error(f"Failed to send payment receipt: {str(e)}", exc_info=True)


@receiver(post_save, sender=Contract)
def contract_notification_handler(sender, instance, created, **kwargs):
    """
    Send notifications when contract is signed.

    Args:
        sender: Contract model
        instance: Contract instance
        created: Whether this is a new contract
    """
    try:
        # Contract signed
        if instance.is_signed and hasattr(instance, '_signature_added'):
            if instance._signature_added:
                NotificationService.send_contract_notification(
                    contract=instance,
                    template_type=NotificationTemplate.CONTRACT_SIGNED
                )
                logger.info(f"Sent contract signed notification for {instance.title}")

    except Exception as e:
        logger.error(f"Failed to send contract notification: {str(e)}", exc_info=True)


@receiver(post_save, sender=Client)
def client_notification_handler(sender, instance, created, **kwargs):
    """
    Send welcome email to new clients.

    Args:
        sender: Client model
        instance: Client instance
        created: Whether this is a new client
    """
    if not created:
        return

    try:
        # Send welcome email to new client
        if instance.lifecycle_stage in [Client.ACTIVE, Client.PROSPECT]:
            NotificationService.send_client_welcome(client=instance)
            logger.info(f"Sent welcome email to {instance.email}")

    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}", exc_info=True)


# Model method modifications to track status changes

def track_invoice_status_change(self):
    """
    Track invoice status changes for notification triggering.
    Add this to Invoice model's save method.
    """
    if self.pk:
        try:
            old_instance = Invoice.objects.get(pk=self.pk)
            self._status_changed = old_instance.status != self.status
        except Invoice.DoesNotExist:
            self._status_changed = False
    else:
        self._status_changed = False


def track_payment_status_change(self):
    """
    Track payment status changes for notification triggering.
    Add this to Payment model's save method.
    """
    if self.pk:
        try:
            old_instance = Payment.objects.get(pk=self.pk)
            self._status_changed = old_instance.status != self.status
        except Payment.DoesNotExist:
            self._status_changed = False
    else:
        self._status_changed = False


def track_contract_signature(self):
    """
    Track contract signature for notification triggering.
    Add this to Contract model's save method.
    """
    if self.pk:
        try:
            old_instance = Contract.objects.get(pk=self.pk)
            self._signature_added = (not old_instance.is_signed) and self.is_signed
        except Contract.DoesNotExist:
            self._signature_added = False
    else:
        self._signature_added = False
