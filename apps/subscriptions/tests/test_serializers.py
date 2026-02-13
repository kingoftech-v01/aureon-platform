"""Tests for subscriptions serializers."""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.subscriptions.models import SubscriptionPlan, Subscription
from apps.subscriptions.serializers import (
    SubscriptionPlanListSerializer,
    SubscriptionPlanDetailSerializer,
    SubscriptionSerializer,
    SubscriptionCreateSerializer,
    SubscriptionChangePlanSerializer,
    SubscriptionCancelSerializer,
    SubscriptionStatsSerializer,
)

User = get_user_model()


@pytest.fixture
def plan_monthly(db):
    return SubscriptionPlan.objects.create(
        name='Pro Monthly', slug='pro-monthly',
        price=Decimal('49.99'), currency='USD', interval='month',
        features=['feature_a', 'feature_b'], is_active=True,
    )


@pytest.fixture
def plan_yearly(db):
    return SubscriptionPlan.objects.create(
        name='Pro Yearly', slug='pro-yearly',
        price=Decimal('499.99'), currency='USD', interval='year',
        features=['feature_a', 'feature_b', 'feature_c'], is_active=True,
    )


@pytest.fixture
def sub_user(db):
    return User.objects.create_user(
        username='subtest', email='subtest@example.com',
        password='SecurePass123!', first_name='Sub', last_name='Tester',
    )


@pytest.fixture
def active_subscription(db, sub_user, plan_monthly):
    return Subscription.objects.create(
        user=sub_user, plan=plan_monthly, status='active',
        current_period_start=timezone.now(),
        current_period_end=timezone.now() + timedelta(days=30),
    )


# ---------------------------------------------------------------------------
# SubscriptionPlanListSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSubscriptionPlanListSerializer:

    def test_expected_fields(self, plan_monthly):
        data = SubscriptionPlanListSerializer(plan_monthly).data
        for field in ['id', 'name', 'slug', 'description', 'price', 'currency',
                      'interval', 'features', 'is_active', 'subscriber_count',
                      'created_at', 'updated_at']:
            assert field in data, f"Missing field: {field}"

    def test_subscriber_count_zero(self, plan_monthly):
        data = SubscriptionPlanListSerializer(plan_monthly).data
        assert data['subscriber_count'] == 0

    def test_subscriber_count_with_active(self, plan_monthly, active_subscription):
        data = SubscriptionPlanListSerializer(plan_monthly).data
        assert data['subscriber_count'] == 1

    def test_subscriber_count_excludes_canceled(self, plan_monthly, sub_user):
        Subscription.objects.create(
            user=sub_user, plan=plan_monthly, status='canceled',
        )
        data = SubscriptionPlanListSerializer(plan_monthly).data
        assert data['subscriber_count'] == 0

    def test_price_serialized(self, plan_monthly):
        data = SubscriptionPlanListSerializer(plan_monthly).data
        assert Decimal(data['price']) == Decimal('49.99')

    def test_features_serialized(self, plan_monthly):
        data = SubscriptionPlanListSerializer(plan_monthly).data
        assert data['features'] == ['feature_a', 'feature_b']

    def test_read_only_fields(self):
        meta = SubscriptionPlanListSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields


# ---------------------------------------------------------------------------
# SubscriptionPlanDetailSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSubscriptionPlanDetailSerializer:

    def test_includes_revenue_monthly(self, plan_monthly):
        data = SubscriptionPlanDetailSerializer(plan_monthly).data
        assert 'revenue_monthly' in data

    def test_revenue_monthly_calculation(self, plan_monthly, active_subscription):
        data = SubscriptionPlanDetailSerializer(plan_monthly).data
        assert data['revenue_monthly'] == float(plan_monthly.price)

    def test_revenue_monthly_yearly_plan(self, plan_yearly, sub_user):
        Subscription.objects.create(
            user=sub_user, plan=plan_yearly, status='active',
        )
        data = SubscriptionPlanDetailSerializer(plan_yearly).data
        expected = float(plan_yearly.price / 12)
        assert abs(data['revenue_monthly'] - expected) < 0.01


