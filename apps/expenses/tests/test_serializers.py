"""
Tests for the expenses app serializers.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.test import RequestFactory

from apps.expenses.models import Expense, ExpenseCategory
from apps.expenses.serializers import (
    ExpenseCategorySerializer,
    ExpenseListSerializer,
    ExpenseDetailSerializer,
    ExpenseCreateUpdateSerializer,
    ExpenseStatsSerializer,
)
from .factories import (
    UserFactory,
    ClientFactory,
    ExpenseCategoryFactory,
    ExpenseFactory,
)


# ============================================================================
# ExpenseCategorySerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseCategorySerializer:
    """Tests for the ExpenseCategorySerializer."""

    def test_serialize_category(self):
        """Test serializing an ExpenseCategory."""
        category = ExpenseCategoryFactory(
            name='Travel',
            description='Travel related expenses',
            color='#FF5733',
        )
        serializer = ExpenseCategorySerializer(category)
        data = serializer.data
        assert data['name'] == 'Travel'
        assert data['description'] == 'Travel related expenses'
        assert data['color'] == '#FF5733'
        assert data['is_active'] is True
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_read_only_fields(self):
        """Test that id, created_at, updated_at are read only."""
        data = {
            'name': 'Test Category',
            'description': 'Desc',
            'color': '#000000',
            'is_active': True,
        }
        serializer = ExpenseCategorySerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        category = serializer.save()
        assert category.pk is not None

    def test_deserialize_valid_data(self):
        """Test creating a category from valid data."""
        data = {
            'name': 'Office Supplies',
            'description': 'Stationery and office equipment',
            'color': '#00FF00',
            'is_active': True,
        }
        serializer = ExpenseCategorySerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_deserialize_minimal_data(self):
        """Test creating a category with minimal required data."""
        data = {'name': 'Minimal Category'}
        serializer = ExpenseCategorySerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_deserialize_missing_name(self):
        """Test that name is required."""
        data = {'description': 'No name'}
        serializer = ExpenseCategorySerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

    def test_update_category(self):
        """Test updating a category via serializer."""
        category = ExpenseCategoryFactory(name='Old Name')
        serializer = ExpenseCategorySerializer(
            category, data={'name': 'New Name'}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.name == 'New Name'

    def test_all_fields_present(self):
        """Test that __all__ fields are serialized."""
        category = ExpenseCategoryFactory()
        serializer = ExpenseCategorySerializer(category)
        data = serializer.data
        expected_fields = {'id', 'name', 'description', 'color', 'is_active', 'created_at', 'updated_at'}
        assert expected_fields == set(data.keys())


# ============================================================================
# ExpenseListSerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseListSerializer:
    """Tests for the ExpenseListSerializer."""

    def test_serialize_expense_list(self):
        """Test serializing an expense for list view."""
        expense = ExpenseFactory()
        serializer = ExpenseListSerializer(expense)
        data = serializer.data
        assert 'id' in data
        assert 'description' in data
        assert 'amount' in data
        assert 'currency' in data
        assert 'expense_date' in data
        assert 'is_billable' in data
        assert 'is_invoiced' in data
        assert 'status' in data
        assert 'created_at' in data

    def test_category_method_field_with_category(self):
        """Test get_category returns id and name when category exists."""
        category = ExpenseCategoryFactory(name='Software')
        expense = ExpenseFactory(category=category)
        serializer = ExpenseListSerializer(expense)
        data = serializer.data
        assert data['category'] is not None
        assert data['category']['id'] == str(category.id)
        assert data['category']['name'] == 'Software'

    def test_category_method_field_without_category(self):
        """Test get_category returns None when category is null."""
        expense = ExpenseFactory(category=None)
        serializer = ExpenseListSerializer(expense)
        data = serializer.data
        assert data['category'] is None

    def test_client_method_field_with_client(self):
        """Test get_client returns id and display_name when client exists."""
        client = ClientFactory(company_name='Acme Corp')
        expense = ExpenseFactory(client=client)
        serializer = ExpenseListSerializer(expense)
        data = serializer.data
        assert data['client'] is not None
        assert data['client']['id'] == str(client.id)
        assert data['client']['name'] == client.get_display_name()

    def test_client_method_field_without_client(self):
        """Test get_client returns None when client is null."""
        expense = ExpenseFactory(client=None)
        serializer = ExpenseListSerializer(expense)
        data = serializer.data
        assert data['client'] is None

    def test_submitted_by_method_field(self):
        """Test get_submitted_by returns id and email."""
        user = UserFactory(email='submitter@test.com')
        expense = ExpenseFactory(submitted_by=user)
        serializer = ExpenseListSerializer(expense)
        data = serializer.data
        assert data['submitted_by'] is not None
        assert data['submitted_by']['id'] == str(user.id)
        assert data['submitted_by']['email'] == 'submitter@test.com'

    def test_list_fields_limited(self):
        """Test that list serializer only includes the specified fields."""
        expense = ExpenseFactory()
        serializer = ExpenseListSerializer(expense)
        data = serializer.data
        expected_fields = {
            'id', 'description', 'amount', 'currency', 'category',
            'expense_date', 'client', 'is_billable', 'is_invoiced',
            'status', 'submitted_by', 'created_at',
        }
        assert set(data.keys()) == expected_fields

    def test_serialize_multiple_expenses(self):
        """Test serializing a queryset of expenses."""
        ExpenseFactory.create_batch(3)
        expenses = Expense.objects.all()
        serializer = ExpenseListSerializer(expenses, many=True)
        assert len(serializer.data) == 3


# ============================================================================
# ExpenseDetailSerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseDetailSerializer:
    """Tests for the ExpenseDetailSerializer."""

    def test_serialize_expense_detail(self):
        """Test serializing an expense with full detail."""
        expense = ExpenseFactory()
        serializer = ExpenseDetailSerializer(expense)
        data = serializer.data
        assert 'id' in data
        assert 'description' in data
        assert 'amount' in data
        assert 'currency' in data
        assert 'category' in data
        assert 'expense_date' in data
        assert 'is_billable' in data
        assert 'is_invoiced' in data
        assert 'status' in data
        assert 'submitted_by' in data
        assert 'approved_by' in data
        assert 'approved_at' in data
        assert 'notes' in data
        assert 'tags' in data
        assert 'metadata' in data
        assert 'vendor' in data
        assert 'payment_method' in data
        assert 'receipt_number' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_nested_category_serialization(self):
        """Test that category is serialized as nested object."""
        category = ExpenseCategoryFactory(name='Travel', color='#123456')
        expense = ExpenseFactory(category=category)
        serializer = ExpenseDetailSerializer(expense)
        data = serializer.data
        assert data['category']['name'] == 'Travel'
        assert data['category']['color'] == '#123456'
        assert 'id' in data['category']

    def test_is_pending_field_included(self):
        """Test that is_pending property is serialized."""
        expense = ExpenseFactory(status=Expense.PENDING)
        serializer = ExpenseDetailSerializer(expense)
        data = serializer.data
        assert data['is_pending'] is True

    def test_is_pending_false_for_approved(self):
        """Test is_pending is False when approved."""
        expense = ExpenseFactory(status=Expense.APPROVED)
        serializer = ExpenseDetailSerializer(expense)
        data = serializer.data
        assert data['is_pending'] is False

    def test_read_only_fields(self):
        """Test that specific fields are read only."""
        read_only = ExpenseDetailSerializer.Meta.read_only_fields
        assert 'id' in read_only
        assert 'submitted_by' in read_only
        assert 'approved_by' in read_only
        assert 'approved_at' in read_only
        assert 'created_at' in read_only
        assert 'updated_at' in read_only

    def test_category_none_when_null(self):
        """Test category is None when expense has no category."""
        expense = ExpenseFactory(category=None)
        serializer = ExpenseDetailSerializer(expense)
        data = serializer.data
        assert data['category'] is None


# ============================================================================
# ExpenseCreateUpdateSerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseCreateUpdateSerializer:
    """Tests for the ExpenseCreateUpdateSerializer."""

    def test_valid_create_data(self):
        """Test creating an expense with valid data."""
        category = ExpenseCategoryFactory()
        client = ClientFactory()
        data = {
            'description': 'New Expense',
            'amount': '150.00',
            'currency': 'USD',
            'category': str(category.pk),
            'expense_date': str(date.today()),
            'client': str(client.pk),
            'is_billable': True,
            'vendor': 'TestVendor',
            'payment_method': 'card',
            'notes': 'Some notes',
            'tags': ['travel'],
        }
        serializer = ExpenseCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_minimal_create_data(self):
        """Test creating an expense with minimal required fields."""
        data = {
            'description': 'Quick expense',
            'amount': '10.00',
            'expense_date': str(date.today()),
        }
        serializer = ExpenseCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_missing_description(self):
        """Test that description is required."""
        data = {
            'amount': '10.00',
            'expense_date': str(date.today()),
        }
        serializer = ExpenseCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'description' in serializer.errors

    def test_missing_amount(self):
        """Test that amount is required."""
        data = {
            'description': 'No amount',
            'expense_date': str(date.today()),
        }
        serializer = ExpenseCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors

    def test_missing_expense_date(self):
        """Test that expense_date is required."""
        data = {
            'description': 'No date',
            'amount': '10.00',
        }
        serializer = ExpenseCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'expense_date' in serializer.errors

    def test_invalid_amount_zero(self):
        """Test that amount of 0 is rejected by model validator."""
        data = {
            'description': 'Zero expense',
            'amount': '0.00',
            'expense_date': str(date.today()),
        }
        serializer = ExpenseCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()

    def test_invalid_amount_negative(self):
        """Test that negative amount is rejected."""
        data = {
            'description': 'Negative expense',
            'amount': '-5.00',
            'expense_date': str(date.today()),
        }
        serializer = ExpenseCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()

    def test_fields_included(self):
        """Test that the correct fields are in the serializer."""
        expected_fields = [
            'description', 'amount', 'currency', 'category', 'expense_date',
            'client', 'contract', 'invoice', 'is_billable', 'receipt_file',
            'receipt_number', 'vendor', 'payment_method', 'notes', 'tags',
        ]
        assert ExpenseCreateUpdateSerializer.Meta.fields == expected_fields

    def test_update_expense(self):
        """Test updating an expense with partial data."""
        expense = ExpenseFactory()
        serializer = ExpenseCreateUpdateSerializer(
            expense, data={'description': 'Updated description'}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.description == 'Updated description'

    def test_update_amount(self):
        """Test updating expense amount."""
        expense = ExpenseFactory(amount=Decimal('100.00'))
        serializer = ExpenseCreateUpdateSerializer(
            expense, data={'amount': '250.00'}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.amount == Decimal('250.00')


# ============================================================================
# ExpenseStatsSerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseStatsSerializer:
    """Tests for the ExpenseStatsSerializer."""

    def test_valid_stats_data(self):
        """Test serializing valid stats data."""
        stats = {
            'total_amount': Decimal('5000.00'),
            'total_billable': Decimal('3000.00'),
            'total_invoiced': Decimal('1500.00'),
            'by_category': [
                {'category_id': 'abc', 'category_name': 'Travel', 'total': Decimal('2000.00'), 'count': 5},
            ],
            'by_status': {'pending': 3, 'approved': 2},
            'by_month': [
                {'month': '2025-01-01', 'total': Decimal('1000.00'), 'count': 3},
            ],
        }
        serializer = ExpenseStatsSerializer(stats)
        data = serializer.data
        assert data['total_amount'] == '5000.00'
        assert data['total_billable'] == '3000.00'
        assert data['total_invoiced'] == '1500.00'
        assert len(data['by_category']) == 1
        assert data['by_status'] == {'pending': 3, 'approved': 2}
        assert len(data['by_month']) == 1

    def test_empty_stats_data(self):
        """Test serializing empty stats data."""
        stats = {
            'total_amount': Decimal('0.00'),
            'total_billable': Decimal('0.00'),
            'total_invoiced': Decimal('0.00'),
            'by_category': [],
            'by_status': {},
            'by_month': [],
        }
        serializer = ExpenseStatsSerializer(stats)
        data = serializer.data
        assert data['total_amount'] == '0.00'
        assert data['total_billable'] == '0.00'
        assert data['total_invoiced'] == '0.00'
        assert data['by_category'] == []
        assert data['by_status'] == {}
        assert data['by_month'] == []

    def test_stats_fields(self):
        """Test that ExpenseStatsSerializer has expected fields."""
        serializer = ExpenseStatsSerializer()
        field_names = set(serializer.fields.keys())
        expected = {'total_amount', 'total_billable', 'total_invoiced', 'by_category', 'by_status', 'by_month'}
        assert expected == field_names

    def test_multiple_categories_in_stats(self):
        """Test stats with multiple categories."""
        stats = {
            'total_amount': Decimal('8000.00'),
            'total_billable': Decimal('5000.00'),
            'total_invoiced': Decimal('2000.00'),
            'by_category': [
                {'category_id': 'a1', 'category_name': 'Travel', 'total': Decimal('3000.00'), 'count': 5},
                {'category_id': 'b2', 'category_name': 'Software', 'total': Decimal('5000.00'), 'count': 10},
            ],
            'by_status': {'pending': 5, 'approved': 8, 'rejected': 2},
            'by_month': [
                {'month': '2025-01-01', 'total': Decimal('4000.00'), 'count': 8},
                {'month': '2025-02-01', 'total': Decimal('4000.00'), 'count': 7},
            ],
        }
        serializer = ExpenseStatsSerializer(stats)
        data = serializer.data
        assert len(data['by_category']) == 2
        assert len(data['by_month']) == 2
        assert len(data['by_status']) == 3
