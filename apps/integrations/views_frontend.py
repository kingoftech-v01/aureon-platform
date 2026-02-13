"""
Frontend views for the integrations app.

Provides class-based views for integration listing, detail, and connection setup.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView

from .models import Integration, IntegrationSyncLog


class IntegrationListView(LoginRequiredMixin, ListView):
    """List all available and configured integrations."""
    template_name = 'integrations/integration_list.html'
    context_object_name = 'integrations'

    def get_queryset(self):
        return Integration.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Integrations'
        context['service_choices'] = Integration.SERVICE_CHOICES
        context['status_choices'] = Integration.STATUS_CHOICES
        context['active_count'] = Integration.objects.filter(
            status=Integration.ACTIVE
        ).count()
        context['total_count'] = Integration.objects.count()
        return context


class IntegrationDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of an integration with sync logs and configuration."""
    template_name = 'integrations/integration_detail.html'
    model = Integration
    context_object_name = 'integration'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Integration: {self.object.name}'
        context['sync_logs'] = self.object.sync_logs.all()[:20]
        context['is_connected'] = self.object.is_connected
        context['needs_reauth'] = self.object.needs_reauth
        context['last_sync_at'] = self.object.last_sync_at
        context['last_sync_status'] = self.object.last_sync_status
        return context


class IntegrationConnectView(LoginRequiredMixin, TemplateView):
    """Integration connection and setup page."""
    template_name = 'integrations/integration_connect.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Connect Integration'
        context['service_choices'] = Integration.SERVICE_CHOICES
        # If connecting a specific integration, pass its details
        pk = self.kwargs.get('pk')
        if pk:
            integration = Integration.objects.get(pk=pk)
            context['integration'] = integration
            context['page_title'] = f'Connect: {integration.name}'
        return context
