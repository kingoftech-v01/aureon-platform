"""Integration views."""

import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Integration, IntegrationSyncLog
from .serializers import IntegrationSerializer, IntegrationSyncLogSerializer

logger = logging.getLogger(__name__)


class IntegrationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing integrations."""

    serializer_class = IntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Integration.objects.all()

    @action(detail=True, methods=['post'])
    def connect(self, request, pk=None):
        """Activate an integration."""
        integration = self.get_object()
        integration.status = Integration.ACTIVE
        integration.save(update_fields=['status', 'updated_at'])
        return Response({'status': 'connected'})

    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """Deactivate an integration."""
        integration = self.get_object()
        integration.status = Integration.INACTIVE
        integration.access_token = ''
        integration.refresh_token = ''
        integration.save(update_fields=['status', 'access_token', 'refresh_token', 'updated_at'])
        return Response({'status': 'disconnected'})

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Trigger a manual sync."""
        integration = self.get_object()
        if integration.status != Integration.ACTIVE:
            return Response(
                {'error': 'Integration is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .tasks import sync_external_service
            sync_external_service.delay(
                integration.service_type,
                {'integration_id': str(integration.id)}
            )
            return Response({'status': 'sync_queued'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get sync logs for an integration."""
        integration = self.get_object()
        logs = IntegrationSyncLog.objects.filter(integration=integration)[:50]
        serializer = IntegrationSyncLogSerializer(logs, many=True)
        return Response(serializer.data)
