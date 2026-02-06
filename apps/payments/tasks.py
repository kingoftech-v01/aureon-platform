"""
Payments Celery tasks for Aureon SaaS Platform.

These tasks handle payment processing and Stripe operations.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5)
def process_stripe_webhook(self, webhook_event_id):
    """Process incoming Stripe webhook event from database record."""
    try:
        from apps.webhooks.models import WebhookEvent
        from apps.webhooks.stripe_handlers import StripeWebhookHandler

        webhook_event = WebhookEvent.objects.get(id=webhook_event_id)
        webhook_event.mark_as_processing()

        handler = StripeWebhookHandler(webhook_event.payload)
        result = handler.handle()

        webhook_event.mark_as_processed(result)
        logger.info(f"Processed Stripe webhook {webhook_event.event_id}")
        return {'status': 'success', 'event_id': str(webhook_event_id), 'result': result}
    except Exception as exc:
        logger.error(f"Stripe webhook processing failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def process_payment(self, payment_id):
    """Process a payment via Stripe."""
    try:
        from apps.payments.models import Payment
        import stripe
        from django.conf import settings

        payment = Payment.objects.select_related('invoice', 'invoice__client').get(id=payment_id)
        logger.info(f"Processing payment {payment.transaction_id}...")

        payment.status = Payment.PROCESSING
        payment.save(update_fields=['status', 'updated_at'])

        # If we already have a payment intent, check its status
        if payment.stripe_payment_intent_id:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)

            if intent.status == 'succeeded':
                payment.status = Payment.SUCCEEDED
                payment.save(update_fields=['status', 'updated_at'])
                # Update invoice
                if payment.invoice:
                    payment.invoice.mark_as_paid(
                        payment_amount=payment.amount,
                        payment_method=payment.get_payment_method_display(),
                        payment_reference=payment.transaction_id
                    )
            elif intent.status == 'requires_payment_method':
                payment.status = Payment.FAILED
                payment.failure_message = 'Payment method required'
                payment.save(update_fields=['status', 'failure_message', 'updated_at'])
            else:
                payment.status = Payment.PENDING
                payment.save(update_fields=['status', 'updated_at'])
        else:
            logger.warning(f"Payment {payment.transaction_id} has no Stripe payment intent")
            payment.status = Payment.FAILED
            payment.failure_message = 'No payment intent configured'
            payment.save(update_fields=['status', 'failure_message', 'updated_at'])

        return {'status': 'success', 'payment_id': str(payment_id), 'payment_status': payment.status}
    except Exception as exc:
        logger.error(f"Payment processing failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def retry_failed_payment(self, payment_id):
    """Retry a failed payment."""
    try:
        from apps.payments.models import Payment

        payment = Payment.objects.get(id=payment_id)
        logger.info(f"Retrying failed payment {payment.transaction_id}...")

        if payment.status != Payment.FAILED:
            return {'status': 'skipped', 'message': f'Payment status is {payment.status}, not failed'}

        # Reset status and reprocess
        payment.status = Payment.PENDING
        payment.failure_code = ''
        payment.failure_message = ''
        payment.save(update_fields=['status', 'failure_code', 'failure_message', 'updated_at'])

        # Queue for processing
        process_payment.delay(payment_id)

        return {'status': 'success', 'payment_id': str(payment_id), 'retried': True}
    except Exception as exc:
        logger.error(f"Payment retry failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


@shared_task(bind=True, max_retries=3)
def sync_stripe_data(self):
    """Sync payment data with Stripe. Runs every 6 hours."""
    try:
        from apps.payments.models import Payment
        import stripe
        from django.conf import settings

        stripe.api_key = settings.STRIPE_SECRET_KEY
        logger.info("Syncing Stripe data...")

        # Sync recent pending/processing payments
        pending_payments = Payment.objects.filter(
            status__in=[Payment.PENDING, Payment.PROCESSING],
            stripe_payment_intent_id__isnull=False,
        ).exclude(stripe_payment_intent_id='')

        synced_count = 0
        for payment in pending_payments:
            try:
                intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                status_map = {
                    'succeeded': Payment.SUCCEEDED,
                    'processing': Payment.PROCESSING,
                    'canceled': Payment.CANCELLED,
                    'requires_payment_method': Payment.FAILED,
                }
                new_status = status_map.get(intent.status, payment.status)
                if new_status != payment.status:
                    payment.status = new_status
                    payment.save(update_fields=['status', 'updated_at'])
                    synced_count += 1

                    # If succeeded, update invoice
                    if new_status == Payment.SUCCEEDED and payment.invoice:
                        payment.invoice.mark_as_paid(
                            payment_amount=payment.amount,
                            payment_reference=payment.transaction_id
                        )
            except Exception as e:
                logger.warning(f"Could not sync payment {payment.transaction_id}: {e}")

        logger.info(f"Stripe sync completed: {synced_count} payments updated")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'synced_count': synced_count
        }
    except Exception as exc:
        logger.error(f"Stripe sync failed: {exc}")
        raise self.retry(exc=exc, countdown=300)
