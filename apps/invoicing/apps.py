"""
Invoicing app configuration.
"""

from django.apps import AppConfig


class InvoicingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.invoicing'
    verbose_name = 'Invoicing'

    def ready(self):
        """Import signals when app is ready."""
        try:
            import apps.invoicing.signals  # noqa
        except ImportError:
            pass
