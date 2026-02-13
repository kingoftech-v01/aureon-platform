"""
URL configuration for expenses app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExpenseCategoryViewSet, ExpenseViewSet
from .views_frontend import (
    ExpenseListView,
    ExpenseDetailView,
    ExpenseCreateView,
    ExpenseCategoryListView,
    ExpenseReportView,
)

app_name = 'expenses'

# API Router
router = DefaultRouter()
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expense-category')
router.register(r'expenses', ExpenseViewSet, basename='expense')

api_urlpatterns = [
    path('', include(router.urls)),
]

frontend_urlpatterns = [
    path('', ExpenseListView.as_view(), name='expense_list'),
    path('create/', ExpenseCreateView.as_view(), name='expense_create'),
    path('categories/', ExpenseCategoryListView.as_view(), name='category_list'),
    path('report/', ExpenseReportView.as_view(), name='expense_report'),
    path('<uuid:pk>/', ExpenseDetailView.as_view(), name='expense_detail'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
