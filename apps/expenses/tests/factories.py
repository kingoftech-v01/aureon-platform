"""
Factory Boy factories for the expenses app.
"""

import factory
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.accounts.models import User
from apps.clients.models import Client
from apps.expenses.models import ExpenseCategory, Expense


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f'expenseuser{n}@test.com')
    username = factory.Sequence(lambda n: f'expenseuser{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    full_name = factory.LazyAttribute(lambda o: f'{o.first_name} {o.last_name}')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_active = True
    role = User.ADMIN


class ClientFactory(factory.django.DjangoModelFactory):
    """Factory for creating Client instances."""

    class Meta:
        model = Client

    client_type = Client.COMPANY
    company_name = factory.Sequence(lambda n: f'Test Company {n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Sequence(lambda n: f'client{n}@testcompany.com')
    lifecycle_stage = Client.ACTIVE
    is_active = True


class ExpenseCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating ExpenseCategory instances."""

    class Meta:
        model = ExpenseCategory

    name = factory.Sequence(lambda n: f'Category {n}')
    description = factory.Faker('sentence')
    color = factory.Faker('hex_color')
    is_active = True


class ExpenseFactory(factory.django.DjangoModelFactory):
    """Factory for creating Expense instances."""

    class Meta:
        model = Expense

    description = factory.Sequence(lambda n: f'Expense {n}')
    amount = factory.LazyFunction(lambda: Decimal('100.00'))
    currency = 'USD'
    category = factory.SubFactory(ExpenseCategoryFactory)
    expense_date = factory.LazyFunction(date.today)
    client = factory.SubFactory(ClientFactory)
    contract = None
    invoice = None
    is_billable = False
    is_invoiced = False
    receipt_number = factory.Sequence(lambda n: f'REC-{n:04d}')
    vendor = factory.Faker('company')
    payment_method = Expense.CARD
    status = Expense.PENDING
    submitted_by = factory.SubFactory(UserFactory)
    approved_by = None
    approved_at = None
    notes = factory.Faker('sentence')
    tags = factory.LazyFunction(list)
    metadata = factory.LazyFunction(dict)
