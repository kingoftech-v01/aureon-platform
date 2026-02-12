"""Tests for subscriptions admin configuration."""

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

from apps.subscriptions.models import SubscriptionPlan, Subscription
from apps.subscriptions.admin import SubscriptionPlanAdmin, SubscriptionAdmin


@pytest.mark.django_db
class TestSubscriptionPlanAdmin:
    """Tests for SubscriptionPlanAdmin."""

    @pytest.fixture
    def plan_admin(self):
        site = AdminSite()
        return SubscriptionPlanAdmin(SubscriptionPlan, site)

    def test_registered_with_admin(self):
        """Test that SubscriptionPlan is registered with admin site."""
        assert SubscriptionPlan in admin.site._registry

    def test_list_display(self, plan_admin):
        """Test list_display configuration."""
        expected = ['name', 'price', 'currency', 'interval', 'is_active', 'created_at']
        assert plan_admin.list_display == expected

    def test_list_filter(self, plan_admin):
        """Test list_filter configuration."""
        assert 'is_active' in plan_admin.list_filter
        assert 'interval' in plan_admin.list_filter
        assert 'currency' in plan_admin.list_filter

    def test_search_fields(self, plan_admin):
        """Test search_fields configuration."""
        assert 'name' in plan_admin.search_fields
        assert 'slug' in plan_admin.search_fields
        assert 'description' in plan_admin.search_fields

    def test_prepopulated_fields(self, plan_admin):
        """Test prepopulated_fields for slug."""
        assert plan_admin.prepopulated_fields == {'slug': ('name',)}

    def test_ordering(self, plan_admin):
        """Test ordering configuration."""
        assert plan_admin.ordering == ['price']


@pytest.mark.django_db
class TestSubscriptionAdmin:
    """Tests for SubscriptionAdmin."""

    @pytest.fixture
    def subscription_admin(self):
        site = AdminSite()
        return SubscriptionAdmin(Subscription, site)

    def test_registered_with_admin(self):
        """Test that Subscription is registered with admin site."""
        assert Subscription in admin.site._registry

    def test_list_display(self, subscription_admin):
        """Test list_display configuration."""
        expected = ['user', 'plan', 'status', 'current_period_end', 'cancel_at_period_end', 'created_at']
        assert subscription_admin.list_display == expected

    def test_list_filter(self, subscription_admin):
        """Test list_filter configuration."""
        assert 'status' in subscription_admin.list_filter
        assert 'plan' in subscription_admin.list_filter
        assert 'cancel_at_period_end' in subscription_admin.list_filter

    def test_search_fields(self, subscription_admin):
        """Test search_fields configuration."""
        assert 'user__email' in subscription_admin.search_fields
        assert 'stripe_subscription_id' in subscription_admin.search_fields

    def test_raw_id_fields(self, subscription_admin):
        """Test raw_id_fields configuration."""
        assert 'user' in subscription_admin.raw_id_fields

    def test_readonly_fields(self, subscription_admin):
        """Test readonly_fields configuration."""
        assert 'created_at' in subscription_admin.readonly_fields
        assert 'updated_at' in subscription_admin.readonly_fields

    def test_ordering(self, subscription_admin):
        """Test ordering configuration."""
        assert subscription_admin.ordering == ['-created_at']
