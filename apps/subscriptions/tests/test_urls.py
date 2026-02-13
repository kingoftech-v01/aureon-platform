"""Tests for subscriptions URL configuration."""

import pytest
from django.urls import reverse, resolve


# We configure a custom ROOT_URLCONF so reverse() finds our app routes.
urlpatterns = __import__(
    'apps.subscriptions.tests.test_urls', fromlist=['urlpatterns']
).__dict__.get('_urls', None)

# Build the URL patterns for test resolution
from django.urls import path, include  # noqa: E402

urlpatterns = [
    path('api/subscriptions/', include('apps.subscriptions.urls')),
]


@pytest.mark.django_db
class TestSubscriptionURLs:

    @pytest.fixture(autouse=True)
    def _set_urls(self, settings):
        settings.ROOT_URLCONF = 'apps.subscriptions.tests.test_urls'

    def test_plan_list_resolves(self):
        url = reverse('subscriptions:subscription-plan-list')
        assert '/api/subscriptions/plans/' in url
        match = resolve(url)
        assert match.url_name == 'subscription-plan-list'

    def test_plan_detail_resolves(self):
        url = reverse('subscriptions:subscription-plan-detail', args=[1])
        assert '/api/subscriptions/plans/1/' in url

    def test_subscription_list_resolves(self):
        url = reverse('subscriptions:subscription-list')
        assert '/api/subscriptions/' in url

    def test_subscribe_resolves(self):
        url = reverse('subscriptions:subscription-subscribe')
        assert 'subscribe' in url

    def test_current_resolves(self):
        url = reverse('subscriptions:subscription-current')
        assert 'current' in url

    def test_stats_resolves(self):
        url = reverse('subscriptions:subscription-stats')
        assert 'stats' in url

    def test_cancel_resolves(self):
        url = reverse('subscriptions:subscription-cancel', args=[1])
        assert 'cancel' in url

    def test_pause_resolves(self):
        url = reverse('subscriptions:subscription-pause', args=[1])
        assert 'pause' in url

    def test_resume_resolves(self):
        url = reverse('subscriptions:subscription-resume', args=[1])
        assert 'resume' in url

    def test_change_plan_resolves(self):
        url = reverse('subscriptions:subscription-change-plan', args=[1])
        assert 'change_plan' in url
