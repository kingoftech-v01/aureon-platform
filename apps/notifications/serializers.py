"""Serializers for the notifications app."""

from rest_framework import serializers
from .models import Notification, NotificationTemplate


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""
    recipient = serializers.ReadOnlyField()
    is_read = serializers.ReadOnlyField()

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'sent_at',
            'delivered_at', 'read_at', 'failed_at',
        ]


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates."""

    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
