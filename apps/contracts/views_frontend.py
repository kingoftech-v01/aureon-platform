"""
Frontend views for the contracts app.

Provides class-based views for contract listing, detail, creation, editing,
signing workflow, and milestone management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView

from .models import Contract, ContractMilestone


class ContractListView(LoginRequiredMixin, ListView):
    """List all contracts with filtering by status."""
    template_name = 'contracts/contract_list.html'
    context_object_name = 'contracts'

    def get_queryset(self):
        queryset = Contract.objects.select_related('client', 'owner').all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        search = self.request.GET.get('q')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(contract_number__icontains=search) |
                Q(client__company_name__icontains=search) |
                Q(client__first_name__icontains=search) |
                Q(client__last_name__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Contracts'
        context['status_choices'] = Contract.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['total_contracts'] = Contract.objects.count()
        context['active_contracts'] = Contract.objects.filter(status=Contract.ACTIVE).count()
        return context


class ContractDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single contract with milestones and invoices."""
    template_name = 'contracts/contract_detail.html'
    model = Contract
    context_object_name = 'contract'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['milestones'] = self.object.milestones.all()
        context['invoices'] = self.object.invoices.all()
        context['page_title'] = f'Contract: {self.object.contract_number} - {self.object.title}'
        context['is_signed'] = self.object.is_signed
        context['outstanding_amount'] = self.object.outstanding_amount
        context['completion_percentage'] = self.object.completion_percentage
        return context


class ContractCreateView(LoginRequiredMixin, CreateView):
    """Create a new contract."""
    template_name = 'contracts/contract_create.html'
    model = Contract
    fields = [
        'client', 'title', 'description', 'contract_type', 'start_date',
        'end_date', 'value', 'currency', 'hourly_rate', 'estimated_hours',
        'payment_terms', 'invoice_schedule', 'terms_and_conditions', 'notes',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Contract'
        context['type_choices'] = Contract.TYPE_CHOICES
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        return context


class ContractEditView(LoginRequiredMixin, TemplateView):
    """Edit an existing contract."""
    template_name = 'contracts/contract_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = Contract.objects.select_related('client', 'owner').get(pk=self.kwargs['pk'])
        context['contract'] = contract
        context['page_title'] = f'Edit Contract: {contract.contract_number}'
        context['type_choices'] = Contract.TYPE_CHOICES
        context['status_choices'] = Contract.STATUS_CHOICES
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        return context


class ContractSignView(LoginRequiredMixin, TemplateView):
    """Contract signing workflow page."""
    template_name = 'contracts/contract_sign.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = Contract.objects.select_related('client', 'owner').get(pk=self.kwargs['pk'])
        context['contract'] = contract
        context['page_title'] = f'Sign Contract: {contract.contract_number}'
        context['is_signed'] = contract.is_signed
        context['signed_by_client'] = contract.signed_by_client
        context['signed_by_company'] = contract.signed_by_company
        context['milestones'] = contract.milestones.all()
        return context


class MilestoneListView(LoginRequiredMixin, ListView):
    """List milestones for a specific contract."""
    template_name = 'contracts/milestone_list.html'
    context_object_name = 'milestones'

    def get_queryset(self):
        return ContractMilestone.objects.filter(
            contract_id=self.kwargs['pk']
        ).select_related('contract', 'completed_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = Contract.objects.get(pk=self.kwargs['pk'])
        context['contract'] = contract
        context['page_title'] = f'Milestones: {contract.contract_number}'
        context['status_choices'] = ContractMilestone.STATUS_CHOICES
        context['completed_count'] = self.get_queryset().filter(
            status=ContractMilestone.COMPLETED
        ).count()
        context['total_count'] = self.get_queryset().count()
        return context
