"""
Views and viewsets for tenant management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
from .models import Tenant, Domain
from .serializers import (
    TenantSerializer,
    TenantCreateSerializer,
    TenantUpdateSerializer,
    TenantPlanUpgradeSerializer,
    DomainSerializer,
)


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tenants.

    Provides CRUD operations and additional actions for tenant management.
    """

    queryset = Tenant.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TenantCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TenantUpdateSerializer
        elif self.action == 'upgrade_plan':
            return TenantPlanUpgradeSerializer
        return TenantSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        if user.is_superuser:
            return Tenant.objects.all()
        # Return only the tenant the user belongs to
        return Tenant.objects.filter(id=user.tenant_id) if hasattr(user, 'tenant_id') else Tenant.objects.none()

    def create(self, request, *args, **kwargs):
        """Create a new tenant with default trial period."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Set trial period (14 days)
        tenant = serializer.save(
            is_trial=True,
            trial_ends_at=timezone.now() + timedelta(days=14),
            plan=Tenant.FREE,
        )

        # Create primary domain
        domain_name = f"{tenant.slug}.aureon.rhematek-solutions.com"
        Domain.objects.create(
            tenant=tenant,
            domain=domain_name,
            is_primary=True,
        )

        return Response(
            TenantSerializer(tenant).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def upgrade_plan(self, request, pk=None):
        """
        Upgrade tenant to a new plan.

        POST /api/tenants/{id}/upgrade_plan/
        Body: {"plan": "starter"}
        """
        tenant = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={'tenant': tenant}
        )
        serializer.is_valid(raise_exception=True)

        new_plan = serializer.validated_data['plan']
        tenant.upgrade_plan(new_plan)

        return Response({
            'message': f'Tenant upgraded to {new_plan} plan successfully.',
            'tenant': TenantSerializer(tenant).data
        })

    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """
        Get current usage statistics for the tenant.

        GET /api/tenants/{id}/usage_stats/
        """
        tenant = self.get_object()

        # TODO: Implement actual usage counting when other apps are ready
        stats = {
            'users': {
                'current': 0,  # tenant.users.filter(is_active=True).count()
                'limit': tenant.max_users,
            },
            'clients': {
                'current': 0,  # tenant.clients.count()
                'limit': tenant.max_clients,
            },
            'contracts': {
                'current': 0,  # tenant.contracts.filter(status='active').count()
                'limit': tenant.max_contracts,
            },
            'invoices_this_month': {
                'current': 0,  # Count invoices created this month
                'limit': tenant.max_invoices_per_month,
            },
        }

        return Response(stats)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a tenant.

        POST /api/tenants/{id}/activate/
        """
        tenant = self.get_object()
        tenant.is_active = True
        tenant.save()

        return Response({
            'message': 'Tenant activated successfully.',
            'tenant': TenantSerializer(tenant).data
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a tenant.

        POST /api/tenants/{id}/deactivate/
        """
        tenant = self.get_object()
        tenant.is_active = False
        tenant.save()

        return Response({
            'message': 'Tenant deactivated successfully.',
            'tenant': TenantSerializer(tenant).data
        })

    @action(detail=True, methods=['get'])
    def trial_status(self, request, pk=None):
        """
        Get trial status for the tenant.

        GET /api/tenants/{id}/trial_status/
        """
        tenant = self.get_object()

        return Response({
            'is_trial': tenant.is_trial,
            'is_on_trial': tenant.is_on_trial,
            'trial_ends_at': tenant.trial_ends_at,
            'days_remaining': tenant.days_until_trial_ends,
        })


class DomainViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tenant domains.
    """

    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter domains based on user's tenant."""
        user = self.request.user
        if user.is_superuser:
            return Domain.objects.all()
        # Return only domains for the user's tenant
        return Domain.objects.filter(tenant_id=user.tenant_id) if hasattr(user, 'tenant_id') else Domain.objects.none()

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify domain ownership.

        POST /api/domains/{id}/verify/
        """
        domain = self.get_object()
        domain.is_verified = True
        domain.verified_at = timezone.now()
        domain.save()

        return Response({
            'message': 'Domain verified successfully.',
            'domain': DomainSerializer(domain).data
        })

    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """
        Set domain as primary for its tenant.

        POST /api/domains/{id}/set_primary/
        """
        domain = self.get_object()
        domain.is_primary = True
        domain.save()  # The model's save method handles setting others to non-primary

        return Response({
            'message': 'Domain set as primary successfully.',
            'domain': DomainSerializer(domain).data
        })
