"""
URL configuration for analytics app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'analytics'

router = DefaultRouter()

urlpatterns = [
    # Analytics API endpoints
    path('dashboard/', views.dashboard_summary, name='dashboard_summary'),
    path('revenue/', views.revenue_metrics, name='revenue_metrics'),
    path('clients/', views.client_metrics, name='client_metrics'),
    path('activity/', views.activity_feed, name='activity_feed'),
    path('recalculate/', views.recalculate_metrics, name='recalculate_metrics'),

    # ViewSets
    path('api/', include(router.urls)),
]
