"""
Views and ViewSets for the contracts app API.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Avg
from .models import Contract, ContractMilestone
from .serializers import (
    ContractListSerializer,
    ContractDetailSerializer,
    ContractCreateUpdateSerializer,
    ContractMilestoneSerializer,
    ContractStatsSerializer,
)
from .filters import ContractFilter


class ContractViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contract CRUD operations.

    list: Get list of contracts with filtering and search
    retrieve: Get contract details with milestones
    create: Create a new contract
    update: Update a contract
    partial_update: Partially update a contract
    destroy: Delete a contract
    """

    queryset = Contract.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ContractFilter
    search_fields = ['contract_number', 'title', 'client__first_name', 'client__last_name', 'client__company_name']
    ordering_fields = ['created_at', 'updated_at', 'start_date', 'end_date', 'value', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ContractListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ContractCreateUpdateSerializer
        return ContractDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset().select_related('client', 'owner')

        # Optionally filter by owner for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(owner=self.request.user) | Q(owner__isnull=True)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get contract statistics.

        Returns total contracts, active, draft, completed, and financial summary.
        """
        queryset = self.filter_queryset(self.get_queryset())

        stats = {
            'total_contracts': queryset.count(),
            'active_contracts': queryset.filter(status=Contract.ACTIVE).count(),
            'draft_contracts': queryset.filter(status=Contract.DRAFT).count(),
            'completed_contracts': queryset.filter(status=Contract.COMPLETED).count(),
            'total_value': queryset.aggregate(Sum('value'))['value__sum'] or 0,
            'total_invoiced': queryset.aggregate(Sum('invoiced_amount'))['invoiced_amount__sum'] or 0,
            'total_paid': queryset.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0,
            'avg_completion': queryset.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0,
        }

        serializer = ContractStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """
        Sign the contract.

        Expects: { "party": "client" | "company", "signature": "signature_data" }
        """
        contract = self.get_object()
        party = request.data.get('party')
        signature = request.data.get('signature')

        if not party or party not in ['client', 'company']:
            return Response(
                {'detail': 'Invalid party. Must be "client" or "company".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not signature:
            return Response(
                {'detail': 'Signature is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update signature
        if party == 'client':
            contract.signed_by_client = True
            contract.signature_client = signature
        else:
            contract.signed_by_company = True
            contract.signature_company = signature

        # Set signed_at timestamp if both parties signed
        if contract.signed_by_client and contract.signed_by_company and not contract.signed_at:
            from django.utils import timezone
            contract.signed_at = timezone.now()

        contract.save()

        serializer = self.get_serializer(contract)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_financial_summary(self, request, pk=None):
        """
        Update contract financial summary from invoices.
        """
        contract = self.get_object()

        try:
            contract.update_financial_summary()
            serializer = self.get_serializer(contract)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': f'Failed to update financial summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def update_completion(self, request, pk=None):
        """
        Update contract completion percentage from milestones.
        """
        contract = self.get_object()

        try:
            contract.update_completion_percentage()
            serializer = self.get_serializer(contract)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': f'Failed to update completion: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def milestones(self, request, pk=None):
        """
        Get all milestones for a contract.
        """
        contract = self.get_object()
        milestones = contract.milestones.all()
        serializer = ContractMilestoneSerializer(milestones, many=True, context={'request': request})
        return Response(serializer.data)


class ContractMilestoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ContractMilestone CRUD operations.
    """

    queryset = ContractMilestone.objects.all()
    serializer_class = ContractMilestoneSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['contract', 'status', 'invoice_generated']
    ordering = ['order', 'due_date']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset().select_related('contract', 'completed_by')

        # Filter by contract access
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(contract__owner=self.request.user) |
                Q(contract__owner__isnull=True)
            )

        return queryset

    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        """
        Mark milestone as completed.
        """
        milestone = self.get_object()

        if milestone.status == ContractMilestone.COMPLETED:
            return Response(
                {'detail': 'Milestone is already completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils import timezone

        milestone.status = ContractMilestone.COMPLETED
        milestone.completed_at = timezone.now()
        milestone.completed_by = request.user
        milestone.save()

        # Update contract completion percentage
        milestone.contract.update_completion_percentage()

        serializer = self.get_serializer(milestone)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def generate_invoice(self, request, pk=None):
        """
        Generate invoice for milestone.
        """
        milestone = self.get_object()

        if milestone.invoice_generated:
            return Response(
                {'detail': 'Invoice already generated for this milestone.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Import here to avoid circular imports
            from apps.invoicing.models import Invoice, InvoiceItem

            # Create invoice
            invoice = Invoice.objects.create(
                client=milestone.contract.client,
                contract=milestone.contract,
                status='draft',
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timezone.timedelta(days=30),
                notes=f"Invoice for milestone: {milestone.title}"
            )

            # Create invoice item
            InvoiceItem.objects.create(
                invoice=invoice,
                description=milestone.title,
                quantity=1,
                unit_price=milestone.amount,
                amount=milestone.amount
            )

            # Update invoice totals
            invoice.calculate_totals()

            # Mark milestone as invoiced
            milestone.invoice_generated = True
            milestone.save()

            return Response({
                'detail': 'Invoice generated successfully.',
                'invoice_id': invoice.id,
                'invoice_number': invoice.invoice_number,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'detail': f'Failed to generate invoice: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
