"""
Tests for invoicing app URL configuration.
"""

import pytest
from django.urls import reverse, resolve

from apps.invoicing.views import InvoiceViewSet, InvoiceItemViewSet


class TestInvoicingURLs:
    """Tests for invoicing URL patterns."""

    def test_invoice_list_url_resolves(self):
        """Test that the invoice list URL resolves correctly."""
        url = reverse('invoicing:invoice-list')
        # App urls.py has path('api/', ...) and config/urls.py includes under 'api/'
        assert url == '/api/api/invoices/'
        resolver = resolve(url)
        assert resolver.func.cls == InvoiceViewSet

    def test_invoice_detail_url_resolves(self):
        """Test that the invoice detail URL resolves correctly."""
        url = reverse('invoicing:invoice-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000001'})
        assert '/invoices/' in url
        resolver = resolve(url)
        assert resolver.func.cls == InvoiceViewSet

    def test_invoice_stats_url_resolves(self):
        """Test that the invoice stats action URL resolves."""
        url = reverse('invoicing:invoice-stats')
        assert url == '/api/api/invoices/stats/'
        resolver = resolve(url)
        assert resolver.func.cls == InvoiceViewSet

    def test_invoice_send_url_resolves(self):
        """Test that the invoice send action URL resolves."""
        url = reverse('invoicing:invoice-send', kwargs={'pk': '00000000-0000-0000-0000-000000000001'})
        assert '/invoices/' in url
        assert '/send/' in url
        resolver = resolve(url)
        assert resolver.func.cls == InvoiceViewSet

    def test_invoice_mark_paid_url_resolves(self):
        """Test that the invoice mark_paid action URL resolves."""
        url = reverse('invoicing:invoice-mark-paid', kwargs={'pk': '00000000-0000-0000-0000-000000000001'})
        assert '/mark_paid/' in url
        resolver = resolve(url)
        assert resolver.func.cls == InvoiceViewSet

    def test_invoice_generate_pdf_url_resolves(self):
        """Test that the invoice generate_pdf action URL resolves."""
        url = reverse('invoicing:invoice-generate-pdf', kwargs={'pk': '00000000-0000-0000-0000-000000000001'})
        assert '/generate_pdf/' in url
        resolver = resolve(url)
        assert resolver.func.cls == InvoiceViewSet

    def test_invoice_recalculate_url_resolves(self):
        """Test that the invoice recalculate action URL resolves."""
        url = reverse('invoicing:invoice-recalculate', kwargs={'pk': '00000000-0000-0000-0000-000000000001'})
        assert '/recalculate/' in url
        resolver = resolve(url)
        assert resolver.func.cls == InvoiceViewSet

    def test_invoice_items_url_resolves(self):
        """Test that the invoice items action URL resolves."""
        url = reverse('invoicing:invoice-items', kwargs={'pk': '00000000-0000-0000-0000-000000000001'})
        assert '/items/' in url
        resolver = resolve(url)
        assert resolver.func.cls == InvoiceViewSet

    def test_invoice_item_list_url_resolves(self):
        """Test that the invoice item list URL resolves correctly."""
        url = reverse('invoicing:invoice-item-list')
        assert url == '/api/api/items/'
        resolver = resolve(url)
        assert resolver.func.cls == InvoiceItemViewSet

    def test_invoice_item_detail_url_resolves(self):
        """Test that the invoice item detail URL resolves correctly."""
        url = reverse('invoicing:invoice-item-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000001'})
        assert '/items/' in url
        resolver = resolve(url)
        assert resolver.func.cls == InvoiceItemViewSet

    def test_app_name(self):
        """Test that the app_name is set correctly."""
        from apps.invoicing import urls as invoicing_urls
        assert invoicing_urls.app_name == 'invoicing'

    def test_router_registered_viewsets(self):
        """Test that the router has registered both viewsets."""
        from apps.invoicing.urls import router
        # router.registry is a list of tuples: (prefix, viewset, basename)
        registered_basenames = [entry[2] for entry in router.registry]
        assert 'invoice' in registered_basenames
        assert 'invoice-item' in registered_basenames
