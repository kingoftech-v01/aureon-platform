"""
Tests for payments app URL configuration.
"""

import pytest
from django.urls import reverse, resolve

from apps.payments.views import PaymentViewSet, PaymentMethodViewSet


class TestPaymentsURLs:
    """Tests for payments URL patterns."""

    def test_payment_list_url_resolves(self):
        """Test that the payment list URL resolves correctly."""
        url = reverse('payments:payment-list')
        # App urls.py has path('api/', ...) and config/urls.py includes under 'api/'
        assert url == '/api/api/payments/'
        resolver = resolve(url)
        assert resolver.func.cls == PaymentViewSet

    def test_payment_detail_url_resolves(self):
        """Test that the payment detail URL resolves correctly."""
        url = reverse('payments:payment-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000001'})
        assert '/payments/' in url
        resolver = resolve(url)
        assert resolver.func.cls == PaymentViewSet

    def test_payment_stats_url_resolves(self):
        """Test that the payment stats action URL resolves."""
        url = reverse('payments:payment-stats')
        assert url == '/api/api/payments/stats/'
        resolver = resolve(url)
        assert resolver.func.cls == PaymentViewSet

    def test_payment_refund_url_resolves(self):
        """Test that the payment refund action URL resolves."""
        url = reverse('payments:payment-refund', kwargs={'pk': '00000000-0000-0000-0000-000000000001'})
        assert '/payments/' in url
        assert '/refund/' in url
        resolver = resolve(url)
        assert resolver.func.cls == PaymentViewSet

    def test_payment_method_list_url_resolves(self):
        """Test that the payment method list URL resolves correctly."""
        url = reverse('payments:payment-method-list')
        assert url == '/api/api/payment-methods/'
        resolver = resolve(url)
        assert resolver.func.cls == PaymentMethodViewSet

    def test_payment_method_detail_url_resolves(self):
        """Test that the payment method detail URL resolves correctly."""
        url = reverse(
            'payments:payment-method-detail',
            kwargs={'pk': '00000000-0000-0000-0000-000000000001'},
        )
        assert '/payment-methods/' in url
        resolver = resolve(url)
        assert resolver.func.cls == PaymentMethodViewSet

    def test_app_name(self):
        """Test that the app_name is set correctly."""
        from apps.payments import urls as payments_urls
        assert payments_urls.app_name == 'payments'

    def test_router_registered_viewsets(self):
        """Test that the router has registered both viewsets."""
        from apps.payments.urls import router
        # router.registry is a list of tuples: (prefix, viewset, basename)
        registered_basenames = [entry[2] for entry in router.registry]
        assert 'payment' in registered_basenames
        assert 'payment-method' in registered_basenames

    def test_payment_list_url_pattern(self):
        """Test the payment list URL pattern matches expected format."""
        url = reverse('payments:payment-list')
        assert url.startswith('/api/')

    def test_payment_method_list_url_pattern(self):
        """Test the payment method list URL pattern matches expected format."""
        url = reverse('payments:payment-method-list')
        assert url.startswith('/api/')
