"""
Views and ViewSets for the expenses app API.
"""

import logging
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from .models import ExpenseCategory, Expense
from .serializers import (
    ExpenseCategorySerializer,
    ExpenseListSerializer,
    ExpenseDetailSerializer,
    ExpenseCreateUpdateSerializer,
    ExpenseStatsSerializer,
)

logger = logging.getLogger(__name__)


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ExpenseCategory CRUD operations.

    list: Get list of expense categories
    retrieve: Get category details
    create: Create a new category
    update: Update a category
    partial_update: Partially update a category
    destroy: Delete a category
    """

    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Expense CRUD operations.

    list: Get list of expenses with filtering and search
    retrieve: Get expense details
    create: Create a new expense
    update: Update an expense
    partial_update: Partially update an expense
    destroy: Delete an expense
    """

    queryset = Expense.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'category', 'client', 'contract',
        'is_billable', 'is_invoiced', 'payment_method',
    ]
    search_fields = ['description', 'vendor', 'receipt_number']
    ordering_fields = ['expense_date', 'created_at', 'amount']
    ordering = ['-expense_date', '-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ExpenseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ExpenseCreateUpdateSerializer
        return ExpenseDetailSerializer

    def get_queryset(self):
        """Filter queryset with select_related for performance."""
        queryset = super().get_queryset().select_related(
            'category', 'client', 'contract', 'invoice',
            'submitted_by', 'approved_by',
        )
        return queryset

    def perform_create(self, serializer):
        """Set submitted_by to current user on create."""
        serializer.save(submitted_by=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve an expense.

        Sets status to APPROVED, approved_by to current user, and approved_at to now.
        """
        expense = self.get_object()

        if expense.status != Expense.PENDING:
            return Response(
                {'detail': 'Only pending expenses can be approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        expense.status = Expense.APPROVED
        expense.approved_by = request.user
        expense.approved_at = timezone.now()
        expense.save()

        serializer = ExpenseDetailSerializer(expense, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject an expense.

        Sets status to REJECTED.
        """
        expense = self.get_object()

        if expense.status != Expense.PENDING:
            return Response(
                {'detail': 'Only pending expenses can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        expense.status = Expense.REJECTED
        expense.save()

        serializer = ExpenseDetailSerializer(expense, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-billable')
    def mark_billable(self, request, pk=None):
        """
        Mark an expense as billable.

        Sets is_billable to True.
        """
        expense = self.get_object()
        expense.is_billable = True
        expense.save()

        serializer = ExpenseDetailSerializer(expense, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-invoiced')
    def mark_invoiced(self, request, pk=None):
        """
        Mark an expense as invoiced.

        Sets is_invoiced to True and status to INVOICED.
        Optionally accepts invoice_id in request data to link the invoice.
        """
        expense = self.get_object()
        expense.is_invoiced = True
        expense.status = Expense.INVOICED
        expense.save()

        # Link invoice if provided
        invoice_id = request.data.get('invoice_id')
        if invoice_id:
            try:
                from apps.invoicing.models import Invoice
                invoice = Invoice.objects.get(id=invoice_id)
                expense.invoice = invoice
                expense.save()
            except Exception as e:
                logger.warning(f"Could not link invoice {invoice_id} to expense: {e}")

        serializer = ExpenseDetailSerializer(expense, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get expense statistics.

        Returns total_amount, total_billable, by_status counts, and by_category amounts.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Total amount
        total_amount = queryset.aggregate(
            total=Sum('amount')
        )['total'] or 0

        # Total billable
        total_billable = queryset.filter(
            is_billable=True
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # Total invoiced
        total_invoiced = queryset.filter(
            is_invoiced=True
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # By status counts
        by_status = {}
        status_counts = queryset.order_by().values('status').annotate(count=Count('id'))
        for entry in status_counts:
            by_status[entry['status']] = entry['count']

        # By category amounts
        by_category = list(
            queryset.filter(category__isnull=False).values(
                'category__id', 'category__name'
            ).annotate(
                total=Sum('amount'),
                count=Count('id'),
            ).order_by('-total')
        )
        by_category_formatted = [
            {
                'category_id': str(entry['category__id']),
                'category_name': entry['category__name'],
                'total': entry['total'],
                'count': entry['count'],
            }
            for entry in by_category
        ]

        # By month
        by_month = list(
            queryset.annotate(
                month=TruncMonth('expense_date')
            ).values('month').annotate(
                total=Sum('amount'),
                count=Count('id'),
            ).order_by('-month')
        )
        by_month_formatted = [
            {
                'month': entry['month'].isoformat() if entry['month'] else None,
                'total': entry['total'],
                'count': entry['count'],
            }
            for entry in by_month
        ]

        stats = {
            'total_amount': total_amount,
            'total_billable': total_billable,
            'total_invoiced': total_invoiced,
            'by_category': by_category_formatted,
            'by_status': by_status,
            'by_month': by_month_formatted,
        }

        serializer = ExpenseStatsSerializer(stats)
        return Response(serializer.data)
