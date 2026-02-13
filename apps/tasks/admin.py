"""
Admin configuration for tasks app.
"""

from django.contrib import admin
from .models import Task, TaskComment


class TaskCommentInline(admin.TabularInline):
    """Inline admin for task comments."""
    model = TaskComment
    extra = 0
    fields = ['author', 'content', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin for Task model."""

    list_display = [
        'title', 'status', 'priority', 'assigned_to', 'client',
        'due_date', 'completed_at', 'created_by', 'created_at',
    ]
    list_filter = ['status', 'priority', 'assigned_to', 'client']
    search_fields = ['title', 'description', 'assigned_to__email', 'client__company_name', 'client__first_name', 'client__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [TaskCommentInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'status', 'priority')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Relations', {
            'fields': ('client', 'contract', 'invoice')
        }),
        ('Dates', {
            'fields': ('due_date', 'completed_at')
        }),
        ('Tags', {
            'fields': ('tags',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Admin for TaskComment model."""

    list_display = ['task', 'author', 'content', 'created_at']
    list_filter = ['author', 'created_at']
    search_fields = ['content', 'task__title', 'author__email']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'task', 'author', 'content')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
