"""Tests for subscriptions REST API views."""

import pytest
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.utils import timezone
from django.urls import path, include
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.subscriptions.models import SubscriptionPlan, Subscription

User = get_user_model()

# URL configuration for tests
urlpatterns = [
    path('api/subscriptions/', include('apps.subscriptions.urls')),
]


@pytest.mark.django_db
class TestSubscriptionPlanViewSet:
    """Tests for SubscriptionPlanViewSet."""

    BASE_URL = '/api/subscriptions/plans/'

    @pytest.fixture(autouse=True)
    def _use_custom_urls(self, settings):
        settings.ROOT_URLCONF = 'apps.subscriptions.tests.test_views'

    @pytest.fixture
    def active_plan(self, db):
        return SubscriptionPlan.objects.create(
            name='Pro', slug='pro', price=Decimal('49.99'),
            interval='month', is_active=True,
            features=['feature_a', 'feature_b'],
        )

    @pytest.fixture
    def inactive_plan(self, db):
        return SubscriptionPlan.objects.create(
            name='Legacy', slug='legacy', price=Decimal('9.99'),
            interval='month', is_active=False,
        )

    # ---- List ----

    def test_list_plans(self, authenticated_admin_client, active_plan):
        response = authenticated_admin_client.get(self.BASE_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_non_staff_only_sees_active(self, authenticated_contributor_client, active_plan, inactive_plan):
        response = authenticated_contributor_client.get(self.BASE_URL)
        assert response.status_code == status.HTTP_200_OK
        slugs = [p['slug'] for p in response.data['results']]
        assert 'pro' in slugs
        assert 'legacy' not in slugs

    def test_staff_sees_all(self, authenticated_admin_client, active_plan, inactive_plan):
        response = authenticated_admin_client.get(self.BASE_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_unauthenticated_denied(self):
        client = APIClient()
        response = client.get(self.BASE_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---- Create ----

    def test_create_plan(self, authenticated_admin_client):
        data = {
            'name': 'Enterprise', 'slug': 'enterprise',
            'price': '199.99', 'interval': 'year',
            'features': ['unlimited'], 'is_active': True,
        }
        response = authenticated_admin_client.post(self.BASE_URL, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert SubscriptionPlan.objects.filter(slug='enterprise').exists()

    # ---- Retrieve ----

    def test_retrieve_plan(self, authenticated_admin_client, active_plan):
        response = authenticated_admin_client.get(f'{self.BASE_URL}{active_plan.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Pro'
        assert 'revenue_monthly' in response.data  # detail serializer

    # ---- Update ----

    def test_update_plan(self, authenticated_admin_client, active_plan):
        data = {
            'name': 'Pro Updated', 'slug': 'pro',
            'price': '59.99', 'interval': 'month',
        }
        response = authenticated_admin_client.put(
            f'{self.BASE_URL}{active_plan.id}/', data, format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        active_plan.refresh_from_db()
        assert active_plan.name == 'Pro Updated'

    # ---- Delete (soft) ----

    def test_delete_soft_deactivates(self, authenticated_admin_client, active_plan):
        response = authenticated_admin_client.delete(f'{self.BASE_URL}{active_plan.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        active_plan.refresh_from_db()
        assert active_plan.is_active is False

    # ---- Filter / Search / Order ----

    def test_filter_by_interval(self, authenticated_admin_client, active_plan):
        response = authenticated_admin_client.get(f'{self.BASE_URL}?interval=month')
        assert response.status_code == status.HTTP_200_OK

    def test_search_by_name(self, authenticated_admin_client, active_plan):
        response = authenticated_admin_client.get(f'{self.BASE_URL}?search=Pro')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestSubscriptionViewSet:
    """Tests for SubscriptionViewSet."""

    BASE_URL = '/api/subscriptions/'

    @pytest.fixture(autouse=True)
    def _use_custom_urls(self, settings):
        settings.ROOT_URLCONF = 'apps.subscriptions.tests.test_views'

    @pytest.fixture
    def plan(self, db):
        return SubscriptionPlan.objects.create(
            name='Pro', slug='pro', price=Decimal('49.99'),
            interval='month', is_active=True,
        )

    @pytest.fixture
    def plan2(self, db):
        return SubscriptionPlan.objects.create(
            name='Enterprise', slug='enterprise', price=Decimal('99.99'),
            interval='month', is_active=True,
        )

    @pytest.fixture
    def subscription(self, db, admin_user, plan):
        return Subscription.objects.create(
            user=admin_user, plan=plan, status='active',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30),
        )

    # ---- List ----

    def test_list_own_subscriptions(self, authenticated_admin_client, subscription):
        response = authenticated_admin_client.get(self.BASE_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_denied(self):
        client = APIClient()
        response = client.get(self.BASE_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---- Retrieve ----

    def test_retrieve_subscription(self, authenticated_admin_client, subscription):
        response = authenticated_admin_client.get(f'{self.BASE_URL}{subscription.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['plan_name'] == 'Pro'

    # ---- Subscribe ----

    def test_subscribe_success(self, authenticated_contributor_client, plan, contributor_user):
        data = {'plan_id': plan.id}
        response = authenticated_contributor_client.post(
            f'{self.BASE_URL}subscribe/', data, format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['plan_name'] == 'Pro'
        assert Subscription.objects.filter(user=contributor_user).exists()

    def test_subscribe_invalid_plan(self, authenticated_admin_client):
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}subscribe/', {'plan_id': 99999}, format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_subscribe_duplicate_rejected(self, authenticated_admin_client, subscription, plan2):
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}subscribe/', {'plan_id': plan2.id}, format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ---- Cancel ----

    def test_cancel_at_period_end(self, authenticated_admin_client, subscription):
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{subscription.id}/cancel/',
            {'immediate': False}, format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['cancel_at_period_end'] is True

    def test_cancel_immediate(self, authenticated_admin_client, subscription):
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{subscription.id}/cancel/',
            {'immediate': True}, format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'canceled'

    def test_cancel_already_canceled(self, authenticated_admin_client, subscription):
        subscription.status = 'canceled'
        subscription.save()
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{subscription.id}/cancel/',
            {'immediate': True}, format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ---- Pause / Resume ----

    def test_pause(self, authenticated_admin_client, subscription):
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{subscription.id}/pause/',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'paused'

    def test_pause_non_active(self, authenticated_admin_client, subscription):
        subscription.status = 'canceled'
        subscription.save()
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{subscription.id}/pause/',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_resume(self, authenticated_admin_client, subscription):
        subscription.status = 'paused'
        subscription.save()
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{subscription.id}/resume/',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'active'

    def test_resume_non_paused(self, authenticated_admin_client, subscription):
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{subscription.id}/resume/',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ---- Change Plan ----

    def test_change_plan(self, authenticated_admin_client, subscription, plan2):
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{subscription.id}/change_plan/',
            {'new_plan_id': plan2.id}, format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['plan_name'] == 'Enterprise'

    def test_change_to_same_plan(self, authenticated_admin_client, subscription):
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{subscription.id}/change_plan/',
            {'new_plan_id': subscription.plan.id}, format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_plan_invalid(self, authenticated_admin_client, subscription):
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{subscription.id}/change_plan/',
            {'new_plan_id': 99999}, format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ---- Current ----

    def test_current_returns_active(self, authenticated_admin_client, subscription):
        response = authenticated_admin_client.get(f'{self.BASE_URL}current/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['plan_name'] == 'Pro'

    def test_current_returns_404_when_none(self, authenticated_contributor_client):
        response = authenticated_contributor_client.get(f'{self.BASE_URL}current/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ---- Stats ----

    def test_stats_admin(self, authenticated_admin_client, subscription):
        response = authenticated_admin_client.get(f'{self.BASE_URL}stats/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_subscriptions' in response.data
        assert 'monthly_recurring_revenue' in response.data

    def test_stats_non_admin_denied(self, authenticated_contributor_client):
        response = authenticated_contributor_client.get(f'{self.BASE_URL}stats/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ---- Non-staff queryset filtering ----

    def test_non_staff_only_sees_own_subscriptions(
        self, authenticated_contributor_client, contributor_user, plan
    ):
        """Non-staff user should only see their own subscriptions (line 91)."""
        # Create subscription for the contributor
        sub = Subscription.objects.create(
            user=contributor_user, plan=plan, status='active',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30),
        )
        response = authenticated_contributor_client.get(self.BASE_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 1
        assert results[0]['plan_name'] == plan.name

    # ---- Subscribe exception handling ----

    def test_subscribe_service_exception(self, authenticated_contributor_client, plan):
        """Subscribe catches service exceptions and returns 400 (lines 111-113)."""
        with patch(
            'apps.subscriptions.views.SubscriptionService.create_subscription'
        ) as mock_create:
            mock_create.side_effect = Exception('Unexpected DB error')
            data = {'plan_id': plan.id}
            response = authenticated_contributor_client.post(
                f'{self.BASE_URL}subscribe/', data, format='json',
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
