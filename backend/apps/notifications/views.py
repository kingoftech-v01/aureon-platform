"""
Views and ViewSets for the notifications app API.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Notification operations.

    list: Return the current user's notifications, ordered by created_at desc
    mark_read: Mark a single notification as read
    mark_all_read: Mark all notifications as read
    unread_count: Return count of unread notifications
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']

    def get_queryset(self):
        """Return notifications for the current user, ordered by newest first."""
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """
        Mark a single notification as read.
        """
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        Mark all of the current user's unread notifications as read.
        """
        from django.utils import timezone

        queryset = self.get_queryset().exclude(status=Notification.READ)
        count = queryset.count()
        queryset.update(
            status=Notification.READ,
            read_at=timezone.now()
        )
        return Response({
            'detail': f'Marked {count} notifications as read.',
            'count': count,
        })

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        Return the count of unread notifications for the current user.
        """
        count = self.get_queryset().exclude(
            status=Notification.READ
        ).count()
        return Response({'count': count})
