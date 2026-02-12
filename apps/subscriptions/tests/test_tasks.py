"""
Tests for subscriptions Celery tasks.

Tests cover subscription payment processing, renewals, and cancellations.
"""
import pytest
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.subscriptions.models import Subscription, SubscriptionPlan
from apps.subscriptions.tasks import (
    process_subscription_payment,
    process_subscription_renewals,
    cancel_subscription,
)

User = get_user_model()


@pytest.fixture
def subscription_plan(db):
    """Create a test subscription plan."""
    return SubscriptionPlan.objects.create(
        name='Pro Plan',
        slug='pro-plan',
        description='Professional plan with all features.',
        price=Decimal('49.99'),
        currency='USD',
        interval='month',
        stripe_price_id='price_test_pro',
        is_active=True,
    )


@pytest.fixture
def subscription_active(db, admin_user, subscription_plan):
    """Create an active subscription with a Stripe subscription ID."""
    return Subscription.objects.create(
        user=admin_user,
        plan=subscription_plan,
        status='active',
        stripe_subscription_id='sub_test_active_123',
        current_period_start=timezone.now() - timedelta(days=15),
        current_period_end=timezone.now() + timedelta(days=15),
        cancel_at_period_end=False,
    )


@pytest.fixture
def subscription_no_stripe(db, admin_user, subscription_plan):
    """Create an active subscription without a Stripe subscription ID."""
    return Subscription.objects.create(
        user=admin_user,
        plan=subscription_plan,
        status='active',
        stripe_subscription_id='',
        current_period_start=timezone.now() - timedelta(days=15),
        current_period_end=timezone.now() + timedelta(days=15),
        cancel_at_period_end=False,
    )


@pytest.fixture
def subscription_expiring(db, manager_user, subscription_plan):
    """Create a subscription expiring within 24 hours."""
    return Subscription.objects.create(
        user=manager_user,
        plan=subscription_plan,
        status='active',
        stripe_subscription_id='sub_test_expiring_123',
        current_period_start=timezone.now() - timedelta(days=29),
        current_period_end=timezone.now() + timedelta(hours=12),
        cancel_at_period_end=False,
    )


@pytest.fixture(autouse=True)
def stripe_settings(settings):
    """Set Stripe secret key for all tests in this module."""
    settings.STRIPE_SECRET_KEY = 'sk_test_fake_key'
    return settings


