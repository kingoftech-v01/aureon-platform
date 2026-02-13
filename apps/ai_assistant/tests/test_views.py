"""
Tests for ai_assistant app API views.

Tests cover:
- AISuggestionViewSet: list, retrieve, accept, dismiss, generate, unauthenticated access
- CashFlowPredictionViewSet: list, retrieve, predict, unauthenticated access
- AIInsightViewSet: list, retrieve, mark_read, mark_all_read, unauthenticated access
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from apps.ai_assistant.models import AISuggestion, CashFlowPrediction, AIInsight
from apps.accounts.models import User
from .factories import (
    UserFactory,
    AISuggestionFactory,
    CashFlowPredictionFactory,
    AIInsightFactory,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def user(db):
    """Create a test user."""
    return UserFactory()


@pytest.fixture
def other_user(db):
    """Create another test user."""
    return UserFactory()


@pytest.fixture
def api_client():
    """Create an API client."""
    client = APIClient()
    client.defaults['HTTP_ORIGIN'] = 'http://testserver'
    client.defaults['SERVER_NAME'] = 'testserver'
    return client


@pytest.fixture
def auth_client(api_client, user):
    """Create an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


# ============================================================================
# AISuggestionViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestAISuggestionViewSet:
    """Tests for the AISuggestionViewSet."""

    def test_list_suggestions(self, auth_client, user):
        """Test listing suggestions returns only user's suggestions."""
        AISuggestionFactory(user=user, title='My suggestion')
        AISuggestionFactory(title='Other suggestion')  # different user

        response = auth_client.get('/api/ai/api/ai-suggestions/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'My suggestion'

    def test_list_suggestions_empty(self, auth_client, user):
        """Test listing suggestions when user has none."""
        response = auth_client.get('/api/ai/api/ai-suggestions/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_retrieve_suggestion(self, auth_client, user):
        """Test retrieving a single suggestion."""
        suggestion = AISuggestionFactory(user=user, title='My suggestion')

        response = auth_client.get(f'/api/ai/api/ai-suggestions/{suggestion.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'My suggestion'

    def test_retrieve_other_users_suggestion_returns_404(self, auth_client):
        """Test retrieving another user's suggestion returns 404."""
        other_suggestion = AISuggestionFactory(title='Other suggestion')

        response = auth_client.get(f'/api/ai/api/ai-suggestions/{other_suggestion.pk}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_accept_suggestion(self, auth_client, user):
        """Test accepting a suggestion."""
        suggestion = AISuggestionFactory(user=user, status=AISuggestion.PENDING)

        response = auth_client.post(f'/api/ai/api/ai-suggestions/{suggestion.pk}/accept/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == AISuggestion.ACCEPTED

        suggestion.refresh_from_db()
        assert suggestion.status == AISuggestion.ACCEPTED
        assert suggestion.accepted_at is not None

    def test_dismiss_suggestion(self, auth_client, user):
        """Test dismissing a suggestion."""
        suggestion = AISuggestionFactory(user=user, status=AISuggestion.PENDING)

        response = auth_client.post(f'/api/ai/api/ai-suggestions/{suggestion.pk}/dismiss/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == AISuggestion.DISMISSED

        suggestion.refresh_from_db()
        assert suggestion.status == AISuggestion.DISMISSED
        assert suggestion.dismissed_at is not None

    def test_generate_suggestions(self, auth_client, user):
        """Test generating suggestions (basic - no overdue invoices/clients)."""
        response = auth_client.post('/api/ai/api/ai-suggestions/generate/')
        assert response.status_code == status.HTTP_201_CREATED
        assert isinstance(response.data, list)

    def test_unauthenticated_list(self, api_client):
        """Test that unauthenticated requests are rejected."""
        response = api_client.get('/api/ai/api/ai-suggestions/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_filter_by_status(self, auth_client, user):
        """Test filtering suggestions by status."""
        AISuggestionFactory(user=user, status=AISuggestion.PENDING)
        AISuggestionFactory(user=user, status=AISuggestion.ACCEPTED)

        response = auth_client.get('/api/ai/api/ai-suggestions/', {'status': 'pending'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['status'] == AISuggestion.PENDING

    def test_filter_by_suggestion_type(self, auth_client, user):
        """Test filtering suggestions by type."""
        AISuggestionFactory(user=user, suggestion_type=AISuggestion.FOLLOW_UP)
        AISuggestionFactory(user=user, suggestion_type=AISuggestion.INVOICE_REMINDER)

        response = auth_client.get(
            '/api/ai/api/ai-suggestions/',
            {'suggestion_type': 'follow_up'}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_filter_by_priority(self, auth_client, user):
        """Test filtering suggestions by priority."""
        AISuggestionFactory(user=user, priority=AISuggestion.HIGH)
        AISuggestionFactory(user=user, priority=AISuggestion.LOW)

        response = auth_client.get('/api/ai/api/ai-suggestions/', {'priority': 'high'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['priority'] == AISuggestion.HIGH


# ============================================================================
# CashFlowPredictionViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestCashFlowPredictionViewSet:
    """Tests for the CashFlowPredictionViewSet."""

    def test_list_predictions(self, auth_client, user):
        """Test listing predictions returns only user's predictions."""
        CashFlowPredictionFactory(user=user, prediction_date=date.today() + timedelta(days=1))
        CashFlowPredictionFactory(prediction_date=date.today() + timedelta(days=2))  # different user

        response = auth_client.get('/api/ai/api/cash-flow-predictions/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_list_predictions_empty(self, auth_client, user):
        """Test listing predictions when user has none."""
        response = auth_client.get('/api/ai/api/cash-flow-predictions/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_retrieve_prediction(self, auth_client, user):
        """Test retrieving a single prediction."""
        prediction = CashFlowPredictionFactory(
            user=user,
            prediction_date=date.today() + timedelta(days=1),
        )

        response = auth_client.get(f'/api/ai/api/cash-flow-predictions/{prediction.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['predicted_net'] is not None

    def test_retrieve_other_users_prediction_returns_404(self, auth_client):
        """Test retrieving another user's prediction returns 404."""
        other_prediction = CashFlowPredictionFactory(
            prediction_date=date.today() + timedelta(days=1),
        )

        response = auth_client.get(
            f'/api/ai/api/cash-flow-predictions/{other_prediction.pk}/'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_predict_endpoint(self, auth_client, user):
        """Test generating predictions via the predict endpoint."""
        response = auth_client.post('/api/ai/api/cash-flow-predictions/predict/')
        assert response.status_code == status.HTTP_201_CREATED
        assert isinstance(response.data, list)
        assert len(response.data) == 30

    def test_predict_creates_30_day_predictions(self, auth_client, user):
        """Test that predict creates predictions for next 30 days."""
        auth_client.post('/api/ai/api/cash-flow-predictions/predict/')

        predictions = CashFlowPrediction.objects.filter(user=user)
        assert predictions.count() == 30

    def test_predict_does_not_duplicate(self, auth_client, user):
        """Test that predict does not create duplicates for existing dates."""
        # First call
        auth_client.post('/api/ai/api/cash-flow-predictions/predict/')
        count_after_first = CashFlowPrediction.objects.filter(user=user).count()

        # Second call should not create new predictions
        auth_client.post('/api/ai/api/cash-flow-predictions/predict/')
        count_after_second = CashFlowPrediction.objects.filter(user=user).count()

        assert count_after_first == count_after_second == 30

    def test_unauthenticated_list(self, api_client):
        """Test that unauthenticated requests are rejected."""
        response = api_client.get('/api/ai/api/cash-flow-predictions/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# AIInsightViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestAIInsightViewSet:
    """Tests for the AIInsightViewSet."""

    def test_list_insights(self, auth_client, user):
        """Test listing insights returns only user's insights."""
        AIInsightFactory(user=user, title='My insight')
        AIInsightFactory(title='Other insight')  # different user

        response = auth_client.get('/api/ai/api/ai-insights/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'My insight'

    def test_list_insights_empty(self, auth_client, user):
        """Test listing insights when user has none."""
        response = auth_client.get('/api/ai/api/ai-insights/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_retrieve_insight(self, auth_client, user):
        """Test retrieving a single insight."""
        insight = AIInsightFactory(user=user, title='Revenue Trend')

        response = auth_client.get(f'/api/ai/api/ai-insights/{insight.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Revenue Trend'

    def test_retrieve_other_users_insight_returns_404(self, auth_client):
        """Test retrieving another user's insight returns 404."""
        other_insight = AIInsightFactory(title='Other insight')

        response = auth_client.get(f'/api/ai/api/ai-insights/{other_insight.pk}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_read(self, auth_client, user):
        """Test marking an insight as read."""
        insight = AIInsightFactory(user=user, is_read=False)

        response = auth_client.post(f'/api/ai/api/ai-insights/{insight.pk}/mark-read/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_read'] is True

        insight.refresh_from_db()
        assert insight.is_read is True
        assert insight.read_at is not None

    def test_mark_all_read(self, auth_client, user):
        """Test marking all insights as read."""
        AIInsightFactory(user=user, is_read=False)
        AIInsightFactory(user=user, is_read=False)
        AIInsightFactory(user=user, is_read=True)

        response = auth_client.post('/api/ai/api/ai-insights/mark-all-read/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['updated_count'] == 2

        unread_count = AIInsight.objects.filter(user=user, is_read=False).count()
        assert unread_count == 0

    def test_mark_all_read_when_none_unread(self, auth_client, user):
        """Test marking all as read when none are unread."""
        AIInsightFactory(user=user, is_read=True)

        response = auth_client.post('/api/ai/api/ai-insights/mark-all-read/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['updated_count'] == 0

    def test_filter_by_insight_type(self, auth_client, user):
        """Test filtering insights by type."""
        AIInsightFactory(user=user, insight_type=AIInsight.REVENUE_TREND)
        AIInsightFactory(user=user, insight_type=AIInsight.CLIENT_RISK)

        response = auth_client.get(
            '/api/ai/api/ai-insights/',
            {'insight_type': 'revenue_trend'}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_filter_by_severity(self, auth_client, user):
        """Test filtering insights by severity."""
        AIInsightFactory(user=user, severity=AIInsight.CRITICAL)
        AIInsightFactory(user=user, severity=AIInsight.INFO)

        response = auth_client.get('/api/ai/api/ai-insights/', {'severity': 'critical'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['severity'] == AIInsight.CRITICAL

    def test_filter_by_is_read(self, auth_client, user):
        """Test filtering insights by is_read."""
        AIInsightFactory(user=user, is_read=True)
        AIInsightFactory(user=user, is_read=False)

        response = auth_client.get('/api/ai/api/ai-insights/', {'is_read': 'true'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['is_read'] is True

    def test_unauthenticated_list(self, api_client):
        """Test that unauthenticated requests are rejected."""
        response = api_client.get('/api/ai/api/ai-insights/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
