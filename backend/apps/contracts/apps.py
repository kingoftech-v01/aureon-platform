"""
Contracts app configuration.
"""

from django.apps import AppConfig


class ContractsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.contracts'
    verbose_name = 'Contracts'

    def ready(self):
        """Import signals when app is ready."""
        try:
            import apps.contracts.signals  # noqa
        except ImportError:
            pass
