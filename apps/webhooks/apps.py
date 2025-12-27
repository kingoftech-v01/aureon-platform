"""Webhooks app configuration."""

from django.apps import AppConfig


class WebhooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.webhooks'
    verbose_name = 'Webhooks'

    def ready(self):
        """Import signals when app is ready."""
        try:
            import apps.webhooks.signals  # noqa
        except ImportError:
            pass