@pytest.mark.django_db
class TestProcessSubscriptionPayment:
    """Tests for process_subscription_payment task."""

    @patch('stripe.Subscription.retrieve')
    def test_active_stripe_subscription(self, mock_retrieve, subscription_active):
        """Test processing an active Stripe subscription updates status and period."""
        mock_stripe_sub = MagicMock()
        mock_stripe_sub.status = 'active'
        mock_stripe_sub.current_period_end = int(
            (timezone.now() + timedelta(days=30)).timestamp()
        )
        mock_retrieve.return_value = mock_stripe_sub

        result = process_subscription_payment(str(subscription_active.id))

        assert result['status'] == 'success'
        assert result['subscription_id'] == str(subscription_active.id)
        assert result['user'] == subscription_active.user.email

        subscription_active.refresh_from_db()
        assert subscription_active.status == 'active'
        assert subscription_active.current_period_end is not None

    @patch('stripe.Subscription.retrieve')
    def test_past_due_stripe_subscription(self, mock_retrieve, subscription_active):
        """Test processing a past_due Stripe subscription updates status."""
        mock_stripe_sub = MagicMock()
        mock_stripe_sub.status = 'past_due'
        mock_retrieve.return_value = mock_stripe_sub

        result = process_subscription_payment(str(subscription_active.id))

        assert result['status'] == 'success'

        subscription_active.refresh_from_db()
        assert subscription_active.status == 'past_due'

    @patch('stripe.Subscription.retrieve')
    def test_unpaid_stripe_subscription(self, mock_retrieve, subscription_active):
        """Test processing an unpaid Stripe subscription marks as past_due."""
        mock_stripe_sub = MagicMock()
        mock_stripe_sub.status = 'unpaid'
        mock_retrieve.return_value = mock_stripe_sub

        result = process_subscription_payment(str(subscription_active.id))

        subscription_active.refresh_from_db()
        assert subscription_active.status == 'past_due'

    def test_subscription_without_stripe_id(self, subscription_no_stripe):
        """Test that a subscription without Stripe ID is processed without error."""
        result = process_subscription_payment(str(subscription_no_stripe.id))

        assert result['status'] == 'success'
        assert result['user'] == subscription_no_stripe.user.email

    def test_subscription_not_found(self):
        """Test that a non-existent subscription returns error."""
        result = process_subscription_payment(str(uuid.uuid4()))

        assert result['status'] == 'error'
        assert 'not found' in result['message']

    @patch('stripe.Subscription.retrieve')
    def test_retries_on_stripe_error(self, mock_retrieve, subscription_active):
        """Test that a Stripe API error raises an exception (triggering retry)."""
        mock_retrieve.side_effect = Exception("Stripe API error")

        with pytest.raises(Exception):
            process_subscription_payment(str(subscription_active.id))

    @patch('stripe.Subscription.retrieve')
    def test_retrieves_correct_stripe_subscription(self, mock_retrieve, subscription_active):
        """Test that the correct Stripe subscription ID is used for retrieval."""
        mock_stripe_sub = MagicMock()
        mock_stripe_sub.status = 'active'
        mock_stripe_sub.current_period_end = int(
            (timezone.now() + timedelta(days=30)).timestamp()
        )
        mock_retrieve.return_value = mock_stripe_sub

        process_subscription_payment(str(subscription_active.id))

        mock_retrieve.assert_called_once_with('sub_test_active_123')


@pytest.mark.django_db
class TestProcessSubscriptionRenewals:
    """Tests for process_subscription_renewals task."""

    @patch('apps.subscriptions.tasks.process_subscription_payment')
    def test_queues_expiring_subscriptions(
        self, mock_process, subscription_expiring
    ):
        """Test that subscriptions expiring within 24 hours are queued for processing."""
        result = process_subscription_renewals()

        assert result['status'] == 'success'
        assert result['renewals_queued'] >= 1
        mock_process.delay.assert_called_with(subscription_expiring.id)

    @patch('apps.subscriptions.tasks.process_subscription_payment')
    def test_does_not_queue_future_subscriptions(
        self, mock_process, subscription_active
    ):
        """Test that subscriptions not expiring soon are not queued."""
        result = process_subscription_renewals()

        assert result['renewals_queued'] == 0
        mock_process.delay.assert_not_called()

    @patch('apps.subscriptions.tasks.process_subscription_payment')
    def test_skips_cancelled_subscriptions(
        self, mock_process, subscription_plan, admin_user
    ):
        """Test that subscriptions with cancel_at_period_end are skipped."""
        Subscription.objects.create(
            user=admin_user,
            plan=subscription_plan,
            status='active',
            stripe_subscription_id='sub_test_cancel',
            current_period_start=timezone.now() - timedelta(days=29),
            current_period_end=timezone.now() + timedelta(hours=12),
            cancel_at_period_end=True,
        )

        result = process_subscription_renewals()

        assert result['renewals_queued'] == 0

    @patch('apps.subscriptions.tasks.process_subscription_payment')
    def test_skips_inactive_subscriptions(
        self, mock_process, subscription_plan, admin_user
    ):
        """Test that non-active subscriptions are skipped."""
        Subscription.objects.create(
            user=admin_user,
            plan=subscription_plan,
            status='canceled',
            stripe_subscription_id='sub_test_inactive',
            current_period_start=timezone.now() - timedelta(days=29),
            current_period_end=timezone.now() + timedelta(hours=12),
            cancel_at_period_end=False,
        )

        result = process_subscription_renewals()

        assert result['renewals_queued'] == 0

    @patch('apps.subscriptions.tasks.process_subscription_payment')
    def test_multiple_expiring_subscriptions(
        self, mock_process, subscription_plan, admin_user, manager_user
    ):
        """Test that multiple expiring subscriptions are all queued."""
        # Create multiple expiring subscriptions
        for i, user in enumerate([admin_user, manager_user]):
            Subscription.objects.create(
                user=user,
                plan=subscription_plan,
                status='active',
                stripe_subscription_id=f'sub_test_multi_{i}',
                current_period_start=timezone.now() - timedelta(days=29),
                current_period_end=timezone.now() + timedelta(hours=6 + i),
                cancel_at_period_end=False,
            )

        result = process_subscription_renewals()

        assert result['renewals_queued'] == 2
        assert mock_process.delay.call_count == 2

    @patch('apps.subscriptions.tasks.process_subscription_payment')
    def test_handles_individual_queue_failure(
        self, mock_process, subscription_expiring
    ):
        """Test that a failure queuing one renewal does not stop others."""
        mock_process.delay.side_effect = Exception("Queue failure")

        result = process_subscription_renewals()

        # Task should still complete even if individual queueing fails
        assert result['status'] == 'success'
        assert result['renewals_queued'] == 0


