"""
Admin configuration for workflows app.
"""

from django.contrib import admin
from .models import (
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    WorkflowActionExecution,
)


class WorkflowActionInline(admin.TabularInline):
    """Inline admin for workflow actions."""
    model = WorkflowAction
    extra = 1
    fields = ['action_type', 'order', 'delay_minutes', 'is_active']
    ordering = ['order']


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    """Admin for Workflow model."""

    list_display = [
        'name', 'trigger_type', 'is_active', 'owner', 'created_at', 'updated_at',
    ]
    list_filter = ['trigger_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WorkflowActionInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active'),
        }),
        ('Trigger', {
            'fields': ('trigger_type', 'trigger_config'),
        }),
        ('Ownership', {
            'fields': ('owner',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(WorkflowAction)
class WorkflowActionAdmin(admin.ModelAdmin):
    """Admin for WorkflowAction model."""

    list_display = [
        'workflow', 'action_type', 'order', 'delay_minutes', 'is_active',
        'created_at',
    ]
    list_filter = ['action_type', 'is_active']
    search_fields = ['workflow__name', 'action_type']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('workflow', 'action_type', 'order', 'delay_minutes', 'is_active'),
        }),
        ('Configuration', {
            'fields': ('action_config',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    """Admin for WorkflowExecution model."""

    list_display = [
        'workflow', 'status', 'triggered_by', 'started_at',
        'completed_at', 'created_at',
    ]
    list_filter = ['status']
    search_fields = ['workflow__name', 'error_message']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Execution Information', {
            'fields': ('workflow', 'status', 'triggered_by'),
        }),
        ('Trigger Data', {
            'fields': ('trigger_data',),
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at'),
        }),
        ('Error', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


@admin.register(WorkflowActionExecution)
class WorkflowActionExecutionAdmin(admin.ModelAdmin):
    """Admin for WorkflowActionExecution model."""

    list_display = [
        'execution', 'action', 'status', 'started_at', 'completed_at',
    ]
    list_filter = ['status']
    search_fields = ['execution__workflow__name', 'action__action_type', 'error_message']

    fieldsets = (
        ('Execution Information', {
            'fields': ('execution', 'action', 'status'),
        }),
        ('Result', {
            'fields': ('result_data',),
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at'),
        }),
        ('Error', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
    )
