"""Documents app configuration."""

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
    verbose_name = 'Document Management'

    def ready(self):
        """Import signals when app is ready."""
        try:
            import apps.documents.signals  # noqa
        except ImportError:
            pass
