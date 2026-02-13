"""
Admin configuration for ai_assistant app.
"""

from django.contrib import admin
from .models import AISuggestion, CashFlowPrediction, AIInsight


@admin.register(AISuggestion)
class AISuggestionAdmin(admin.ModelAdmin):
    """Admin for AISuggestion model."""

    list_display = [
        'title', 'suggestion_type', 'priority', 'status',
        'user', 'client', 'expires_at', 'created_at',
    ]
    list_filter = ['suggestion_type', 'priority', 'status']
    search_fields = ['title', 'description', 'user__email', 'client__first_name', 'client__last_name']
    readonly_fields = ['id', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'suggestion_type', 'title', 'description', 'detail', 'priority', 'status')
        }),
        ('Relationships', {
            'fields': ('user', 'client', 'contract', 'invoice')
        }),
        ('Timing', {
            'fields': ('expires_at', 'accepted_at', 'dismissed_at')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CashFlowPrediction)
class CashFlowPredictionAdmin(admin.ModelAdmin):
    """Admin for CashFlowPrediction model."""

    list_display = [
        'prediction_date', 'user', 'predicted_income', 'predicted_expenses',
        'predicted_net', 'confidence_score', 'actual_income', 'actual_expenses',
        'created_at',
    ]
    list_filter = ['prediction_date', 'user']
    search_fields = ['user__email']
    readonly_fields = ['id', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'prediction_date')
        }),
        ('Predictions', {
            'fields': ('predicted_income', 'predicted_expenses', 'predicted_net', 'confidence_score')
        }),
        ('Actuals', {
            'fields': ('actual_income', 'actual_expenses')
        }),
        ('Analysis', {
            'fields': ('factors',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    """Admin for AIInsight model."""

    list_display = [
        'title', 'insight_type', 'severity', 'user',
        'is_read', 'read_at', 'created_at',
    ]
    list_filter = ['insight_type', 'severity', 'is_read']
    search_fields = ['title', 'description', 'user__email']
    readonly_fields = ['id', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'insight_type', 'title', 'description', 'data', 'severity')
        }),
        ('Relationships', {
            'fields': ('user',)
        }),
        ('Read Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
