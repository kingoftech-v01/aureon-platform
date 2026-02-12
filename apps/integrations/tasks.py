"""
Integrations Celery tasks for Aureon SaaS Platform.

These tasks handle third-party integration sync, token refresh,
and webhook processing using the service layer.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_external_service(self, service_name, data):
    """Sync data with an external service using the service layer."""
    try:
        from .models import Integration
        from .services import get_service

        integration_id = data.get('integration_id')
        sync_type = data.get('sync_type', 'full')

        if integration_id:
            integration = Integration.objects.get(id=integration_id)
        else:
            integration = Integration.objects.filter(
                service_type=service_name, status=Integration.ACTIVE,
            ).first()
            if not integration:
                logger.warning(f"No active {service_name} integration found")
                return {'status': 'skipped', 'message': f'No active {service_name} integration'}

        service = get_service(integration)

        # Refresh token if needed before sync
        if integration.needs_reauth:
            service.refresh_token()

        log = service.sync(sync_type=sync_type)

        return {
            'status': 'success',
            'service': service_name,
            'records_synced': log.records_synced,
            'duration_ms': log.duration_ms,
        }
    except Exception as exc:
        logger.error(f"External sync failed for {service_name}: {exc}")
        raise self.retry(exc=exc, countdown=120)


@shared_task(bind=True, max_retries=2)
def scheduled_sync_all(self):
    """
    Run scheduled sync for all active integrations whose interval has elapsed.
    Should be called periodically via Celery Beat (e.g. every 15 minutes).
    """
    try:
        from .models import Integration

        now = timezone.now()
        active_integrations = Integration.objects.filter(
            status=Integration.ACTIVE,
            sync_enabled=True,
        )

        queued = 0
        for integration in active_integrations:
            # Check if enough time has elapsed since last sync
            if integration.last_sync_at:
                from datetime import timedelta
                next_sync = integration.last_sync_at + timedelta(
                    minutes=integration.sync_interval_minutes
                )
                if now < next_sync:
                    continue

            sync_external_service.delay(
                integration.service_type,
                {
                    'integration_id': str(integration.id),
                    'sync_type': 'incremental',
                },
            )
            queued += 1

        logger.info(f"Queued {queued} scheduled syncs")
        return {'status': 'success', 'queued': queued}

    except Exception as exc:
        logger.error(f"Scheduled sync failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=2)
def refresh_all_tokens(self):
    """Refresh OAuth tokens for integrations nearing expiry."""
    try:
        from .models import Integration
        from .services import get_service

        refreshed = 0
        failed = 0

        integrations = Integration.objects.filter(
            status=Integration.ACTIVE,
            token_expires_at__isnull=False,
        )

        for integration in integrations:
            if not integration.needs_reauth:
                continue
            try:
                service = get_service(integration)
                service.refresh_token()
                refreshed += 1
            except Exception:
                logger.exception(f"Token refresh failed for {integration.name}")
                failed += 1

        logger.info(f"Token refresh: {refreshed} refreshed, {failed} failed")
        return {'status': 'success', 'refreshed': refreshed, 'failed': failed}

    except Exception as exc:
        logger.error(f"Token refresh task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=2)
def process_integration_webhook(self, integration_type, payload):
    """Process webhook from an integration partner."""
    try:
        from .models import Integration, IntegrationSyncLog

        logger.info(f"Processing {integration_type} webhook...")

        integration = Integration.objects.filter(
            service_type=integration_type, status=Integration.ACTIVE,
        ).first()

        if not integration:
            logger.warning(f"No active {integration_type} integration for webhook")
            return {'status': 'skipped', 'message': f'No active {integration_type} integration'}

        log = IntegrationSyncLog.objects.create(
            integration=integration,
            status='running',
            metadata={'source': 'webhook', 'payload_keys': list(payload.keys())},
        )

        if integration_type == 'quickbooks':
            result = _process_quickbooks_webhook(payload)
        elif integration_type == 'xero':
            result = _process_xero_webhook(payload)
        elif integration_type == 'slack':
            result = _process_slack_webhook(payload)
        else:
            result = {'processed': False, 'message': f'No webhook handler for {integration_type}'}

        log.status = 'success' if result.get('processed') else 'skipped'
        log.records_synced = result.get('records_processed', 0)
        log.metadata.update(result)
        log.completed_at = timezone.now()
        log.save()

        logger.info(f"Processed {integration_type} webhook")
        return {'status': 'success', 'integration': integration_type, 'result': result}

    except Exception as exc:
        logger.error(f"Integration webhook failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


def _process_quickbooks_webhook(payload):
    """Process QuickBooks webhook event and sync affected entities."""
    entities = []
    for notification in payload.get('eventNotifications', []):
        for entity in notification.get('dataChangeEvent', {}).get('entities', []):
            entities.append({
                'name': entity.get('name', 'unknown'),
                'id': entity.get('id', ''),
                'operation': entity.get('operation', ''),
            })

    logger.info(f"QuickBooks webhook: {len(entities)} entity changes")
    return {
        'processed': True,
        'records_processed': len(entities),
        'entities': entities,
    }


def _process_xero_webhook(payload):
    """Process Xero webhook event."""
    events = payload.get('events', [])
    processed = []
    for event in events:
        processed.append({
            'resourceId': event.get('resourceId', ''),
            'eventCategory': event.get('eventCategory', ''),
            'eventType': event.get('eventType', ''),
        })

    logger.info(f"Xero webhook: {len(processed)} events")
    return {
        'processed': True,
        'records_processed': len(processed),
        'events': processed,
    }


def _process_slack_webhook(payload):
    """Process Slack webhook (e.g. interactive messages, slash commands)."""
    event_type = payload.get('type', 'unknown')
    logger.info(f"Slack webhook type: {event_type}")
    return {
        'processed': True,
        'records_processed': 1,
        'event_type': event_type,
    }
