"""Subscription business logic and Stripe integration."""

import logging
from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models import SubscriptionPlan, Subscription

logger = logging.getLogger(__name__)


def _get_stripe():
    """Lazily import and configure stripe."""
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


class SubscriptionService:
    """Core subscription business logic with Stripe integration."""

    @staticmethod
    @transaction.atomic
    def create_subscription(user, plan_id, payment_method_id=None):
        """Create a new subscription, optionally via Stripe."""
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)

        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status='active',
            current_period_start=timezone.now(),
            current_period_end=_compute_period_end(plan.interval),
        )

        if plan.stripe_price_id and payment_method_id:
            try:
                stripe = _get_stripe()

                # Ensure customer exists in Stripe
                customer_id = _ensure_stripe_customer(stripe, user, payment_method_id)

                # Create the Stripe subscription
                stripe_sub = stripe.Subscription.create(
                    customer=customer_id,
                    items=[{'price': plan.stripe_price_id}],
                    default_payment_method=payment_method_id,
                    metadata={
                        'aureon_subscription_id': str(subscription.id),
                        'aureon_user_id': str(user.id),
                    },
                )

                subscription.stripe_subscription_id = stripe_sub.id
                subscription.status = _map_stripe_status(stripe_sub.status)
                if stripe_sub.current_period_end:
                    import datetime as _dt
                    subscription.current_period_end = _dt.datetime.fromtimestamp(
                        stripe_sub.current_period_end, tz=_dt.timezone.utc
                    )
                subscription.save(update_fields=[
                    'stripe_subscription_id', 'status',
                    'current_period_end', 'updated_at',
                ])

                logger.info(
                    f"Created Stripe subscription {stripe_sub.id} for user {user.email}"
                )
            except Exception:
                logger.exception(
                    f"Stripe subscription creation failed for user {user.email}, "
                    f"keeping local subscription active"
                )

        logger.info(f"Subscription {subscription.id} created for user {user.email}")
        return subscription

    @staticmethod
    @transaction.atomic
    def cancel_subscription(subscription_id, immediate=False, reason=''):
        """Cancel a subscription, optionally immediately."""
        subscription = Subscription.objects.select_for_update().get(id=subscription_id)

        if subscription.status == 'canceled':
            raise ValueError('Subscription is already canceled.')

        # Cancel in Stripe if linked
        if subscription.stripe_subscription_id:
            try:
                stripe = _get_stripe()
                if immediate:
                    stripe.Subscription.cancel(subscription.stripe_subscription_id)
                else:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True,
                        metadata={'cancel_reason': reason},
                    )
            except Exception:
                logger.exception(
                    f"Stripe cancellation failed for {subscription.stripe_subscription_id}"
                )

        if immediate:
            subscription.status = 'canceled'
            subscription.canceled_at = timezone.now()
            subscription.cancel_at_period_end = False
        else:
            subscription.cancel_at_period_end = True

        subscription.save(update_fields=[
            'status', 'canceled_at', 'cancel_at_period_end', 'updated_at',
        ])

        logger.info(
            f"Subscription {subscription_id} canceled "
            f"(immediate={immediate}, reason={reason})"
        )
        return subscription

    @staticmethod
    @transaction.atomic
    def pause_subscription(subscription_id):
        """Pause a subscription."""
        subscription = Subscription.objects.select_for_update().get(id=subscription_id)

        if subscription.status != 'active':
            raise ValueError('Only active subscriptions can be paused.')

        if subscription.stripe_subscription_id:
            try:
                stripe = _get_stripe()
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    pause_collection={'behavior': 'mark_uncollectible'},
                )
            except Exception:
                logger.exception(
                    f"Stripe pause failed for {subscription.stripe_subscription_id}"
                )

        subscription.status = 'paused'
        subscription.save(update_fields=['status', 'updated_at'])

        logger.info(f"Subscription {subscription_id} paused")
        return subscription

    @staticmethod
    @transaction.atomic
    def resume_subscription(subscription_id):
        """Resume a paused subscription."""
        subscription = Subscription.objects.select_for_update().get(id=subscription_id)

        if subscription.status != 'paused':
            raise ValueError('Only paused subscriptions can be resumed.')

        if subscription.stripe_subscription_id:
            try:
                stripe = _get_stripe()
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    pause_collection='',
                )
            except Exception:
                logger.exception(
                    f"Stripe resume failed for {subscription.stripe_subscription_id}"
                )

        subscription.status = 'active'
        subscription.save(update_fields=['status', 'updated_at'])

        logger.info(f"Subscription {subscription_id} resumed")
        return subscription

    @staticmethod
    @transaction.atomic
    def change_plan(subscription_id, new_plan_id, prorate=True):
        """Upgrade or downgrade a subscription's plan."""
        subscription = Subscription.objects.select_for_update().get(id=subscription_id)
        new_plan = SubscriptionPlan.objects.get(id=new_plan_id, is_active=True)

        if subscription.plan_id == new_plan_id:
            raise ValueError('Already subscribed to this plan.')

        if subscription.status not in ('active', 'trialing'):
            raise ValueError('Can only change plan for active or trialing subscriptions.')

        old_plan = subscription.plan

        if subscription.stripe_subscription_id and new_plan.stripe_price_id:
            try:
                stripe = _get_stripe()
                stripe_sub = stripe.Subscription.retrieve(
                    subscription.stripe_subscription_id
                )
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        'id': stripe_sub['items']['data'][0]['id'],
                        'price': new_plan.stripe_price_id,
                    }],
                    proration_behavior='create_prorations' if prorate else 'none',
                    metadata={'plan_change': f'{old_plan.slug}->{new_plan.slug}'},
                )
            except Exception:
                logger.exception(
                    f"Stripe plan change failed for {subscription.stripe_subscription_id}"
                )

        subscription.plan = new_plan
        subscription.save(update_fields=['plan', 'updated_at'])

        logger.info(
            f"Subscription {subscription_id} changed from "
            f"{old_plan.name} to {new_plan.name}"
        )
        return subscription

    @staticmethod
    def get_stats():
        """Calculate subscription statistics."""
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        total = Subscription.objects.count()
        by_status = dict(
            Subscription.objects.values_list('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )

        active_count = by_status.get('active', 0)

        # MRR calculation
        mrr = Decimal('0.00')
        active_subs = Subscription.objects.filter(status='active').select_related('plan')
        for sub in active_subs:
            if sub.plan.interval == 'year':
                mrr += sub.plan.price / 12
            else:
                mrr += sub.plan.price

        arr = mrr * 12
        arpu = mrr / active_count if active_count > 0 else Decimal('0.00')

        # Churn rate: canceled in last 30 days / total active at start of period
        recently_canceled = Subscription.objects.filter(
            status='canceled',
            canceled_at__gte=thirty_days_ago,
        ).count()
        churn_denominator = active_count + recently_canceled
        churn_rate = (
            Decimal(recently_canceled) / Decimal(churn_denominator) * 100
            if churn_denominator > 0
            else Decimal('0.00')
        )

        return {
            'total_subscriptions': total,
            'active_subscriptions': active_count,
            'canceled_subscriptions': by_status.get('canceled', 0),
            'past_due_subscriptions': by_status.get('past_due', 0),
            'trialing_subscriptions': by_status.get('trialing', 0),
            'paused_subscriptions': by_status.get('paused', 0),
            'monthly_recurring_revenue': mrr.quantize(Decimal('0.01')),
            'annual_recurring_revenue': arr.quantize(Decimal('0.01')),
            'average_revenue_per_user': arpu.quantize(Decimal('0.01')),
            'churn_rate': churn_rate.quantize(Decimal('0.01')),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_period_end(interval):
    """Compute the next period end from now."""
    now = timezone.now()
    if interval == 'year':
        return now + timedelta(days=365)
    return now + timedelta(days=30)


def _ensure_stripe_customer(stripe, user, payment_method_id):
    """Get or create a Stripe customer for the user."""
    stripe_customer_id = getattr(user, 'stripe_customer_id', None)
    if stripe_customer_id:
        return stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=getattr(user, 'get_full_name', lambda: user.email)(),
        payment_method=payment_method_id,
        invoice_settings={'default_payment_method': payment_method_id},
        metadata={'aureon_user_id': str(user.id)},
    )
    # Persist customer ID if the user model supports it
    if hasattr(user, 'stripe_customer_id'):
        user.stripe_customer_id = customer.id
        user.save(update_fields=['stripe_customer_id'])

    return customer.id


def _map_stripe_status(stripe_status):
    """Map Stripe subscription status to internal status."""
    mapping = {
        'active': 'active',
        'past_due': 'past_due',
        'unpaid': 'past_due',
        'canceled': 'canceled',
        'incomplete': 'past_due',
        'incomplete_expired': 'canceled',
        'trialing': 'trialing',
        'paused': 'paused',
    }
    return mapping.get(stripe_status, 'active')
