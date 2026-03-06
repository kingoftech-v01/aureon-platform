"""Document admin configuration."""

from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'file_type', 'file_size', 'uploaded_by', 'client', 'created_at']
    list_filter = ['document_type', 'processing_status', 'is_public', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'file_size', 'file_type', 'processing_status', 'created_at', 'updated_at']
    raw_id_fields = ['uploaded_by', 'client', 'contract', 'invoice']
