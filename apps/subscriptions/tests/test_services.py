"""Tests for subscriptions services."""

import pytest
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.subscriptions.models import SubscriptionPlan, Subscription
from apps.subscriptions.services import (
    SubscriptionService,
    _compute_period_end,
    _map_stripe_status,
    _ensure_stripe_customer,
)

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='svcuser', email='svcuser@example.com',
        password='SecurePass123!', first_name='Svc', last_name='User',
    )


@pytest.fixture
def plan(db):
    return SubscriptionPlan.objects.create(
        name='Basic', slug='basic', price=Decimal('19.99'),
        interval='month', is_active=True,
    )


@pytest.fixture
def plan_yearly(db):
    return SubscriptionPlan.objects.create(
        name='Annual', slug='annual', price=Decimal('199.99'),
        interval='year', is_active=True,
    )


@pytest.fixture
def plan_with_stripe(db):
    return SubscriptionPlan.objects.create(
        name='Stripe Plan', slug='stripe-plan', price=Decimal('29.99'),
        interval='month', is_active=True, stripe_price_id='price_abc123',
    )


@pytest.fixture
def active_sub(db, user, plan):
    return Subscription.objects.create(
        user=user, plan=plan, status='active',
        current_period_start=timezone.now(),
        current_period_end=timezone.now() + timedelta(days=30),
    )


# ---------------------------------------------------------------------------
# create_subscription
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateSubscription:

    def test_creates_subscription(self, user, plan):
        sub = SubscriptionService.create_subscription(user, plan.id)
        assert sub.user == user
        assert sub.plan == plan
        assert sub.status == 'active'
        assert sub.current_period_start is not None
        assert sub.current_period_end is not None

    def test_creates_with_stripe(self, user, plan_with_stripe):
        mock_stripe_sub = MagicMock()
        mock_stripe_sub.id = 'sub_stripe123'
        mock_stripe_sub.status = 'active'
        mock_stripe_sub.current_period_end = int(
            (timezone.now() + timedelta(days=30)).timestamp()
        )

        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            mock_stripe.return_value.Subscription.create.return_value = mock_stripe_sub
            mock_stripe.return_value.Customer.create.return_value = MagicMock(id='cus_123')

            sub = SubscriptionService.create_subscription(
                user, plan_with_stripe.id, payment_method_id='pm_test',
            )

        assert sub.stripe_subscription_id == 'sub_stripe123'

    def test_stripe_failure_keeps_local_sub(self, user, plan_with_stripe):
        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            mock_stripe.return_value.Customer.create.side_effect = Exception('Stripe down')

            sub = SubscriptionService.create_subscription(
                user, plan_with_stripe.id, payment_method_id='pm_test',
            )

        assert sub.status == 'active'
        assert sub.stripe_subscription_id == ''

    def test_plan_not_found_raises(self, user):
        with pytest.raises(SubscriptionPlan.DoesNotExist):
            SubscriptionService.create_subscription(user, 99999)


# ---------------------------------------------------------------------------
# cancel_subscription
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCancelSubscription:

    def test_cancel_at_period_end(self, active_sub):
        updated = SubscriptionService.cancel_subscription(active_sub.id)
        assert updated.cancel_at_period_end is True
        assert updated.status == 'active'

    def test_cancel_immediate(self, active_sub):
        updated = SubscriptionService.cancel_subscription(
            active_sub.id, immediate=True,
        )
        assert updated.status == 'canceled'
        assert updated.canceled_at is not None

    def test_cancel_already_canceled(self, active_sub):
        active_sub.status = 'canceled'
        active_sub.save()
        with pytest.raises(ValueError, match='already canceled'):
            SubscriptionService.cancel_subscription(active_sub.id)

    def test_cancel_with_stripe(self, active_sub):
        active_sub.stripe_subscription_id = 'sub_123'
        active_sub.save()
        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            SubscriptionService.cancel_subscription(
                active_sub.id, immediate=True,
            )
            mock_stripe.return_value.Subscription.cancel.assert_called_once_with('sub_123')

    def test_cancel_stripe_failure_continues(self, active_sub):
        active_sub.stripe_subscription_id = 'sub_fail'
        active_sub.save()
        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            mock_stripe.return_value.Subscription.cancel.side_effect = Exception('fail')
            updated = SubscriptionService.cancel_subscription(
                active_sub.id, immediate=True,
            )
        assert updated.status == 'canceled'


