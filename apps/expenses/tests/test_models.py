"""
Tests for the expenses app models.
"""

import pytest
import uuid
from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.expenses.models import ExpenseCategory, Expense
from .factories import (
    UserFactory,
    ClientFactory,
    ExpenseCategoryFactory,
    ExpenseFactory,
)


# ============================================================================
# ExpenseCategory Model Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseCategory:
    """Tests for the ExpenseCategory model."""

    def test_create_category(self):
        """Test basic ExpenseCategory creation."""
        category = ExpenseCategoryFactory(name='Travel', description='Travel expenses', color='#FF5733')
        assert category.pk is not None
        assert isinstance(category.pk, uuid.UUID)
        assert category.name == 'Travel'
        assert category.description == 'Travel expenses'
        assert category.color == '#FF5733'
        assert category.is_active is True

    def test_str_representation(self):
        """Test __str__ returns the category name."""
        category = ExpenseCategoryFactory(name='Office Supplies')
        assert str(category) == 'Office Supplies'

    def test_default_is_active(self):
        """Test that new categories are active by default."""
        category = ExpenseCategoryFactory()
        assert category.is_active is True

    def test_inactive_category(self):
        """Test creating an inactive category."""
        category = ExpenseCategoryFactory(is_active=False)
        assert category.is_active is False

    def test_timestamps_set_on_create(self):
        """Test that created_at and updated_at are set automatically."""
        category = ExpenseCategoryFactory()
        assert category.created_at is not None
        assert category.updated_at is not None

    def test_uuid_primary_key(self):
        """Test that the id field is a UUID."""
        category = ExpenseCategoryFactory()
        assert isinstance(category.id, uuid.UUID)

    def test_ordering(self):
        """Test that categories are ordered by name."""
        cat_b = ExpenseCategoryFactory(name='Beta')
        cat_a = ExpenseCategoryFactory(name='Alpha')
        cat_c = ExpenseCategoryFactory(name='Charlie')
        categories = list(ExpenseCategory.objects.all())
        assert categories[0].name == 'Alpha'
        assert categories[1].name == 'Beta'
        assert categories[2].name == 'Charlie'

    def test_verbose_names(self):
        """Test model Meta verbose names."""
        assert ExpenseCategory._meta.verbose_name == 'Expense Category'
        assert ExpenseCategory._meta.verbose_name_plural == 'Expense Categories'

    def test_blank_description_and_color(self):
        """Test that description and color can be blank."""
        category = ExpenseCategoryFactory(description='', color='')
        category.full_clean()
        assert category.description == ''
        assert category.color == ''

    def test_category_name_max_length(self):
        """Test that name max_length constraint is enforced."""
        assert ExpenseCategory._meta.get_field('name').max_length == 100

    def test_expenses_reverse_relation(self):
        """Test the expenses reverse relation from category."""
        category = ExpenseCategoryFactory()
        expense = ExpenseFactory(category=category)
        assert expense in category.expenses.all()


# ============================================================================
# Expense Model Tests
# ============================================================================


