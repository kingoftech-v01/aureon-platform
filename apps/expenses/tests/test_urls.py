"""
Tests for the expenses app URL configuration.
"""

import pytest
import uuid
from django.urls import reverse, resolve

from apps.expenses.views_api import ExpenseCategoryViewSet, ExpenseViewSet
from apps.expenses.views_frontend import (
    ExpenseListView,
    ExpenseDetailView,
    ExpenseCreateView,
    ExpenseCategoryListView,
    ExpenseReportView,
)


class TestExpenseCategoryAPIURLs:
    """Tests for ExpenseCategory API URL patterns."""

    def test_category_list_url_resolves(self):
        """Test that the expense-category-list URL resolves correctly."""
        url = reverse('expenses:expense-category-list')
        assert url == '/api/expenses/expense-categories/'
        resolver = resolve(url)
        assert resolver.func.cls == ExpenseCategoryViewSet

    def test_category_detail_url_resolves(self):
        """Test that the expense-category-detail URL resolves correctly."""
        pk = uuid.uuid4()
        url = reverse('expenses:expense-category-detail', kwargs={'pk': pk})
        assert f'/api/expenses/expense-categories/{pk}/' == url
        resolver = resolve(url)
        assert resolver.func.cls == ExpenseCategoryViewSet

    def test_category_list_url_name(self):
        """Test the URL name for category list."""
        url = reverse('expenses:expense-category-list')
        assert url is not None

    def test_category_detail_url_name(self):
        """Test the URL name for category detail."""
        pk = uuid.uuid4()
        url = reverse('expenses:expense-category-detail', kwargs={'pk': pk})
        assert url is not None


class TestExpenseAPIURLs:
    """Tests for Expense API URL patterns."""

    def test_expense_list_url_resolves(self):
        """Test that the expense-list URL resolves correctly."""
        url = reverse('expenses:expense-list')
        assert url == '/api/expenses/expenses/'
        resolver = resolve(url)
        assert resolver.func.cls == ExpenseViewSet

    def test_expense_detail_url_resolves(self):
        """Test that the expense-detail URL resolves correctly."""
        pk = uuid.uuid4()
        url = reverse('expenses:expense-detail', kwargs={'pk': pk})
        assert f'/api/expenses/expenses/{pk}/' == url
        resolver = resolve(url)
        assert resolver.func.cls == ExpenseViewSet

    def test_expense_approve_url_resolves(self):
        """Test that the expense-approve URL resolves correctly."""
        pk = uuid.uuid4()
        url = reverse('expenses:expense-approve', kwargs={'pk': pk})
        assert f'/api/expenses/expenses/{pk}/approve/' == url
        resolver = resolve(url)
        assert resolver.func.cls == ExpenseViewSet

    def test_expense_reject_url_resolves(self):
        """Test that the expense-reject URL resolves correctly."""
        pk = uuid.uuid4()
        url = reverse('expenses:expense-reject', kwargs={'pk': pk})
        assert f'/api/expenses/expenses/{pk}/reject/' == url
        resolver = resolve(url)
        assert resolver.func.cls == ExpenseViewSet

    def test_expense_mark_billable_url_resolves(self):
        """Test that the expense-mark-billable URL resolves correctly."""
        pk = uuid.uuid4()
        url = reverse('expenses:expense-mark-billable', kwargs={'pk': pk})
        assert f'/api/expenses/expenses/{pk}/mark-billable/' == url
        resolver = resolve(url)
        assert resolver.func.cls == ExpenseViewSet

    def test_expense_mark_invoiced_url_resolves(self):
        """Test that the expense-mark-invoiced URL resolves correctly."""
        pk = uuid.uuid4()
        url = reverse('expenses:expense-mark-invoiced', kwargs={'pk': pk})
        assert f'/api/expenses/expenses/{pk}/mark-invoiced/' == url
        resolver = resolve(url)
        assert resolver.func.cls == ExpenseViewSet

    def test_expense_stats_url_resolves(self):
        """Test that the expense-stats URL resolves correctly."""
        url = reverse('expenses:expense-stats')
        assert url == '/api/expenses/expenses/stats/'
        resolver = resolve(url)
        assert resolver.func.cls == ExpenseViewSet


class TestExpenseFrontendURLs:
    """Tests for expense frontend URL patterns."""

    def test_expense_list_frontend_url(self):
        """Test the expense_list frontend URL resolves."""
        url = reverse('expenses:expense_list')
        assert url == '/api/expenses/'
        resolver = resolve(url)
        assert resolver.func.view_class == ExpenseListView

    def test_expense_create_frontend_url(self):
        """Test the expense_create frontend URL resolves."""
        url = reverse('expenses:expense_create')
        assert url == '/api/expenses/create/'
        resolver = resolve(url)
        assert resolver.func.view_class == ExpenseCreateView

    def test_category_list_frontend_url(self):
        """Test the category_list frontend URL resolves."""
        url = reverse('expenses:category_list')
        assert url == '/api/expenses/categories/'
        resolver = resolve(url)
        assert resolver.func.view_class == ExpenseCategoryListView

    def test_expense_report_frontend_url(self):
        """Test the expense_report frontend URL resolves."""
        url = reverse('expenses:expense_report')
        assert url == '/api/expenses/report/'
        resolver = resolve(url)
        assert resolver.func.view_class == ExpenseReportView

    def test_expense_detail_frontend_url(self):
        """Test the expense_detail frontend URL resolves with UUID."""
        pk = uuid.uuid4()
        url = reverse('expenses:expense_detail', kwargs={'pk': pk})
        assert url == f'/api/expenses/{pk}/'
        resolver = resolve(url)
        assert resolver.func.view_class == ExpenseDetailView

    def test_app_name_is_expenses(self):
        """Test that the app_name is 'expenses'."""
        # Verify we can resolve URLs with expenses namespace
        url = reverse('expenses:expense-list')
        assert 'expenses' in url or url is not None


class TestURLPatternCompleteness:
    """Tests to ensure all expected URL patterns are registered."""

    def test_all_api_action_urls_exist(self):
        """Test that all expected custom action URLs exist."""
        pk = uuid.uuid4()
        expected_urls = [
            ('expenses:expense-list', {}),
            ('expenses:expense-detail', {'pk': pk}),
            ('expenses:expense-approve', {'pk': pk}),
            ('expenses:expense-reject', {'pk': pk}),
            ('expenses:expense-mark-billable', {'pk': pk}),
            ('expenses:expense-mark-invoiced', {'pk': pk}),
            ('expenses:expense-stats', {}),
            ('expenses:expense-category-list', {}),
            ('expenses:expense-category-detail', {'pk': pk}),
        ]
        for url_name, kwargs in expected_urls:
            url = reverse(url_name, kwargs=kwargs)
            assert url is not None, f"URL {url_name} could not be resolved"

    def test_all_frontend_urls_exist(self):
        """Test that all expected frontend URLs exist."""
        pk = uuid.uuid4()
        expected_urls = [
            ('expenses:expense_list', {}),
            ('expenses:expense_create', {}),
            ('expenses:category_list', {}),
            ('expenses:expense_report', {}),
            ('expenses:expense_detail', {'pk': pk}),
        ]
        for url_name, kwargs in expected_urls:
            url = reverse(url_name, kwargs=kwargs)
            assert url is not None, f"URL {url_name} could not be resolved"
