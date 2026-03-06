"""
Serializers for the notifications app.
"""

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.

    Exposes key fields for the frontend notification system.
    """
    type = serializers.CharField(source='channel', read_only=True)
    title = serializers.CharField(source='subject', read_only=True)
    message = serializers.CharField(source='message_text', read_only=True)
    is_read = serializers.ReadOnlyField()
    data = serializers.JSONField(source='metadata', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'is_read',
            'created_at', 'data',
        ]
        read_only_fields = ['id', 'created_at']
