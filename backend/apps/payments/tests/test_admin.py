"""
Tests for payments app admin configuration.
"""

import pytest
from django.contrib.admin.sites import AdminSite

from apps.payments.models import Payment, PaymentMethod
from apps.payments.admin import PaymentAdmin, PaymentMethodAdmin


# ============================================================================
# PaymentAdmin Tests
# ============================================================================


class TestPaymentAdmin:
    """Tests for PaymentAdmin."""

    def test_payment_is_registered(self):
        """Test that Payment model is registered in admin."""
        from django.contrib import admin
        assert Payment in admin.site._registry

    def test_payment_admin_class(self):
        """Test that Payment is registered with PaymentAdmin."""
        from django.contrib import admin
        admin_class = admin.site._registry[Payment]
        assert isinstance(admin_class, PaymentAdmin)

    def test_list_display(self):
        """Test list_display configuration."""
        expected = [
            'transaction_id', 'invoice', 'amount', 'currency',
            'payment_method', 'status', 'payment_date',
        ]
        assert PaymentAdmin.list_display == expected

    def test_list_filter(self):
        """Test list_filter configuration."""
        assert 'status' in PaymentAdmin.list_filter
        assert 'payment_method' in PaymentAdmin.list_filter
        assert 'payment_date' in PaymentAdmin.list_filter

    def test_search_fields(self):
        """Test search_fields configuration."""
        assert 'transaction_id' in PaymentAdmin.search_fields
        assert 'invoice__invoice_number' in PaymentAdmin.search_fields
        assert 'stripe_payment_intent_id' in PaymentAdmin.search_fields

    def test_readonly_fields(self):
        """Test readonly_fields configuration."""
        assert 'transaction_id' in PaymentAdmin.readonly_fields
        assert 'created_at' in PaymentAdmin.readonly_fields
        assert 'updated_at' in PaymentAdmin.readonly_fields

    def test_fieldsets_structure(self):
        """Test fieldsets structure."""
        fieldsets = PaymentAdmin.fieldsets
        fieldset_names = [fs[0] for fs in fieldsets]

        assert 'Basic Information' in fieldset_names
        assert 'Payment Date' in fieldset_names
        assert 'Stripe Integration' in fieldset_names
        assert 'Card Details' in fieldset_names
        assert 'Refund Information' in fieldset_names
        assert 'Failure Information' in fieldset_names
        assert 'Receipt' in fieldset_names
        assert 'Notes' in fieldset_names
        assert 'Timestamps' in fieldset_names

    def test_fieldsets_basic_information_fields(self):
        """Test that Basic Information fieldset contains expected fields."""
        fieldsets = PaymentAdmin.fieldsets
        basic_info = next(fs for fs in fieldsets if fs[0] == 'Basic Information')
        fields = basic_info[1]['fields']

        assert 'transaction_id' in fields
        assert 'invoice' in fields
        assert 'amount' in fields
        assert 'currency' in fields
        assert 'payment_method' in fields
        assert 'status' in fields

    def test_fieldsets_stripe_integration_fields(self):
        """Test that Stripe Integration fieldset contains expected fields."""
        fieldsets = PaymentAdmin.fieldsets
        stripe_fs = next(fs for fs in fieldsets if fs[0] == 'Stripe Integration')
        fields = stripe_fs[1]['fields']

        assert 'stripe_payment_intent_id' in fields
        assert 'stripe_charge_id' in fields
        assert 'stripe_customer_id' in fields

    def test_fieldsets_refund_fields(self):
        """Test that Refund Information fieldset contains expected fields."""
        fieldsets = PaymentAdmin.fieldsets
        refund_fs = next(fs for fs in fieldsets if fs[0] == 'Refund Information')
        fields = refund_fs[1]['fields']

        assert 'refunded_amount' in fields
        assert 'refund_reason' in fields
        assert 'refunded_at' in fields

    def test_fieldsets_failure_fields(self):
        """Test that Failure Information fieldset contains expected fields."""
        fieldsets = PaymentAdmin.fieldsets
        failure_fs = next(fs for fs in fieldsets if fs[0] == 'Failure Information')
        fields = failure_fs[1]['fields']

        assert 'failure_code' in fields
        assert 'failure_message' in fields

    def test_timestamps_collapsed(self):
        """Test that Timestamps fieldset is collapsed."""
        fieldsets = PaymentAdmin.fieldsets
        timestamps_fs = next(fs for fs in fieldsets if fs[0] == 'Timestamps')
        assert 'collapse' in timestamps_fs[1].get('classes', ())


