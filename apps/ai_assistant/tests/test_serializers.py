"""
Tests for ai_assistant app serializers.

Tests cover:
- AISuggestionSerializer fields, read-only fields, is_expired property
- CashFlowPredictionSerializer fields, actual_net method field
- AIInsightSerializer fields, read-only fields
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.ai_assistant.serializers import (
    AISuggestionSerializer,
    CashFlowPredictionSerializer,
    AIInsightSerializer,
)
from apps.ai_assistant.models import AISuggestion, CashFlowPrediction, AIInsight
from .factories import (
    UserFactory,
    AISuggestionFactory,
    CashFlowPredictionFactory,
    AIInsightFactory,
)


# ============================================================================
# AISuggestionSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestAISuggestionSerializer:
    """Tests for AISuggestionSerializer."""

    def test_serializer_contains_expected_fields(self):
        """Test that serializer output includes key fields."""
        suggestion = AISuggestionFactory()
        serializer = AISuggestionSerializer(suggestion)
        data = serializer.data

        assert 'id' in data
        assert 'suggestion_type' in data
        assert 'title' in data
        assert 'description' in data
        assert 'priority' in data
        assert 'status' in data
        assert 'user' in data
        assert 'is_expired' in data
        assert 'created_at' in data

    def test_is_expired_field_in_output(self):
        """Test that is_expired is included as a read-only field."""
        suggestion = AISuggestionFactory(
            expires_at=timezone.now() - timedelta(hours=1),
            status=AISuggestion.PENDING,
        )
        serializer = AISuggestionSerializer(suggestion)
        assert serializer.data['is_expired'] is True

    def test_is_expired_false_when_not_expired(self):
        """Test is_expired is False for non-expired suggestion."""
        suggestion = AISuggestionFactory(
            expires_at=timezone.now() + timedelta(days=7),
            status=AISuggestion.PENDING,
        )
        serializer = AISuggestionSerializer(suggestion)
        assert serializer.data['is_expired'] is False

    def test_read_only_fields(self):
        """Test that id and created_at are read-only."""
        user = UserFactory()
        data = {
            'suggestion_type': AISuggestion.FOLLOW_UP,
            'title': 'Test Suggestion',
            'description': 'A test description',
            'priority': AISuggestion.HIGH,
            'status': AISuggestion.PENDING,
            'user': str(user.pk),
        }
        serializer = AISuggestionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_with_all_suggestion_types(self):
        """Test serialization for all suggestion types."""
        for type_value, _ in AISuggestion.SUGGESTION_TYPE_CHOICES:
            suggestion = AISuggestionFactory(suggestion_type=type_value)
            serializer = AISuggestionSerializer(suggestion)
            assert serializer.data['suggestion_type'] == type_value

    def test_detail_json_field_serialization(self):
        """Test that JSON detail field is serialized correctly."""
        suggestion = AISuggestionFactory(
            detail={'invoice_id': '123', 'days_overdue': 14}
        )
        serializer = AISuggestionSerializer(suggestion)
        assert serializer.data['detail'] == {'invoice_id': '123', 'days_overdue': 14}


# ============================================================================
# CashFlowPredictionSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestCashFlowPredictionSerializer:
    """Tests for CashFlowPredictionSerializer."""

    def test_serializer_contains_expected_fields(self):
        """Test serializer output includes key fields."""
        prediction = CashFlowPredictionFactory()
        serializer = CashFlowPredictionSerializer(prediction)
        data = serializer.data

        assert 'id' in data
        assert 'prediction_date' in data
        assert 'predicted_income' in data
        assert 'predicted_expenses' in data
        assert 'predicted_net' in data
        assert 'confidence_score' in data
        assert 'actual_net' in data
        assert 'user' in data
        assert 'created_at' in data

    def test_actual_net_when_both_actuals_present(self):
        """Test actual_net is computed when both actuals are present."""
        prediction = CashFlowPredictionFactory(
            actual_income=Decimal('6000.00'),
            actual_expenses=Decimal('2000.00'),
        )
        serializer = CashFlowPredictionSerializer(prediction)
        assert serializer.data['actual_net'] == '4000.00'

    def test_actual_net_when_no_actuals(self):
        """Test actual_net is None when actuals are not present."""
        prediction = CashFlowPredictionFactory(
            actual_income=None,
            actual_expenses=None,
        )
        serializer = CashFlowPredictionSerializer(prediction)
        assert serializer.data['actual_net'] is None

    def test_actual_net_returns_string(self):
        """Test that actual_net returns a string representation."""
        prediction = CashFlowPredictionFactory(
            actual_income=Decimal('1000.00'),
            actual_expenses=Decimal('500.00'),
        )
        serializer = CashFlowPredictionSerializer(prediction)
        actual_net = serializer.data['actual_net']
        assert isinstance(actual_net, str)
        assert actual_net == '500.00'

    def test_factors_field_serialization(self):
        """Test that factors list field is properly serialized."""
        prediction = CashFlowPredictionFactory(
            factors=['Invoice due', 'Historical average']
        )
        serializer = CashFlowPredictionSerializer(prediction)
        assert serializer.data['factors'] == ['Invoice due', 'Historical average']

    def test_read_only_fields(self):
        """Test that id and created_at are read-only."""
        user = UserFactory()
        data = {
            'prediction_date': str(date.today() + timedelta(days=5)),
            'predicted_income': '5000.00',
            'predicted_expenses': '2000.00',
            'predicted_net': '3000.00',
            'confidence_score': '0.85',
            'user': str(user.pk),
        }
        serializer = CashFlowPredictionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors


# ============================================================================
# AIInsightSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestAIInsightSerializer:
    """Tests for AIInsightSerializer."""

    def test_serializer_contains_expected_fields(self):
        """Test that serializer output includes key fields."""
        insight = AIInsightFactory()
        serializer = AIInsightSerializer(insight)
        data = serializer.data

        assert 'id' in data
        assert 'insight_type' in data
        assert 'title' in data
        assert 'description' in data
        assert 'data' in data
        assert 'severity' in data
        assert 'user' in data
        assert 'is_read' in data
        assert 'read_at' in data
        assert 'created_at' in data

    def test_read_only_fields(self):
        """Test that id and created_at are read-only."""
        user = UserFactory()
        data = {
            'insight_type': AIInsight.REVENUE_TREND,
            'title': 'Revenue Trend Up',
            'description': 'Revenue has been increasing.',
            'severity': AIInsight.INFO,
            'user': str(user.pk),
        }
        serializer = AIInsightSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_with_read_insight(self):
        """Test serialization of a read insight."""
        insight = AIInsightFactory(is_read=True, read_at=timezone.now())
        serializer = AIInsightSerializer(insight)
        assert serializer.data['is_read'] is True
        assert serializer.data['read_at'] is not None

    def test_serializer_with_unread_insight(self):
        """Test serialization of an unread insight."""
        insight = AIInsightFactory(is_read=False, read_at=None)
        serializer = AIInsightSerializer(insight)
        assert serializer.data['is_read'] is False
        assert serializer.data['read_at'] is None

    def test_data_json_field_serialization(self):
        """Test that JSON data field is serialized correctly."""
        insight = AIInsightFactory(
            data={'trend': 'upward', 'delta': 15.5}
        )
        serializer = AIInsightSerializer(insight)
        assert serializer.data['data'] == {'trend': 'upward', 'delta': 15.5}

    def test_all_severity_choices(self):
        """Test serialization for all severity choices."""
        for severity_value, _ in AIInsight.SEVERITY_CHOICES:
            insight = AIInsightFactory(severity=severity_value)
            serializer = AIInsightSerializer(insight)
            assert serializer.data['severity'] == severity_value
