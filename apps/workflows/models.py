"""
Workflow models for automated triggers and actions.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Workflow(models.Model):
    """
    Workflow model representing an automated workflow with triggers and actions.
    """

    # Trigger Types
    CONTRACT_SIGNED = 'contract_signed'
    INVOICE_CREATED = 'invoice_created'
    INVOICE_OVERDUE = 'invoice_overdue'
    INVOICE_PAID = 'invoice_paid'
    PAYMENT_RECEIVED = 'payment_received'
    PAYMENT_FAILED = 'payment_failed'
    CLIENT_CREATED = 'client_created'
    CLIENT_UPDATED = 'client_updated'
    MILESTONE_COMPLETED = 'milestone_completed'
    SUBSCRIPTION_CANCELLED = 'subscription_cancelled'
    MANUAL = 'manual'

    TRIGGER_TYPE_CHOICES = [
        (CONTRACT_SIGNED, _('Contract Signed')),
        (INVOICE_CREATED, _('Invoice Created')),
        (INVOICE_OVERDUE, _('Invoice Overdue')),
        (INVOICE_PAID, _('Invoice Paid')),
        (PAYMENT_RECEIVED, _('Payment Received')),
        (PAYMENT_FAILED, _('Payment Failed')),
        (CLIENT_CREATED, _('Client Created')),
        (CLIENT_UPDATED, _('Client Updated')),
        (MILESTONE_COMPLETED, _('Milestone Completed')),
        (SUBSCRIPTION_CANCELLED, _('Subscription Cancelled')),
        (MANUAL, _('Manual')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        _('Name'),
        max_length=255,
        help_text=_('Name of the workflow')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description of what this workflow does')
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this workflow is currently active')
    )

    trigger_type = models.CharField(
        _('Trigger Type'),
        max_length=30,
        choices=TRIGGER_TYPE_CHOICES,
        help_text=_('Event that triggers this workflow')
    )

    trigger_config = models.JSONField(
        _('Trigger Configuration'),
        default=dict,
        blank=True,
        help_text=_('Additional trigger configuration in JSON format')
    )

    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflows',
        help_text=_('User who owns this workflow')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Workflow')
        verbose_name_plural = _('Workflows')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trigger_type']),
            models.Index(fields=['owner']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class WorkflowAction(models.Model):
    """
    Individual action within a workflow, executed in order.
    """

    # Action Types
    SEND_EMAIL = 'send_email'
    SEND_NOTIFICATION = 'send_notification'
    UPDATE_CLIENT_STAGE = 'update_client_stage'
    CREATE_TASK = 'create_task'
    CREATE_INVOICE = 'create_invoice'
    WEBHOOK_CALL = 'webhook_call'

    ACTION_TYPE_CHOICES = [
        (SEND_EMAIL, _('Send Email')),
        (SEND_NOTIFICATION, _('Send Notification')),
        (UPDATE_CLIENT_STAGE, _('Update Client Stage')),
        (CREATE_TASK, _('Create Task')),
        (CREATE_INVOICE, _('Create Invoice')),
        (WEBHOOK_CALL, _('Webhook Call')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='actions',
        help_text=_('Workflow this action belongs to')
    )

    action_type = models.CharField(
        _('Action Type'),
        max_length=30,
        choices=ACTION_TYPE_CHOICES,
        help_text=_('Type of action to perform')
    )

    action_config = models.JSONField(
        _('Action Configuration'),
        default=dict,
        blank=True,
        help_text=_('Action configuration in JSON format')
    )

    order = models.IntegerField(
        _('Order'),
        default=0,
        help_text=_('Execution order of this action within the workflow')
    )

    delay_minutes = models.IntegerField(
        _('Delay (minutes)'),
        default=0,
        help_text=_('Delay in minutes before executing this action')
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this action is currently active')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Workflow Action')
        verbose_name_plural = _('Workflow Actions')
        ordering = ['order']
        unique_together = [['workflow', 'order']]

    def __str__(self):
        return f"{self.workflow.name} - {self.action_type} (#{self.order})"


class WorkflowExecution(models.Model):
    """
    Record of a workflow execution, tracking status and results.
    """

    # Execution Status
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (RUNNING, _('Running')),
        (COMPLETED, _('Completed')),
        (FAILED, _('Failed')),
        (CANCELLED, _('Cancelled')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='executions',
        help_text=_('Workflow that was executed')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        help_text=_('Current execution status')
    )

    triggered_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_executions',
        help_text=_('User who triggered the execution')
    )

    trigger_data = models.JSONField(
        _('Trigger Data'),
        default=dict,
        blank=True,
        help_text=_('Data associated with the trigger event')
    )

    started_at = models.DateTimeField(
        _('Started At'),
        null=True,
        blank=True,
        help_text=_('When the execution started')
    )

    completed_at = models.DateTimeField(
        _('Completed At'),
        null=True,
        blank=True,
        help_text=_('When the execution completed')
    )

    error_message = models.TextField(
        _('Error Message'),
        blank=True,
        help_text=_('Error message if execution failed')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Workflow Execution')
        verbose_name_plural = _('Workflow Executions')
        ordering = ['-created_at']

    def __str__(self):
        return f"Execution of {self.workflow.name} - {self.status}"

    @property
    def duration(self):
        """Return the duration of the execution as a timedelta."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class WorkflowActionExecution(models.Model):
    """
    Record of an individual action execution within a workflow execution.
    """

    # Execution Status
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (RUNNING, _('Running')),
        (COMPLETED, _('Completed')),
        (FAILED, _('Failed')),
        (SKIPPED, _('Skipped')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name='action_executions',
        help_text=_('Parent workflow execution')
    )

    action = models.ForeignKey(
        WorkflowAction,
        on_delete=models.CASCADE,
        related_name='executions',
        help_text=_('Workflow action that was executed')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        help_text=_('Current action execution status')
    )

    result_data = models.JSONField(
        _('Result Data'),
        default=dict,
        blank=True,
        help_text=_('Result data from the action execution')
    )

    started_at = models.DateTimeField(
        _('Started At'),
        null=True,
        blank=True,
        help_text=_('When the action execution started')
    )

    completed_at = models.DateTimeField(
        _('Completed At'),
        null=True,
        blank=True,
        help_text=_('When the action execution completed')
    )

    error_message = models.TextField(
        _('Error Message'),
        blank=True,
        help_text=_('Error message if action execution failed')
    )

    class Meta:
        verbose_name = _('Workflow Action Execution')
        verbose_name_plural = _('Workflow Action Executions')
        ordering = ['action__order']

    def __str__(self):
        return f"Action execution {self.action.action_type} - {self.status}"
