"""
Factory Boy factories for the ai_assistant app.
"""

import factory
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.accounts.models import User
from apps.ai_assistant.models import AISuggestion, CashFlowPrediction, AIInsight


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f'aiuser{n}@test.com')
    username = factory.Sequence(lambda n: f'aiuser{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    full_name = factory.LazyAttribute(lambda o: f'{o.first_name} {o.last_name}')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_active = True
    role = User.ADMIN


class AISuggestionFactory(factory.django.DjangoModelFactory):
    """Factory for creating AISuggestion instances."""

    class Meta:
        model = AISuggestion

    suggestion_type = AISuggestion.FOLLOW_UP
    title = factory.Sequence(lambda n: f'AI Suggestion {n}')
    description = factory.Faker('sentence')
    detail = factory.LazyFunction(dict)
    priority = AISuggestion.MEDIUM
    status = AISuggestion.PENDING
    user = factory.SubFactory(UserFactory)
    client = None
    contract = None
    invoice = None
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    metadata = factory.LazyFunction(dict)


class CashFlowPredictionFactory(factory.django.DjangoModelFactory):
    """Factory for creating CashFlowPrediction instances."""

    class Meta:
        model = CashFlowPrediction

    prediction_date = factory.LazyFunction(lambda: date.today() + timedelta(days=1))
    predicted_income = Decimal('5000.00')
    predicted_expenses = Decimal('2000.00')
    predicted_net = Decimal('3000.00')
    confidence_score = Decimal('0.85')
    actual_income = None
    actual_expenses = None
    factors = factory.LazyFunction(lambda: ['Historical average', 'Upcoming invoices'])
    user = factory.SubFactory(UserFactory)


class AIInsightFactory(factory.django.DjangoModelFactory):
    """Factory for creating AIInsight instances."""

    class Meta:
        model = AIInsight

    insight_type = AIInsight.REVENUE_TREND
    title = factory.Sequence(lambda n: f'AI Insight {n}')
    description = factory.Faker('sentence')
    data = factory.LazyFunction(lambda: {'trend': 'upward', 'percentage': 15})
    severity = AIInsight.INFO
    user = factory.SubFactory(UserFactory)
    is_read = False
    read_at = None
