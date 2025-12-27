"""Django admin configuration for notifications app."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import NotificationTemplate, Notification


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin interface for NotificationTemplate model."""

    list_display = [
        'name',
        'template_type',
        'channel_badge',
        'is_active',
        'send_to_client',
        'send_to_owner',
        'updated_at',
    ]

    list_filter = [
        'channel',
        'is_active',
        'send_to_client',
        'send_to_owner',
        'template_type',
    ]

    search_fields = [
        'name',
        'template_type',
        'subject',
        'body_text',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'preview_html',
    ]

    fieldsets = (
        ('Template Information', {
            'fields': (
                'id',
                'name',
                'template_type',
                'channel',
            )
        }),
        ('Content', {
            'fields': (
                'subject',
                'body_text',
                'body_html',
                'preview_html',
            )
        }),
        ('Configuration', {
            'fields': (
                'is_active',
                'send_to_client',
                'send_to_owner',
            )
        }),
        ('Template Variables', {
            'fields': (
                'available_variables',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def channel_badge(self, obj):
        """Display channel with colored badge."""
        colors = {
            'email': '#3B82F6',
            'sms': '#10B981',
            'in_app': '#F59E0B',
        }
        color = colors.get(obj.channel, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_channel_display()
        )
    channel_badge.short_description = 'Channel'

    def preview_html(self, obj):
        """Display HTML preview."""
        if obj.body_html:
            return format_html('<div style="border: 1px solid #ddd; padding: 10px; max-height: 400px; overflow: auto;">{}</div>', mark_safe(obj.body_html))
        return '-'
    preview_html.short_description = 'HTML Preview'

    actions = ['duplicate_template', 'activate_templates', 'deactivate_templates']

    def duplicate_template(self, request, queryset):
        """Duplicate selected templates."""
        count = 0
        for template in queryset:
            template.pk = None
            template.id = None
            template.name = f"{template.name} (Copy)"
            template.template_type = f"{template.template_type}_copy"
            template.save()
            count += 1

        self.message_user(request, f"Duplicated {count} templates.")
    duplicate_template.short_description = "Duplicate selected templates"

    def activate_templates(self, request, queryset):
        """Activate selected templates."""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} templates.")
    activate_templates.short_description = "Activate selected templates"

    def deactivate_templates(self, request, queryset):
        """Deactivate selected templates."""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} templates.")
    deactivate_templates.short_description = "Deactivate selected templates"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model."""

    list_display = [
        'id_short',
        'recipient',
        'subject_short',
        'channel_badge',
        'status_badge',
        'priority',
        'created_at',
        'sent_at',
    ]

    list_filter = [
        'channel',
        'status',
        'priority',
        'created_at',
        'sent_at',
    ]

    search_fields = [
        'subject',
        'email',
        'message_text',
        'user__email',
    ]

    readonly_fields = [
        'id',
        'template',
        'user',
        'email',
        'phone',
        'channel',
        'priority',
        'status',
        'subject',
        'message_text_display',
        'message_html_display',
        'sent_at',
        'delivered_at',
        'read_at',
        'failed_at',
        'error_message',
        'external_id',
        'retry_count',
        'metadata',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Notification Info', {
            'fields': (
                'id',
                'template',
                'channel',
                'priority',
                'status',
            )
        }),
        ('Recipient', {
            'fields': (
                'user',
                'email',
                'phone',
            )
        }),
        ('Content', {
            'fields': (
                'subject',
                'message_text_display',
                'message_html_display',
            )
        }),
        ('Delivery Status', {
            'fields': (
                'sent_at',
                'delivered_at',
                'read_at',
                'failed_at',
                'error_message',
                'retry_count',
                'external_id',
            )
        }),
        ('Related Objects', {
            'fields': (
                'related_invoice',
                'related_payment',
                'related_contract',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'metadata',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def id_short(self, obj):
        """Display shortened ID."""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'

    def subject_short(self, obj):
        """Display truncated subject."""
        if len(obj.subject) > 50:
            return f"{obj.subject[:50]}..."
        return obj.subject
    subject_short.short_description = 'Subject'

    def channel_badge(self, obj):
        """Display channel with colored badge."""
        colors = {
            'email': '#3B82F6',
            'sms': '#10B981',
            'in_app': '#F59E0B',
        }
        color = colors.get(obj.channel, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_channel_display()
        )
    channel_badge.short_description = 'Channel'

    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            'pending': '#6B7280',
            'sent': '#3B82F6',
            'delivered': '#10B981',
            'failed': '#EF4444',
            'read': '#8B5CF6',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def message_text_display(self, obj):
        """Display formatted plain text message."""
        return format_html('<pre style="white-space: pre-wrap;">{}</pre>', obj.message_text)
    message_text_display.short_description = 'Message (Text)'

    def message_html_display(self, obj):
        """Display HTML message preview."""
        if obj.message_html:
            return format_html('<div style="border: 1px solid #ddd; padding: 10px; max-height: 400px; overflow: auto;">{}</div>', mark_safe(obj.message_html))
        return '-'
    message_html_display.short_description = 'Message (HTML)'

    actions = ['resend_notifications', 'mark_as_read']

    def resend_notifications(self, request, queryset):
        """Resend selected notifications."""
        from .tasks import send_notification_async

        count = 0
        for notification in queryset.filter(status__in=['failed', 'pending']):
            send_notification_async.delay(str(notification.id))
            count += 1

        self.message_user(request, f"Queued {count} notifications for resending.")
    resend_notifications.short_description = "Resend selected notifications"

    def mark_as_read(self, request, queryset):
        """Mark notifications as read."""
        count = 0
        for notification in queryset:
            notification.mark_as_read()
            count += 1

        self.message_user(request, f"Marked {count} notifications as read.")
    mark_as_read.short_description = "Mark selected as read"
