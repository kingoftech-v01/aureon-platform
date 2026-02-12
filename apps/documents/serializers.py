"""Document serializers."""

from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    file_extension = serializers.ReadOnlyField()
    is_pdf = serializers.ReadOnlyField()
    is_image = serializers.ReadOnlyField()
    uploaded_by_name = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'document_type', 'file', 'file_type',
            'file_size', 'uploaded_by', 'uploaded_by_name', 'client', 'contract',
            'invoice', 'processing_status', 'is_public', 'tags', 'metadata',
            'file_extension', 'is_pdf', 'is_image', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'file_type', 'file_size', 'processing_status', 'created_at', 'updated_at']

    def get_client(self, obj):
        """Return client ID as string for consistent JSON serialization."""
        return str(obj.client_id) if obj.client_id else None

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.email
        return None


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['title', 'description', 'document_type', 'file', 'client', 'contract', 'invoice', 'is_public', 'tags']