@pytest.mark.django_db
class TestCancelSubscription:
    """Tests for cancel_subscription task."""

    def test_cancel_subscription_immediate(self, subscription_active):
        """Test that immediate cancellation sets status to canceled."""
        result = cancel_subscription(str(subscription_active.id), immediate=True)

        assert result['status'] == 'success'
        assert result['immediate'] is True

        subscription_active.refresh_from_db()
        assert subscription_active.status == 'canceled'
        assert subscription_active.canceled_at is not None

    def test_cancel_subscription_end_of_period(self, subscription_active):
        """Test that end-of-period cancellation sets cancel_at_period_end."""
        result = cancel_subscription(str(subscription_active.id), immediate=False)

        assert result['status'] == 'success'
        assert result['immediate'] is False

        subscription_active.refresh_from_db()
        assert subscription_active.cancel_at_period_end is True
        assert subscription_active.status == 'active'
        assert subscription_active.canceled_at is None

    def test_cancel_returns_subscription_id(self, subscription_active):
        """Test that the result includes the subscription ID."""
        result = cancel_subscription(str(subscription_active.id), immediate=True)

        assert result['subscription_id'] == str(subscription_active.id)

    def test_cancel_nonexistent_subscription_retries(self):
        """Test that cancelling a non-existent subscription raises an exception (triggering retry)."""
        with pytest.raises(Exception):
            cancel_subscription(str(uuid.uuid4()), immediate=True)

    def test_immediate_cancel_sets_canceled_at(self, subscription_active):
        """Test that immediate cancellation records the cancellation timestamp."""
        before = timezone.now()
        cancel_subscription(str(subscription_active.id), immediate=True)

        subscription_active.refresh_from_db()
        assert subscription_active.canceled_at >= before

    def test_end_of_period_cancel_preserves_status(self, subscription_active):
        """Test that end-of-period cancellation keeps the subscription active."""
        cancel_subscription(str(subscription_active.id), immediate=False)

        subscription_active.refresh_from_db()
        assert subscription_active.status == 'active'

    def test_cancel_already_canceled_subscription(self, subscription_active):
        """Test cancelling an already canceled subscription."""
        subscription_active.status = 'canceled'
        subscription_active.save()

        result = cancel_subscription(str(subscription_active.id), immediate=True)

        assert result['status'] == 'success'


# =============================================================================
# Retry Exception Tests for process_subscription_renewals (covers lines 101-103)
# =============================================================================

@pytest.mark.django_db
class TestProcessSubscriptionRenewalsRetry:
    """Tests for retry behavior of process_subscription_renewals."""

    def test_retries_on_top_level_exception(self):
        """Task should retry when a top-level exception occurs."""
        with patch('apps.subscriptions.models.Subscription.objects') as mock_objects:
            mock_objects.filter.side_effect = Exception('DB connection lost')

            with pytest.raises(Exception, match='DB connection lost'):
                process_subscription_renewals()
