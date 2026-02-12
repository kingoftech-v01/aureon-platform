"""Integration REST API views for Aureon SaaS Platform."""

import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Integration, IntegrationSyncLog
from .serializers import (
    IntegrationSerializer,
    IntegrationDetailSerializer,
    IntegrationCreateUpdateSerializer,
    IntegrationSyncLogSerializer,
    IntegrationStatsSerializer,
)

logger = logging.getLogger(__name__)


class IntegrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing third-party integrations.

    list:         GET  /api/integrations/                    — all integrations
    create:       POST /api/integrations/                    — add integration
    retrieve:     GET  /api/integrations/{id}/               — integration detail
    update:       PUT  /api/integrations/{id}/               — update config
    destroy:      DEL  /api/integrations/{id}/               — remove integration
    connect:      POST /api/integrations/{id}/connect/       — activate
    disconnect:   POST /api/integrations/{id}/disconnect/    — deactivate + clear tokens
    sync:         POST /api/integrations/{id}/sync/          — trigger manual sync
    test:         POST /api/integrations/{id}/test/          — test connection
    logs:         GET  /api/integrations/{id}/logs/          — sync history
    stats:        GET  /api/integrations/stats/              — aggregate metrics
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['service_type', 'status', 'sync_enabled']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'last_sync_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Integration.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IntegrationDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return IntegrationCreateUpdateSerializer
        return IntegrationSerializer

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'])
    def connect(self, request, pk=None):
        """Activate an integration with optional OAuth tokens."""
        integration = self.get_object()

        access_token = request.data.get('access_token', '')
        refresh_token = request.data.get('refresh_token', '')
        token_expires_at = request.data.get('token_expires_at')

        if access_token:
            integration.access_token = access_token
        if refresh_token:
            integration.refresh_token = refresh_token
        if token_expires_at:
            from django.utils.dateparse import parse_datetime
            integration.token_expires_at = parse_datetime(token_expires_at)

        integration.status = Integration.ACTIVE
        integration.save(update_fields=[
            'status', 'access_token', 'refresh_token', 'token_expires_at', 'updated_at',
        ])

        serializer = IntegrationSerializer(integration)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """Deactivate an integration and clear credentials."""
        integration = self.get_object()
        integration.status = Integration.INACTIVE
        integration.access_token = ''
        integration.refresh_token = ''
        integration.token_expires_at = None
        integration.save(update_fields=[
            'status', 'access_token', 'refresh_token', 'token_expires_at', 'updated_at',
        ])
        return Response({'status': 'disconnected'})

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Trigger a manual sync for this integration."""
        integration = self.get_object()

        if integration.status != Integration.ACTIVE:
            return Response(
                {'error': 'Integration is not active. Connect it first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sync_type = request.data.get('sync_type', 'full')

        try:
            from .tasks import sync_external_service
            sync_external_service.delay(
                integration.service_type,
                {
                    'integration_id': str(integration.id),
                    'sync_type': sync_type,
                },
            )
            return Response({
                'status': 'sync_queued',
                'sync_type': sync_type,
                'integration': str(integration.id),
            })
        except Exception as e:
            logger.exception(f"Failed to queue sync for {integration.name}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ------------------------------------------------------------------
    # Test connection
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test the integration connection without syncing data."""
        integration = self.get_object()

        if not integration.access_token:
            return Response(
                {'connected': False, 'error': 'No access token configured.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from .services import get_service
            service = get_service(integration)
            result = service.test_connection()
            http_status = (
                status.HTTP_200_OK if result.get('connected')
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=http_status)
        except ValueError as e:
            return Response(
                {'connected': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get sync logs for an integration."""
        integration = self.get_object()
        limit = int(request.query_params.get('limit', 50))
        logs = IntegrationSyncLog.objects.filter(
            integration=integration
        ).order_by('-started_at')[:limit]
        serializer = IntegrationSyncLogSerializer(logs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Aggregate integration metrics."""
        from django.db.models import Count, Avg, Sum, Q

        integrations = Integration.objects.all()

        total = integrations.count()
        by_status = dict(
            integrations.values_list('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        by_service = dict(
            integrations.values_list('service_type')
            .annotate(count=Count('id'))
            .values_list('service_type', 'count')
        )

        # Recent sync stats
        from django.utils import timezone
        from datetime import timedelta
        last_24h = timezone.now() - timedelta(hours=24)

        recent_logs = IntegrationSyncLog.objects.filter(started_at__gte=last_24h)
        sync_stats = recent_logs.aggregate(
            total_syncs=Count('id'),
            successful_syncs=Count('id', filter=Q(status='success')),
            failed_syncs=Count('id', filter=Q(status='error')),
            total_records=Sum('records_synced'),
            avg_duration=Avg('duration_ms'),
        )

        data = {
            'total_integrations': total,
            'active_integrations': by_status.get('active', 0),
            'inactive_integrations': by_status.get('inactive', 0),
            'error_integrations': by_status.get('error', 0),
            'integrations_by_service': by_service,
            'syncs_last_24h': sync_stats['total_syncs'] or 0,
            'successful_syncs_last_24h': sync_stats['successful_syncs'] or 0,
            'failed_syncs_last_24h': sync_stats['failed_syncs'] or 0,
            'records_synced_last_24h': sync_stats['total_records'] or 0,
            'avg_sync_duration_ms': round(sync_stats['avg_duration'] or 0),
        }

        serializer = IntegrationStatsSerializer(data)
        return Response(serializer.data)
