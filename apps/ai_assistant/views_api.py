"""
API views for the ai_assistant app.
"""

import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Avg
from django.utils import timezone
from rest_framework import mixins, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from django_filters.rest_framework import DjangoFilterBackend

from .models import AISuggestion, CashFlowPrediction, AIInsight
from .serializers import (
    AISuggestionSerializer,
    CashFlowPredictionSerializer,
    AIInsightSerializer,
)

logger = logging.getLogger(__name__)


class AISuggestionViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          GenericViewSet):
    """
    ViewSet for AI suggestions.

    list: Get list of AI suggestions for the current user
    retrieve: Get a specific AI suggestion
    accept: Accept a suggestion
    dismiss: Dismiss a suggestion
    generate: Generate new AI suggestions based on user data
    """

    serializer_class = AISuggestionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['suggestion_type', 'status', 'priority', 'client']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter suggestions to the current user."""
        return AISuggestion.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept an AI suggestion.

        Sets the suggestion status to ACCEPTED and records the timestamp.
        """
        suggestion = self.get_object()
        suggestion.status = AISuggestion.ACCEPTED
        suggestion.accepted_at = timezone.now()
        suggestion.save()

        serializer = self.get_serializer(suggestion)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """
        Dismiss an AI suggestion.

        Sets the suggestion status to DISMISSED and records the timestamp.
        """
        suggestion = self.get_object()
        suggestion.status = AISuggestion.DISMISSED
        suggestion.dismissed_at = timezone.now()
        suggestion.save()

        serializer = self.get_serializer(suggestion)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate AI suggestions based on the user's data.

        Analyzes overdue invoices, clients not contacted recently,
        and contracts expiring soon to create actionable suggestions.
        """
        user = request.user
        now = timezone.now()
        created_suggestions = []

        # 1. Check for overdue invoices and create INVOICE_REMINDER suggestions
        try:
            from apps.invoicing.models import Invoice

            overdue_invoices = Invoice.objects.filter(
                client__owner=user,
                status__in=[Invoice.SENT, Invoice.VIEWED, Invoice.PARTIALLY_PAID],
                due_date__lt=now.date()
            )

            for invoice in overdue_invoices:
                days_overdue = (now.date() - invoice.due_date).days
                suggestion = AISuggestion.objects.create(
                    suggestion_type=AISuggestion.INVOICE_REMINDER,
                    title=f"Overdue invoice {invoice.invoice_number}",
                    description=(
                        f"Invoice {invoice.invoice_number} for "
                        f"{invoice.client.get_display_name()} is {days_overdue} "
                        f"days overdue. Balance due: {invoice.balance_due} "
                        f"{invoice.currency}."
                    ),
                    detail={
                        'invoice_id': str(invoice.id),
                        'invoice_number': invoice.invoice_number,
                        'days_overdue': days_overdue,
                        'balance_due': str(invoice.balance_due),
                    },
                    priority=AISuggestion.HIGH if days_overdue > 14 else AISuggestion.MEDIUM,
                    user=user,
                    client=invoice.client,
                    invoice=invoice,
                    expires_at=now + timedelta(days=7),
                )
                created_suggestions.append(suggestion)
        except Exception as e:
            logger.warning(f"Error generating invoice reminder suggestions: {e}")

        # 2. Check for clients not contacted in 14+ days and create FOLLOW_UP suggestions
        try:
            from apps.clients.models import Client, ClientNote

            owned_clients = Client.objects.filter(
                owner=user,
                is_active=True,
                lifecycle_stage__in=[Client.ACTIVE, Client.PROSPECT]
            )

            cutoff_date = now - timedelta(days=14)

            for client in owned_clients:
                latest_note = ClientNote.objects.filter(
                    client=client
                ).order_by('-created_at').first()

                if latest_note is None or latest_note.created_at < cutoff_date:
                    days_since = (
                        (now - latest_note.created_at).days
                        if latest_note
                        else None
                    )
                    description = (
                        f"No contact with {client.get_display_name()} "
                        f"in {days_since} days."
                        if days_since
                        else f"No recorded contact with {client.get_display_name()}."
                    )
                    suggestion = AISuggestion.objects.create(
                        suggestion_type=AISuggestion.FOLLOW_UP,
                        title=f"Follow up with {client.get_display_name()}",
                        description=description,
                        detail={
                            'client_id': str(client.id),
                            'days_since_contact': days_since,
                        },
                        priority=AISuggestion.MEDIUM,
                        user=user,
                        client=client,
                        expires_at=now + timedelta(days=7),
                    )
                    created_suggestions.append(suggestion)
        except Exception as e:
            logger.warning(f"Error generating follow-up suggestions: {e}")

        # 3. Check for contracts expiring within 30 days and create CONTRACT_DRAFT suggestions
        try:
            from apps.contracts.models import Contract

            expiring_contracts = Contract.objects.filter(
                owner=user,
                status=Contract.ACTIVE,
                end_date__isnull=False,
                end_date__lte=(now + timedelta(days=30)).date(),
                end_date__gte=now.date(),
            )

            for contract in expiring_contracts:
                days_until_expiry = (contract.end_date - now.date()).days
                suggestion = AISuggestion.objects.create(
                    suggestion_type=AISuggestion.CONTRACT_DRAFT,
                    title=f"Contract {contract.contract_number} expiring soon",
                    description=(
                        f"Contract \"{contract.title}\" with "
                        f"{contract.client.get_display_name()} expires in "
                        f"{days_until_expiry} days. Consider drafting a renewal."
                    ),
                    detail={
                        'contract_id': str(contract.id),
                        'contract_number': contract.contract_number,
                        'days_until_expiry': days_until_expiry,
                        'end_date': str(contract.end_date),
                    },
                    priority=AISuggestion.HIGH if days_until_expiry <= 7 else AISuggestion.MEDIUM,
                    user=user,
                    client=contract.client,
                    contract=contract,
                    expires_at=now + timedelta(days=days_until_expiry),
                )
                created_suggestions.append(suggestion)
        except Exception as e:
            logger.warning(f"Error generating contract draft suggestions: {e}")

        serializer = self.get_serializer(created_suggestions, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CashFlowPredictionViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                GenericViewSet):
    """
    ViewSet for cash flow predictions.

    list: Get list of cash flow predictions for the current user
    retrieve: Get a specific cash flow prediction
    predict: Generate cash flow predictions for the next 30 days
    """

    serializer_class = CashFlowPredictionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {'prediction_date': ['gte', 'lte', 'exact']}
    ordering_fields = ['prediction_date', 'created_at']
    ordering = ['-prediction_date']

    def get_queryset(self):
        """Filter predictions to the current user."""
        return CashFlowPrediction.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def predict(self, request):
        """
        Generate cash flow predictions for the next 30 days.

        Analyzes upcoming invoice due dates for predicted income
        and historical expense averages for predicted expenses.
        Creates CashFlowPrediction records for each day.
        """
        user = request.user
        now = timezone.now()
        today = now.date()
        predictions = []

        # Calculate average historical daily expenses
        try:
            from apps.invoicing.models import Invoice

            # Get paid invoices from the last 90 days as a proxy for expenses
            ninety_days_ago = today - timedelta(days=90)
            historical_expenses = Invoice.objects.filter(
                client__owner=user,
                status=Invoice.PAID,
                paid_at__date__gte=ninety_days_ago,
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')

            avg_daily_expense = historical_expenses / Decimal('90')
        except Exception as e:
            logger.warning(f"Error calculating historical expenses: {e}")
            avg_daily_expense = Decimal('0.00')

        # Generate predictions for each of the next 30 days
        for day_offset in range(1, 31):
            prediction_date = today + timedelta(days=day_offset)

            # Check if a prediction already exists for this date
            existing = CashFlowPrediction.objects.filter(
                user=user,
                prediction_date=prediction_date,
            ).first()

            if existing:
                predictions.append(existing)
                continue

            # Calculate predicted income from invoices due on this date
            try:
                from apps.invoicing.models import Invoice

                predicted_income = Invoice.objects.filter(
                    client__owner=user,
                    status__in=[Invoice.SENT, Invoice.VIEWED, Invoice.PARTIALLY_PAID],
                    due_date=prediction_date,
                ).aggregate(
                    total=Sum('balance_due')
                )['total'] or Decimal('0.00')

                # If aggregate on property doesn't work, compute manually
                if predicted_income == Decimal('0.00'):
                    due_invoices = Invoice.objects.filter(
                        client__owner=user,
                        status__in=[Invoice.SENT, Invoice.VIEWED, Invoice.PARTIALLY_PAID],
                        due_date=prediction_date,
                    )
                    predicted_income = sum(
                        inv.balance_due for inv in due_invoices
                    )
            except Exception as e:
                logger.warning(f"Error calculating predicted income for {prediction_date}: {e}")
                predicted_income = Decimal('0.00')

            predicted_expenses = avg_daily_expense
            predicted_net = predicted_income - predicted_expenses

            # Calculate confidence score based on data availability
            days_out = day_offset
            confidence = max(Decimal('0.00'), Decimal('1.00') - (Decimal(str(days_out)) * Decimal('0.02')))

            factors = []
            if predicted_income > 0:
                factors.append(f"Invoices due on {prediction_date}")
            if avg_daily_expense > 0:
                factors.append("Historical 90-day expense average")

            prediction = CashFlowPrediction.objects.create(
                prediction_date=prediction_date,
                predicted_income=predicted_income,
                predicted_expenses=predicted_expenses,
                predicted_net=predicted_net,
                confidence_score=min(confidence, Decimal('1.00')),
                factors=factors,
                user=user,
            )
            predictions.append(prediction)

        serializer = self.get_serializer(predictions, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AIInsightViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       GenericViewSet):
    """
    ViewSet for AI insights.

    list: Get list of AI insights for the current user
    retrieve: Get a specific AI insight
    mark_read: Mark a single insight as read
    mark_all_read: Mark all unread insights as read
    """

    serializer_class = AIInsightSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['insight_type', 'severity', 'is_read']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter insights to the current user."""
        return AIInsight.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """
        Mark an insight as read.
        """
        insight = self.get_object()
        insight.mark_as_read()

        serializer = self.get_serializer(insight)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        Mark all unread insights as read for the current user.
        """
        now = timezone.now()
        updated_count = AIInsight.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=now
        )

        return Response({
            'detail': f'{updated_count} insights marked as read.',
            'updated_count': updated_count,
        })
