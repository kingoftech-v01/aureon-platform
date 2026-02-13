"""
URL configuration for analytics app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_frontend import (
    DashboardView,
    RevenueView,
    ClientMetricsView,
    ActivityFeedView,
)

app_name = 'analytics'

router = DefaultRouter()

api_urlpatterns = [
    # Analytics API endpoints
    path('dashboard/', views.dashboard_summary, name='dashboard_summary'),
    path('revenue/', views.revenue_metrics, name='revenue_metrics'),
    path('clients/', views.client_metrics, name='client_metrics'),
    path('activity/', views.activity_feed, name='activity_feed'),
    path('recalculate/', views.recalculate_metrics, name='recalculate_metrics'),

    # ViewSets
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('overview/', DashboardView.as_view(), name='dashboard'),
    path('revenue-report/', RevenueView.as_view(), name='revenue_report'),
    path('client-metrics/', ClientMetricsView.as_view(), name='client_metrics_report'),
    path('activity-feed/', ActivityFeedView.as_view(), name='activity_feed_view'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
