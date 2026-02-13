"""
Serializers for the ai_assistant app.
"""

from rest_framework import serializers
from .models import AISuggestion, CashFlowPrediction, AIInsight


class AISuggestionSerializer(serializers.ModelSerializer):
    """
    Serializer for AI suggestions.
    """
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = AISuggestion
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class CashFlowPredictionSerializer(serializers.ModelSerializer):
    """
    Serializer for cash flow predictions.
    """
    actual_net = serializers.SerializerMethodField()

    class Meta:
        model = CashFlowPrediction
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_actual_net(self, obj):
        """Get the actual net cash flow value."""
        actual = obj.actual_net
        if actual is not None:
            return str(actual)
        return None


class AIInsightSerializer(serializers.ModelSerializer):
    """
    Serializer for AI insights.
    """

    class Meta:
        model = AIInsight
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
