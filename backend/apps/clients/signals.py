"""
Signals for clients app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Client


@receiver(post_save, sender=Client)
def log_client_creation(sender, instance, created, **kwargs):
    """Log client creation."""
    if created:
        import logging
        logger = logging.getLogger('aureon.clients')
        logger.info(f"New client created: {instance.get_display_name()} ({instance.email})")
