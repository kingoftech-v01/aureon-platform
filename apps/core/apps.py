from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core Security'

    def ready(self):
        import apps.core.validators  # noqa: F401 — register custom validators
        try:
            import apps.core.security  # noqa: F401 — register rate limiters, IP blockers
        except Exception:
            # Security module may fail at import if Redis/cache is unavailable
            # (e.g. during migrations or tests). It will be loaded on first use.
            import logging
            logging.getLogger(__name__).warning(
                'Core security module deferred — cache backend not available at startup'
            )
