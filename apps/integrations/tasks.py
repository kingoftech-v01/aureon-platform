"""
Integrations Celery tasks for Aureon SaaS Platform.

These tasks handle third-party integrations.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_external_service(self, service_name, data):
    """
    Sync data with an external service.
    """
    try:
        logger.info(f"Syncing with {service_name}...")
        return {'status': 'success', 'service': service_name}
    except Exception as exc:
        logger.error(f"External sync failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


@shared_task(bind=True, max_retries=2)
def process_integration_webhook(self, integration_type, payload):
    """
    Process webhook from an integration.
    """
    try:
        logger.info(f"Processing {integration_type} webhook...")
        return {'status': 'success', 'integration': integration_type}
    except Exception as exc:
        logger.error(f"Integration webhook failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
