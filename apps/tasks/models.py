"""
Task and activity management models.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Task(models.Model):
    """
    Task model for tracking work items tied to clients, contracts, and invoices.
    """

    # Task Status
    TODO = 'todo'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (TODO, _('To Do')),
        (IN_PROGRESS, _('In Progress')),
        (DONE, _('Done')),
        (CANCELLED, _('Cancelled')),
    ]

    # Task Priority
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'

    PRIORITY_CHOICES = [
        (LOW, _('Low')),
        (MEDIUM, _('Medium')),
        (HIGH, _('High')),
        (URGENT, _('Urgent')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    title = models.CharField(
        _('Title'),
        max_length=255,
        help_text=_('Brief title describing the task')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Detailed description of the task')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=TODO
    )

    priority = models.CharField(
        _('Priority'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=MEDIUM
    )

    due_date = models.DateTimeField(
        _('Due Date'),
        null=True,
        blank=True,
        help_text=_('Task due date and time')
    )

    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        help_text=_('User assigned to this task')
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='created_tasks',
        help_text=_('User who created this task')
    )

    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        help_text=_('Client associated with this task')
    )

    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        help_text=_('Contract associated with this task')
    )

    invoice = models.ForeignKey(
        'invoicing.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        help_text=_('Invoice associated with this task')
    )

    tags = models.JSONField(
        _('Tags'),
        default=list,
        blank=True,
        help_text=_('Tags for categorization')
    )

    completed_at = models.DateTimeField(
        _('Completed At'),
        null=True,
        blank=True,
        help_text=_('When the task was completed')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['due_date']),
            models.Index(fields=['client']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        """Check if task is overdue."""
        from django.utils import timezone
        if self.status in [self.DONE, self.CANCELLED]:
            return False
        if self.due_date is None:
            return False
        return timezone.now() > self.due_date


class TaskComment(models.Model):
    """
    Comment on a task.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text=_('Task this comment belongs to')
    )

    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='task_comments',
        help_text=_('User who wrote this comment')
    )

    content = models.TextField(
        _('Content'),
        help_text=_('Comment content')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Task Comment')
        verbose_name_plural = _('Task Comments')
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.task.title} by {self.author}"
