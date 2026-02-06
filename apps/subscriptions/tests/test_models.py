"""Tests for subscriptions models."""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.subscriptions.models import SubscriptionPlan, Subscription

User = get_user_model()


@pytest.mark.django_db
class TestSubscriptionPlan:
    """Tests for the SubscriptionPlan model."""

    def _create_plan(self, **kwargs):
        """Helper to create a SubscriptionPlan."""
        defaults = {
            'name': 'Pro Plan',
            'slug': 'pro-plan',
            'description': 'Professional plan for growing businesses.',
            'price': Decimal('49.99'),
            'currency': 'USD',
            'interval': 'month',
            'stripe_price_id': 'price_test_pro',
            'features': ['Unlimited contracts', 'Priority support', 'Analytics'],
            'is_active': True,
        }
        defaults.update(kwargs)
        return SubscriptionPlan.objects.create(**defaults)

    def test_create_plan(self):
        """Test creating a subscription plan."""
        plan = self._create_plan()
        assert plan.pk is not None
        assert plan.name == 'Pro Plan'
        assert plan.price == Decimal('49.99')

    def test_str_representation(self):
        """Test string representation of subscription plan."""
        plan = self._create_plan()
        expected = "Pro Plan - 49.99 USD/month"
        assert str(plan) == expected

    def test_str_representation_yearly(self):
        """Test string representation of yearly plan."""
        plan = self._create_plan(
            name='Annual Plan',
            slug='annual-plan',
            price=Decimal('499.99'),
            interval='year',
        )
        expected = "Annual Plan - 499.99 USD/year"
        assert str(plan) == expected

    def test_interval_choices(self):
        """Test interval choices."""
        plan_monthly = self._create_plan()
        assert plan_monthly.interval == 'month'

        plan_yearly = self._create_plan(
            name='Yearly Plan',
            slug='yearly-plan',
            interval='year',
        )
        assert plan_yearly.interval == 'year'

    def test_default_values(self):
        """Test default values on plan creation."""
        plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            price=Decimal('9.99'),
        )
        assert plan.currency == 'USD'
        assert plan.interval == 'month'
        assert plan.is_active is True
        assert plan.features == []
        assert plan.description == ''
        assert plan.stripe_price_id == ''

    def test_slug_unique(self):
        """Test that slug field is unique."""
        self._create_plan()
        with pytest.raises(Exception):
            self._create_plan(name='Another Pro')

    def test_features_json_field(self):
        """Test features JSON field stores and retrieves list."""
        features = ['Feature 1', 'Feature 2', 'Feature 3']
        plan = self._create_plan(slug='features-plan', features=features)
        plan.refresh_from_db()
        assert plan.features == features

    def test_features_empty_list(self):
        """Test features with empty list."""
        plan = self._create_plan(slug='empty-features', features=[])
        plan.refresh_from_db()
        assert plan.features == []

    def test_meta_ordering(self):
        """Test model ordering by price."""
        plan3 = self._create_plan(name='Expensive', slug='expensive', price=Decimal('99.99'))
        plan1 = self._create_plan(name='Cheap', slug='cheap', price=Decimal('9.99'))
        plan2 = self._create_plan(name='Mid', slug='mid', price=Decimal('49.99'))

        plans = list(SubscriptionPlan.objects.all())
        assert plans[0].price <= plans[1].price <= plans[2].price

    def test_meta_verbose_names(self):
        """Test meta verbose names."""
        assert SubscriptionPlan._meta.verbose_name == 'Subscription Plan'
        assert SubscriptionPlan._meta.verbose_name_plural == 'Subscription Plans'

    def test_timestamps_set_automatically(self):
        """Test that created_at and updated_at are set automatically."""
        plan = self._create_plan()
        assert plan.created_at is not None
        assert plan.updated_at is not None

    def test_different_currencies(self):
        """Test plans with different currencies."""
        plan_eur = self._create_plan(
            name='Euro Plan',
            slug='euro-plan',
            currency='EUR',
            price=Decimal('39.99'),
        )
        assert plan_eur.currency == 'EUR'
        assert str(plan_eur) == "Euro Plan - 39.99 EUR/month"

    def test_stripe_price_id_blank(self):
        """Test that stripe_price_id can be blank."""
        plan = self._create_plan(slug='no-stripe', stripe_price_id='')
        assert plan.stripe_price_id == ''

    def test_inactive_plan(self):
        """Test creating an inactive plan."""
        plan = self._create_plan(slug='inactive', is_active=False)
        assert plan.is_active is False


