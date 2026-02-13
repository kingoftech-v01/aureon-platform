"""
Frontend views for the ai_assistant app.

Provides class-based views for AI dashboard, suggestions, cash flow predictions,
and insights management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView

from .models import AISuggestion, CashFlowPrediction, AIInsight


class AIDashboardView(LoginRequiredMixin, TemplateView):
    """AI Assistant dashboard with overview of suggestions, predictions, and insights."""
    template_name = 'ai_assistant/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['page_title'] = 'AI Assistant'
        context['pending_suggestions'] = AISuggestion.objects.filter(
            user=user, status=AISuggestion.PENDING
        )[:5]
        context['recent_predictions'] = CashFlowPrediction.objects.filter(
            user=user
        )[:7]
        context['unread_insights'] = AIInsight.objects.filter(
            user=user, is_read=False
        )[:5]
        context['suggestion_count'] = AISuggestion.objects.filter(
            user=user, status=AISuggestion.PENDING
        ).count()
        context['insight_count'] = AIInsight.objects.filter(
            user=user, is_read=False
        ).count()
        return context


class SuggestionListView(LoginRequiredMixin, ListView):
    """List all AI suggestions with filtering by type and status."""
    template_name = 'ai_assistant/suggestion_list.html'
    context_object_name = 'suggestions'
    paginate_by = 20

    def get_queryset(self):
        queryset = AISuggestion.objects.filter(user=self.request.user)
        suggestion_type = self.request.GET.get('type')
        if suggestion_type:
            queryset = queryset.filter(suggestion_type=suggestion_type)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'AI Suggestions'
        context['type_choices'] = AISuggestion.SUGGESTION_TYPE_CHOICES
        context['status_choices'] = AISuggestion.STATUS_CHOICES
        context['priority_choices'] = AISuggestion.PRIORITY_CHOICES
        context['current_type'] = self.request.GET.get('type', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        return context


class SuggestionDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single AI suggestion."""
    template_name = 'ai_assistant/suggestion_detail.html'
    context_object_name = 'suggestion'

    def get_queryset(self):
        return AISuggestion.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.title
        return context


class CashFlowPredictionView(LoginRequiredMixin, ListView):
    """Cash flow predictions timeline view."""
    template_name = 'ai_assistant/cash_flow_predictions.html'
    context_object_name = 'predictions'
    paginate_by = 30

    def get_queryset(self):
        return CashFlowPrediction.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Cash Flow Predictions'
        return context


class InsightListView(LoginRequiredMixin, ListView):
    """List all AI insights with filtering by type and severity."""
    template_name = 'ai_assistant/insight_list.html'
    context_object_name = 'insights'
    paginate_by = 20

    def get_queryset(self):
        queryset = AIInsight.objects.filter(user=self.request.user)
        insight_type = self.request.GET.get('type')
        if insight_type:
            queryset = queryset.filter(insight_type=insight_type)
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        is_read = self.request.GET.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read == 'true')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'AI Insights'
        context['type_choices'] = AIInsight.INSIGHT_TYPE_CHOICES
        context['severity_choices'] = AIInsight.SEVERITY_CHOICES
        context['current_type'] = self.request.GET.get('type', '')
        context['current_severity'] = self.request.GET.get('severity', '')
        return context


class InsightDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single AI insight."""
    template_name = 'ai_assistant/insight_detail.html'
    context_object_name = 'insight'

    def get_queryset(self):
        return AIInsight.objects.filter(user=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_read:
            obj.mark_as_read()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.title
        return context