# ---------------------------------------------------------------------------
# pause_subscription / resume_subscription
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPauseResumeSubscription:

    def test_pause(self, active_sub):
        updated = SubscriptionService.pause_subscription(active_sub.id)
        assert updated.status == 'paused'

    def test_pause_non_active_raises(self, active_sub):
        active_sub.status = 'canceled'
        active_sub.save()
        with pytest.raises(ValueError, match='Only active'):
            SubscriptionService.pause_subscription(active_sub.id)

    def test_resume(self, active_sub):
        active_sub.status = 'paused'
        active_sub.save()
        updated = SubscriptionService.resume_subscription(active_sub.id)
        assert updated.status == 'active'

    def test_resume_non_paused_raises(self, active_sub):
        with pytest.raises(ValueError, match='Only paused'):
            SubscriptionService.resume_subscription(active_sub.id)

    def test_pause_with_stripe(self, active_sub):
        active_sub.stripe_subscription_id = 'sub_123'
        active_sub.save()
        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            SubscriptionService.pause_subscription(active_sub.id)
            mock_stripe.return_value.Subscription.modify.assert_called_once()

    def test_resume_with_stripe(self, active_sub):
        active_sub.status = 'paused'
        active_sub.stripe_subscription_id = 'sub_123'
        active_sub.save()
        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            SubscriptionService.resume_subscription(active_sub.id)
            mock_stripe.return_value.Subscription.modify.assert_called_once()


# ---------------------------------------------------------------------------
# change_plan
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChangePlan:

    def test_change_plan(self, active_sub, plan_yearly):
        updated = SubscriptionService.change_plan(active_sub.id, plan_yearly.id)
        assert updated.plan == plan_yearly

    def test_same_plan_raises(self, active_sub):
        with pytest.raises(ValueError, match='Already subscribed'):
            SubscriptionService.change_plan(active_sub.id, active_sub.plan.id)

    def test_canceled_raises(self, active_sub, plan_yearly):
        active_sub.status = 'canceled'
        active_sub.save()
        with pytest.raises(ValueError, match='Can only change'):
            SubscriptionService.change_plan(active_sub.id, plan_yearly.id)

    def test_change_with_stripe(self, active_sub, plan_yearly):
        active_sub.stripe_subscription_id = 'sub_123'
        active_sub.save()
        plan_yearly.stripe_price_id = 'price_yearly'
        plan_yearly.save()

        mock_stripe_sub = {'items': {'data': [{'id': 'si_old'}]}}
        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            mock_stripe.return_value.Subscription.retrieve.return_value = mock_stripe_sub
            updated = SubscriptionService.change_plan(active_sub.id, plan_yearly.id)

        assert updated.plan == plan_yearly
        mock_stripe.return_value.Subscription.modify.assert_called_once()


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGetStats:

    def test_empty_stats(self):
        stats = SubscriptionService.get_stats()
        assert stats['total_subscriptions'] == 0
        assert stats['active_subscriptions'] == 0
        assert stats['monthly_recurring_revenue'] == Decimal('0.00')

    def test_stats_with_data(self, active_sub, user, plan_yearly):
        user2 = User.objects.create_user(
            username='stat2', email='stat2@example.com', password='Pass123!',
        )
        Subscription.objects.create(user=user2, plan=plan_yearly, status='active')
        stats = SubscriptionService.get_stats()
        assert stats['total_subscriptions'] == 2
        assert stats['active_subscriptions'] == 2
        assert stats['monthly_recurring_revenue'] > Decimal('0')
        assert stats['annual_recurring_revenue'] > Decimal('0')

    def test_churn_rate(self, user, plan):
        Subscription.objects.create(
            user=user, plan=plan, status='canceled',
            canceled_at=timezone.now(),
        )
        stats = SubscriptionService.get_stats()
        assert stats['churn_rate'] == Decimal('100.00')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestHelpers:

    def test_compute_period_end_month(self):
        end = _compute_period_end('month')
        assert (end - timezone.now()).days >= 29

    def test_compute_period_end_year(self):
        end = _compute_period_end('year')
        assert (end - timezone.now()).days >= 364

    def test_map_stripe_status(self):
        assert _map_stripe_status('active') == 'active'
        assert _map_stripe_status('past_due') == 'past_due'
        assert _map_stripe_status('canceled') == 'canceled'
        assert _map_stripe_status('trialing') == 'trialing'
        assert _map_stripe_status('paused') == 'paused'
        assert _map_stripe_status('incomplete') == 'past_due'
        assert _map_stripe_status('unknown_status') == 'active'

    def test_ensure_stripe_customer_creates(self):
        mock_stripe = MagicMock()
        mock_stripe.Customer.create.return_value = MagicMock(id='cus_new')
        user = MagicMock(email='test@example.com', id=1)
        user.get_full_name.return_value = 'Test User'
        del user.stripe_customer_id  # simulate missing attr

        cid = _ensure_stripe_customer(mock_stripe, user, 'pm_abc')
        assert cid == 'cus_new'
        mock_stripe.Customer.create.assert_called_once()

    def test_ensure_stripe_customer_returns_existing(self):
        """When user already has stripe_customer_id, return it directly."""
        mock_stripe = MagicMock()
        user = MagicMock(email='test@example.com', id=1)
        user.stripe_customer_id = 'cus_existing'

        cid = _ensure_stripe_customer(mock_stripe, user, 'pm_abc')
        assert cid == 'cus_existing'
        mock_stripe.Customer.create.assert_not_called()

    def test_ensure_stripe_customer_saves_id(self):
        """When user has stripe_customer_id attr, save the new ID."""
        mock_stripe = MagicMock()
        mock_stripe.Customer.create.return_value = MagicMock(id='cus_saved')
        user = MagicMock(email='test@example.com', id=1)
        user.stripe_customer_id = None  # attr exists but is None/empty
        user.get_full_name.return_value = 'Test User'

        cid = _ensure_stripe_customer(mock_stripe, user, 'pm_xyz')
        assert cid == 'cus_saved'
        assert user.stripe_customer_id == 'cus_saved'
        user.save.assert_called_once()


