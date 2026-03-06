"""
Tests for contracts app admin configuration.
"""

import pytest
from django.contrib.admin.sites import AdminSite
from apps.contracts.models import Contract, ContractMilestone
from apps.contracts.admin import (
    ContractAdmin,
    ContractMilestoneAdmin,
    ContractMilestoneInline,
)


@pytest.mark.django_db
class TestContractAdmin:
    """Tests for ContractAdmin."""

    def setup_method(self):
        """Set up admin site and admin class."""
        self.site = AdminSite()
        self.admin = ContractAdmin(Contract, self.site)

    def test_contract_admin_is_registered(self):
        """Test Contract model is registered in admin."""
        from django.contrib import admin
        assert Contract in admin.site._registry

    def test_list_display(self):
        """Test list_display fields."""
        expected = [
            'contract_number', 'client', 'title', 'contract_type',
            'value', 'status', 'start_date', 'end_date', 'is_signed',
        ]
        assert self.admin.list_display == expected

    def test_list_filter(self):
        """Test list_filter fields."""
        expected = ['status', 'contract_type', 'signed_by_client', 'signed_by_company']
        assert self.admin.list_filter == expected

    def test_search_fields(self):
        """Test search_fields."""
        assert 'contract_number' in self.admin.search_fields
        assert 'title' in self.admin.search_fields
        assert 'client__first_name' in self.admin.search_fields
        assert 'client__last_name' in self.admin.search_fields
        assert 'client__company_name' in self.admin.search_fields

    def test_readonly_fields(self):
        """Test readonly_fields."""
        assert 'contract_number' in self.admin.readonly_fields
        assert 'created_at' in self.admin.readonly_fields
        assert 'updated_at' in self.admin.readonly_fields

    def test_inlines(self):
        """Test inlines include ContractMilestoneInline."""
        assert ContractMilestoneInline in self.admin.inlines

    def test_fieldsets_present(self):
        """Test fieldsets are defined."""
        assert self.admin.fieldsets is not None
        assert len(self.admin.fieldsets) > 0

    def test_fieldsets_sections(self):
        """Test fieldsets have expected sections."""
        section_names = [f[0] for f in self.admin.fieldsets]
        assert 'Basic Information' in section_names
        assert 'Dates' in section_names
        assert 'Financial Details' in section_names
        assert 'Signature' in section_names
        assert 'Timestamps' in section_names


@pytest.mark.django_db
class TestContractMilestoneAdmin:
    """Tests for ContractMilestoneAdmin."""

    def setup_method(self):
        """Set up admin site and admin class."""
        self.site = AdminSite()
        self.admin = ContractMilestoneAdmin(ContractMilestone, self.site)

    def test_milestone_admin_is_registered(self):
        """Test ContractMilestone model is registered in admin."""
        from django.contrib import admin
        assert ContractMilestone in admin.site._registry

    def test_list_display(self):
        """Test list_display fields."""
        expected = ['title', 'contract', 'due_date', 'amount', 'status', 'completed_at']
        assert self.admin.list_display == expected

    def test_list_filter(self):
        """Test list_filter fields."""
        assert 'status' in self.admin.list_filter
        assert 'invoice_generated' in self.admin.list_filter

    def test_search_fields(self):
        """Test search_fields."""
        assert 'title' in self.admin.search_fields
        assert 'contract__contract_number' in self.admin.search_fields
        assert 'contract__title' in self.admin.search_fields

    def test_readonly_fields(self):
        """Test readonly_fields."""
        assert 'created_at' in self.admin.readonly_fields
        assert 'updated_at' in self.admin.readonly_fields

    def test_fieldsets_present(self):
        """Test fieldsets are defined."""
        assert self.admin.fieldsets is not None
        assert len(self.admin.fieldsets) > 0

    def test_fieldsets_sections(self):
        """Test fieldsets have expected sections."""
        section_names = [f[0] for f in self.admin.fieldsets]
        assert 'Basic Information' in section_names
        assert 'Completion' in section_names
        assert 'Invoice' in section_names
        assert 'Deliverables' in section_names
        assert 'Timestamps' in section_names


@pytest.mark.django_db
class TestContractMilestoneInline:
    """Tests for ContractMilestoneInline."""

    def test_inline_model(self):
        """Test inline model is ContractMilestone."""
        assert ContractMilestoneInline.model == ContractMilestone

    def test_inline_extra(self):
        """Test inline extra is 1."""
        assert ContractMilestoneInline.extra == 1

    def test_inline_fields(self):
        """Test inline fields."""
        expected = ['title', 'due_date', 'amount', 'status', 'order']
        assert ContractMilestoneInline.fields == expected

    def test_inline_ordering(self):
        """Test inline ordering."""
        assert ContractMilestoneInline.ordering == ['order', 'due_date']
