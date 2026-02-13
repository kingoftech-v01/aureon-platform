"""
Frontend views for the tasks app.

Provides class-based views for task listing, detail, creation,
and kanban board view.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.db.models import Q

from .models import Task, TaskComment


class TaskListView(LoginRequiredMixin, ListView):
    """List all tasks with filtering by status, priority, and assignee."""
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        queryset = Task.objects.select_related(
            'assigned_to', 'created_by', 'client', 'contract'
        ).all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        assigned = self.request.GET.get('assigned')
        if assigned == 'me':
            queryset = queryset.filter(assigned_to=self.request.user)
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tasks'
        context['status_choices'] = Task.STATUS_CHOICES
        context['priority_choices'] = Task.PRIORITY_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        context['current_assigned'] = self.request.GET.get('assigned', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['my_task_count'] = Task.objects.filter(
            assigned_to=self.request.user
        ).exclude(status=Task.DONE).count()
        context['overdue_count'] = Task.objects.filter(
            assigned_to=self.request.user,
            due_date__lt=__import__('django.utils', fromlist=['timezone']).timezone.now(),
            status__in=[Task.TODO, Task.IN_PROGRESS]
        ).count()
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single task with comments and related entities."""
    template_name = 'tasks/task_detail.html'
    model = Task
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Task: {self.object.title}'
        context['comments'] = self.object.comments.select_related('author').all()
        context['is_overdue'] = self.object.is_overdue
        context['assigned_to'] = self.object.assigned_to
        context['created_by'] = self.object.created_by
        context['client'] = self.object.client
        context['contract'] = self.object.contract
        context['invoice'] = self.object.invoice
        context['status_choices'] = Task.STATUS_CHOICES
        context['priority_choices'] = Task.PRIORITY_CHOICES
        return context


class TaskCreateView(LoginRequiredMixin, CreateView):
    """Create a new task."""
    template_name = 'tasks/task_create.html'
    model = Task
    fields = [
        'title', 'description', 'status', 'priority', 'due_date',
        'assigned_to', 'client', 'contract', 'invoice', 'tags',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Task'
        context['status_choices'] = Task.STATUS_CHOICES
        context['priority_choices'] = Task.PRIORITY_CHOICES
        from apps.accounts.models import User
        context['users'] = User.objects.filter(is_active=True)
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        from apps.contracts.models import Contract
        context['contracts'] = Contract.objects.filter(status=Contract.ACTIVE)
        return context


class TaskBoardView(LoginRequiredMixin, TemplateView):
    """Kanban board view of tasks grouped by status."""
    template_name = 'tasks/task_board.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Task Board'
        base_queryset = Task.objects.select_related(
            'assigned_to', 'client'
        )
        assigned = self.request.GET.get('assigned')
        if assigned == 'me':
            base_queryset = base_queryset.filter(assigned_to=self.request.user)
        context['todo_tasks'] = base_queryset.filter(status=Task.TODO)
        context['in_progress_tasks'] = base_queryset.filter(status=Task.IN_PROGRESS)
        context['done_tasks'] = base_queryset.filter(status=Task.DONE)[:20]
        context['cancelled_tasks'] = base_queryset.filter(status=Task.CANCELLED)[:10]
        context['priority_choices'] = Task.PRIORITY_CHOICES
        context['current_assigned'] = self.request.GET.get('assigned', '')
        return context
