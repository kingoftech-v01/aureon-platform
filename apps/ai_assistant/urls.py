"""
URL configuration for ai_assistant app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AISuggestionViewSet, CashFlowPredictionViewSet, AIInsightViewSet
from .views_frontend import (
    AIDashboardView,
    SuggestionListView,
    SuggestionDetailView,
    CashFlowPredictionView,
    InsightListView,
    InsightDetailView,
)

app_name = 'ai_assistant'

# API Router
router = DefaultRouter()
router.register(r'ai-suggestions', AISuggestionViewSet, basename='ai-suggestion')
router.register(r'cash-flow-predictions', CashFlowPredictionViewSet, basename='cash-flow-prediction')
router.register(r'ai-insights', AIInsightViewSet, basename='ai-insight')

api_urlpatterns = [
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('', AIDashboardView.as_view(), name='dashboard'),
    path('suggestions/', SuggestionListView.as_view(), name='suggestion_list'),
    path('suggestions/<uuid:pk>/', SuggestionDetailView.as_view(), name='suggestion_detail'),
    path('predictions/', CashFlowPredictionView.as_view(), name='cash_flow_predictions'),
    path('insights/', InsightListView.as_view(), name='insight_list'),
    path('insights/<uuid:pk>/', InsightDetailView.as_view(), name='insight_detail'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
