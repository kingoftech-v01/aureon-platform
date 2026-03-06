"""
Views and ViewSets for the tenants app API.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Tenant
from .serializers import TenantSerializer


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tenant CRUD operations.

    list: Get list of tenants the user has access to
    retrieve: Get tenant details
    update: Update a tenant
    partial_update: Partially update a tenant
    current: Get the current user's tenant
    """

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset to tenants owned by the current user."""
        return Tenant.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Set owner to current user on create."""
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Get the current user's tenant.

        Returns the first active tenant owned by the authenticated user.
        """
        tenant = Tenant.objects.filter(
            owner=request.user,
            is_active=True
        ).first()

        if not tenant:
            return Response(
                {'detail': 'No active tenant found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(tenant)
        return Response(serializer.data)
