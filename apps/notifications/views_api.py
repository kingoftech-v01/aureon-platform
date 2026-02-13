"""Views for the notifications app API."""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Notification, NotificationTemplate
from .serializers import NotificationSerializer, NotificationTemplateSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Notification CRUD operations.

    list: Get notifications for the current user
    retrieve: Get notification detail
    create: Create a new notification
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'channel', 'priority']
    ordering_fields = ['created_at', 'sent_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter notifications to current user unless staff."""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(user=self.request.user) | Q(email=self.request.user.email)
            )
        return queryset

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all unread notifications as read."""
        from django.utils import timezone
        qs = self.get_queryset().exclude(status=Notification.READ)
        count = qs.update(status=Notification.READ, read_at=timezone.now())
        return Response({'marked_read': count})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = self.get_queryset().exclude(status=Notification.READ).count()
        return Response({'unread_count': count})


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for NotificationTemplate CRUD operations."""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['template_type', 'channel', 'is_active']
    ordering = ['template_type']
