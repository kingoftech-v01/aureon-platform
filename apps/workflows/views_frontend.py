"""
Frontend views for the workflows app.

Provides class-based views for workflow listing, detail, creation,
editing, and execution history.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView

from .models import Workflow, WorkflowAction, WorkflowExecution, WorkflowActionExecution


class WorkflowListView(LoginRequiredMixin, ListView):
    """List all workflows with filtering by trigger type and active status."""
    template_name = 'workflows/workflow_list.html'
    context_object_name = 'workflows'

    def get_queryset(self):
        queryset = Workflow.objects.select_related('owner').all()
        trigger_type = self.request.GET.get('trigger_type')
        if trigger_type:
            queryset = queryset.filter(trigger_type=trigger_type)
        active_only = self.request.GET.get('active')
        if active_only == 'true':
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Workflows'
        context['trigger_type_choices'] = Workflow.TRIGGER_TYPE_CHOICES
        context['current_trigger_type'] = self.request.GET.get('trigger_type', '')
        context['active_count'] = Workflow.objects.filter(is_active=True).count()
        context['total_count'] = Workflow.objects.count()
        return context


class WorkflowDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a workflow with its actions and recent executions."""
    template_name = 'workflows/workflow_detail.html'
    model = Workflow
    context_object_name = 'workflow'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Workflow: {self.object.name}'
        context['actions'] = self.object.actions.all()
        context['recent_executions'] = self.object.executions.all()[:20]
        context['trigger_type_display'] = self.object.get_trigger_type_display()
        context['is_active'] = self.object.is_active
        context['total_executions'] = self.object.executions.count()
        context['successful_executions'] = self.object.executions.filter(
            status=WorkflowExecution.COMPLETED
        ).count()
        context['failed_executions'] = self.object.executions.filter(
            status=WorkflowExecution.FAILED
        ).count()
        return context


class WorkflowCreateView(LoginRequiredMixin, CreateView):
    """Create a new workflow."""
    template_name = 'workflows/workflow_create.html'
    model = Workflow
    fields = ['name', 'description', 'trigger_type', 'trigger_config', 'is_active']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Workflow'
        context['trigger_type_choices'] = Workflow.TRIGGER_TYPE_CHOICES
        context['action_type_choices'] = WorkflowAction.ACTION_TYPE_CHOICES
        return context


class WorkflowEditView(LoginRequiredMixin, TemplateView):
    """Edit an existing workflow and its actions."""
    template_name = 'workflows/workflow_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workflow = Workflow.objects.get(pk=self.kwargs['pk'])
        context['workflow'] = workflow
        context['actions'] = workflow.actions.all()
        context['page_title'] = f'Edit Workflow: {workflow.name}'
        context['trigger_type_choices'] = Workflow.TRIGGER_TYPE_CHOICES
        context['action_type_choices'] = WorkflowAction.ACTION_TYPE_CHOICES
        return context


class WorkflowExecutionListView(LoginRequiredMixin, ListView):
    """List all workflow executions across all workflows."""
    template_name = 'workflows/workflow_execution_list.html'
    context_object_name = 'executions'

    def get_queryset(self):
        queryset = WorkflowExecution.objects.select_related(
            'workflow', 'triggered_by'
        ).all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        workflow_id = self.request.GET.get('workflow')
        if workflow_id:
            queryset = queryset.filter(workflow_id=workflow_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Workflow Executions'
        context['status_choices'] = WorkflowExecution.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['workflows'] = Workflow.objects.all()
        context['current_workflow'] = self.request.GET.get('workflow', '')
        context['total_executions'] = WorkflowExecution.objects.count()
        context['running_count'] = WorkflowExecution.objects.filter(
            status=WorkflowExecution.RUNNING
        ).count()
        return context