# ============================================================================
# PaymentMethodAdmin Tests
# ============================================================================


class TestPaymentMethodAdmin:
    """Tests for PaymentMethodAdmin."""

    def test_payment_method_is_registered(self):
        """Test that PaymentMethod model is registered in admin."""
        from django.contrib import admin
        assert PaymentMethod in admin.site._registry

    def test_payment_method_admin_class(self):
        """Test that PaymentMethod is registered with PaymentMethodAdmin."""
        from django.contrib import admin
        admin_class = admin.site._registry[PaymentMethod]
        assert isinstance(admin_class, PaymentMethodAdmin)

    def test_list_display(self):
        """Test list_display configuration."""
        expected = ['client', 'type', 'card_brand', 'card_last4', 'is_default', 'is_active']
        assert PaymentMethodAdmin.list_display == expected

    def test_list_filter(self):
        """Test list_filter configuration."""
        assert 'type' in PaymentMethodAdmin.list_filter
        assert 'is_default' in PaymentMethodAdmin.list_filter
        assert 'is_active' in PaymentMethodAdmin.list_filter

    def test_search_fields(self):
        """Test search_fields configuration."""
        assert 'client__first_name' in PaymentMethodAdmin.search_fields
        assert 'client__last_name' in PaymentMethodAdmin.search_fields
        assert 'stripe_payment_method_id' in PaymentMethodAdmin.search_fields

    def test_fieldsets_structure(self):
        """Test fieldsets structure."""
        fieldsets = PaymentMethodAdmin.fieldsets
        fieldset_names = [fs[0] for fs in fieldsets]

        assert 'Basic Information' in fieldset_names
        assert 'Card Details' in fieldset_names
        assert 'Stripe Integration' in fieldset_names
        assert 'Timestamps' in fieldset_names

    def test_fieldsets_basic_information_fields(self):
        """Test that Basic Information fieldset contains expected fields."""
        fieldsets = PaymentMethodAdmin.fieldsets
        basic_info = next(fs for fs in fieldsets if fs[0] == 'Basic Information')
        fields = basic_info[1]['fields']

        assert 'client' in fields
        assert 'type' in fields
        assert 'is_default' in fields
        assert 'is_active' in fields

    def test_fieldsets_card_details_fields(self):
        """Test that Card Details fieldset contains expected fields."""
        fieldsets = PaymentMethodAdmin.fieldsets
        card_fs = next(fs for fs in fieldsets if fs[0] == 'Card Details')
        fields = card_fs[1]['fields']

        assert 'card_last4' in fields
        assert 'card_brand' in fields
        assert 'card_exp_month' in fields
        assert 'card_exp_year' in fields

    def test_fieldsets_stripe_integration_fields(self):
        """Test that Stripe Integration fieldset contains expected fields."""
        fieldsets = PaymentMethodAdmin.fieldsets
        stripe_fs = next(fs for fs in fieldsets if fs[0] == 'Stripe Integration')
        fields = stripe_fs[1]['fields']

        assert 'stripe_payment_method_id' in fields

    def test_timestamps_collapsed(self):
        """Test that Timestamps fieldset is collapsed."""
        fieldsets = PaymentMethodAdmin.fieldsets
        timestamps_fs = next(fs for fs in fieldsets if fs[0] == 'Timestamps')
        assert 'collapse' in timestamps_fs[1].get('classes', ())
