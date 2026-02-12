"""
Tests for invoicing app filters.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.utils import timezone

from apps.invoicing.models import Invoice
from apps.invoicing.filters import InvoiceFilter


@pytest.fixture
def invoice_cancelled(db, client_company, contract_fixed):
    """Create a cancelled invoice."""
    return Invoice.objects.create(
        client=client_company,
        contract=contract_fixed,
        status=Invoice.CANCELLED,
        issue_date=date.today() - timedelta(days=10),
        due_date=date.today() - timedelta(days=5),
        subtotal=Decimal('1000.00'),
        total=Decimal('1000.00'),
        currency='USD',
    )


@pytest.fixture
def invoice_high_value(db, client_company, contract_fixed):
    """Create a high-value invoice."""
    return Invoice.objects.create(
        client=client_company,
        contract=contract_fixed,
        status=Invoice.SENT,
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        subtotal=Decimal('50000.00'),
        total=Decimal('50000.00'),
        currency='USD',
    )


# ============================================================================
# InvoiceFilter Tests
# ============================================================================


class TestInvoiceFilter:
    """Tests for InvoiceFilter."""

    @pytest.mark.django_db
    def test_filter_by_single_status(self, invoice_draft, invoice_sent, invoice_paid):
        """Test filtering invoices by a single status."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({'status': [Invoice.DRAFT]}, queryset=qs)
        result = f.qs

        assert invoice_draft in result
        assert invoice_sent not in result
        assert invoice_paid not in result

    @pytest.mark.django_db
    def test_filter_by_multiple_statuses(self, invoice_draft, invoice_sent, invoice_paid):
        """Test filtering invoices by multiple statuses."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({'status': [Invoice.DRAFT, Invoice.SENT]}, queryset=qs)
        result = f.qs

        assert invoice_draft in result
        assert invoice_sent in result
        assert invoice_paid not in result

    @pytest.mark.django_db
    def test_filter_by_client(self, invoice_draft, invoice_overdue, client_company):
        """Test filtering by client UUID."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({'client': str(client_company.id)}, queryset=qs)
        result = f.qs

        assert invoice_draft in result
        # invoice_overdue belongs to client_individual
        assert invoice_overdue not in result

    @pytest.mark.django_db
    def test_filter_by_contract(self, invoice_draft, invoice_overdue, contract_fixed):
        """Test filtering by contract UUID."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({'contract': str(contract_fixed.id)}, queryset=qs)
        result = f.qs

        assert invoice_draft in result
        # invoice_overdue has no contract
        assert invoice_overdue not in result

    @pytest.mark.django_db
    def test_filter_by_min_total(self, invoice_draft, invoice_sent, invoice_overdue):
        """Test filtering by minimum total."""
        qs = Invoice.objects.all()
        # invoice_draft.total=5400, invoice_sent.total=8100, invoice_overdue.total=1500
        f = InvoiceFilter({'min_total': '5000'}, queryset=qs)
        result = f.qs

        assert invoice_draft in result
        assert invoice_sent in result
        assert invoice_overdue not in result

    @pytest.mark.django_db
    def test_filter_by_max_total(self, invoice_draft, invoice_sent, invoice_overdue):
        """Test filtering by maximum total."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({'max_total': '5500'}, queryset=qs)
        result = f.qs

        assert invoice_draft in result
        assert invoice_sent not in result
        assert invoice_overdue in result

    @pytest.mark.django_db
    def test_filter_by_min_and_max_total(self, invoice_draft, invoice_sent, invoice_overdue):
        """Test filtering by both min and max total."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({'min_total': '2000', 'max_total': '6000'}, queryset=qs)
        result = f.qs

        assert invoice_draft in result
        assert invoice_sent not in result
        assert invoice_overdue not in result

    @pytest.mark.django_db
    def test_filter_is_paid_true(self, invoice_draft, invoice_paid, invoice_overdue):
        """Test filtering for paid invoices."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({'is_paid': True}, queryset=qs)
        result = f.qs

        assert invoice_paid in result
        assert invoice_draft not in result
        assert invoice_overdue not in result

    @pytest.mark.django_db
    def test_filter_is_paid_false(self, invoice_draft, invoice_paid, invoice_overdue):
        """Test filtering for unpaid invoices."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({'is_paid': False}, queryset=qs)
        result = f.qs

        assert invoice_paid not in result
        assert invoice_draft in result
        assert invoice_overdue in result

    @pytest.mark.django_db
    def test_filter_is_overdue_true(self, invoice_draft, invoice_overdue, invoice_paid):
        """Test filtering for overdue invoices."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({'is_overdue': True}, queryset=qs)
        result = f.qs

        # invoice_overdue has due_date in the past and status is OVERDUE
        assert invoice_overdue in result
        # Paid invoices should be excluded even if past due
        assert invoice_paid not in result

    @pytest.mark.django_db
    def test_filter_is_overdue_false(
        self, invoice_draft, invoice_overdue, invoice_paid, invoice_cancelled
    ):
        """Test filtering for non-overdue invoices."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({'is_overdue': False}, queryset=qs)
        result = f.qs

        # Paid and cancelled invoices count as non-overdue
        assert invoice_paid in result
        assert invoice_cancelled in result
        # invoice_draft has future due_date
        assert invoice_draft in result
        # invoice_overdue has past due_date and is not paid/cancelled
        assert invoice_overdue not in result

    @pytest.mark.django_db
    def test_filter_issue_date_after(self, invoice_draft, invoice_paid):
        """Test filtering by issue_date_after."""
        qs = Invoice.objects.all()
        # invoice_draft.issue_date=today, invoice_paid.issue_date=today-30
        yesterday = date.today() - timedelta(days=1)
        f = InvoiceFilter({'issue_date_after': str(yesterday)}, queryset=qs)
        result = f.qs

        assert invoice_draft in result
        assert invoice_paid not in result

    @pytest.mark.django_db
    def test_filter_issue_date_before(self, invoice_draft, invoice_paid):
        """Test filtering by issue_date_before."""
        qs = Invoice.objects.all()
        yesterday = date.today() - timedelta(days=1)
        f = InvoiceFilter({'issue_date_before': str(yesterday)}, queryset=qs)
        result = f.qs

        assert invoice_paid in result
        assert invoice_draft not in result

    @pytest.mark.django_db
    def test_filter_due_date_after(self, invoice_draft, invoice_overdue):
        """Test filtering by due_date_after."""
        qs = Invoice.objects.all()
        today = date.today()
        f = InvoiceFilter({'due_date_after': str(today)}, queryset=qs)
        result = f.qs

        # invoice_draft.due_date=today+30
        assert invoice_draft in result
        # invoice_overdue.due_date=today-15
        assert invoice_overdue not in result

    @pytest.mark.django_db
    def test_filter_due_date_before(self, invoice_draft, invoice_overdue):
        """Test filtering by due_date_before."""
        qs = Invoice.objects.all()
        today = date.today()
        f = InvoiceFilter({'due_date_before': str(today)}, queryset=qs)
        result = f.qs

        assert invoice_overdue in result
        assert invoice_draft not in result

    @pytest.mark.django_db
    def test_filter_issue_date_range(self, invoice_draft, invoice_sent, invoice_paid):
        """Test filtering by issue date range."""
        qs = Invoice.objects.all()
        start = date.today() - timedelta(days=10)
        end = date.today()
        f = InvoiceFilter(
            {'issue_date_after': str(start), 'issue_date_before': str(end)},
            queryset=qs,
        )
        result = f.qs

        # invoice_draft.issue_date=today, invoice_sent.issue_date=today-5
        assert invoice_draft in result
        assert invoice_sent in result
        # invoice_paid.issue_date=today-30
        assert invoice_paid not in result

    @pytest.mark.django_db
    def test_no_filters_returns_all(self, invoice_draft, invoice_sent, invoice_paid):
        """Test that no filters returns all invoices."""
        qs = Invoice.objects.all()
        f = InvoiceFilter({}, queryset=qs)
        result = f.qs

        assert result.count() == 3

    @pytest.mark.django_db
    def test_combined_filters(self, invoice_draft, invoice_sent, invoice_paid, invoice_overdue):
        """Test combining multiple filters."""
        qs = Invoice.objects.all()
        f = InvoiceFilter(
            {
                'status': [Invoice.SENT],
                'min_total': '5000',
            },
            queryset=qs,
        )
        result = f.qs

        # Only invoice_sent matches (status=sent, total=8100)
        assert invoice_sent in result
        assert result.count() == 1

    @pytest.mark.django_db
    def test_meta_fields(self):
        """Test that Meta.fields are correctly defined."""
        assert 'status' in InvoiceFilter.Meta.fields
        assert 'client' in InvoiceFilter.Meta.fields
        assert 'contract' in InvoiceFilter.Meta.fields
