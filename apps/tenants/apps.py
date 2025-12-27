"""
Django app configuration for tenants app.
"""

from django.apps import AppConfig


class TenantsConfig(AppConfig):
    """Configuration for the Tenants app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tenants'
    verbose_name = 'Tenant Management'

    def ready(self):
        """Import signals when app is ready."""
        import apps.tenants.signals  # noqa
