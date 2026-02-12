"""Webhook views for receiving and processing webhook events."""

import json
import logging
import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import WebhookEvent
from .stripe_handlers import StripeWebhookHandler

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Receive and process Stripe webhook events.

    This endpoint:
    1. Verifies the Stripe signature
    2. Logs the event
    3. Processes the event with appropriate handler
    4. Returns appropriate HTTP response

    Security: Uses Stripe's webhook signature verification to prevent
    unauthorized webhook calls.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.DJSTRIPE_WEBHOOK_SECRET

    # Get client IP for logging
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid Stripe webhook payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid Stripe webhook signature: {str(e)}")
        return HttpResponse(status=400)

    # Log webhook event
    webhook_event = WebhookEvent.objects.create(
        source=WebhookEvent.STRIPE,
        event_type=event['type'],
        event_id=event['id'],
        payload=event,
        headers={
            'stripe_signature': sig_header,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        },
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )

    # Process webhook asynchronously if Celery is available
    try:
        from .tasks import process_stripe_webhook
        process_stripe_webhook.delay(webhook_event.id)
        logger.info(f"Queued Stripe webhook {event['id']} for async processing")
        return JsonResponse({'received': True, 'queued': True}, status=202)
    except (ImportError, Exception) as e:
        # Celery not available or failed, process synchronously
        logger.info(f"Processing Stripe webhook {event['id']} synchronously")
        return process_webhook_sync(webhook_event, event)


def process_webhook_sync(webhook_event, event):
    """
    Process webhook synchronously.

    Args:
        webhook_event: WebhookEvent model instance
        event: Stripe event dict

    Returns:
        JsonResponse: Processing result
    """
    try:
        webhook_event.mark_as_processing()

        # Handle the event
        handler = StripeWebhookHandler(event)
        result = handler.handle()

        webhook_event.mark_as_processed(result)

        return JsonResponse({
            'received': True,
            'processed': True,
            'result': result
        }, status=200)

    except Exception as e:
        logger.error(f"Error processing webhook {event['id']}: {str(e)}", exc_info=True)
        webhook_event.mark_as_failed(str(e), should_retry=True)

        return JsonResponse({
            'received': True,
            'processed': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generic_webhook(request, endpoint_id):
    """
    Receive generic webhook events from external systems.

    Args:
        request: Django HTTP request
        endpoint_id: UUID of the WebhookEndpoint

    Returns:
        HttpResponse: Processing result
    """
    from .models import WebhookEndpoint

    try:
        endpoint = WebhookEndpoint.objects.get(id=endpoint_id, is_active=True)
    except WebhookEndpoint.DoesNotExist:
        logger.error(f"Webhook endpoint {endpoint_id} not found or inactive")
        return HttpResponse(status=404)

    # Parse payload
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON payload for endpoint {endpoint_id}")
        return HttpResponse(status=400)

    # Get event type from payload
    event_type = payload.get('event_type', 'unknown')

    # Verify signature if provided
    signature = request.META.get('HTTP_X_WEBHOOK_SIGNATURE')
    if endpoint.secret_key:
        import hmac
        import hashlib
        expected_signature = hmac.new(
            endpoint.secret_key.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).hexdigest()
        if not signature or not hmac.compare_digest(signature, expected_signature):
            logger.warning(f"Invalid webhook signature for endpoint {endpoint_id}")
            return HttpResponse(status=401)

    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')

    # Log webhook event
    webhook_event = WebhookEvent.objects.create(
        source=WebhookEvent.CUSTOM,
        event_type=event_type,
        event_id=payload.get('id', f"custom_{timezone.now().timestamp()}"),
        payload=payload,
        headers={
            'signature': signature,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        },
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )

    # Mark as processed (for now, just log it)
    webhook_event.mark_as_processed({'status': 'logged'})

    logger.info(f"Received custom webhook: {event_type} for endpoint {endpoint_id}")

    return JsonResponse({'received': True}, status=200)


@require_http_methods(["GET"])
def webhook_health(request):
    """
    Health check endpoint for webhook service.

    Returns:
        JsonResponse: Health status
    """
    from django.db import connection

    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Get recent webhook stats
        recent_events = WebhookEvent.objects.filter(
            received_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()

        processed = WebhookEvent.objects.filter(
            status=WebhookEvent.PROCESSED,
            received_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()

        failed = WebhookEvent.objects.filter(
            status=WebhookEvent.FAILED,
            received_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()

        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'stats_24h': {
                'total': recent_events,
                'processed': processed,
                'failed': failed,
                'success_rate': f"{(processed / recent_events * 100) if recent_events > 0 else 0:.2f}%"
            }
        }, status=200)

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
