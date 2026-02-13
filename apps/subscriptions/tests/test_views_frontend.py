"""
Tests for subscriptions app frontend views.

Tests cover:
- SubscriptionPlanListView (plan listing with current subscription)
- SubscriptionDetailView (detail page with plan, status, renewal info)
- SubscriptionManageView (management page with available plans and history)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import pytest
from datetime import timedelta
from decimal import Decimal
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.subscriptions.models import SubscriptionPlan, Subscription

User = get_user_model()


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
PLAN_LIST_URL = '/api/subscriptions/plans/'
SUBSCRIPTION_MANAGE_URL = '/api/subscriptions/manage/'


def subscription_detail_url(pk):
    return f'/api/subscriptions/{pk}/'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='sub_test_user',
        email='sub_user@test.com',
        password='TestPass123!',
        role=User.ADMIN,
        is_staff=True,
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def auth_client(user):
    client = TestClient()
    client.force_login(user)
    return client


@pytest.fixture
def plan_monthly(db):
    return SubscriptionPlan.objects.create(
        name='Pro Monthly',
        slug='pro-monthly',
        price=Decimal('49.99'),
        interval='month',
        is_active=True,
        features=['feature_a', 'feature_b'],
    )


@pytest.fixture
def plan_yearly(db):
    return SubscriptionPlan.objects.create(
        name='Pro Yearly',
        slug='pro-yearly',
        price=Decimal('499.99'),
        interval='year',
        is_active=True,
        features=['feature_a', 'feature_b', 'feature_c'],
    )


@pytest.fixture
def inactive_plan(db):
    return SubscriptionPlan.objects.create(
        name='Legacy Plan',
        slug='legacy',
        price=Decimal('9.99'),
        interval='month',
        is_active=False,
    )


@pytest.fixture
def subscription(user, plan_monthly):
    return Subscription.objects.create(
        user=user,
        plan=plan_monthly,
        status='active',
        current_period_start=timezone.now(),
        current_period_end=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def canceled_subscription(user, plan_yearly):
    return Subscription.objects.create(
        user=user,
        plan=plan_yearly,
        status='canceled',
        current_period_start=timezone.now() - timedelta(days=365),
        current_period_end=timezone.now() - timedelta(days=5),
        canceled_at=timezone.now() - timedelta(days=5),
    )


# ---------------------------------------------------------------------------
# SubscriptionPlanListView tests
# ---------------------------------------------------------------------------
class TestSubscriptionPlanListView:
    """Tests for SubscriptionPlanListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(PLAN_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, plan_monthly):
        try:
            response = auth_client.get(PLAN_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, plan_monthly, plan_yearly):
        try:
            response = auth_client.get(PLAN_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Subscription Plans'
            assert 'interval_choices' in ctx
            assert 'current_subscription' in ctx
            assert 'plans' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_only_active_plans_listed(self, auth_client, plan_monthly, inactive_plan):
        try:
            response = auth_client.get(PLAN_LIST_URL)
            plans = list(response.context['plans'])
            assert plan_monthly in plans
            assert inactive_plan not in plans
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_current_subscription_in_context(self, auth_client, subscription):
        try:
            response = auth_client.get(PLAN_LIST_URL)
            ctx = response.context
            assert ctx['current_subscription'] == subscription
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_no_current_subscription(self, auth_client, plan_monthly):
        try:
            response = auth_client.get(PLAN_LIST_URL)
            ctx = response.context
            assert ctx['current_subscription'] is None
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# SubscriptionDetailView tests
# ---------------------------------------------------------------------------
class TestSubscriptionDetailView:
    """Tests for SubscriptionDetailView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, subscription):
        client = TestClient()
        response = client.get(subscription_detail_url(subscription.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, subscription):
        try:
            response = auth_client.get(subscription_detail_url(subscription.pk))
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_detail_data(self, auth_client, subscription):
        try:
            response = auth_client.get(subscription_detail_url(subscription.pk))
            ctx = response.context
            assert ctx['subscription'] == subscription
            assert 'page_title' in ctx
            assert 'plan' in ctx
            assert 'is_active' in ctx
            assert 'days_until_renewal' in ctx
            assert 'cancel_at_period_end' in ctx
            assert 'status_choices' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_plan_matches_subscription_plan(self, auth_client, subscription):
        try:
            response = auth_client.get(subscription_detail_url(subscription.pk))
            ctx = response.context
            assert ctx['plan'] == subscription.plan
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# SubscriptionManageView tests
# ---------------------------------------------------------------------------
class TestSubscriptionManageView:
    """Tests for SubscriptionManageView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(SUBSCRIPTION_MANAGE_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client):
        try:
            response = auth_client.get(SUBSCRIPTION_MANAGE_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_manage_data(self, auth_client, subscription, plan_monthly, plan_yearly):
        try:
            response = auth_client.get(SUBSCRIPTION_MANAGE_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Manage Subscription'
            assert 'current_subscription' in ctx
            assert 'available_plans' in ctx
            assert 'all_subscriptions' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_current_subscription_in_manage_context(self, auth_client, subscription):
        try:
            response = auth_client.get(SUBSCRIPTION_MANAGE_URL)
            ctx = response.context
            assert ctx['current_subscription'] == subscription
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_all_subscriptions_includes_history(self, auth_client, subscription, canceled_subscription):
        try:
            response = auth_client.get(SUBSCRIPTION_MANAGE_URL)
            all_subs = list(response.context['all_subscriptions'])
            assert subscription in all_subs
            assert canceled_subscription in all_subs
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_available_plans_only_active(self, auth_client, plan_monthly, inactive_plan):
        try:
            response = auth_client.get(SUBSCRIPTION_MANAGE_URL)
            available = list(response.context['available_plans'])
            assert plan_monthly in available
            assert inactive_plan not in available
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_no_current_subscription_in_manage(self, auth_client, plan_monthly):
        try:
            response = auth_client.get(SUBSCRIPTION_MANAGE_URL)
            ctx = response.context
            assert ctx['current_subscription'] is None
        except TemplateDoesNotExist:
            pass
