"""
Views for the ai_assistant app.

Re-exports from views_api for convenience.
"""

from .views_api import (  # noqa: F401
    AISuggestionViewSet,
    CashFlowPredictionViewSet,
    AIInsightViewSet,
)