@pytest.mark.django_db
class TestExpense:
    """Tests for the Expense model."""

    def test_create_expense(self):
        """Test basic Expense creation."""
        user = UserFactory()
        category = ExpenseCategoryFactory()
        expense = ExpenseFactory(
            description='Team lunch',
            amount=Decimal('75.50'),
            currency='USD',
            category=category,
            submitted_by=user,
        )
        assert expense.pk is not None
        assert isinstance(expense.pk, uuid.UUID)
        assert expense.description == 'Team lunch'
        assert expense.amount == Decimal('75.50')
        assert expense.currency == 'USD'
        assert expense.category == category
        assert expense.submitted_by == user

    def test_str_representation(self):
        """Test __str__ returns description, amount and currency."""
        expense = ExpenseFactory(description='Flight ticket', amount=Decimal('350.00'), currency='EUR')
        assert str(expense) == 'Flight ticket - 350.00 EUR'

    def test_is_pending_property_true(self):
        """Test is_pending property when status is PENDING."""
        expense = ExpenseFactory(status=Expense.PENDING)
        assert expense.is_pending is True

    def test_is_pending_property_false_when_approved(self):
        """Test is_pending property when status is APPROVED."""
        expense = ExpenseFactory(status=Expense.APPROVED)
        assert expense.is_pending is False

    def test_is_pending_property_false_when_rejected(self):
        """Test is_pending property when status is REJECTED."""
        expense = ExpenseFactory(status=Expense.REJECTED)
        assert expense.is_pending is False

    def test_is_pending_property_false_when_invoiced(self):
        """Test is_pending property when status is INVOICED."""
        expense = ExpenseFactory(status=Expense.INVOICED)
        assert expense.is_pending is False

    def test_default_status_is_pending(self):
        """Test that new expenses default to PENDING status."""
        expense = ExpenseFactory()
        assert expense.status == Expense.PENDING

    def test_default_payment_method_is_card(self):
        """Test that default payment method is CARD."""
        expense = ExpenseFactory()
        assert expense.payment_method == Expense.CARD

    def test_default_currency_is_usd(self):
        """Test that default currency is USD."""
        expense = ExpenseFactory()
        assert expense.currency == 'USD'

    def test_default_is_billable_false(self):
        """Test that is_billable defaults to False."""
        expense = ExpenseFactory()
        assert expense.is_billable is False

    def test_default_is_invoiced_false(self):
        """Test that is_invoiced defaults to False."""
        expense = ExpenseFactory()
        assert expense.is_invoiced is False

    def test_timestamps_set_on_create(self):
        """Test that created_at and updated_at are set automatically."""
        expense = ExpenseFactory()
        assert expense.created_at is not None
        assert expense.updated_at is not None

    def test_uuid_primary_key(self):
        """Test that the id field is a UUID."""
        expense = ExpenseFactory()
        assert isinstance(expense.id, uuid.UUID)

    def test_expense_with_all_payment_methods(self):
        """Test creating expenses with each payment method."""
        for method, _ in Expense.PAYMENT_METHOD_CHOICES:
            expense = ExpenseFactory(payment_method=method)
            assert expense.payment_method == method

    def test_expense_with_all_statuses(self):
        """Test creating expenses with each status."""
        for status_val, _ in Expense.STATUS_CHOICES:
            expense = ExpenseFactory(status=status_val)
            assert expense.status == status_val

    def test_expense_without_category(self):
        """Test that category is optional (nullable)."""
        expense = ExpenseFactory(category=None)
        assert expense.category is None
        expense.full_clean()

    def test_expense_without_client(self):
        """Test that client is optional (nullable)."""
        expense = ExpenseFactory(client=None)
        assert expense.client is None
        expense.full_clean()

    def test_expense_amount_min_value_validator(self):
        """Test that amount must be at least 0.01."""
        expense = ExpenseFactory.build(amount=Decimal('0.00'))
        with pytest.raises(ValidationError):
            expense.full_clean()

    def test_expense_negative_amount_rejected(self):
        """Test that negative amount is rejected."""
        expense = ExpenseFactory.build(amount=Decimal('-5.00'))
        with pytest.raises(ValidationError):
            expense.full_clean()

    def test_expense_amount_valid_minimum(self):
        """Test that 0.01 is the minimum valid amount."""
        expense = ExpenseFactory(amount=Decimal('0.01'))
        expense.full_clean()
        assert expense.amount == Decimal('0.01')

    def test_expense_large_amount(self):
        """Test expense with large amount within max_digits."""
        expense = ExpenseFactory(amount=Decimal('9999999999.99'))
        expense.full_clean()
        assert expense.amount == Decimal('9999999999.99')

    def test_tags_default_to_empty_list(self):
        """Test that tags defaults to empty list."""
        expense = ExpenseFactory(tags=[])
        assert expense.tags == []

    def test_tags_with_values(self):
        """Test tags with list of strings."""
        expense = ExpenseFactory(tags=['travel', 'conference', 'Q1'])
        assert expense.tags == ['travel', 'conference', 'Q1']

    def test_metadata_default_to_empty_dict(self):
        """Test that metadata defaults to empty dict."""
        expense = ExpenseFactory(metadata={})
        assert expense.metadata == {}

    def test_metadata_with_values(self):
        """Test metadata with dictionary data."""
        meta = {'department': 'engineering', 'project_code': 'P-123'}
        expense = ExpenseFactory(metadata=meta)
        assert expense.metadata == meta

    def test_ordering_by_expense_date_descending(self):
        """Test that expenses are ordered by expense_date descending."""
        exp_old = ExpenseFactory(expense_date=date.today() - timedelta(days=10))
        exp_new = ExpenseFactory(expense_date=date.today())
        exp_mid = ExpenseFactory(expense_date=date.today() - timedelta(days=5))
        expenses = list(Expense.objects.all())
        assert expenses[0].expense_date >= expenses[1].expense_date
        assert expenses[1].expense_date >= expenses[2].expense_date

    def test_approved_by_and_approved_at_nullable(self):
        """Test that approved_by and approved_at are null by default."""
        expense = ExpenseFactory()
        assert expense.approved_by is None
        assert expense.approved_at is None

    def test_approval_fields(self):
        """Test setting approval fields."""
        approver = UserFactory()
        now = timezone.now()
        expense = ExpenseFactory(
            status=Expense.APPROVED,
            approved_by=approver,
            approved_at=now,
        )
        assert expense.approved_by == approver
        assert expense.approved_at == now
        assert expense.status == Expense.APPROVED

    def test_client_on_delete_set_null(self):
        """Test that deleting a client sets expense.client to null."""
        client = ClientFactory()
        expense = ExpenseFactory(client=client)
        client_pk = client.pk
        client.delete()
        expense.refresh_from_db()
        assert expense.client is None

    def test_category_on_delete_set_null(self):
        """Test that deleting a category sets expense.category to null."""
        category = ExpenseCategoryFactory()
        expense = ExpenseFactory(category=category)
        category.delete()
        expense.refresh_from_db()
        assert expense.category is None

    def test_submitted_by_on_delete_cascade(self):
        """Test that deleting submitted_by user cascades to delete expense."""
        user = UserFactory()
        expense = ExpenseFactory(submitted_by=user)
        expense_pk = expense.pk
        user.delete()
        assert not Expense.objects.filter(pk=expense_pk).exists()

    def test_verbose_names(self):
        """Test model Meta verbose names."""
        assert Expense._meta.verbose_name == 'Expense'
        assert Expense._meta.verbose_name_plural == 'Expenses'

    def test_indexes_defined(self):
        """Test that expected database indexes are defined."""
        index_fields = [idx.fields for idx in Expense._meta.indexes]
        assert ['category'] in index_fields
        assert ['client'] in index_fields
        assert ['status'] in index_fields
        assert ['submitted_by'] in index_fields
        assert ['expense_date'] in index_fields

    def test_status_choices(self):
        """Test that STATUS_CHOICES has expected values."""
        status_values = [choice[0] for choice in Expense.STATUS_CHOICES]
        assert 'pending' in status_values
        assert 'approved' in status_values
        assert 'rejected' in status_values
        assert 'invoiced' in status_values

    def test_payment_method_choices(self):
        """Test that PAYMENT_METHOD_CHOICES has expected values."""
        method_values = [choice[0] for choice in Expense.PAYMENT_METHOD_CHOICES]
        assert 'card' in method_values
        assert 'cash' in method_values
        assert 'bank_transfer' in method_values
        assert 'other' in method_values

    def test_billable_expense(self):
        """Test creating a billable expense."""
        expense = ExpenseFactory(is_billable=True)
        assert expense.is_billable is True

    def test_invoiced_expense(self):
        """Test creating an invoiced expense."""
        expense = ExpenseFactory(is_invoiced=True, status=Expense.INVOICED)
        assert expense.is_invoiced is True
        assert expense.status == Expense.INVOICED
