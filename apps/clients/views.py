"""
Views and ViewSets for the clients app API.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from .models import Client, ClientNote, ClientDocument
from .serializers import (
    ClientListSerializer,
    ClientDetailSerializer,
    ClientCreateUpdateSerializer,
    ClientNoteSerializer,
    ClientDocumentSerializer,
    ClientStatsSerializer,
)
from .filters import ClientFilter


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client CRUD operations.

    list: Get list of clients with filtering and search
    retrieve: Get client details
    create: Create a new client
    update: Update a client
    partial_update: Partially update a client
    destroy: Delete a client
    """

    queryset = Client.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ClientFilter
    search_fields = ['first_name', 'last_name', 'company_name', 'email', 'phone']
    ordering_fields = ['created_at', 'updated_at', 'first_name', 'last_name', 'company_name', 'lifecycle_stage']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ClientListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClientCreateUpdateSerializer
        return ClientDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Filter by current tenant (multi-tenancy)
        # This will be handled by django-tenants middleware
        # queryset = queryset.filter(tenant=self.request.tenant)

        # Optionally filter by owner for non-admin users
        if not self.request.user.is_staff:
            # Show only clients owned by the user or unassigned
            queryset = queryset.filter(
                Q(owner=self.request.user) | Q(owner__isnull=True)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get client statistics.

        Returns total clients, active clients, leads, prospects, and financial summary.
        """
        queryset = self.filter_queryset(self.get_queryset())

        stats = {
            'total_clients': queryset.count(),
            'active_clients': queryset.filter(is_active=True).count(),
            'leads': queryset.filter(lifecycle_stage=Client.LEAD).count(),
            'prospects': queryset.filter(lifecycle_stage=Client.PROSPECT).count(),
            'total_value': queryset.aggregate(Sum('total_value'))['total_value__sum'] or 0,
            'total_paid': queryset.aggregate(Sum('total_paid'))['total_paid__sum'] or 0,
            'outstanding_balance': queryset.aggregate(Sum('outstanding_balance'))['outstanding_balance__sum'] or 0,
        }

        serializer = ClientStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def create_portal_access(self, request, pk=None):
        """
        Create portal access for a client.

        Creates a user account for the client to access the client portal.
        """
        client = self.get_object()

        if client.portal_user:
            return Response(
                {'detail': 'Portal access already exists for this client.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = client.create_portal_access()
            return Response({
                'detail': 'Portal access created successfully.',
                'user_id': user.id,
                'email': user.email,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'detail': f'Failed to create portal access: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def update_financial_summary(self, request, pk=None):
        """
        Update client financial summary from invoices and contracts.
        """
        client = self.get_object()

        try:
            client.update_financial_summary()
            serializer = self.get_serializer(client)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': f'Failed to update financial summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def notes(self, request, pk=None):
        """
        Get all notes for a client.
        """
        client = self.get_object()
        notes = client.client_notes.all()
        serializer = ClientNoteSerializer(notes, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """
        Get all documents for a client.
        """
        client = self.get_object()
        documents = client.documents.all()
        serializer = ClientDocumentSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)


class ClientNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ClientNote CRUD operations.
    """

    queryset = ClientNote.objects.all()
    serializer_class = ClientNoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['client', 'note_type', 'author']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Filter by client access
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(client__owner=self.request.user) |
                Q(client__owner__isnull=True) |
                Q(author=self.request.user)
            )

        return queryset

    def perform_create(self, serializer):
        """Set author to current user on create."""
        serializer.save(author=self.request.user)


class ClientDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ClientDocument CRUD operations.
    """

    queryset = ClientDocument.objects.all()
    serializer_class = ClientDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['client', 'uploaded_by']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Filter by client access
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(client__owner=self.request.user) |
                Q(client__owner__isnull=True) |
                Q(uploaded_by=self.request.user)
            )

        return queryset

    def perform_create(self, serializer):
        """Set uploaded_by to current user on create."""
        serializer.save(uploaded_by=self.request.user)
