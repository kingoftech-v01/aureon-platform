"""
Integrations Celery tasks for Aureon SaaS Platform.

These tasks handle third-party integrations.
"""
from celery import shared_task
from django.utils import timezone
import logging
import json

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_external_service(self, service_name, data):
    """Sync data with an external service (e.g., QuickBooks, Xero)."""
    try:
        import requests

        logger.info(f"Syncing with {service_name}...")

        # Service-specific sync logic
        if service_name == 'quickbooks':
            result = _sync_quickbooks(data)
        elif service_name == 'xero':
            result = _sync_xero(data)
        else:
            logger.warning(f"Unknown service: {service_name}")
            result = {'synced': False, 'message': f'Service {service_name} not configured'}

        logger.info(f"Sync with {service_name} completed")
        return {'status': 'success', 'service': service_name, 'result': result}
    except Exception as exc:
        logger.error(f"External sync failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


def _sync_quickbooks(data):
    """Sync data with QuickBooks."""
    from django.conf import settings

    api_url = getattr(settings, 'QUICKBOOKS_API_URL', None)
    api_token = getattr(settings, 'QUICKBOOKS_API_TOKEN', None)

    if not api_url or not api_token:
        logger.info("QuickBooks not configured, skipping sync")
        return {'synced': False, 'message': 'QuickBooks not configured'}

    import requests
    headers = {'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'}
    response = requests.post(f"{api_url}/sync", json=data, headers=headers, timeout=30)
    response.raise_for_status()
    return {'synced': True, 'response': response.json()}


def _sync_xero(data):
    """Sync data with Xero."""
    from django.conf import settings

    api_url = getattr(settings, 'XERO_API_URL', None)
    api_token = getattr(settings, 'XERO_API_TOKEN', None)

    if not api_url or not api_token:
        logger.info("Xero not configured, skipping sync")
        return {'synced': False, 'message': 'Xero not configured'}

    import requests
    headers = {'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'}
    response = requests.post(f"{api_url}/sync", json=data, headers=headers, timeout=30)
    response.raise_for_status()
    return {'synced': True, 'response': response.json()}


@shared_task(bind=True, max_retries=2)
def process_integration_webhook(self, integration_type, payload):
    """Process webhook from an integration partner."""
    try:
        logger.info(f"Processing {integration_type} webhook...")

        if integration_type == 'quickbooks':
            result = _process_quickbooks_webhook(payload)
        elif integration_type == 'xero':
            result = _process_xero_webhook(payload)
        else:
            result = {'processed': False, 'message': f'Unknown integration: {integration_type}'}

        logger.info(f"Processed {integration_type} webhook")
        return {'status': 'success', 'integration': integration_type, 'result': result}
    except Exception as exc:
        logger.error(f"Integration webhook failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


def _process_quickbooks_webhook(payload):
    """Process QuickBooks webhook event."""
    event_type = payload.get('eventNotifications', [{}])[0].get('dataChangeEvent', {}).get('entities', [{}])[0].get('name', 'unknown')
    logger.info(f"QuickBooks event: {event_type}")
    return {'processed': True, 'event_type': event_type}


def _process_xero_webhook(payload):
    """Process Xero webhook event."""
    events = payload.get('events', [])
    logger.info(f"Xero events received: {len(events)}")
    return {'processed': True, 'events_count': len(events)}
