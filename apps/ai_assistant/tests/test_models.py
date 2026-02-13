"""
Tests for ai_assistant app models.

Tests cover:
- AISuggestion model creation, __str__, is_expired property
- CashFlowPrediction model creation, __str__, actual_net, accuracy properties
- AIInsight model creation, __str__, mark_as_read method
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.ai_assistant.models import AISuggestion, CashFlowPrediction, AIInsight
from .factories import (
    UserFactory,
    AISuggestionFactory,
    CashFlowPredictionFactory,
    AIInsightFactory,
)


# ============================================================================
# AISuggestion Model Tests
# ============================================================================

@pytest.mark.django_db
class TestAISuggestionModel:
    """Tests for the AISuggestion model."""

    def test_create_suggestion(self):
        """Test creating an AI suggestion with required fields."""
        suggestion = AISuggestionFactory()
        assert suggestion.pk is not None
        assert suggestion.suggestion_type == AISuggestion.FOLLOW_UP
        assert suggestion.status == AISuggestion.PENDING
        assert suggestion.priority == AISuggestion.MEDIUM

    def test_str_representation(self):
        """Test __str__ returns title and type."""
        suggestion = AISuggestionFactory(
            title='Follow up with Acme',
            suggestion_type=AISuggestion.FOLLOW_UP,
        )
        assert str(suggestion) == 'Follow up with Acme (follow_up)'

    def test_str_with_different_types(self):
        """Test __str__ for different suggestion types."""
        suggestion = AISuggestionFactory(
            title='Overdue Invoice',
            suggestion_type=AISuggestion.INVOICE_REMINDER,
        )
        assert str(suggestion) == 'Overdue Invoice (invoice_reminder)'

    def test_is_expired_when_past_expires_at_and_pending(self):
        """Test is_expired returns True when expires_at is in the past and status is pending."""
        suggestion = AISuggestionFactory(
            expires_at=timezone.now() - timedelta(hours=1),
            status=AISuggestion.PENDING,
        )
        assert suggestion.is_expired is True

    def test_is_expired_when_future_expires_at(self):
        """Test is_expired returns False when expires_at is in the future."""
        suggestion = AISuggestionFactory(
            expires_at=timezone.now() + timedelta(days=7),
            status=AISuggestion.PENDING,
        )
        assert suggestion.is_expired is False

    def test_is_expired_when_no_expires_at(self):
        """Test is_expired returns False when expires_at is None."""
        suggestion = AISuggestionFactory(expires_at=None)
        assert suggestion.is_expired is False

    def test_is_expired_when_accepted(self):
        """Test is_expired returns False when status is accepted, even if past expires_at."""
        suggestion = AISuggestionFactory(
            expires_at=timezone.now() - timedelta(hours=1),
            status=AISuggestion.ACCEPTED,
        )
        assert suggestion.is_expired is False

    def test_is_expired_when_dismissed(self):
        """Test is_expired returns False when status is dismissed."""
        suggestion = AISuggestionFactory(
            expires_at=timezone.now() - timedelta(hours=1),
            status=AISuggestion.DISMISSED,
        )
        assert suggestion.is_expired is False

    def test_suggestion_type_choices(self):
        """Test all suggestion type choices can be set."""
        user = UserFactory()
        for type_value, _ in AISuggestion.SUGGESTION_TYPE_CHOICES:
            suggestion = AISuggestionFactory(
                user=user,
                suggestion_type=type_value,
            )
            assert suggestion.suggestion_type == type_value

    def test_priority_choices(self):
        """Test all priority choices."""
        for priority_value, _ in AISuggestion.PRIORITY_CHOICES:
            suggestion = AISuggestionFactory(priority=priority_value)
            assert suggestion.priority == priority_value

    def test_default_ordering(self):
        """Test that suggestions are ordered by -created_at."""
        user = UserFactory()
        s1 = AISuggestionFactory(user=user, title='First')
        s2 = AISuggestionFactory(user=user, title='Second')
        suggestions = list(AISuggestion.objects.filter(user=user))
        assert suggestions[0] == s2
        assert suggestions[1] == s1

    def test_json_fields_default(self):
        """Test that JSON fields have correct defaults."""
        suggestion = AISuggestionFactory()
        assert suggestion.detail == {}
        assert suggestion.metadata == {}


# ============================================================================
# CashFlowPrediction Model Tests
# ============================================================================

@pytest.mark.django_db
class TestCashFlowPredictionModel:
    """Tests for the CashFlowPrediction model."""

    def test_create_prediction(self):
        """Test creating a cash flow prediction."""
        prediction = CashFlowPredictionFactory()
        assert prediction.pk is not None
        assert prediction.predicted_income == Decimal('5000.00')
        assert prediction.predicted_expenses == Decimal('2000.00')
        assert prediction.predicted_net == Decimal('3000.00')

    def test_str_representation(self):
        """Test __str__ returns prediction date and net."""
        pred_date = date(2026, 3, 15)
        prediction = CashFlowPredictionFactory(
            prediction_date=pred_date,
            predicted_net=Decimal('1500.00'),
        )
        assert str(prediction) == 'Prediction for 2026-03-15: net 1500.00'

    def test_actual_net_with_both_actuals(self):
        """Test actual_net property when both actuals are available."""
        prediction = CashFlowPredictionFactory(
            actual_income=Decimal('6000.00'),
            actual_expenses=Decimal('2500.00'),
        )
        assert prediction.actual_net == Decimal('3500.00')

    def test_actual_net_with_no_actuals(self):
        """Test actual_net returns None when actuals are not available."""
        prediction = CashFlowPredictionFactory(
            actual_income=None,
            actual_expenses=None,
        )
        assert prediction.actual_net is None

    def test_actual_net_with_only_income(self):
        """Test actual_net returns None when only income is available."""
        prediction = CashFlowPredictionFactory(
            actual_income=Decimal('6000.00'),
            actual_expenses=None,
        )
        assert prediction.actual_net is None

    def test_actual_net_with_only_expenses(self):
        """Test actual_net returns None when only expenses are available."""
        prediction = CashFlowPredictionFactory(
            actual_income=None,
            actual_expenses=Decimal('2000.00'),
        )
        assert prediction.actual_net is None

    def test_accuracy_when_prediction_matches(self):
        """Test accuracy when prediction matches actual perfectly."""
        prediction = CashFlowPredictionFactory(
            predicted_net=Decimal('3000.00'),
            actual_income=Decimal('5000.00'),
            actual_expenses=Decimal('2000.00'),
        )
        # actual_net = 3000.00, predicted_net = 3000.00
        # accuracy = 1 - |3000 - 3000| / |3000| = 1.0
        assert prediction.accuracy == Decimal('1')

    def test_accuracy_when_prediction_differs(self):
        """Test accuracy when prediction differs from actual."""
        prediction = CashFlowPredictionFactory(
            predicted_net=Decimal('4000.00'),
            actual_income=Decimal('5000.00'),
            actual_expenses=Decimal('2000.00'),
        )
        # actual_net = 3000.00, predicted_net = 4000.00
        # accuracy = 1 - |4000 - 3000| / |3000| = 1 - 1/3 ~= 0.6667
        expected = 1 - abs(Decimal('4000.00') - Decimal('3000.00')) / abs(Decimal('3000.00'))
        assert prediction.accuracy == expected

    def test_accuracy_when_no_actuals(self):
        """Test accuracy returns None when actuals are not available."""
        prediction = CashFlowPredictionFactory(
            actual_income=None,
            actual_expenses=None,
        )
        assert prediction.accuracy is None

    def test_accuracy_when_actual_net_is_zero(self):
        """Test accuracy returns None when actual net is zero (avoid division by zero)."""
        prediction = CashFlowPredictionFactory(
            predicted_net=Decimal('1000.00'),
            actual_income=Decimal('2000.00'),
            actual_expenses=Decimal('2000.00'),
        )
        # actual_net = 0, so accuracy should be None
        assert prediction.accuracy is None

    def test_unique_together_user_prediction_date(self):
        """Test that user + prediction_date must be unique."""
        user = UserFactory()
        pred_date = date(2026, 4, 1)
        CashFlowPredictionFactory(user=user, prediction_date=pred_date)

        with pytest.raises(Exception):
            CashFlowPredictionFactory(user=user, prediction_date=pred_date)

    def test_confidence_score_bounds(self):
        """Test confidence score validators."""
        prediction = CashFlowPredictionFactory(confidence_score=Decimal('0.95'))
        assert prediction.confidence_score == Decimal('0.95')


# ============================================================================
# AIInsight Model Tests
# ============================================================================

@pytest.mark.django_db
class TestAIInsightModel:
    """Tests for the AIInsight model."""

    def test_create_insight(self):
        """Test creating an AI insight."""
        insight = AIInsightFactory()
        assert insight.pk is not None
        assert insight.insight_type == AIInsight.REVENUE_TREND
        assert insight.severity == AIInsight.INFO
        assert insight.is_read is False

    def test_str_representation(self):
        """Test __str__ returns title and severity."""
        insight = AIInsightFactory(
            title='Revenue is growing',
            severity=AIInsight.INFO,
        )
        assert str(insight) == 'Revenue is growing (info)'

    def test_str_with_warning_severity(self):
        """Test __str__ for warning severity."""
        insight = AIInsightFactory(
            title='Late payments detected',
            severity=AIInsight.WARNING,
        )
        assert str(insight) == 'Late payments detected (warning)'

    def test_str_with_critical_severity(self):
        """Test __str__ for critical severity."""
        insight = AIInsightFactory(
            title='Client at risk',
            severity=AIInsight.CRITICAL,
        )
        assert str(insight) == 'Client at risk (critical)'

    def test_mark_as_read(self):
        """Test mark_as_read sets is_read and read_at."""
        insight = AIInsightFactory(is_read=False, read_at=None)
        assert insight.is_read is False
        assert insight.read_at is None

        insight.mark_as_read()

        insight.refresh_from_db()
        assert insight.is_read is True
        assert insight.read_at is not None

    def test_mark_as_read_sets_timestamp(self):
        """Test mark_as_read sets read_at to approximately now."""
        insight = AIInsightFactory()
        before = timezone.now()
        insight.mark_as_read()
        after = timezone.now()

        insight.refresh_from_db()
        assert before <= insight.read_at <= after

    def test_insight_type_choices(self):
        """Test all insight type choices."""
        user = UserFactory()
        for type_value, _ in AIInsight.INSIGHT_TYPE_CHOICES:
            insight = AIInsightFactory(user=user, insight_type=type_value)
            assert insight.insight_type == type_value

    def test_severity_choices(self):
        """Test all severity choices."""
        for severity_value, _ in AIInsight.SEVERITY_CHOICES:
            insight = AIInsightFactory(severity=severity_value)
            assert insight.severity == severity_value

    def test_default_ordering(self):
        """Test that insights are ordered by -created_at."""
        user = UserFactory()
        i1 = AIInsightFactory(user=user, title='First')
        i2 = AIInsightFactory(user=user, title='Second')
        insights = list(AIInsight.objects.filter(user=user))
        assert insights[0] == i2
        assert insights[1] == i1

    def test_data_json_field_default(self):
        """Test that data field defaults to empty dict."""
        insight = AIInsightFactory(data={})
        assert insight.data == {}
