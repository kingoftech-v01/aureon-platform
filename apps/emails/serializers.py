"""
Serializers for the emails app.
"""

from rest_framework import serializers
from .models import EmailAccount, EmailMessage, EmailAttachment, EmailTemplate


class EmailAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for email accounts.
    """

    class Meta:
        model = EmailAccount
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for email attachments.
    """

    class Meta:
        model = EmailAttachment
        fields = '__all__'
        read_only_fields = ['id', 'file_size', 'created_at']


class EmailMessageListSerializer(serializers.ModelSerializer):
    """
    Serializer for email message list view (minimal fields for performance).
    """
    attachments_count = serializers.SerializerMethodField()

    class Meta:
        model = EmailMessage
        fields = [
            'id', 'account', 'direction', 'from_email', 'to_emails',
            'subject', 'status', 'client', 'is_read', 'sent_at',
            'received_at', 'created_at', 'attachments_count',
        ]
        read_only_fields = ['id', 'created_at']

    def get_attachments_count(self, obj):
        """Get the number of attachments for this email."""
        return obj.attachments.count()


class EmailMessageDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for email message detail view.
    """
    attachments = EmailAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = EmailMessage
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailMessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating email messages.
    """

    class Meta:
        model = EmailMessage
        fields = [
            'account', 'to_emails', 'cc_emails', 'bcc_emails',
            'subject', 'body_text', 'body_html', 'client',
            'contract', 'invoice', 'in_reply_to',
        ]


class EmailTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for email templates.
    """

    class Meta:
        model = EmailTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
