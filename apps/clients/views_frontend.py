"""
Frontend views for the clients app.

Provides class-based views for client listing, detail, creation, editing,
client portal access, and portal messaging.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView

from .models import Client, ClientNote, ClientDocument, PortalMessage


class ClientListView(LoginRequiredMixin, ListView):
    """List all clients with filtering by lifecycle stage and search."""
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        queryset = Client.objects.select_related('owner').filter(is_active=True)
        stage = self.request.GET.get('stage')
        if stage:
            queryset = queryset.filter(lifecycle_stage=stage)
        search = self.request.GET.get('q')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(company_name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Clients'
        context['stage_choices'] = Client.STAGE_CHOICES
        context['current_stage'] = self.request.GET.get('stage', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['total_clients'] = Client.objects.filter(is_active=True).count()
        return context


class ClientDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single client with notes, documents, contracts, and invoices."""
    template_name = 'clients/client_detail.html'
    model = Client
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notes'] = self.object.client_notes.select_related('author').all()[:20]
        context['documents'] = self.object.documents.all()[:20]
        context['contracts'] = self.object.contracts.all()[:10]
        context['invoices'] = self.object.invoices.all()[:10]
        context['portal_messages'] = self.object.portal_messages.all()[:10]
        context['page_title'] = f'Client: {self.object.get_display_name()}'
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    """Create a new client."""
    template_name = 'clients/client_create.html'
    model = Client
    fields = [
        'client_type', 'company_name', 'first_name', 'last_name',
        'email', 'phone', 'website', 'address_line1', 'address_line2',
        'city', 'state', 'postal_code', 'country', 'industry',
        'lifecycle_stage', 'source', 'notes',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add New Client'
        context['type_choices'] = Client.TYPE_CHOICES
        context['stage_choices'] = Client.STAGE_CHOICES
        return context


class ClientEditView(LoginRequiredMixin, TemplateView):
    """Edit an existing client."""
    template_name = 'clients/client_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = Client.objects.get(pk=self.kwargs['pk'])
        context['client'] = client
        context['page_title'] = f'Edit Client: {client.get_display_name()}'
        context['type_choices'] = Client.TYPE_CHOICES
        context['stage_choices'] = Client.STAGE_CHOICES
        return context


class ClientPortalView(LoginRequiredMixin, TemplateView):
    """Client portal view showing contracts, invoices, and documents for a client."""
    template_name = 'clients/client_portal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = Client.objects.get(pk=self.kwargs['pk'])
        context['client'] = client
        context['contracts'] = client.contracts.filter(status__in=['active', 'completed']).all()
        context['invoices'] = client.invoices.exclude(status='draft').all()
        context['documents'] = client.documents.all()
        context['portal_messages'] = client.portal_messages.order_by('-created_at')[:20]
        context['page_title'] = f'Portal: {client.get_display_name()}'
        return context


class PortalMessagesView(LoginRequiredMixin, ListView):
    """List of portal messages for a specific client."""
    template_name = 'clients/portal_messages.html'
    context_object_name = 'messages'

    def get_queryset(self):
        return PortalMessage.objects.filter(
            client_id=self.kwargs['pk']
        ).select_related('sender', 'client').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = Client.objects.get(pk=self.kwargs['pk'])
        context['client'] = client
        context['page_title'] = f'Messages: {client.get_display_name()}'
        context['unread_count'] = PortalMessage.objects.filter(
            client=client, is_read=False, is_from_client=True
        ).count()
        return context
