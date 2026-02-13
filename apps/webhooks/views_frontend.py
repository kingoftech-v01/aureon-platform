"""
Frontend views for the webhooks app.

Provides class-based views for webhook event listing, event detail,
and webhook endpoint management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView

from .models import WebhookEvent, WebhookEndpoint


class WebhookEventListView(LoginRequiredMixin, ListView):
    """List all incoming webhook events with filtering by source and status."""
    template_name = 'webhooks/webhook_event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        queryset = WebhookEvent.objects.all()
        source = self.request.GET.get('source')
        if source:
            queryset = queryset.filter(source=source)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Webhook Events'
        context['source_choices'] = WebhookEvent.SOURCE_CHOICES
        context['status_choices'] = WebhookEvent.STATUS_CHOICES
        context['current_source'] = self.request.GET.get('source', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['total_events'] = WebhookEvent.objects.count()
        context['failed_count'] = WebhookEvent.objects.filter(
            status=WebhookEvent.FAILED
        ).count()
        context['processed_count'] = WebhookEvent.objects.filter(
            status=WebhookEvent.PROCESSED
        ).count()
        return context


class WebhookEventDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a webhook event with payload and processing information."""
    template_name = 'webhooks/webhook_event_detail.html'
    model = WebhookEvent
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Webhook Event: {self.object.event_type}'
        context['payload'] = self.object.payload
        context['headers'] = self.object.headers
        context['can_retry'] = self.object.can_retry
        context['is_stripe_event'] = self.object.is_stripe_event
        context['retry_count'] = self.object.retry_count
        context['max_retries'] = self.object.max_retries
        return context


class WebhookEndpointListView(LoginRequiredMixin, ListView):
    """List all configured outgoing webhook endpoints."""
    template_name = 'webhooks/webhook_endpoint_list.html'
    context_object_name = 'endpoints'

    def get_queryset(self):
        return WebhookEndpoint.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Webhook Endpoints'
        context['event_type_choices'] = WebhookEndpoint.EVENT_TYPES
        context['active_count'] = WebhookEndpoint.objects.filter(is_active=True).count()
        context['total_count'] = WebhookEndpoint.objects.count()
        return context
