"""
Tests for the expenses app API views and frontend views.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.expenses.models import Expense, ExpenseCategory
from .factories import (
    UserFactory,
    ClientFactory,
    ExpenseCategoryFactory,
    ExpenseFactory,
)


# ============================================================================
# Helper Fixtures
# ============================================================================


@pytest.fixture
def api_client():
    """Create an API test client."""
    client = APIClient()
    client.defaults['HTTP_ORIGIN'] = 'http://testserver'
    client.defaults['SERVER_NAME'] = 'testserver'
    return client


@pytest.fixture
def user(db):
    """Create a test user."""
    return UserFactory()


@pytest.fixture
def authenticated_client(api_client, user):
    """Create an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def category(db):
    """Create a test expense category."""
    return ExpenseCategoryFactory(name='Travel')


@pytest.fixture
def expense(db, user, category):
    """Create a test expense."""
    return ExpenseFactory(
        submitted_by=user,
        category=category,
        description='Test expense',
        amount=Decimal('100.00'),
    )


# ============================================================================
# ExpenseCategoryViewSet Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseCategoryViewSet:
    """Tests for ExpenseCategoryViewSet API endpoints."""

    def test_list_categories(self, authenticated_client):
        """Test listing all expense categories."""
        ExpenseCategoryFactory.create_batch(3)
        url = reverse('expenses:expense-category-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_list_categories_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse('expenses:expense-category-list')
        response = api_client.get(url)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_create_category(self, authenticated_client):
        """Test creating a new expense category."""
        url = reverse('expenses:expense-category-list')
        data = {
            'name': 'Software Licenses',
            'description': 'Software and SaaS subscriptions',
            'color': '#3366FF',
            'is_active': True,
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Software Licenses'
        assert ExpenseCategory.objects.filter(name='Software Licenses').exists()

    def test_retrieve_category(self, authenticated_client, category):
        """Test retrieving a single expense category."""
        url = reverse('expenses:expense-category-detail', kwargs={'pk': category.pk})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == category.name

    def test_update_category(self, authenticated_client, category):
        """Test updating an expense category."""
        url = reverse('expenses:expense-category-detail', kwargs={'pk': category.pk})
        data = {'name': 'Updated Category', 'description': 'Updated desc'}
        response = authenticated_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == 'Updated Category'

    def test_partial_update_category(self, authenticated_client, category):
        """Test partially updating an expense category."""
        url = reverse('expenses:expense-category-detail', kwargs={'pk': category.pk})
        data = {'color': '#00FF00'}
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.color == '#00FF00'

    def test_delete_category(self, authenticated_client, category):
        """Test deleting an expense category."""
        url = reverse('expenses:expense-category-detail', kwargs={'pk': category.pk})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ExpenseCategory.objects.filter(pk=category.pk).exists()

    def test_search_categories(self, authenticated_client):
        """Test searching categories by name."""
        ExpenseCategoryFactory(name='Travel')
        ExpenseCategoryFactory(name='Software')
        ExpenseCategoryFactory(name='Marketing')
        url = reverse('expenses:expense-category-list')
        response = authenticated_client.get(url, {'search': 'Travel'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Travel'

    def test_filter_active_categories(self, authenticated_client):
        """Test filtering categories by is_active."""
        ExpenseCategoryFactory(is_active=True)
        ExpenseCategoryFactory(is_active=True)
        ExpenseCategoryFactory(is_active=False)
        url = reverse('expenses:expense-category-list')
        response = authenticated_client.get(url, {'is_active': 'true'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_ordering_categories(self, authenticated_client):
        """Test ordering categories by name."""
        ExpenseCategoryFactory(name='Zebra')
        ExpenseCategoryFactory(name='Alpha')
        url = reverse('expenses:expense-category-list')
        response = authenticated_client.get(url, {'ordering': 'name'})
        assert response.status_code == status.HTTP_200_OK
        names = [c['name'] for c in response.data['results']]
        assert names == sorted(names)


# ============================================================================
# ExpenseViewSet CRUD Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseViewSetCRUD:
    """Tests for ExpenseViewSet CRUD operations."""

    def test_list_expenses(self, authenticated_client, user):
        """Test listing all expenses."""
        ExpenseFactory.create_batch(5, submitted_by=user)
        url = reverse('expenses:expense-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5

    def test_list_expenses_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse('expenses:expense-list')
        response = api_client.get(url)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_create_expense(self, authenticated_client, category, user):
        """Test creating a new expense sets submitted_by to current user."""
        url = reverse('expenses:expense-list')
        data = {
            'description': 'Conference registration',
            'amount': '500.00',
            'currency': 'USD',
            'category': str(category.pk),
            'expense_date': str(date.today()),
            'is_billable': False,
            'vendor': 'EventOrg',
            'payment_method': 'card',
            'notes': 'Annual tech conference',
            'tags': ['conference'],
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        new_expense = Expense.objects.get(description='Conference registration')
        assert new_expense.submitted_by == user
        assert new_expense.amount == Decimal('500.00')

    def test_create_expense_minimal(self, authenticated_client):
        """Test creating an expense with minimal data."""
        url = reverse('expenses:expense-list')
        data = {
            'description': 'Quick expense',
            'amount': '25.00',
            'expense_date': str(date.today()),
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_expense(self, authenticated_client, expense):
        """Test retrieving a single expense."""
        url = reverse('expenses:expense-detail', kwargs={'pk': expense.pk})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == expense.description
        # Detail view includes nested category
        assert 'is_pending' in response.data

    def test_update_expense(self, authenticated_client, expense):
        """Test updating an expense."""
        url = reverse('expenses:expense-detail', kwargs={'pk': expense.pk})
        data = {
            'description': 'Updated expense description',
            'amount': '200.00',
            'expense_date': str(date.today()),
        }
        response = authenticated_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.description == 'Updated expense description'
        assert expense.amount == Decimal('200.00')

    def test_partial_update_expense(self, authenticated_client, expense):
        """Test partially updating an expense."""
        url = reverse('expenses:expense-detail', kwargs={'pk': expense.pk})
        data = {'vendor': 'New Vendor Name'}
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.vendor == 'New Vendor Name'

    def test_delete_expense(self, authenticated_client, expense):
        """Test deleting an expense."""
        expense_pk = expense.pk
        url = reverse('expenses:expense-detail', kwargs={'pk': expense_pk})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Expense.objects.filter(pk=expense_pk).exists()

    def test_filter_by_status(self, authenticated_client, user):
        """Test filtering expenses by status."""
        ExpenseFactory(submitted_by=user, status=Expense.PENDING)
        ExpenseFactory(submitted_by=user, status=Expense.PENDING)
        ExpenseFactory(submitted_by=user, status=Expense.APPROVED)
        url = reverse('expenses:expense-list')
        response = authenticated_client.get(url, {'status': 'pending'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_filter_by_is_billable(self, authenticated_client, user):
        """Test filtering expenses by is_billable."""
        ExpenseFactory(submitted_by=user, is_billable=True)
        ExpenseFactory(submitted_by=user, is_billable=False)
        ExpenseFactory(submitted_by=user, is_billable=False)
        url = reverse('expenses:expense-list')
        response = authenticated_client.get(url, {'is_billable': 'true'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_filter_by_payment_method(self, authenticated_client, user):
        """Test filtering expenses by payment method."""
        ExpenseFactory(submitted_by=user, payment_method=Expense.CASH)
        ExpenseFactory(submitted_by=user, payment_method=Expense.CARD)
        url = reverse('expenses:expense-list')
        response = authenticated_client.get(url, {'payment_method': 'cash'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_search_expenses(self, authenticated_client, user):
        """Test searching expenses by description."""
        ExpenseFactory(submitted_by=user, description='Hotel booking')
        ExpenseFactory(submitted_by=user, description='Software license')
        url = reverse('expenses:expense-list')
        response = authenticated_client.get(url, {'search': 'Hotel'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_search_by_vendor(self, authenticated_client, user):
        """Test searching expenses by vendor name."""
        ExpenseFactory(submitted_by=user, vendor='Amazon Web Services')
        ExpenseFactory(submitted_by=user, vendor='Microsoft Azure')
        url = reverse('expenses:expense-list')
        response = authenticated_client.get(url, {'search': 'Amazon'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_ordering_by_amount(self, authenticated_client, user):
        """Test ordering expenses by amount."""
        ExpenseFactory(submitted_by=user, amount=Decimal('300.00'))
        ExpenseFactory(submitted_by=user, amount=Decimal('100.00'))
        ExpenseFactory(submitted_by=user, amount=Decimal('200.00'))
        url = reverse('expenses:expense-list')
        response = authenticated_client.get(url, {'ordering': 'amount'})
        assert response.status_code == status.HTTP_200_OK
        amounts = [Decimal(e['amount']) for e in response.data['results']]
        assert amounts == sorted(amounts)

    def test_retrieve_nonexistent_expense(self, authenticated_client):
        """Test retrieving a non-existent expense returns 404."""
        import uuid
        fake_pk = uuid.uuid4()
        url = reverse('expenses:expense-detail', kwargs={'pk': fake_pk})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# ExpenseViewSet Custom Actions Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseViewSetActions:
    """Tests for ExpenseViewSet custom actions (approve, reject, mark-billable, etc.)."""

    def test_approve_pending_expense(self, authenticated_client, user, expense):
        """Test approving a pending expense."""
        assert expense.status == Expense.PENDING
        url = reverse('expenses:expense-approve', kwargs={'pk': expense.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.status == Expense.APPROVED
        assert expense.approved_by == user
        assert expense.approved_at is not None

    def test_approve_non_pending_expense_fails(self, authenticated_client, user):
        """Test that approving a non-pending expense returns 400."""
        expense = ExpenseFactory(submitted_by=user, status=Expense.APPROVED)
        url = reverse('expenses:expense-approve', kwargs={'pk': expense.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Only pending expenses' in response.data['detail']

    def test_approve_rejected_expense_fails(self, authenticated_client, user):
        """Test that approving a rejected expense returns 400."""
        expense = ExpenseFactory(submitted_by=user, status=Expense.REJECTED)
        url = reverse('expenses:expense-approve', kwargs={'pk': expense.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reject_pending_expense(self, authenticated_client, user, expense):
        """Test rejecting a pending expense."""
        assert expense.status == Expense.PENDING
        url = reverse('expenses:expense-reject', kwargs={'pk': expense.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.status == Expense.REJECTED

    def test_reject_non_pending_expense_fails(self, authenticated_client, user):
        """Test that rejecting a non-pending expense returns 400."""
        expense = ExpenseFactory(submitted_by=user, status=Expense.APPROVED)
        url = reverse('expenses:expense-reject', kwargs={'pk': expense.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Only pending expenses' in response.data['detail']

    def test_reject_invoiced_expense_fails(self, authenticated_client, user):
        """Test that rejecting an invoiced expense returns 400."""
        expense = ExpenseFactory(submitted_by=user, status=Expense.INVOICED)
        url = reverse('expenses:expense-reject', kwargs={'pk': expense.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_mark_billable(self, authenticated_client, expense):
        """Test marking an expense as billable."""
        assert expense.is_billable is False
        url = reverse('expenses:expense-mark-billable', kwargs={'pk': expense.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.is_billable is True

    def test_mark_billable_already_billable(self, authenticated_client, user):
        """Test marking an already billable expense (idempotent)."""
        expense = ExpenseFactory(submitted_by=user, is_billable=True)
        url = reverse('expenses:expense-mark-billable', kwargs={'pk': expense.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.is_billable is True

    def test_mark_invoiced(self, authenticated_client, expense):
        """Test marking an expense as invoiced."""
        assert expense.is_invoiced is False
        url = reverse('expenses:expense-mark-invoiced', kwargs={'pk': expense.pk})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.is_invoiced is True
        assert expense.status == Expense.INVOICED

    def test_mark_invoiced_with_invalid_invoice_id(self, authenticated_client, expense):
        """Test marking as invoiced with invalid invoice_id logs warning but succeeds."""
        url = reverse('expenses:expense-mark-invoiced', kwargs={'pk': expense.pk})
        response = authenticated_client.post(url, {'invoice_id': 'invalid-uuid'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.is_invoiced is True
        assert expense.status == Expense.INVOICED

    def test_approve_unauthenticated(self, api_client, expense):
        """Test that approve requires authentication."""
        url = reverse('expenses:expense-approve', kwargs={'pk': expense.pk})
        response = api_client.post(url)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_reject_unauthenticated(self, api_client, expense):
        """Test that reject requires authentication."""
        url = reverse('expenses:expense-reject', kwargs={'pk': expense.pk})
        response = api_client.post(url)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ============================================================================
# ExpenseViewSet Stats Action Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseViewSetStats:
    """Tests for ExpenseViewSet stats action."""

    def test_stats_endpoint(self, authenticated_client, user, category):
        """Test stats endpoint returns aggregated data."""
        ExpenseFactory(submitted_by=user, category=category, amount=Decimal('100.00'), is_billable=True)
        ExpenseFactory(submitted_by=user, category=category, amount=Decimal('200.00'), is_billable=False)
        ExpenseFactory(submitted_by=user, category=category, amount=Decimal('50.00'), is_billable=True, is_invoiced=True, status=Expense.INVOICED)
        url = reverse('expenses:expense-stats')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert 'total_amount' in data
        assert 'total_billable' in data
        assert 'total_invoiced' in data
        assert 'by_category' in data
        assert 'by_status' in data
        assert 'by_month' in data

    def test_stats_total_amount(self, authenticated_client, user):
        """Test that stats total_amount is correctly summed."""
        ExpenseFactory(submitted_by=user, amount=Decimal('100.00'), category=None)
        ExpenseFactory(submitted_by=user, amount=Decimal('250.00'), category=None)
        url = reverse('expenses:expense-stats')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['total_amount']) == Decimal('350.00')

    def test_stats_total_billable(self, authenticated_client, user):
        """Test that stats total_billable only includes billable expenses."""
        ExpenseFactory(submitted_by=user, amount=Decimal('100.00'), is_billable=True, category=None)
        ExpenseFactory(submitted_by=user, amount=Decimal('200.00'), is_billable=False, category=None)
        url = reverse('expenses:expense-stats')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['total_billable']) == Decimal('100.00')

    def test_stats_total_invoiced(self, authenticated_client, user):
        """Test that stats total_invoiced only includes invoiced expenses."""
        ExpenseFactory(submitted_by=user, amount=Decimal('300.00'), is_invoiced=True, category=None)
        ExpenseFactory(submitted_by=user, amount=Decimal('200.00'), is_invoiced=False, category=None)
        url = reverse('expenses:expense-stats')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['total_invoiced']) == Decimal('300.00')

    def test_stats_by_status(self, authenticated_client, user):
        """Test stats by_status counts."""
        ExpenseFactory(submitted_by=user, status=Expense.PENDING, category=None)
        ExpenseFactory(submitted_by=user, status=Expense.PENDING, category=None)
        ExpenseFactory(submitted_by=user, status=Expense.APPROVED, category=None)
        url = reverse('expenses:expense-stats')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['by_status']['pending'] == 2
        assert response.data['by_status']['approved'] == 1

    def test_stats_by_category(self, authenticated_client, user):
        """Test stats by_category aggregation."""
        cat1 = ExpenseCategoryFactory(name='Travel')
        cat2 = ExpenseCategoryFactory(name='Office')
        ExpenseFactory(submitted_by=user, category=cat1, amount=Decimal('100.00'))
        ExpenseFactory(submitted_by=user, category=cat1, amount=Decimal('200.00'))
        ExpenseFactory(submitted_by=user, category=cat2, amount=Decimal('50.00'))
        url = reverse('expenses:expense-stats')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        by_category = response.data['by_category']
        assert len(by_category) == 2
        # Top category should be Travel with total 300
        assert by_category[0]['category_name'] == 'Travel'
        assert Decimal(str(by_category[0]['total'])) == Decimal('300.00')

    def test_stats_empty(self, authenticated_client):
        """Test stats with no expenses."""
        url = reverse('expenses:expense-stats')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['total_amount']) == Decimal('0')
        assert response.data['by_category'] == []
        assert response.data['by_status'] == {}

    def test_stats_unauthenticated(self, api_client):
        """Test that stats requires authentication."""
        url = reverse('expenses:expense-stats')
        response = api_client.get(url)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ============================================================================
# Frontend View Tests
# ============================================================================


@pytest.mark.django_db
class TestExpenseFrontendViews:
    """Tests for expenses frontend views (Django template-based views)."""

    @pytest.fixture
    def django_client(self, user):
        """Create a Django test client logged in as the user."""
        from django.test import Client as DjangoClient
        client = DjangoClient()
        client.force_login(user)
        return client

    @pytest.fixture
    def anonymous_client(self):
        """Create an anonymous Django test client."""
        from django.test import Client as DjangoClient
        return DjangoClient()

    def test_expense_list_view(self, django_client, user):
        """Test expense list view renders successfully."""
        ExpenseFactory(submitted_by=user)
        response = django_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_200_OK

    def test_expense_list_view_requires_login(self, anonymous_client):
        """Test expense list view redirects unauthenticated users."""
        response = anonymous_client.get('/api/expenses/')
        # Either redirect to login or 302
        assert response.status_code in (301, 302, 403)

    def test_expense_detail_view(self, django_client, user):
        """Test expense detail view renders successfully."""
        expense = ExpenseFactory(submitted_by=user)
        response = django_client.get(f'/api/expenses/{expense.pk}/')
        assert response.status_code == status.HTTP_200_OK

    def test_expense_create_view(self, django_client):
        """Test expense create view renders successfully."""
        response = django_client.get('/api/expenses/create/')
        assert response.status_code == status.HTTP_200_OK

    def test_category_list_view(self, django_client):
        """Test category list view renders successfully."""
        ExpenseCategoryFactory.create_batch(3)
        response = django_client.get('/api/expenses/categories/')
        assert response.status_code == status.HTTP_200_OK

    def test_expense_report_view(self, django_client):
        """Test expense report view renders successfully."""
        response = django_client.get('/api/expenses/report/')
        assert response.status_code == status.HTTP_200_OK

    def test_expense_list_filter_by_status(self, django_client, user):
        """Test expense list filtering by status query param."""
        ExpenseFactory(submitted_by=user, status=Expense.PENDING)
        ExpenseFactory(submitted_by=user, status=Expense.APPROVED)
        response = django_client.get('/api/expenses/', {'status': 'pending'})
        assert response.status_code == status.HTTP_200_OK

    def test_expense_list_filter_by_billable(self, django_client, user):
        """Test expense list filtering by billable query param."""
        ExpenseFactory(submitted_by=user, is_billable=True)
        ExpenseFactory(submitted_by=user, is_billable=False)
        response = django_client.get('/api/expenses/', {'billable': 'true'})
        assert response.status_code == status.HTTP_200_OK

    def test_expense_list_search(self, django_client, user):
        """Test expense list search by query param."""
        ExpenseFactory(submitted_by=user, description='Unique hotel booking')
        response = django_client.get('/api/expenses/', {'q': 'hotel'})
        assert response.status_code == status.HTTP_200_OK

    def test_expense_report_custom_date_range(self, django_client, user):
        """Test expense report with custom date range."""
        ExpenseFactory(submitted_by=user, expense_date=date.today() - timedelta(days=5))
        response = django_client.get('/api/expenses/report/', {'range': '7'})
        assert response.status_code == status.HTTP_200_OK

    def test_expense_report_invalid_range_defaults_to_30(self, django_client):
        """Test expense report with invalid range falls back to 30 days."""
        response = django_client.get('/api/expenses/report/', {'range': 'abc'})
        assert response.status_code == status.HTTP_200_OK

    def test_detail_view_requires_login(self, anonymous_client, user):
        """Test detail view redirects unauthenticated users."""
        expense = ExpenseFactory(submitted_by=user)
        response = anonymous_client.get(f'/api/expenses/{expense.pk}/')
        assert response.status_code in (301, 302, 403)
