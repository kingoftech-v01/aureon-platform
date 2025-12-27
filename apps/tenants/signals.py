"""
Signals for tenant app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Tenant, Domain


@receiver(post_save, sender=Tenant)
def create_tenant_schema(sender, instance, created, **kwargs):
    """
    Create database schema when a new tenant is created.

    This is handled automatically by django-tenants, but we can add
    additional post-creation logic here.
    """
    if created:
        # Log tenant creation
        import logging
        logger = logging.getLogger('aureon.tenants')
        logger.info(f"New tenant created: {instance.name} ({instance.schema_name})")


@receiver(post_save, sender=Domain)
def log_domain_creation(sender, instance, created, **kwargs):
    """Log domain creation."""
    if created:
        import logging
        logger = logging.getLogger('aureon.tenants')
        logger.info(f"New domain created: {instance.domain} for tenant {instance.tenant.name}")
