"""
URL configuration for analytics app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_insights import AIInsightsView
from .views_export import ExportReportView
from .views_bulk import BulkInvoiceActionView, BulkClientActionView
from .views_forecast import RevenueForecastView

app_name = 'analytics'

router = DefaultRouter()

urlpatterns = [
    # Analytics API endpoints
    path('dashboard/', views.dashboard_summary, name='dashboard_summary'),
    path('revenue/', views.revenue_metrics, name='revenue_metrics'),
    path('clients/', views.client_metrics, name='client_metrics'),
    path('activity/', views.activity_feed, name='activity_feed'),
    path('recalculate/', views.recalculate_metrics, name='recalculate_metrics'),

    # AI Insights, Export, and Bulk Operations
    path('insights/', AIInsightsView.as_view(), name='ai-insights'),
    path('export/', ExportReportView.as_view(), name='export-report'),
    path('bulk/invoices/', BulkInvoiceActionView.as_view(), name='bulk-invoices'),
    path('bulk/clients/', BulkClientActionView.as_view(), name='bulk-clients'),
    path('forecast/', RevenueForecastView.as_view(), name='revenue-forecast'),

    # ViewSets
    path('', include(router.urls)),
]
