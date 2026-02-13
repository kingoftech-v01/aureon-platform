"""
Views and ViewSets for the payments app API.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from .models import Payment, PaymentMethod
from .serializers import PaymentSerializer, PaymentMethodSerializer, PaymentStatsSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Payment CRUD operations.
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['invoice', 'status', 'payment_method']
    search_fields = ['transaction_id', 'invoice__invoice_number']
    ordering_fields = ['created_at', 'payment_date', 'amount']
    ordering = ['-payment_date']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset().select_related('invoice', 'invoice__client')

        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(invoice__client__owner=self.request.user) |
                Q(invoice__client__owner__isnull=True)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get payment statistics."""
        queryset = self.filter_queryset(self.get_queryset())

        stats = {
            'total_payments': queryset.count(),
            'successful_payments': queryset.filter(status=Payment.SUCCEEDED).count(),
            'failed_payments': queryset.filter(status=Payment.FAILED).count(),
            'refunded_payments': queryset.filter(status=Payment.REFUNDED).count(),
            'total_amount': queryset.filter(status=Payment.SUCCEEDED).aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_refunded': queryset.aggregate(Sum('refunded_amount'))['refunded_amount__sum'] or 0,
        }

        serializer = PaymentStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Refund a payment.

        Expects: {
            "refund_amount": 100.00,
            "reason": "Customer request"
        }
        """
        payment = self.get_object()
        refund_amount = request.data.get('refund_amount')
        reason = request.data.get('reason')

        if not refund_amount:
            return Response(
                {'detail': 'Refund amount is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from decimal import Decimal, InvalidOperation
            refund_amount = Decimal(str(refund_amount))
            payment.process_refund(refund_amount, reason)

            serializer = self.get_serializer(payment)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': f'Failed to process refund: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PaymentMethod CRUD operations.
    """

    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client', 'type', 'is_default', 'is_active']
    ordering = ['-is_default', '-created_at']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset().select_related('client')

        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(client__owner=self.request.user) |
                Q(client__owner__isnull=True)
            )

        return queryset