# ---------------------------------------------------------------------------
# Additional Stripe path coverage
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCancelSubscriptionStripePeriodEnd:
    """Cover cancel at period end with Stripe (line 99)."""

    def test_cancel_at_period_end_with_stripe(self, active_sub):
        active_sub.stripe_subscription_id = 'sub_pe'
        active_sub.save()
        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            updated = SubscriptionService.cancel_subscription(
                active_sub.id, immediate=False, reason='Too expensive',
            )
            mock_stripe.return_value.Subscription.modify.assert_called_once_with(
                'sub_pe',
                cancel_at_period_end=True,
                metadata={'cancel_reason': 'Too expensive'},
            )
        assert updated.cancel_at_period_end is True


@pytest.mark.django_db
class TestPauseSubscriptionStripeFailure:
    """Cover Stripe pause failure except block (lines 142-143)."""

    def test_pause_stripe_failure_continues(self, active_sub):
        active_sub.stripe_subscription_id = 'sub_pf'
        active_sub.save()
        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            mock_stripe.return_value.Subscription.modify.side_effect = Exception('fail')
            updated = SubscriptionService.pause_subscription(active_sub.id)
        assert updated.status == 'paused'


@pytest.mark.django_db
class TestResumeSubscriptionStripeFailure:
    """Cover Stripe resume failure except block (lines 169-170)."""

    def test_resume_stripe_failure_continues(self, active_sub):
        active_sub.status = 'paused'
        active_sub.stripe_subscription_id = 'sub_rf'
        active_sub.save()
        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            mock_stripe.return_value.Subscription.modify.side_effect = Exception('fail')
            updated = SubscriptionService.resume_subscription(active_sub.id)
        assert updated.status == 'active'


@pytest.mark.django_db
class TestChangePlanStripeFailure:
    """Cover Stripe change plan failure except block (lines 210-211)."""

    def test_change_plan_stripe_failure_continues(self, active_sub, plan_yearly):
        active_sub.stripe_subscription_id = 'sub_cpf'
        active_sub.save()
        plan_yearly.stripe_price_id = 'price_yearly'
        plan_yearly.save()

        with patch('apps.subscriptions.services._get_stripe') as mock_stripe:
            mock_stripe.return_value.Subscription.retrieve.side_effect = Exception('fail')
            updated = SubscriptionService.change_plan(active_sub.id, plan_yearly.id)
        assert updated.plan == plan_yearly
