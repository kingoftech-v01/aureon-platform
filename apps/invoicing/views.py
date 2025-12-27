"""
Views and ViewSets for the invoicing app API.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from .models import Invoice, InvoiceItem
from .serializers import (
    InvoiceListSerializer,
    InvoiceDetailSerializer,
    InvoiceCreateUpdateSerializer,
    InvoiceItemSerializer,
    InvoiceStatsSerializer,
)
from .filters import InvoiceFilter


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Invoice CRUD operations.

    list: Get list of invoices with filtering and search
    retrieve: Get invoice details with items
    create: Create a new invoice
    update: Update an invoice
    partial_update: Partially update an invoice
    destroy: Delete an invoice
    """

    queryset = Invoice.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InvoiceFilter
    search_fields = ['invoice_number', 'client__first_name', 'client__last_name', 'client__company_name']
    ordering_fields = ['created_at', 'updated_at', 'issue_date', 'due_date', 'total', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return InvoiceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return InvoiceCreateUpdateSerializer
        return InvoiceDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset().select_related('client', 'contract')

        # Optionally filter for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(client__owner=self.request.user) | Q(client__owner__isnull=True)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get invoice statistics.

        Returns total invoices, drafts, sent, paid, overdue, and financial summary.
        """
        queryset = self.filter_queryset(self.get_queryset())

        stats = {
            'total_invoices': queryset.count(),
            'draft_invoices': queryset.filter(status=Invoice.DRAFT).count(),
            'sent_invoices': queryset.filter(status=Invoice.SENT).count(),
            'paid_invoices': queryset.filter(status=Invoice.PAID).count(),
            'overdue_invoices': queryset.filter(status=Invoice.OVERDUE).count(),
            'total_invoiced': queryset.aggregate(Sum('total'))['total__sum'] or 0,
            'total_paid': queryset.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0,
            'total_outstanding': queryset.aggregate(
                outstanding=Sum('total') - Sum('paid_amount')
            )['outstanding'] or 0,
        }

        serializer = InvoiceStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """
        Send invoice to client via email.
        """
        invoice = self.get_object()

        if invoice.status != Invoice.DRAFT:
            return Response(
                {'detail': 'Only draft invoices can be sent.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            invoice.mark_as_sent()

            # TODO: Send email to client with invoice PDF
            # send_invoice_email(invoice)

            serializer = self.get_serializer(invoice)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': f'Failed to send invoice: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """
        Mark invoice as paid.

        Expects: {
            "payment_amount": 1000.00,  (optional, defaults to balance due)
            "payment_method": "card",  (optional)
            "payment_reference": "txn_123"  (optional)
        }
        """
        invoice = self.get_object()

        payment_amount = request.data.get('payment_amount')
        payment_method = request.data.get('payment_method')
        payment_reference = request.data.get('payment_reference')

        try:
            invoice.mark_as_paid(
                payment_amount=payment_amount,
                payment_method=payment_method,
                payment_reference=payment_reference
            )

            serializer = self.get_serializer(invoice)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': f'Failed to mark invoice as paid: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        """
        Generate PDF for invoice.
        """
        invoice = self.get_object()

        try:
            invoice.generate_pdf()

            return Response({
                'detail': 'PDF generated successfully.',
                'pdf_url': invoice.pdf_file.url if invoice.pdf_file else None
            })
        except Exception as e:
            return Response(
                {'detail': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        """
        Recalculate invoice totals from items.
        """
        invoice = self.get_object()

        try:
            invoice.calculate_totals()
            serializer = self.get_serializer(invoice)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': f'Failed to recalculate totals: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """
        Get all items for an invoice.
        """
        invoice = self.get_object()
        items = invoice.items.all()
        serializer = InvoiceItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for InvoiceItem CRUD operations.
    """

    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['invoice']
    ordering = ['order']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset().select_related('invoice')

        # Filter by invoice access
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(invoice__client__owner=self.request.user) |
                Q(invoice__client__owner__isnull=True)
            )

        return queryset

    def perform_create(self, serializer):
        """Recalculate invoice totals after creating item."""
        item = serializer.save()
        item.invoice.calculate_totals()

    def perform_update(self, serializer):
        """Recalculate invoice totals after updating item."""
        item = serializer.save()
        item.invoice.calculate_totals()

    def perform_destroy(self, instance):
        """Recalculate invoice totals after deleting item."""
        invoice = instance.invoice
        instance.delete()
        invoice.calculate_totals()