@pytest.mark.django_db
class TestSubscription:
    """Tests for the Subscription model."""

    @pytest.fixture
    def plan(self):
        """Create a subscription plan for testing."""
        return SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price=Decimal('29.99'),
        )

    @pytest.fixture
    def user(self, tenant):
        """Create a user for testing."""
        return User.objects.create_user(
            email='subscriber@test.com',
            password='TestPass123!',
            first_name='Sub',
            last_name='Scriber',
            tenant=tenant,
        )

    def _create_subscription(self, user, plan, **kwargs):
        """Helper to create a Subscription."""
        defaults = {
            'user': user,
            'plan': plan,
            'status': 'active',
            'stripe_subscription_id': 'sub_test_123',
            'current_period_start': timezone.now() - timedelta(days=15),
            'current_period_end': timezone.now() + timedelta(days=15),
        }
        defaults.update(kwargs)
        return Subscription.objects.create(**defaults)

    def test_create_subscription(self, user, plan):
        """Test creating a subscription."""
        sub = self._create_subscription(user, plan)
        assert sub.pk is not None
        assert sub.user == user
        assert sub.plan == plan
        assert sub.status == 'active'

    def test_str_representation(self, user, plan):
        """Test string representation of subscription."""
        sub = self._create_subscription(user, plan)
        expected = f"{user.email} - {plan.name} (active)"
        assert str(sub) == expected

    def test_str_representation_canceled(self, user, plan):
        """Test string representation of canceled subscription."""
        sub = self._create_subscription(user, plan, status='canceled')
        expected = f"{user.email} - {plan.name} (canceled)"
        assert str(sub) == expected

    def test_status_choices(self):
        """Test all status choices are valid."""
        expected_statuses = ['active', 'canceled', 'past_due', 'trialing', 'paused']
        actual_statuses = [choice[0] for choice in Subscription.STATUS_CHOICES]
        assert actual_statuses == expected_statuses

    def test_is_active_property_active_with_future_end(self, user, plan):
        """Test is_active returns True for active subscription with future end date."""
        sub = self._create_subscription(
            user, plan,
            status='active',
            current_period_end=timezone.now() + timedelta(days=15),
        )
        assert sub.is_active is True

    def test_is_active_property_active_without_end_date(self, user, plan):
        """Test is_active returns True for active subscription without end date."""
        sub = self._create_subscription(
            user, plan,
            status='active',
            current_period_end=None,
        )
        assert sub.is_active is True

    def test_is_active_property_active_expired(self, user, plan):
        """Test is_active returns False for active subscription with past end date."""
        sub = self._create_subscription(
            user, plan,
            status='active',
            current_period_end=timezone.now() - timedelta(days=1),
        )
        assert sub.is_active is False

    def test_is_active_property_canceled(self, user, plan):
        """Test is_active returns False for canceled subscription."""
        sub = self._create_subscription(user, plan, status='canceled')
        assert sub.is_active is False

    def test_is_active_property_past_due(self, user, plan):
        """Test is_active returns False for past_due subscription."""
        sub = self._create_subscription(user, plan, status='past_due')
        assert sub.is_active is False

    def test_is_active_property_trialing(self, user, plan):
        """Test is_active returns False for trialing subscription."""
        sub = self._create_subscription(user, plan, status='trialing')
        assert sub.is_active is False

    def test_is_active_property_paused(self, user, plan):
        """Test is_active returns False for paused subscription."""
        sub = self._create_subscription(user, plan, status='paused')
        assert sub.is_active is False

    def test_days_until_renewal_future(self, user, plan):
        """Test days_until_renewal with future end date."""
        end_date = timezone.now() + timedelta(days=10)
        sub = self._create_subscription(
            user, plan,
            current_period_end=end_date,
        )
        days = sub.days_until_renewal
        # Allow for minor timing differences
        assert 9 <= days <= 10

    def test_days_until_renewal_past(self, user, plan):
        """Test days_until_renewal with past end date returns 0."""
        sub = self._create_subscription(
            user, plan,
            current_period_end=timezone.now() - timedelta(days=5),
        )
        assert sub.days_until_renewal == 0

    def test_days_until_renewal_none(self, user, plan):
        """Test days_until_renewal returns None when no end date."""
        sub = self._create_subscription(
            user, plan,
            current_period_end=None,
        )
        assert sub.days_until_renewal is None

    def test_days_until_renewal_today(self, user, plan):
        """Test days_until_renewal when expiring today."""
        sub = self._create_subscription(
            user, plan,
            current_period_end=timezone.now() + timedelta(hours=1),
        )
        assert sub.days_until_renewal == 0

    def test_default_values(self, user, plan):
        """Test default values on subscription creation."""
        sub = Subscription.objects.create(
            user=user,
            plan=plan,
        )
        assert sub.status == 'active'
        assert sub.cancel_at_period_end is False
        assert sub.canceled_at is None
        assert sub.stripe_subscription_id == ''

    def test_cancel_at_period_end(self, user, plan):
        """Test cancel_at_period_end flag."""
        sub = self._create_subscription(
            user, plan,
            cancel_at_period_end=True,
        )
        assert sub.cancel_at_period_end is True

    def test_canceled_at(self, user, plan):
        """Test canceled_at timestamp."""
        canceled_time = timezone.now()
        sub = self._create_subscription(
            user, plan,
            status='canceled',
            canceled_at=canceled_time,
        )
        assert sub.canceled_at is not None

    def test_meta_ordering(self, user, plan):
        """Test model ordering by -created_at."""
        sub1 = self._create_subscription(user, plan, stripe_subscription_id='sub_1')
        sub2 = self._create_subscription(user, plan, stripe_subscription_id='sub_2')

        subs = list(Subscription.objects.all())
        assert subs[0].created_at >= subs[1].created_at

    def test_meta_verbose_names(self):
        """Test meta verbose names."""
        assert Subscription._meta.verbose_name == 'Subscription'
        assert Subscription._meta.verbose_name_plural == 'Subscriptions'

    def test_timestamps_set_automatically(self, user, plan):
        """Test that timestamps are set automatically."""
        sub = self._create_subscription(user, plan)
        assert sub.created_at is not None
        assert sub.updated_at is not None

    def test_plan_protect_on_delete(self, user, plan):
        """Test that deleting plan with subscriptions raises ProtectedError."""
        self._create_subscription(user, plan)
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            plan.delete()

    def test_user_cascade_on_delete(self, user, plan):
        """Test that deleting user cascades to subscriptions."""
        self._create_subscription(user, plan)
        user_id = user.pk
        user.delete()
        assert Subscription.objects.filter(user_id=user_id).count() == 0

    def test_related_name_from_user(self, user, plan):
        """Test related_name 'subscriptions' from user."""
        self._create_subscription(user, plan)
        assert user.subscriptions.count() == 1

    def test_related_name_from_plan(self, user, plan):
        """Test related_name 'subscriptions' from plan."""
        self._create_subscription(user, plan)
        assert plan.subscriptions.count() == 1

    def test_multiple_subscriptions_per_user(self, user, plan):
        """Test user can have multiple subscriptions."""
        plan2 = SubscriptionPlan.objects.create(
            name='Premium Plan',
            slug='premium-plan',
            price=Decimal('99.99'),
        )
        self._create_subscription(user, plan, stripe_subscription_id='sub_1')
        self._create_subscription(user, plan2, stripe_subscription_id='sub_2')
        assert user.subscriptions.count() == 2

    def test_all_status_values(self, user, plan):
        """Test creating subscriptions with all status values."""
        statuses = ['active', 'canceled', 'past_due', 'trialing', 'paused']
        for i, status in enumerate(statuses):
            sub = self._create_subscription(
                user, plan,
                status=status,
                stripe_subscription_id=f'sub_{i}',
            )
            assert sub.status == status
