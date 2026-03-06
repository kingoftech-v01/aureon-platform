"""
Tests for invoicing app admin configuration.
"""

import pytest
from django.contrib.admin.sites import AdminSite

from apps.invoicing.models import Invoice, InvoiceItem
from apps.invoicing.admin import InvoiceAdmin, InvoiceItemAdmin, InvoiceItemInline


# ============================================================================
# InvoiceAdmin Tests
# ============================================================================


class TestInvoiceAdmin:
    """Tests for InvoiceAdmin."""

    def test_invoice_is_registered(self):
        """Test that Invoice model is registered in admin."""
        from django.contrib import admin
        assert Invoice in admin.site._registry

    def test_invoice_admin_class(self):
        """Test that Invoice is registered with InvoiceAdmin."""
        from django.contrib import admin
        admin_class = admin.site._registry[Invoice]
        assert isinstance(admin_class, InvoiceAdmin)

    def test_list_display(self):
        """Test list_display configuration."""
        expected = [
            'invoice_number', 'client', 'status', 'issue_date', 'due_date',
            'total', 'paid_amount', 'balance_due', 'is_overdue',
        ]
        assert InvoiceAdmin.list_display == expected

    def test_list_filter(self):
        """Test list_filter configuration."""
        assert 'status' in InvoiceAdmin.list_filter
        assert 'issue_date' in InvoiceAdmin.list_filter
        assert 'due_date' in InvoiceAdmin.list_filter

    def test_search_fields(self):
        """Test search_fields configuration."""
        assert 'invoice_number' in InvoiceAdmin.search_fields
        assert 'client__first_name' in InvoiceAdmin.search_fields
        assert 'client__last_name' in InvoiceAdmin.search_fields
        assert 'client__company_name' in InvoiceAdmin.search_fields

    def test_readonly_fields(self):
        """Test readonly_fields configuration."""
        assert 'invoice_number' in InvoiceAdmin.readonly_fields
        assert 'subtotal' in InvoiceAdmin.readonly_fields
        assert 'tax_amount' in InvoiceAdmin.readonly_fields
        assert 'total' in InvoiceAdmin.readonly_fields
        assert 'created_at' in InvoiceAdmin.readonly_fields
        assert 'updated_at' in InvoiceAdmin.readonly_fields

    def test_inlines(self):
        """Test that InvoiceItemInline is configured."""
        assert InvoiceItemInline in InvoiceAdmin.inlines

    def test_fieldsets_structure(self):
        """Test fieldsets structure."""
        fieldsets = InvoiceAdmin.fieldsets
        fieldset_names = [fs[0] for fs in fieldsets]

        assert 'Basic Information' in fieldset_names
        assert 'Dates' in fieldset_names
        assert 'Financial Details' in fieldset_names
        assert 'Payment Information' in fieldset_names
        assert 'Notes & Terms' in fieldset_names
        assert 'Documents' in fieldset_names
        assert 'Stripe Integration' in fieldset_names
        assert 'Email Tracking' in fieldset_names
        assert 'Metadata' in fieldset_names
        assert 'Timestamps' in fieldset_names

    @pytest.mark.django_db
    def test_balance_due_method(self, invoice_draft):
        """Test the balance_due admin method."""
        site = AdminSite()
        admin_obj = InvoiceAdmin(Invoice, site)
        result = admin_obj.balance_due(invoice_draft)
        assert result == invoice_draft.balance_due

    def test_balance_due_short_description(self):
        """Test balance_due method has short_description."""
        site = AdminSite()
        admin_obj = InvoiceAdmin(Invoice, site)
        assert admin_obj.balance_due.short_description == 'Balance Due'


# ============================================================================
# InvoiceItemInline Tests
# ============================================================================


class TestInvoiceItemInline:
    """Tests for InvoiceItemInline."""

    def test_model(self):
        """Test inline model."""
        assert InvoiceItemInline.model == InvoiceItem

    def test_extra(self):
        """Test extra forms."""
        assert InvoiceItemInline.extra == 1

    def test_fields(self):
        """Test fields configuration."""
        expected = ['description', 'quantity', 'unit_price', 'amount', 'order']
        assert InvoiceItemInline.fields == expected

    def test_readonly_fields(self):
        """Test readonly fields."""
        assert 'amount' in InvoiceItemInline.readonly_fields

    def test_ordering(self):
        """Test ordering."""
        assert InvoiceItemInline.ordering == ['order']


# ============================================================================
# InvoiceItemAdmin Tests
# ============================================================================


class TestInvoiceItemAdmin:
    """Tests for InvoiceItemAdmin."""

    def test_invoice_item_is_registered(self):
        """Test that InvoiceItem model is registered in admin."""
        from django.contrib import admin
        assert InvoiceItem in admin.site._registry

    def test_invoice_item_admin_class(self):
        """Test that InvoiceItem is registered with InvoiceItemAdmin."""
        from django.contrib import admin
        admin_class = admin.site._registry[InvoiceItem]
        assert isinstance(admin_class, InvoiceItemAdmin)

    def test_list_display(self):
        """Test list_display configuration."""
        expected = ['description', 'invoice', 'quantity', 'unit_price', 'amount']
        assert InvoiceItemAdmin.list_display == expected

    def test_search_fields(self):
        """Test search_fields configuration."""
        assert 'description' in InvoiceItemAdmin.search_fields
        assert 'invoice__invoice_number' in InvoiceItemAdmin.search_fields

    def test_readonly_fields(self):
        """Test readonly fields."""
        assert 'amount' in InvoiceItemAdmin.readonly_fields

    def test_fieldsets_structure(self):
        """Test fieldsets structure."""
        fieldsets = InvoiceItemAdmin.fieldsets
        fieldset_names = [fs[0] for fs in fieldsets]
        assert 'Basic Information' in fieldset_names

        # Check that Basic Information contains expected fields
        basic_info = fieldsets[0]
        fields = basic_info[1]['fields']
        assert 'invoice' in fields
        assert 'description' in fields
        assert 'quantity' in fields
        assert 'unit_price' in fields
        assert 'amount' in fields
        assert 'order' in fields
