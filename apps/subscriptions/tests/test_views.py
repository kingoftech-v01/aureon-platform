"""Tests for subscriptions views."""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.test import RequestFactory, TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from unittest.mock import MagicMock

from apps.subscriptions.models import SubscriptionPlan, Subscription
from apps.subscriptions.views import SubscriptionPlanListView, UserSubscriptionView

User = get_user_model()


@pytest.mark.django_db
class TestSubscriptionPlanListView:
    """Tests for SubscriptionPlanListView."""

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    def _create_plans(self):
        """Create test subscription plans."""
        active_plan1 = SubscriptionPlan.objects.create(
            name='Basic Plan',
            slug='basic',
            price=Decimal('9.99'),
            is_active=True,
        )
        active_plan2 = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro',
            price=Decimal('49.99'),
            is_active=True,
        )
        inactive_plan = SubscriptionPlan.objects.create(
            name='Legacy Plan',
            slug='legacy',
            price=Decimal('19.99'),
            is_active=False,
        )
        return active_plan1, active_plan2, inactive_plan

    def test_view_returns_only_active_plans(self, factory):
        """Test that only active plans are returned."""
        active1, active2, inactive = self._create_plans()
        request = factory.get('/subscriptions/plans/')
        view = SubscriptionPlanListView()
        view.request = request

        queryset = view.get_queryset()

        assert queryset.count() == 2
        assert inactive not in queryset

    def test_view_model(self):
        """Test that view uses SubscriptionPlan model."""
        assert SubscriptionPlanListView.model == SubscriptionPlan

    def test_view_template_name(self):
        """Test the template name."""
        assert SubscriptionPlanListView.template_name == 'subscriptions/plan_list.html'

    def test_view_context_object_name(self):
        """Test the context object name."""
        assert SubscriptionPlanListView.context_object_name == 'plans'

    def test_empty_plans(self, factory):
        """Test view with no plans."""
        request = factory.get('/subscriptions/plans/')
        view = SubscriptionPlanListView()
        view.request = request

        queryset = view.get_queryset()

        assert queryset.count() == 0

    def test_all_inactive_plans(self, factory):
        """Test view when all plans are inactive."""
        SubscriptionPlan.objects.create(
            name='Inactive 1', slug='inactive-1',
            price=Decimal('9.99'), is_active=False,
        )
        SubscriptionPlan.objects.create(
            name='Inactive 2', slug='inactive-2',
            price=Decimal('19.99'), is_active=False,
        )
        request = factory.get('/subscriptions/plans/')
        view = SubscriptionPlanListView()
        view.request = request

        queryset = view.get_queryset()

        assert queryset.count() == 0


@pytest.mark.django_db
class TestUserSubscriptionView:
    """Tests for UserSubscriptionView."""

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    @pytest.fixture
    def plan(self):
        return SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price=Decimal('29.99'),
        )

    @pytest.fixture
    def user(self, tenant):
        return User.objects.create_user(
            email='subuser@test.com',
            password='TestPass123!',
            first_name='Sub',
            last_name='User',
            tenant=tenant,
        )

    def test_view_returns_active_subscription(self, factory, user, plan):
        """Test that view returns the active subscription for the user."""
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status='active',
            current_period_end=timezone.now() + timedelta(days=15),
        )
        request = factory.get('/subscriptions/my/')
        request.user = user

        view = UserSubscriptionView()
        view.request = request
        view.kwargs = {}

        obj = view.get_object()

        assert obj == subscription

    def test_view_returns_none_when_no_active_subscription(self, factory, user, plan):
        """Test that view returns None when no active subscription exists."""
        Subscription.objects.create(
            user=user,
            plan=plan,
            status='canceled',
        )
        request = factory.get('/subscriptions/my/')
        request.user = user

        view = UserSubscriptionView()
        view.request = request
        view.kwargs = {}

        obj = view.get_object()

        assert obj is None

    def test_view_returns_none_when_no_subscriptions(self, factory, user):
        """Test that view returns None when user has no subscriptions."""
        request = factory.get('/subscriptions/my/')
        request.user = user

        view = UserSubscriptionView()
        view.request = request
        view.kwargs = {}

        obj = view.get_object()

        assert obj is None

    def test_view_returns_first_active_subscription(self, factory, user, plan):
        """Test that view returns first active subscription if multiple exist."""
        plan2 = SubscriptionPlan.objects.create(
            name='Other Plan',
            slug='other-plan',
            price=Decimal('99.99'),
        )
        sub1 = Subscription.objects.create(
            user=user,
            plan=plan,
            status='active',
        )
        sub2 = Subscription.objects.create(
            user=user,
            plan=plan2,
            status='active',
        )
        request = factory.get('/subscriptions/my/')
        request.user = user

        view = UserSubscriptionView()
        view.request = request
        view.kwargs = {}

        obj = view.get_object()

        # .first() returns the first one based on ordering
        assert obj is not None
        assert obj.status == 'active'

    def test_view_model(self):
        """Test that view uses Subscription model."""
        assert UserSubscriptionView.model == Subscription

    def test_view_template_name(self):
        """Test the template name."""
        assert UserSubscriptionView.template_name == 'subscriptions/subscription_detail.html'

    def test_view_context_object_name(self):
        """Test the context object name."""
        assert UserSubscriptionView.context_object_name == 'subscription'

    def test_view_requires_login(self):
        """Test that view requires authentication (LoginRequiredMixin)."""
        from django.contrib.auth.mixins import LoginRequiredMixin
        assert issubclass(UserSubscriptionView, LoginRequiredMixin)

    def test_view_ignores_other_users_subscriptions(self, factory, user, plan, tenant):
        """Test that view only returns subscriptions for the requesting user."""
        other_user = User.objects.create_user(
            email='other@test.com',
            password='TestPass123!',
            first_name='Other',
            last_name='User',
            tenant=tenant,
        )
        Subscription.objects.create(
            user=other_user,
            plan=plan,
            status='active',
        )
        request = factory.get('/subscriptions/my/')
        request.user = user

        view = UserSubscriptionView()
        view.request = request
        view.kwargs = {}

        obj = view.get_object()

        assert obj is None
