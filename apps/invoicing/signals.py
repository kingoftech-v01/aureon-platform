"""
Signals for the invoicing app.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Invoice, InvoiceItem


@receiver(post_save, sender=InvoiceItem)
def recalculate_invoice_on_item_save(sender, instance, created, **kwargs):
    """
    Recalculate invoice totals when item is saved.
    """
    instance.invoice.calculate_totals()


@receiver(post_delete, sender=InvoiceItem)
def recalculate_invoice_on_item_delete(sender, instance, **kwargs):
    """
    Recalculate invoice totals when item is deleted.
    """
    instance.invoice.calculate_totals()
