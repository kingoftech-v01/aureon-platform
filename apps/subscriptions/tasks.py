"""
Subscriptions Celery tasks for Aureon SaaS Platform.

These tasks handle subscription processing and renewals.
"""
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5)
def process_subscription_payment(self, subscription_id):
    """
    Process a subscription payment.
    High priority task for payment processing.
    """
    try:
        from apps.subscriptions.models import Subscription

        logger.info(f"Processing subscription payment for {subscription_id}...")

        try:
            subscription = Subscription.objects.get(id=subscription_id)

            # Process via Stripe if configured
            if subscription.stripe_subscription_id:
                import stripe
                from django.conf import settings
                stripe.api_key = settings.STRIPE_SECRET_KEY

                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)

                if stripe_sub.status == 'active':
                    subscription.status = 'active'
                    import datetime as _dt
                    subscription.current_period_end = _dt.datetime.fromtimestamp(
                        stripe_sub.current_period_end, tz=_dt.timezone.utc
                    )
                    subscription.save(update_fields=['status', 'current_period_end', 'updated_at'])
                    logger.info(f"Subscription {subscription_id} payment confirmed via Stripe")
                elif stripe_sub.status in ('past_due', 'unpaid'):
                    subscription.status = 'past_due'
                    subscription.save(update_fields=['status', 'updated_at'])
                    logger.warning(f"Subscription {subscription_id} is {stripe_sub.status}")
            else:
                logger.info(f"Subscription {subscription_id} has no Stripe ID, marking as processed")

            return {
                'status': 'success',
                'subscription_id': str(subscription_id),
                'user': subscription.user.email
            }
        except (Subscription.DoesNotExist, ValueError):
            logger.warning(f"Subscription {subscription_id} not found")
            return {'status': 'error', 'message': 'Subscription not found'}

    except Exception as exc:
        logger.error(f"Subscription payment processing failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def process_subscription_renewals(self):
    """
    Process subscription renewals.
    Runs daily at 1 AM to renew expiring subscriptions.
    """
    try:
        from apps.subscriptions.models import Subscription

        logger.info("Processing subscription renewals...")

        # Find subscriptions expiring in the next 24 hours
        tomorrow = timezone.now() + timedelta(days=1)
        expiring_subscriptions = Subscription.objects.filter(
            status='active',
            cancel_at_period_end=False,
            current_period_end__lte=tomorrow,
            current_period_end__gt=timezone.now()
        )

        renewed_count = 0
        for subscription in expiring_subscriptions:
            try:
                # Queue individual payment processing
                process_subscription_payment.delay(subscription.id)
                renewed_count += 1
            except Exception as e:
                logger.error(f"Failed to queue renewal for subscription {subscription.id}: {e}")

        logger.info(f"Queued {renewed_count} subscription renewals")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'renewals_queued': renewed_count
        }

    except Exception as exc:
        logger.error(f"Subscription renewal processing failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=2)
def cancel_subscription(self, subscription_id, immediate=False):
    """
    Cancel a subscription.
    """
    try:
        from apps.subscriptions.models import Subscription

        logger.info(f"Canceling subscription {subscription_id}...")

        subscription = Subscription.objects.get(id=subscription_id)

        if immediate:
            subscription.status = 'canceled'
            subscription.canceled_at = timezone.now()
        else:
            subscription.cancel_at_period_end = True

        subscription.save()

        return {
            'status': 'success',
            'subscription_id': subscription_id,
            'immediate': immediate
        }

    except Exception as exc:
        logger.error(f"Subscription cancellation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
