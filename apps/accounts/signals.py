"""
Signals for accounts app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """Log user creation."""
    if created:
        import logging
        logger = logging.getLogger('aureon.accounts')
        logger.info(f"New user created: {instance.email} - Tenant: {instance.tenant}")
