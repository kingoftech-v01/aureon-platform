"""
Django app configuration for clients app.
"""

from django.apps import AppConfig


class ClientsConfig(AppConfig):
    """Configuration for the Clients app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clients'
    verbose_name = 'Client Management (CRM)'

    def ready(self):
        """Import signals when app is ready."""
        import apps.clients.signals  # noqa
