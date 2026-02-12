"""Analytics signals for tracking activity."""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='contracts.Contract')
def log_contract_activity(sender, instance, created, **kwargs):
    """Log contract creation/update activity."""
    try:
        from apps.analytics.services import ActivityLogger
        if created:
            ActivityLogger.log_activity(
                activity_type='contract_created',
                description=f"Contract {instance.contract_number} created for {instance.client}",
            )
        elif instance.status == 'active' and instance.is_signed:
            ActivityLogger.log_activity(
                activity_type='contract_signed',
                description=f"Contract {instance.contract_number} signed",
            )
    except Exception as e:
        logger.warning(f"Could not log contract activity: {e}")


@receiver(post_save, sender='invoicing.Invoice')
def log_invoice_activity(sender, instance, created, **kwargs):
    """Log invoice creation/update activity."""
    try:
        from apps.analytics.services import ActivityLogger
        if created:
            ActivityLogger.log_activity(
                activity_type='invoice_created',
                description=f"Invoice {instance.invoice_number} created for {instance.client}",
            )
        elif instance.status == 'paid':
            ActivityLogger.log_activity(
                activity_type='invoice_paid',
                description=f"Invoice {instance.invoice_number} paid",
            )
    except Exception as e:
        logger.warning(f"Could not log invoice activity: {e}")


@receiver(post_save, sender='payments.Payment')
def log_payment_activity(sender, instance, created, **kwargs):
    """Log payment activity."""
    try:
        from apps.analytics.services import ActivityLogger
        if instance.status == 'succeeded':
            ActivityLogger.log_activity(
                activity_type='payment_received',
                description=f"Payment of {instance.currency} {instance.amount} received",
            )
    except Exception as e:
        logger.warning(f"Could not log payment activity: {e}")
