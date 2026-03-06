"""
Signals for the payments app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment


@receiver(post_save, sender=Payment)
def update_invoice_on_payment(sender, instance, created, **kwargs):
    """
    Update invoice status when payment is received.
    """
    if instance.status == Payment.SUCCEEDED and not created:
        # Payment succeeded, update invoice
        instance.invoice.mark_as_paid(
            payment_amount=instance.amount,
            payment_method=instance.payment_method,
            payment_reference=instance.transaction_id
        )