# ---------------------------------------------------------------------------
# SubscriptionSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSubscriptionSerializer:

    def test_expected_fields(self, active_subscription):
        data = SubscriptionSerializer(active_subscription).data
        for field in ['id', 'user', 'user_email', 'plan', 'plan_name',
                      'plan_price', 'plan_interval', 'status',
                      'stripe_subscription_id', 'current_period_start',
                      'current_period_end', 'cancel_at_period_end',
                      'canceled_at', 'is_active', 'days_until_renewal',
                      'created_at', 'updated_at']:
            assert field in data, f"Missing field: {field}"

    def test_nested_plan_fields(self, active_subscription):
        data = SubscriptionSerializer(active_subscription).data
        assert data['plan_name'] == 'Pro Monthly'
        assert Decimal(data['plan_price']) == Decimal('49.99')
        assert data['plan_interval'] == 'month'

    def test_user_email(self, active_subscription):
        data = SubscriptionSerializer(active_subscription).data
        assert data['user_email'] == 'subtest@example.com'

    def test_is_active_property(self, active_subscription):
        data = SubscriptionSerializer(active_subscription).data
        assert data['is_active'] is True

    def test_days_until_renewal(self, active_subscription):
        data = SubscriptionSerializer(active_subscription).data
        assert data['days_until_renewal'] >= 29

    def test_read_only_fields(self):
        meta = SubscriptionSerializer.Meta
        for field in ['id', 'user', 'status', 'stripe_subscription_id',
                      'current_period_start', 'current_period_end',
                      'cancel_at_period_end', 'canceled_at',
                      'created_at', 'updated_at']:
            assert field in meta.read_only_fields


# ---------------------------------------------------------------------------
# SubscriptionCreateSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSubscriptionCreateSerializer:

    def _make_request(self, user):
        factory = APIRequestFactory()
        request = factory.post('/api/subscriptions/subscribe/')
        request.user = user
        return request

    def test_valid_data(self, sub_user, plan_monthly):
        request = self._make_request(sub_user)
        serializer = SubscriptionCreateSerializer(
            data={'plan_id': plan_monthly.id},
            context={'request': request},
        )
        assert serializer.is_valid(), serializer.errors

    def test_invalid_plan_id(self, sub_user):
        request = self._make_request(sub_user)
        serializer = SubscriptionCreateSerializer(
            data={'plan_id': 99999},
            context={'request': request},
        )
        assert not serializer.is_valid()
        assert 'plan_id' in serializer.errors

    def test_inactive_plan_rejected(self, sub_user, plan_monthly):
        plan_monthly.is_active = False
        plan_monthly.save()
        request = self._make_request(sub_user)
        serializer = SubscriptionCreateSerializer(
            data={'plan_id': plan_monthly.id},
            context={'request': request},
        )
        assert not serializer.is_valid()

    def test_duplicate_active_subscription(self, sub_user, plan_monthly, active_subscription):
        request = self._make_request(sub_user)
        serializer = SubscriptionCreateSerializer(
            data={'plan_id': plan_monthly.id},
            context={'request': request},
        )
        assert not serializer.is_valid()
        assert 'plan_id' in serializer.errors

    def test_payment_method_id_optional(self, sub_user, plan_monthly):
        request = self._make_request(sub_user)
        serializer = SubscriptionCreateSerializer(
            data={'plan_id': plan_monthly.id, 'payment_method_id': ''},
            context={'request': request},
        )
        assert serializer.is_valid()


# ---------------------------------------------------------------------------
# SubscriptionChangePlanSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSubscriptionChangePlanSerializer:

    def test_valid_data(self, plan_monthly):
        serializer = SubscriptionChangePlanSerializer(
            data={'new_plan_id': plan_monthly.id},
        )
        assert serializer.is_valid()

    def test_invalid_plan(self):
        serializer = SubscriptionChangePlanSerializer(
            data={'new_plan_id': 99999},
        )
        assert not serializer.is_valid()

    def test_prorate_default_true(self, plan_monthly):
        serializer = SubscriptionChangePlanSerializer(
            data={'new_plan_id': plan_monthly.id},
        )
        serializer.is_valid()
        assert serializer.validated_data['prorate'] is True


# ---------------------------------------------------------------------------
# SubscriptionCancelSerializer
# ---------------------------------------------------------------------------

class TestSubscriptionCancelSerializer:

    def test_default_not_immediate(self):
        serializer = SubscriptionCancelSerializer(data={})
        serializer.is_valid()
        assert serializer.validated_data['immediate'] is False

    def test_immediate_true(self):
        serializer = SubscriptionCancelSerializer(data={'immediate': True})
        serializer.is_valid()
        assert serializer.validated_data['immediate'] is True

    def test_reason_optional(self):
        serializer = SubscriptionCancelSerializer(data={'reason': 'Too expensive'})
        assert serializer.is_valid()
        assert serializer.validated_data['reason'] == 'Too expensive'


# ---------------------------------------------------------------------------
# SubscriptionStatsSerializer
# ---------------------------------------------------------------------------

class TestSubscriptionStatsSerializer:

    def test_serializes_all_fields(self):
        data = {
            'total_subscriptions': 100,
            'active_subscriptions': 80,
            'canceled_subscriptions': 10,
            'past_due_subscriptions': 5,
            'trialing_subscriptions': 3,
            'paused_subscriptions': 2,
            'monthly_recurring_revenue': Decimal('5000.00'),
            'annual_recurring_revenue': Decimal('60000.00'),
            'average_revenue_per_user': Decimal('62.50'),
            'churn_rate': Decimal('11.11'),
        }
        serializer = SubscriptionStatsSerializer(data)
        for key in data:
            assert key in serializer.data
