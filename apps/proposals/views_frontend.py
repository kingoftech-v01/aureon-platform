"""
Frontend views for the proposals app.

Provides class-based views for proposal listing, detail, creation,
editing, and the public client-facing proposal view.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.db.models import Q

from .models import Proposal, ProposalSection, ProposalPricingOption, ProposalActivity


class ProposalListView(LoginRequiredMixin, ListView):
    """List all proposals with filtering by status and search."""
    template_name = 'proposals/proposal_list.html'
    context_object_name = 'proposals'

    def get_queryset(self):
        queryset = Proposal.objects.select_related('client', 'owner', 'contract').all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(proposal_number__icontains=search) |
                Q(client__company_name__icontains=search) |
                Q(client__first_name__icontains=search) |
                Q(client__last_name__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Proposals'
        context['status_choices'] = Proposal.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['total_proposals'] = Proposal.objects.count()
        context['pending_count'] = Proposal.objects.filter(
            status__in=[Proposal.SENT, Proposal.VIEWED]
        ).count()
        context['accepted_count'] = Proposal.objects.filter(
            status=Proposal.ACCEPTED
        ).count()
        return context


class ProposalDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single proposal with sections, pricing, and activity."""
    template_name = 'proposals/proposal_detail.html'
    model = Proposal
    context_object_name = 'proposal'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Proposal: {self.object.proposal_number} - {self.object.title}'
        context['sections'] = self.object.sections.all()
        context['pricing_options'] = self.object.pricing_options.all()
        context['activities'] = self.object.activities.select_related('user').all()[:20]
        context['is_expired'] = self.object.is_expired
        context['client'] = self.object.client
        context['contract'] = self.object.contract
        return context


class ProposalCreateView(LoginRequiredMixin, CreateView):
    """Create a new proposal."""
    template_name = 'proposals/proposal_create.html'
    model = Proposal
    fields = [
        'client', 'title', 'description', 'valid_until',
        'total_value', 'currency',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Proposal'
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        context['section_type_choices'] = ProposalSection.SECTION_TYPE_CHOICES
        return context


class ProposalEditView(LoginRequiredMixin, TemplateView):
    """Edit an existing proposal with sections and pricing options."""
    template_name = 'proposals/proposal_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proposal = Proposal.objects.select_related('client', 'owner').get(pk=self.kwargs['pk'])
        context['proposal'] = proposal
        context['sections'] = proposal.sections.all()
        context['pricing_options'] = proposal.pricing_options.all()
        context['page_title'] = f'Edit Proposal: {proposal.proposal_number}'
        context['status_choices'] = Proposal.STATUS_CHOICES
        context['section_type_choices'] = ProposalSection.SECTION_TYPE_CHOICES
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        return context


class ProposalClientView(TemplateView):
    """Public client-facing proposal view -- no login required.

    Allows clients to view, accept, or decline proposals via a unique link.
    """
    template_name = 'proposals/proposal_client.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proposal = Proposal.objects.select_related('client', 'owner').get(pk=self.kwargs['pk'])
        context['proposal'] = proposal
        context['sections'] = proposal.sections.all()
        context['pricing_options'] = proposal.pricing_options.all()
        context['page_title'] = f'Proposal: {proposal.title}'
        context['is_expired'] = proposal.is_expired
        context['client'] = proposal.client
        context['total_value'] = proposal.total_value
        context['valid_until'] = proposal.valid_until
        return context
