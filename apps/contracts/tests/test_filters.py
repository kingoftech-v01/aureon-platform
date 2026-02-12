"""
Tests for contracts app filters.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.contracts.models import Contract
from apps.contracts.filters import ContractFilter


@pytest.mark.django_db
class TestContractFilter:
    """Tests for ContractFilter."""

    def test_filter_by_status_single(self, contract_fixed, contract_draft):
        """Test filtering by a single status."""
        qs = Contract.objects.all()
        f = ContractFilter({'status': [Contract.ACTIVE]}, queryset=qs)
        result = f.qs
        assert contract_fixed in result
        assert contract_draft not in result

    def test_filter_by_status_multiple(self, contract_fixed, contract_draft, contract_hourly):
        """Test filtering by multiple statuses."""
        qs = Contract.objects.all()
        f = ContractFilter(
            {'status': [Contract.ACTIVE, Contract.DRAFT]},
            queryset=qs,
        )
        result = f.qs
        assert contract_fixed in result
        assert contract_draft in result

    def test_filter_by_contract_type(self, contract_fixed, contract_hourly):
        """Test filtering by contract type."""
        qs = Contract.objects.all()
        f = ContractFilter({'contract_type': Contract.HOURLY}, queryset=qs)
        result = f.qs
        assert contract_hourly in result
        assert contract_fixed not in result

    def test_filter_by_client(self, contract_fixed, contract_draft, client_company):
        """Test filtering by client UUID."""
        qs = Contract.objects.all()
        f = ContractFilter({'client': str(client_company.id)}, queryset=qs)
        result = f.qs
        assert contract_fixed in result
        # contract_draft is for client_individual
        assert contract_draft not in result

    def test_filter_by_owner(self, contract_fixed, contract_draft, admin_user):
        """Test filtering by owner UUID."""
        qs = Contract.objects.all()
        f = ContractFilter({'owner': str(admin_user.id)}, queryset=qs)
        result = f.qs
        assert contract_fixed in result
        # contract_draft is owned by manager_user
        assert contract_draft not in result

    def test_filter_is_signed_true(self, contract_fixed, contract_draft):
        """Test filtering fully signed contracts."""
        qs = Contract.objects.all()
        f = ContractFilter({'is_signed': True}, queryset=qs)
        result = f.qs
        assert contract_fixed in result
        assert contract_draft not in result

    def test_filter_is_signed_false(self, contract_fixed, contract_draft):
        """Test filtering unsigned contracts."""
        qs = Contract.objects.all()
        f = ContractFilter({'is_signed': False}, queryset=qs)
        result = f.qs
        assert contract_draft in result
        assert contract_fixed not in result

    def test_filter_signed_by_client(self, contract_fixed, contract_draft):
        """Test filtering by signed_by_client."""
        qs = Contract.objects.all()
        f = ContractFilter({'signed_by_client': True}, queryset=qs)
        result = f.qs
        assert contract_fixed in result
        assert contract_draft not in result

    def test_filter_signed_by_company(self, contract_fixed, contract_draft):
        """Test filtering by signed_by_company."""
        qs = Contract.objects.all()
        f = ContractFilter({'signed_by_company': True}, queryset=qs)
        result = f.qs
        assert contract_fixed in result
        assert contract_draft not in result

    def test_filter_min_value(self, contract_fixed, contract_hourly):
        """Test min_value filter."""
        qs = Contract.objects.all()
        f = ContractFilter({'min_value': 10000}, queryset=qs)
        result = f.qs
        assert contract_fixed in result  # 15000
        assert contract_hourly not in result  # 5000

    def test_filter_max_value(self, contract_fixed, contract_hourly):
        """Test max_value filter."""
        qs = Contract.objects.all()
        f = ContractFilter({'max_value': 10000}, queryset=qs)
        result = f.qs
        assert contract_hourly in result  # 5000
        assert contract_fixed not in result  # 15000

    def test_filter_min_and_max_value(self, contract_fixed, contract_hourly, contract_draft):
        """Test combined min and max value filter."""
        qs = Contract.objects.all()
        f = ContractFilter(
            {'min_value': 7000, 'max_value': 10000},
            queryset=qs,
        )
        result = f.qs
        assert contract_draft in result  # 8000
        assert contract_fixed not in result  # 15000
        assert contract_hourly not in result  # 5000

    def test_filter_start_date_after(self, contract_fixed, contract_draft):
        """Test start_date_after filter."""
        qs = Contract.objects.all()
        # contract_draft starts 7 days from now
        tomorrow = date.today() + timedelta(days=1)
        f = ContractFilter({'start_date_after': str(tomorrow)}, queryset=qs)
        result = f.qs
        assert contract_draft in result
        assert contract_fixed not in result

    def test_filter_start_date_before(self, contract_fixed, contract_draft):
        """Test start_date_before filter."""
        qs = Contract.objects.all()
        tomorrow = date.today() + timedelta(days=1)
        f = ContractFilter({'start_date_before': str(tomorrow)}, queryset=qs)
        result = f.qs
        assert contract_fixed in result
        assert contract_draft not in result

    def test_filter_end_date_after(self, contract_fixed, contract_draft):
        """Test end_date_after filter."""
        qs = Contract.objects.all()
        # contract_fixed ends 90 days from now, contract_draft 37 days
        cutoff = date.today() + timedelta(days=50)
        f = ContractFilter({'end_date_after': str(cutoff)}, queryset=qs)
        result = f.qs
        assert contract_fixed in result
        assert contract_draft not in result

    def test_filter_end_date_before(self, contract_fixed, contract_draft):
        """Test end_date_before filter."""
        qs = Contract.objects.all()
        cutoff = date.today() + timedelta(days=50)
        f = ContractFilter({'end_date_before': str(cutoff)}, queryset=qs)
        result = f.qs
        assert contract_draft in result
        assert contract_fixed not in result

    def test_filter_is_active_period_true(self, contract_fixed, contract_draft):
        """Test is_active_period filter for active contracts."""
        qs = Contract.objects.all()
        f = ContractFilter({'is_active_period': True}, queryset=qs)
        result = f.qs
        # contract_fixed starts today, so should be in active period
        assert contract_fixed in result
        # contract_draft starts in 7 days, so not in active period
        assert contract_draft not in result

    def test_filter_is_active_period_false(self, contract_fixed, contract_draft):
        """Test is_active_period filter for non-active period contracts."""
        qs = Contract.objects.all()
        f = ContractFilter({'is_active_period': False}, queryset=qs)
        result = f.qs
        assert contract_draft in result
        assert contract_fixed not in result

    def test_filter_is_active_period_with_null_end_date(self, client_company, admin_user):
        """Test is_active_period for contracts with no end date."""
        contract = Contract.objects.create(
            client=client_company,
            title='No End Date',
            description='Open ended contract.',
            contract_type=Contract.RETAINER,
            status=Contract.ACTIVE,
            start_date=date.today() - timedelta(days=10),
            value=Decimal('3000.00'),
            owner=admin_user,
        )
        qs = Contract.objects.all()
        f = ContractFilter({'is_active_period': True}, queryset=qs)
        result = f.qs
        assert contract in result

    def test_empty_filter_returns_all(self, contract_fixed, contract_hourly, contract_draft):
        """Test empty filter returns all contracts."""
        qs = Contract.objects.all()
        f = ContractFilter({}, queryset=qs)
        assert f.qs.count() == qs.count()

    def test_meta_model(self):
        """Test Meta model is correctly set."""
        assert ContractFilter.Meta.model == Contract

    def test_meta_fields(self):
        """Test Meta fields list."""
        expected = [
            'status', 'contract_type', 'client',
            'owner', 'signed_by_client', 'signed_by_company',
        ]
        assert ContractFilter.Meta.fields == expected
