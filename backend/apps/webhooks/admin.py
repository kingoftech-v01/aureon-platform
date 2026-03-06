"""Django admin configuration for webhooks app."""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import WebhookEvent, WebhookEndpoint


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    """Admin interface for WebhookEvent model."""

    list_display = [
        'event_id',
        'source',
        'event_type',
        'status_badge',
        'retry_count',
        'received_at',
        'processed_at',
    ]

    list_filter = [
        'source',
        'status',
        'received_at',
        'processed_at',
    ]

    search_fields = [
        'event_id',
        'event_type',
        'error_message',
    ]

    readonly_fields = [
        'id',
        'event_id',
        'source',
        'event_type',
        'status',
        'payload_display',
        'headers_display',
        'response_body_display',
        'ip_address',
        'user_agent',
        'received_at',
        'updated_at',
        'processed_at',
    ]

    fieldsets = (
        ('Event Information', {
            'fields': (
                'id',
                'source',
                'event_type',
                'event_id',
                'status',
            )
        }),
        ('Payload', {
            'fields': (
                'payload_display',
                'headers_display',
            ),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': (
                'retry_count',
                'max_retries',
                'error_message',
                'response_code',
                'response_body_display',
            )
        }),
        ('Request Details', {
            'fields': (
                'ip_address',
                'user_agent',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'received_at',
                'processed_at',
                'updated_at',
            )
        }),
    )

    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            'pending': 'gray',
            'processing': 'blue',
            'processed': 'green',
            'failed': 'red',
            'retrying': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def payload_display(self, obj):
        """Display formatted JSON payload."""
        try:
            formatted = json.dumps(obj.payload, indent=2)
            return format_html('<pre>{}</pre>', formatted)
        except:
            return str(obj.payload)
    payload_display.short_description = 'Payload'

    def headers_display(self, obj):
        """Display formatted headers."""
        try:
            formatted = json.dumps(obj.headers, indent=2)
            return format_html('<pre>{}</pre>', formatted)
        except:
            return str(obj.headers)
    headers_display.short_description = 'Headers'

    def response_body_display(self, obj):
        """Display formatted response body."""
        if obj.response_body:
            try:
                formatted = json.dumps(obj.response_body, indent=2)
                return format_html('<pre>{}</pre>', formatted)
            except:
                return str(obj.response_body)
        return '-'
    response_body_display.short_description = 'Response Body'

    actions = ['retry_failed_webhooks', 'mark_as_processed']

    def retry_failed_webhooks(self, request, queryset):
        """Admin action to retry failed webhooks."""
        from .tasks import process_stripe_webhook

        count = 0
        for webhook in queryset.filter(status__in=['failed', 'retrying']):
            if webhook.can_retry:
                process_stripe_webhook.delay(webhook.id)
                count += 1

        self.message_user(request, f"Queued {count} webhooks for retry.")
    retry_failed_webhooks.short_description = "Retry selected failed webhooks"

    def mark_as_processed(self, request, queryset):
        """Admin action to manually mark webhooks as processed."""
        count = queryset.update(status='processed')
        self.message_user(request, f"Marked {count} webhooks as processed.")
    mark_as_processed.short_description = "Mark selected as processed"


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    """Admin interface for WebhookEndpoint model."""

    list_display = [
        'url',
        'is_active',
        'event_count',
        'success_rate_display',
        'total_deliveries',
        'last_delivery_at',
    ]

    list_filter = [
        'is_active',
        'created_at',
        'last_delivery_at',
    ]

    search_fields = [
        'url',
        'event_types',
    ]

    readonly_fields = [
        'id',
        'success_rate_display',
        'total_deliveries',
        'successful_deliveries',
        'failed_deliveries',
        'last_delivery_at',
        'last_success_at',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Endpoint Configuration', {
            'fields': (
                'id',
                'url',
                'secret_key',
                'is_active',
            )
        }),
        ('Event Subscriptions', {
            'fields': (
                'event_types',
            )
        }),
        ('HTTP Configuration', {
            'fields': (
                'headers',
                'timeout',
            ),
            'classes': ('collapse',)
        }),
        ('Retry Configuration', {
            'fields': (
                'max_retries',
                'retry_delay',
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'success_rate_display',
                'total_deliveries',
                'successful_deliveries',
                'failed_deliveries',
                'last_delivery_at',
                'last_success_at',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def event_count(self, obj):
        """Display number of subscribed events."""
        return len(obj.event_types)
    event_count.short_description = 'Events'

    def success_rate_display(self, obj):
        """Display success rate with color coding."""
        rate = obj.success_rate
        if rate >= 95:
            color = 'green'
        elif rate >= 80:
            color = 'orange'
        else:
            color = 'red'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            rate
        )
    success_rate_display.short_description = 'Success Rate'

    actions = ['test_webhook_endpoint']

    def test_webhook_endpoint(self, request, queryset):
        """Admin action to send test webhook to selected endpoints."""
        from .tasks import send_outgoing_webhook

        for endpoint in queryset.filter(is_active=True):
            send_outgoing_webhook.delay(
                str(endpoint.id),
                'test.event',
                {'message': 'Test webhook from admin'}
            )

        count = queryset.filter(is_active=True).count()
        self.message_user(request, f"Sent test webhooks to {count} endpoints.")
    test_webhook_endpoint.short_description = "Send test webhook to selected endpoints"
