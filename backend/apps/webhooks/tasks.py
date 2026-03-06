"""Celery tasks for webhook processing."""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_stripe_webhook(self, webhook_event_id):
    """
    Process a Stripe webhook event asynchronously.

    Args:
        webhook_event_id: UUID of the WebhookEvent to process

    Returns:
        dict: Processing result
    """
    from .models import WebhookEvent
    from .stripe_handlers import StripeWebhookHandler

    try:
        webhook_event = WebhookEvent.objects.get(id=webhook_event_id)
    except WebhookEvent.DoesNotExist:
        logger.error(f"WebhookEvent {webhook_event_id} not found")
        return {'error': 'WebhookEvent not found'}

    try:
        webhook_event.mark_as_processing()

        # Handle the event
        handler = StripeWebhookHandler(webhook_event.payload)
        result = handler.handle()

        webhook_event.mark_as_processed(result)

        logger.info(f"Successfully processed webhook {webhook_event.event_id}")
        return result

    except Exception as e:
        logger.error(f"Error processing webhook {webhook_event.event_id}: {str(e)}", exc_info=True)

        # Retry with exponential backoff
        if webhook_event.can_retry:
            webhook_event.mark_as_failed(str(e), should_retry=True)
            raise self.retry(exc=e, countdown=60 * (2 ** webhook_event.retry_count))
        else:
            webhook_event.mark_as_failed(str(e), should_retry=False)
            return {'error': str(e)}


@shared_task
def retry_failed_webhooks():
    """
    Retry failed webhook events.

    This task runs periodically to retry webhooks that failed but are eligible for retry.
    """
    from .models import WebhookEvent

    failed_webhooks = WebhookEvent.objects.filter(
        status__in=[WebhookEvent.FAILED, WebhookEvent.RETRYING]
    ).filter(
        retry_count__lt=3
    ).order_by('received_at')[:100]  # Process up to 100 at a time

    logger.info(f"Retrying {failed_webhooks.count()} failed webhooks")

    for webhook in failed_webhooks:
        if webhook.is_stripe_event:
            process_stripe_webhook.delay(webhook.id)
        else:
            logger.info(f"Skipping non-Stripe webhook {webhook.id}")

    return {
        'retried': failed_webhooks.count(),
        'timestamp': timezone.now().isoformat()
    }


@shared_task
def cleanup_old_webhooks():
    """
    Clean up old webhook events to prevent database bloat.

    Deletes webhook events older than 90 days that have been successfully processed.
    Failed webhooks are kept for debugging.
    """
    from .models import WebhookEvent
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=90)

    deleted_count, _ = WebhookEvent.objects.filter(
        status=WebhookEvent.PROCESSED,
        received_at__lt=cutoff_date
    ).delete()

    logger.info(f"Cleaned up {deleted_count} old webhook events")

    return {
        'deleted': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task
def send_outgoing_webhook(webhook_endpoint_id, event_type, payload):
    """
    Send a webhook to an external endpoint.

    Args:
        webhook_endpoint_id: UUID of the WebhookEndpoint
        event_type: Type of event
        payload: Data to send

    Returns:
        dict: Delivery result
    """
    import requests
    import hmac
    import hashlib
    import json
    from .models import WebhookEndpoint

    try:
        endpoint = WebhookEndpoint.objects.get(id=webhook_endpoint_id, is_active=True)
    except WebhookEndpoint.DoesNotExist:
        logger.error(f"WebhookEndpoint {webhook_endpoint_id} not found or inactive")
        return {'error': 'Endpoint not found'}

    # Check if endpoint subscribes to this event type
    if event_type not in endpoint.event_types:
        logger.info(f"Endpoint {endpoint_id} not subscribed to {event_type}")
        return {'skipped': 'Not subscribed to event type'}

    # Prepare payload
    webhook_payload = {
        'event_type': event_type,
        'timestamp': timezone.now().isoformat(),
        'data': payload
    }

    # Generate HMAC signature
    payload_bytes = json.dumps(webhook_payload).encode('utf-8')
    signature = hmac.new(
        endpoint.secret_key.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': signature,
        'X-Event-Type': event_type,
        **endpoint.headers
    }

    # Send webhook
    try:
        response = requests.post(
            endpoint.url,
            json=webhook_payload,
            headers=headers,
            timeout=endpoint.timeout
        )

        success = response.status_code in [200, 201, 202, 204]
        endpoint.record_delivery(success=success)

        if success:
            logger.info(f"Successfully delivered webhook to {endpoint.url}")
            return {
                'delivered': True,
                'status_code': response.status_code
            }
        else:
            logger.warning(f"Webhook delivery failed: {response.status_code} - {response.text}")
            return {
                'delivered': False,
                'status_code': response.status_code,
                'error': response.text
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error delivering webhook to {endpoint.url}: {str(e)}")
        endpoint.record_delivery(success=False)
        return {
            'delivered': False,
            'error': str(e)
        }
