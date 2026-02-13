"""
Views and ViewSets for the proposals app API.
"""

import logging
from django.db.models import Q, Sum, Count
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Proposal, ProposalSection, ProposalPricingOption, ProposalActivity
from .serializers import (
    ProposalListSerializer,
    ProposalDetailSerializer,
    ProposalCreateUpdateSerializer,
    ProposalSectionSerializer,
    ProposalPricingOptionSerializer,
    ProposalActivitySerializer,
    ProposalStatsSerializer,
)

logger = logging.getLogger(__name__)


class ProposalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Proposal CRUD operations.

    list: Get list of proposals with filtering and search
    retrieve: Get proposal details with sections, pricing options, and activities
    create: Create a new proposal
    update: Update a proposal
    partial_update: Partially update a proposal
    destroy: Delete a proposal
    """

    queryset = Proposal.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'client', 'owner']
    search_fields = ['proposal_number', 'title', 'description']
    ordering_fields = ['created_at', 'total_value']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProposalListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProposalCreateUpdateSerializer
        return ProposalDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset().select_related('client', 'owner', 'contract')

        # Optionally filter for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(owner=self.request.user) | Q(owner__isnull=True)
            )

        return queryset

    def perform_create(self, serializer):
        """Set owner to current user and create CREATED activity."""
        proposal = serializer.save(owner=self.request.user)

        # Create CREATED activity
        ProposalActivity.objects.create(
            proposal=proposal,
            activity_type=ProposalActivity.CREATED,
            description=f'Proposal "{proposal.title}" was created.',
            user=self.request.user,
            ip_address=self._get_client_ip(),
        )

    def _get_client_ip(self):
        """Extract client IP address from request."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR')

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """
        Send proposal to client.

        Sets status to SENT and records sent_at timestamp.
        """
        proposal = self.get_object()

        if proposal.status != Proposal.DRAFT:
            return Response(
                {'detail': 'Only draft proposals can be sent.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        proposal.status = Proposal.SENT
        proposal.sent_at = timezone.now()
        proposal.save()

        # Create SENT activity
        ProposalActivity.objects.create(
            proposal=proposal,
            activity_type=ProposalActivity.SENT,
            description=f'Proposal "{proposal.title}" was sent to client.',
            user=request.user,
            ip_address=self._get_client_ip(),
        )

        serializer = ProposalDetailSerializer(proposal, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept proposal.

        Sets status to ACCEPTED, records accepted_at timestamp.
        Optionally accepts signature and client_message.
        """
        proposal = self.get_object()

        if proposal.status not in [Proposal.SENT, Proposal.VIEWED]:
            return Response(
                {'detail': 'Only sent or viewed proposals can be accepted.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        proposal.status = Proposal.ACCEPTED
        proposal.accepted_at = timezone.now()

        # Optional fields
        signature = request.data.get('signature')
        client_message = request.data.get('client_message')

        if signature:
            proposal.signature = signature
        if client_message:
            proposal.client_message = client_message

        proposal.save()

        # Create ACCEPTED activity
        ProposalActivity.objects.create(
            proposal=proposal,
            activity_type=ProposalActivity.ACCEPTED,
            description=f'Proposal "{proposal.title}" was accepted by the client.',
            user=request.user,
            ip_address=self._get_client_ip(),
            metadata={
                'has_signature': bool(signature),
                'has_message': bool(client_message),
            },
        )

        serializer = ProposalDetailSerializer(proposal, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """
        Decline proposal.

        Sets status to DECLINED, records declined_at timestamp.
        Optionally accepts client_message.
        """
        proposal = self.get_object()

        if proposal.status not in [Proposal.SENT, Proposal.VIEWED]:
            return Response(
                {'detail': 'Only sent or viewed proposals can be declined.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        proposal.status = Proposal.DECLINED
        proposal.declined_at = timezone.now()

        # Optional fields
        client_message = request.data.get('client_message')

        if client_message:
            proposal.client_message = client_message

        proposal.save()

        # Create DECLINED activity
        ProposalActivity.objects.create(
            proposal=proposal,
            activity_type=ProposalActivity.DECLINED,
            description=f'Proposal "{proposal.title}" was declined by the client.',
            user=request.user,
            ip_address=self._get_client_ip(),
            metadata={
                'has_message': bool(client_message),
            },
        )

        serializer = ProposalDetailSerializer(proposal, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def convert_to_contract(self, request, pk=None):
        """
        Convert accepted proposal to a contract.

        Creates a new Contract from proposal data, sets status to CONVERTED,
        and links the contract to the proposal.
        """
        proposal = self.get_object()

        if proposal.status != Proposal.ACCEPTED:
            return Response(
                {'detail': 'Only accepted proposals can be converted to contracts.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if proposal.contract:
            return Response(
                {'detail': 'This proposal has already been converted to a contract.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from apps.contracts.models import Contract
            from apps.contracts.serializers import ContractDetailSerializer

            # Create contract from proposal data
            contract = Contract.objects.create(
                client=proposal.client,
                title=proposal.title,
                description=proposal.description,
                contract_type=Contract.FIXED_PRICE,
                status=Contract.DRAFT,
                start_date=timezone.now().date(),
                value=proposal.total_value,
                currency=proposal.currency,
                owner=proposal.owner,
                metadata={
                    'converted_from_proposal': str(proposal.id),
                    'proposal_number': proposal.proposal_number,
                },
            )

            # Update proposal
            proposal.status = Proposal.CONVERTED
            proposal.contract = contract
            proposal.save()

            # Create CONVERTED activity
            ProposalActivity.objects.create(
                proposal=proposal,
                activity_type=ProposalActivity.CONVERTED,
                description=f'Proposal "{proposal.title}" was converted to contract "{contract.contract_number}".',
                user=request.user,
                ip_address=self._get_client_ip(),
                metadata={
                    'contract_id': str(contract.id),
                    'contract_number': contract.contract_number,
                },
            )

            contract_serializer = ContractDetailSerializer(contract, context={'request': request})
            return Response(contract_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Failed to convert proposal to contract: {e}")
            return Response(
                {'detail': f'Failed to convert proposal to contract: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate a proposal.

        Creates a deep copy of the proposal including sections and pricing options.
        The new proposal starts in DRAFT status with a new proposal number.
        """
        proposal = self.get_object()

        try:
            # Create new proposal as a copy
            new_proposal = Proposal(
                client=proposal.client,
                title=f"{proposal.title} (Copy)",
                description=proposal.description,
                status=Proposal.DRAFT,
                valid_until=proposal.valid_until,
                total_value=proposal.total_value,
                currency=proposal.currency,
                owner=request.user,
                metadata=proposal.metadata,
            )
            # proposal_number will be auto-generated in save()
            new_proposal.save()

            # Copy sections
            for section in proposal.sections.all():
                ProposalSection.objects.create(
                    proposal=new_proposal,
                    title=section.title,
                    content=section.content,
                    order=section.order,
                    section_type=section.section_type,
                )

            # Copy pricing options
            for option in proposal.pricing_options.all():
                ProposalPricingOption.objects.create(
                    proposal=new_proposal,
                    name=option.name,
                    description=option.description,
                    price=option.price,
                    is_recommended=option.is_recommended,
                    features=option.features,
                    order=option.order,
                )

            # Create CREATED activity for the new proposal
            ProposalActivity.objects.create(
                proposal=new_proposal,
                activity_type=ProposalActivity.CREATED,
                description=f'Proposal duplicated from {proposal.proposal_number}.',
                user=request.user,
                ip_address=self._get_client_ip(),
                metadata={
                    'duplicated_from': str(proposal.id),
                    'original_proposal_number': proposal.proposal_number,
                },
            )

            serializer = ProposalDetailSerializer(new_proposal, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Failed to duplicate proposal: {e}")
            return Response(
                {'detail': f'Failed to duplicate proposal: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get proposal statistics.

        Returns total proposals, counts by status, total value, and conversion rate.
        """
        queryset = self.filter_queryset(self.get_queryset())

        total = queryset.count()

        # Count by status
        by_status = {}
        for status_choice, _ in Proposal.STATUS_CHOICES:
            by_status[status_choice] = queryset.filter(status=status_choice).count()

        # Total value
        total_value = queryset.aggregate(Sum('total_value'))['total_value__sum'] or 0

        # Conversion rate: proposals that became ACCEPTED or CONVERTED
        # out of all non-DRAFT proposals
        non_draft = queryset.exclude(status=Proposal.DRAFT).count()
        converted_or_accepted = queryset.filter(
            status__in=[Proposal.ACCEPTED, Proposal.CONVERTED]
        ).count()
        conversion_rate = (converted_or_accepted / non_draft * 100) if non_draft > 0 else 0.0

        stats_data = {
            'total': total,
            'by_status': by_status,
            'total_value': total_value,
            'conversion_rate': round(conversion_rate, 2),
        }

        serializer = ProposalStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """
        Get all activities for a proposal.
        """
        proposal = self.get_object()
        activities = proposal.activities.all()
        serializer = ProposalActivitySerializer(activities, many=True, context={'request': request})
        return Response(serializer.data)


class ProposalSectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProposalSection CRUD operations.
    """

    queryset = ProposalSection.objects.all()
    serializer_class = ProposalSectionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['proposal', 'section_type']
    ordering = ['order']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset().select_related('proposal')

        # Filter by proposal access
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(proposal__owner=self.request.user) |
                Q(proposal__owner__isnull=True)
            )

        return queryset


class ProposalPricingOptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProposalPricingOption CRUD operations.
    """

    queryset = ProposalPricingOption.objects.all()
    serializer_class = ProposalPricingOptionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['proposal']
    ordering = ['order']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset().select_related('proposal')

        # Filter by proposal access
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(proposal__owner=self.request.user) |
                Q(proposal__owner__isnull=True)
            )

        return queryset
