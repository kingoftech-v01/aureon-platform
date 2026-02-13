"""
Admin interface for email management.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import EmailAccount, EmailMessage, EmailAttachment, EmailTemplate


class EmailAttachmentInline(admin.TabularInline):
    """Inline admin for email attachments."""
    model = EmailAttachment
    extra = 0
    fields = ('file', 'file_name', 'file_size', 'file_type', 'created_at')
    readonly_fields = ('file_size', 'created_at')


@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    """Admin interface for EmailAccount model."""

    list_display = [
        'email_address',
        'display_name',
        'user',
        'provider',
        'is_active',
        'is_default',
        'created_at',
    ]

    list_filter = [
        'provider',
        'is_active',
        'is_default',
        'created_at',
    ]

    search_fields = [
        'email_address',
        'display_name',
        'user__email',
        'user__first_name',
        'user__last_name',
    ]

    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['user']


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    """Admin interface for EmailMessage model."""

    list_display = [
        'subject',
        'from_email',
        'direction',
        'status',
        'client',
        'is_read',
        'sent_at',
        'created_at',
    ]

    list_filter = [
        'direction',
        'status',
        'is_read',
        'created_at',
        'sent_at',
    ]

    search_fields = [
        'subject',
        'from_email',
        'body_text',
        'message_id',
        'thread_id',
    ]

    readonly_fields = [
        'id',
        'opened_count',
        'created_at',
        'updated_at',
    ]

    raw_id_fields = ['account', 'client', 'contract', 'invoice', 'in_reply_to']

    inlines = [EmailAttachmentInline]


@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    """Admin interface for EmailAttachment model."""

    list_display = ['file_name', 'email', 'file_type', 'file_size', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['file_name', 'email__subject']
    readonly_fields = ['id', 'file_size', 'created_at']
    raw_id_fields = ['email']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin interface for EmailTemplate model."""

    list_display = [
        'name',
        'category',
        'subject',
        'is_active',
        'owner',
        'created_at',
    ]

    list_filter = [
        'category',
        'is_active',
        'created_at',
    ]

    search_fields = [
        'name',
        'subject',
        'body_text',
    ]

    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['owner']
