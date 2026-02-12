"""
Tests for clients app filters.
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from apps.clients.models import Client
from apps.clients.filters import ClientFilter


@pytest.mark.django_db
class TestClientFilter:
    """Tests for ClientFilter."""

    def test_filter_by_lifecycle_stage_single(self, client_company, client_individual, client_lead):
        """Test filtering by a single lifecycle stage."""
        qs = Client.objects.all()
        f = ClientFilter({'lifecycle_stage': [Client.ACTIVE]}, queryset=qs)
        result = f.qs
        assert client_company in result
        assert client_individual not in result
        assert client_lead not in result

    def test_filter_by_lifecycle_stage_multiple(self, client_company, client_individual, client_lead):
        """Test filtering by multiple lifecycle stages."""
        qs = Client.objects.all()
        f = ClientFilter(
            {'lifecycle_stage': [Client.ACTIVE, Client.PROSPECT]},
            queryset=qs,
        )
        result = f.qs
        assert client_company in result
        assert client_individual in result
        assert client_lead not in result

    def test_filter_by_client_type_company(self, client_company, client_individual):
        """Test filtering by company client type."""
        qs = Client.objects.all()
        f = ClientFilter({'client_type': Client.COMPANY}, queryset=qs)
        result = f.qs
        assert client_company in result
        assert client_individual not in result

    def test_filter_by_client_type_individual(self, client_company, client_individual):
        """Test filtering by individual client type."""
        qs = Client.objects.all()
        f = ClientFilter({'client_type': Client.INDIVIDUAL}, queryset=qs)
        result = f.qs
        assert client_individual in result
        assert client_company not in result

    def test_filter_by_is_active_true(self, client_company, admin_user):
        """Test filtering for active clients."""
        inactive = Client.objects.create(
            client_type=Client.INDIVIDUAL,
            first_name='Inactive',
            last_name='Client',
            email='inactive.client@example.com',
            lifecycle_stage=Client.INACTIVE,
            is_active=False,
        )
        qs = Client.objects.all()
        f = ClientFilter({'is_active': True}, queryset=qs)
        result = f.qs
        assert client_company in result
        assert inactive not in result

    def test_filter_by_is_active_false(self, client_company, admin_user):
        """Test filtering for inactive clients."""
        inactive = Client.objects.create(
            client_type=Client.INDIVIDUAL,
            first_name='Inactive',
            last_name='Client',
            email='inactive2@example.com',
            lifecycle_stage=Client.INACTIVE,
            is_active=False,
        )
        qs = Client.objects.all()
        f = ClientFilter({'is_active': False}, queryset=qs)
        result = f.qs
        assert inactive in result
        assert client_company not in result

    def test_filter_by_owner(self, client_company, client_lead, admin_user):
        """Test filtering by owner UUID."""
        qs = Client.objects.all()
        f = ClientFilter({'owner': str(admin_user.id)}, queryset=qs)
        result = f.qs
        assert client_company in result
        assert client_lead not in result

    def test_filter_by_tags(self, client_company, client_individual, client_lead):
        """Test filtering by tags (comma-separated)."""
        qs = Client.objects.all()
        f = ClientFilter({'tags': 'enterprise'}, queryset=qs)
        result = f.qs
        assert client_company in result
        assert client_individual not in result

    def test_filter_by_tags_multiple(self, client_company, client_individual, client_lead):
        """Test filtering by multiple tags."""
        qs = Client.objects.all()
        f = ClientFilter({'tags': 'enterprise,freelance'}, queryset=qs)
        result = f.qs
        assert client_company in result
        assert client_individual in result
        assert client_lead not in result

    def test_filter_by_tags_empty_value(self, client_company, client_individual, client_lead):
        """Test tags filter with empty value returns all."""
        qs = Client.objects.all()
        f = ClientFilter({'tags': ''}, queryset=qs)
        result = f.qs
        assert result.count() == qs.count()

    def test_filter_by_tags_empty_value_direct(self, client_company, client_individual, client_lead):
        """Test filter_by_tags method directly with empty value."""
        qs = Client.objects.all()
        f = ClientFilter(queryset=qs)
        result = f.filter_by_tags(qs, 'tags', '')
        assert result.count() == qs.count()

    def test_filter_min_total_value(self, client_company, client_lead):
        """Test min_total_value filter."""
        client_company.total_value = Decimal('5000.00')
        client_company.save()
        client_lead.total_value = Decimal('100.00')
        client_lead.save()

        qs = Client.objects.all()
        f = ClientFilter({'min_total_value': 1000}, queryset=qs)
        result = f.qs
        assert client_company in result
        assert client_lead not in result

    def test_filter_max_total_value(self, client_company, client_lead):
        """Test max_total_value filter."""
        client_company.total_value = Decimal('5000.00')
        client_company.save()
        client_lead.total_value = Decimal('100.00')
        client_lead.save()

        qs = Client.objects.all()
        f = ClientFilter({'max_total_value': 1000}, queryset=qs)
        result = f.qs
        assert client_lead in result
        assert client_company not in result

    def test_filter_min_and_max_total_value(self, client_company, client_individual, client_lead):
        """Test combined min and max total value filter."""
        client_company.total_value = Decimal('5000.00')
        client_company.save()
        client_individual.total_value = Decimal('2000.00')
        client_individual.save()
        client_lead.total_value = Decimal('100.00')
        client_lead.save()

        qs = Client.objects.all()
        f = ClientFilter(
            {'min_total_value': 500, 'max_total_value': 3000},
            queryset=qs,
        )
        result = f.qs
        assert client_individual in result
        assert client_company not in result
        assert client_lead not in result

    def test_filter_has_outstanding_balance_true(self, client_company, client_lead):
        """Test filtering clients with outstanding balance."""
        client_company.outstanding_balance = Decimal('500.00')
        client_company.save()
        client_lead.outstanding_balance = Decimal('0.00')
        client_lead.save()

        qs = Client.objects.all()
        f = ClientFilter({'has_outstanding_balance': True}, queryset=qs)
        result = f.qs
        assert client_company in result
        assert client_lead not in result

    def test_filter_has_outstanding_balance_false(self, client_company, client_lead):
        """Test filtering clients without outstanding balance."""
        client_company.outstanding_balance = Decimal('500.00')
        client_company.save()
        client_lead.outstanding_balance = Decimal('0.00')
        client_lead.save()

        qs = Client.objects.all()
        f = ClientFilter({'has_outstanding_balance': False}, queryset=qs)
        result = f.qs
        assert client_lead in result
        assert client_company not in result

    def test_filter_created_after(self, client_company, client_lead):
        """Test created_after date filter."""
        qs = Client.objects.all()
        past_date = timezone.now() - timedelta(days=1)
        f = ClientFilter(
            {'created_after': past_date.isoformat()},
            queryset=qs,
        )
        result = f.qs
        # All clients created just now should match
        assert client_company in result

    def test_filter_created_before(self, client_company, client_lead):
        """Test created_before date filter."""
        qs = Client.objects.all()
        future_date = timezone.now() + timedelta(days=1)
        f = ClientFilter(
            {'created_before': future_date.isoformat()},
            queryset=qs,
        )
        result = f.qs
        assert client_company in result
        assert client_lead in result

    def test_filter_created_before_excludes_future(self, client_company):
        """Test created_before excludes clients created after cutoff."""
        qs = Client.objects.all()
        past_date = timezone.now() - timedelta(days=1)
        f = ClientFilter(
            {'created_before': past_date.isoformat()},
            queryset=qs,
        )
        result = f.qs
        assert client_company not in result

    def test_empty_filter_returns_all(self, client_company, client_individual, client_lead):
        """Test that empty filter returns all clients."""
        qs = Client.objects.all()
        f = ClientFilter({}, queryset=qs)
        assert f.qs.count() == qs.count()

    def test_meta_model(self):
        """Test Meta model is correctly set."""
        assert ClientFilter.Meta.model == Client

    def test_meta_fields(self):
        """Test Meta fields list."""
        expected = [
            'lifecycle_stage', 'client_type', 'is_active', 'owner', 'tags',
        ]
        assert ClientFilter.Meta.fields == expected
