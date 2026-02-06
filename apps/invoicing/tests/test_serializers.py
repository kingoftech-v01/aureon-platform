"""
Tests for invoicing app serializers.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from rest_framework.test import APIRequestFactory

from apps.invoicing.models import Invoice, InvoiceItem
from apps.invoicing.serializers import (
    InvoiceItemSerializer,
    InvoiceListSerializer,
    InvoiceDetailSerializer,
    InvoiceCreateUpdateSerializer,
    InvoiceStatsSerializer,
)


# ============================================================================
# InvoiceItemSerializer Tests
# ============================================================================


class TestInvoiceItemSerializer:
    """Tests for InvoiceItemSerializer."""

    @pytest.mark.django_db
    def test_serializes_all_fields(self, invoice_item):
        """Test that all expected fields are present."""
        serializer = InvoiceItemSerializer(invoice_item)
        data = serializer.data

        assert 'id' in data
        assert 'description' in data
        assert 'quantity' in data
        assert 'unit_price' in data
        assert 'amount' in data
        assert 'order' in data

    @pytest.mark.django_db
    def test_read_only_fields(self, invoice_item):
        """Test that id and amount are read-only."""
        serializer = InvoiceItemSerializer(invoice_item)
        assert 'id' in serializer.Meta.read_only_fields
        assert 'amount' in serializer.Meta.read_only_fields

    @pytest.mark.django_db
    def test_serialized_values_match(self, invoice_item):
        """Test that serialized values match the model instance."""
        serializer = InvoiceItemSerializer(invoice_item)
        data = serializer.data

        assert data['description'] == invoice_item.description
        assert Decimal(data['quantity']) == invoice_item.quantity
        assert Decimal(data['unit_price']) == invoice_item.unit_price
        assert Decimal(data['amount']) == invoice_item.amount
        assert data['order'] == invoice_item.order

    @pytest.mark.django_db
    def test_valid_item_data(self, invoice_draft):
        """Test deserialization with valid data."""
        data = {
            'description': 'Consulting Services',
            'quantity': '10.00',
            'unit_price': '150.00',
            'order': 1,
        }
        serializer = InvoiceItemSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    @pytest.mark.django_db
    def test_missing_required_fields(self):
        """Test that missing required fields cause validation errors."""
        serializer = InvoiceItemSerializer(data={})
        assert not serializer.is_valid()
        assert 'description' in serializer.errors
        assert 'unit_price' in serializer.errors


# ============================================================================
# InvoiceListSerializer Tests
# ============================================================================


class TestInvoiceListSerializer:
    """Tests for InvoiceListSerializer."""

    @pytest.mark.django_db
    def test_serializes_expected_fields(self, invoice_draft):
        """Test that all list fields are present."""
        serializer = InvoiceListSerializer(invoice_draft)
        data = serializer.data

        expected_fields = [
            'id', 'invoice_number', 'client', 'client_name', 'contract',
            'status', 'issue_date', 'due_date', 'total', 'paid_amount',
            'balance_due', 'is_overdue', 'currency', 'created_at', 'updated_at',
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    @pytest.mark.django_db
    def test_client_name_company(self, invoice_draft):
        """Test client_name for a company client."""
        serializer = InvoiceListSerializer(invoice_draft)
        data = serializer.data

        assert data['client_name'] == invoice_draft.client.get_display_name()
        # client_company has company_name='Test Company Inc.'
        assert data['client_name'] == 'Test Company Inc.'

    @pytest.mark.django_db
    def test_client_name_individual(self, invoice_overdue):
        """Test client_name for an individual client."""
        serializer = InvoiceListSerializer(invoice_overdue)
        data = serializer.data

        # client_individual: first_name='Jane', last_name='Smith'
        assert data['client_name'] == invoice_overdue.client.get_display_name()

    @pytest.mark.django_db
    def test_is_overdue_field(self, invoice_overdue):
        """Test is_overdue property is serialized."""
        serializer = InvoiceListSerializer(invoice_overdue)
        data = serializer.data

        assert data['is_overdue'] is True

    @pytest.mark.django_db
    def test_balance_due_field(self, invoice_draft):
        """Test balance_due property is serialized."""
        serializer = InvoiceListSerializer(invoice_draft)
        data = serializer.data

        expected_balance = invoice_draft.total - invoice_draft.paid_amount
        assert Decimal(data['balance_due']) == expected_balance

    @pytest.mark.django_db
    def test_paid_invoice_not_overdue(self, invoice_paid):
        """Test paid invoice is not overdue."""
        serializer = InvoiceListSerializer(invoice_paid)
        data = serializer.data

        assert data['is_overdue'] is False

    @pytest.mark.django_db
    def test_read_only_fields(self):
        """Test read-only fields are declared."""
        read_only = InvoiceListSerializer.Meta.read_only_fields
        assert 'id' in read_only
        assert 'invoice_number' in read_only
        assert 'created_at' in read_only
        assert 'updated_at' in read_only

    @pytest.mark.django_db
    def test_balance_due_zero_for_paid(self, invoice_paid):
        """Test balance_due is zero for fully paid invoice."""
        serializer = InvoiceListSerializer(invoice_paid)
        data = serializer.data

        assert Decimal(data['balance_due']) == Decimal('0.00')


# ============================================================================
# InvoiceDetailSerializer Tests
# ============================================================================


class TestInvoiceDetailSerializer:
    """Tests for InvoiceDetailSerializer."""

    @pytest.mark.django_db
    def test_serializes_all_model_fields(self, invoice_draft):
        """Test that __all__ fields are serialized."""
        serializer = InvoiceDetailSerializer(invoice_draft)
        data = serializer.data

        # Should include nested client and contract
        assert 'client' in data
        assert 'contract' in data
        assert 'items' in data
        assert 'is_overdue' in data
        assert 'balance_due' in data
        assert 'is_fully_paid' in data

    @pytest.mark.django_db
    def test_nested_client_serialization(self, invoice_draft):
        """Test that client is serialized with ClientListSerializer."""
        serializer = InvoiceDetailSerializer(invoice_draft)
        data = serializer.data

        # client should be an object, not just the id
        assert isinstance(data['client'], dict)
        assert 'id' in data['client']
        assert 'email' in data['client']

    @pytest.mark.django_db
    def test_nested_contract_serialization(self, invoice_draft):
        """Test that contract is serialized with ContractListSerializer."""
        serializer = InvoiceDetailSerializer(invoice_draft)
        data = serializer.data

        assert isinstance(data['contract'], dict)
        assert 'id' in data['contract']
        assert 'title' in data['contract']

    @pytest.mark.django_db
    def test_items_are_serialized(self, invoice_draft, invoice_item):
        """Test that items are serialized as a list."""
        serializer = InvoiceDetailSerializer(invoice_draft)
        data = serializer.data

        assert isinstance(data['items'], list)
        assert len(data['items']) == 1
        assert data['items'][0]['description'] == 'Web Development Services'

    @pytest.mark.django_db
    def test_empty_items_list(self, invoice_sent):
        """Test that invoice with no items returns empty list."""
        serializer = InvoiceDetailSerializer(invoice_sent)
        data = serializer.data

        assert data['items'] == []

    @pytest.mark.django_db
    def test_is_fully_paid_true(self, invoice_paid):
        """Test is_fully_paid is True for paid invoice."""
        serializer = InvoiceDetailSerializer(invoice_paid)
        data = serializer.data

        assert data['is_fully_paid'] is True

    @pytest.mark.django_db
    def test_is_fully_paid_false(self, invoice_draft):
        """Test is_fully_paid is False for unpaid invoice."""
        serializer = InvoiceDetailSerializer(invoice_draft)
        data = serializer.data

        assert data['is_fully_paid'] is False

    @pytest.mark.django_db
    def test_read_only_fields(self):
        """Test read-only fields are declared."""
        read_only = InvoiceDetailSerializer.Meta.read_only_fields
        assert 'id' in read_only
        assert 'invoice_number' in read_only
        assert 'subtotal' in read_only
        assert 'tax_amount' in read_only
        assert 'total' in read_only

    @pytest.mark.django_db
    def test_null_contract(self, invoice_overdue):
        """Test invoice with no contract serializes contract as None."""
        serializer = InvoiceDetailSerializer(invoice_overdue)
        data = serializer.data

        assert data['contract'] is None


# ============================================================================
# InvoiceCreateUpdateSerializer Tests
# ============================================================================


class TestInvoiceCreateUpdateSerializer:
    """Tests for InvoiceCreateUpdateSerializer."""

    @pytest.mark.django_db
    def test_valid_create_without_items(self, client_company, contract_fixed):
        """Test creating invoice without items."""
        data = {
            'client': str(client_company.id),
            'contract': str(contract_fixed.id),
            'status': 'draft',
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_rate': '8.00',
            'currency': 'USD',
        }
        serializer = InvoiceCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        invoice = serializer.save()
        assert invoice.client == client_company
        assert invoice.contract == contract_fixed
        assert invoice.status == 'draft'
        assert invoice.invoice_number.startswith('INV-')

    @pytest.mark.django_db
    def test_valid_create_with_items(self, client_company):
        """Test creating invoice with items."""
        data = {
            'client': str(client_company.id),
            'status': 'draft',
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_rate': '10.00',
            'currency': 'USD',
            'items': [
                {
                    'description': 'Design Services',
                    'quantity': '2.00',
                    'unit_price': '500.00',
                    'order': 0,
                },
                {
                    'description': 'Development Services',
                    'quantity': '1.00',
                    'unit_price': '3000.00',
                    'order': 1,
                },
            ],
        }
        serializer = InvoiceCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        invoice = serializer.save()
        assert invoice.items.count() == 2
        # Totals should have been calculated
        assert invoice.subtotal > 0

    @pytest.mark.django_db
    def test_due_date_before_issue_date_fails(self, client_company):
        """Test that due_date before issue_date raises validation error."""
        data = {
            'client': str(client_company.id),
            'status': 'draft',
            'issue_date': str(date.today()),
            'due_date': str(date.today() - timedelta(days=1)),
            'currency': 'USD',
        }
        serializer = InvoiceCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'due_date' in serializer.errors

    @pytest.mark.django_db
    def test_due_date_equals_issue_date_is_valid(self, client_company):
        """Test that due_date equal to issue_date is valid."""
        today = date.today()
        data = {
            'client': str(client_company.id),
            'status': 'draft',
            'issue_date': str(today),
            'due_date': str(today),
            'currency': 'USD',
        }
        serializer = InvoiceCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    @pytest.mark.django_db
    def test_update_invoice_fields(self, invoice_draft):
        """Test updating invoice fields."""
        data = {
            'notes': 'Updated notes',
            'terms': 'Updated terms',
        }
        serializer = InvoiceCreateUpdateSerializer(
            instance=invoice_draft,
            data=data,
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()
        assert updated.notes == 'Updated notes'
        assert updated.terms == 'Updated terms'

    @pytest.mark.django_db
    def test_update_invoice_with_new_items(self, invoice_draft):
        """Test updating invoice with new items replaces old ones."""
        data = {
            'items': [
                {
                    'description': 'New Service',
                    'quantity': '5.00',
                    'unit_price': '200.00',
                    'order': 0,
                },
            ],
        }
        serializer = InvoiceCreateUpdateSerializer(
            instance=invoice_draft,
            data=data,
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()
        assert updated.items.count() == 1
        assert updated.items.first().description == 'New Service'

    @pytest.mark.django_db
    def test_update_invoice_items_none_preserves_items(self, invoice_draft, invoice_item):
        """Test update without items field preserves existing items."""
        data = {
            'notes': 'Just updating notes',
        }
        serializer = InvoiceCreateUpdateSerializer(
            instance=invoice_draft,
            data=data,
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()
        # Items should be preserved since items was not in validated_data
        assert updated.items.count() == 1

    @pytest.mark.django_db
    def test_create_without_contract(self, client_company):
        """Test creating invoice without contract (optional field)."""
        data = {
            'client': str(client_company.id),
            'status': 'draft',
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=30)),
            'currency': 'USD',
        }
        serializer = InvoiceCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        invoice = serializer.save()
        assert invoice.contract is None

    @pytest.mark.django_db
    def test_validate_only_due_date_provided(self, client_company):
        """Test validation when only due_date is provided (no issue_date)."""
        data = {
            'client': str(client_company.id),
            'status': 'draft',
            'due_date': str(date.today() + timedelta(days=30)),
            'currency': 'USD',
        }
        serializer = InvoiceCreateUpdateSerializer(data=data)
        # issue_date is required on the model, so this should fail
        assert not serializer.is_valid()

    @pytest.mark.django_db
    def test_metadata_field(self, client_company):
        """Test creating invoice with metadata."""
        data = {
            'client': str(client_company.id),
            'status': 'draft',
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=30)),
            'currency': 'USD',
            'metadata': {'source': 'api', 'version': '1.0'},
        }
        serializer = InvoiceCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        invoice = serializer.save()
        assert invoice.metadata == {'source': 'api', 'version': '1.0'}

    @pytest.mark.django_db
    def test_update_with_empty_items_list_clears_items(self, invoice_draft, invoice_item):
        """Test that passing empty items list deletes all items."""
        data = {
            'items': [],
        }
        serializer = InvoiceCreateUpdateSerializer(
            instance=invoice_draft,
            data=data,
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()
        assert updated.items.count() == 0


# ============================================================================
# InvoiceStatsSerializer Tests
# ============================================================================


class TestInvoiceStatsSerializer:
    """Tests for InvoiceStatsSerializer."""

    def test_serializes_stats_data(self):
        """Test serialization of statistics data."""
        stats = {
            'total_invoices': 100,
            'draft_invoices': 20,
            'sent_invoices': 30,
            'paid_invoices': 40,
            'overdue_invoices': 10,
            'total_invoiced': Decimal('50000.00'),
            'total_paid': Decimal('35000.00'),
            'total_outstanding': Decimal('15000.00'),
        }
        serializer = InvoiceStatsSerializer(stats)
        data = serializer.data

        assert data['total_invoices'] == 100
        assert data['draft_invoices'] == 20
        assert data['sent_invoices'] == 30
        assert data['paid_invoices'] == 40
        assert data['overdue_invoices'] == 10
        assert Decimal(data['total_invoiced']) == Decimal('50000.00')
        assert Decimal(data['total_paid']) == Decimal('35000.00')
        assert Decimal(data['total_outstanding']) == Decimal('15000.00')

    def test_serializes_zero_stats(self):
        """Test serialization with all zeros."""
        stats = {
            'total_invoices': 0,
            'draft_invoices': 0,
            'sent_invoices': 0,
            'paid_invoices': 0,
            'overdue_invoices': 0,
            'total_invoiced': Decimal('0.00'),
            'total_paid': Decimal('0.00'),
            'total_outstanding': Decimal('0.00'),
        }
        serializer = InvoiceStatsSerializer(stats)
        data = serializer.data

        assert data['total_invoices'] == 0
        assert Decimal(data['total_invoiced']) == Decimal('0.00')

    def test_valid_data_deserialization(self):
        """Test that valid stats data passes validation."""
        data = {
            'total_invoices': 5,
            'draft_invoices': 1,
            'sent_invoices': 2,
            'paid_invoices': 1,
            'overdue_invoices': 1,
            'total_invoiced': '10000.00',
            'total_paid': '5000.00',
            'total_outstanding': '5000.00',
        }
        serializer = InvoiceStatsSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_missing_required_field(self):
        """Test that missing fields cause validation errors."""
        data = {
            'total_invoices': 5,
            # Missing other required fields
        }
        serializer = InvoiceStatsSerializer(data=data)
        assert not serializer.is_valid()
        assert 'draft_invoices' in serializer.errors
