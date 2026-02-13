"""
Frontend views for the subscriptions app.

Provides class-based views for subscription plan listing,
subscription detail, and subscription management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView

from .models import SubscriptionPlan, Subscription


class SubscriptionPlanListView(LoginRequiredMixin, ListView):
    """List all available subscription plans."""
    template_name = 'subscriptions/plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Subscription Plans'
        context['interval_choices'] = SubscriptionPlan.INTERVAL_CHOICES
        # Get current user subscription if exists
        context['current_subscription'] = Subscription.objects.filter(
            user=self.request.user, status='active'
        ).select_related('plan').first()
        return context


class SubscriptionDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a user's subscription."""
    template_name = 'subscriptions/subscription_detail.html'
    model = Subscription
    context_object_name = 'subscription'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Subscription: {self.object.plan.name}'
        context['plan'] = self.object.plan
        context['is_active'] = self.object.is_active
        context['days_until_renewal'] = self.object.days_until_renewal
        context['cancel_at_period_end'] = self.object.cancel_at_period_end
        context['status_choices'] = Subscription.STATUS_CHOICES
        return context


class SubscriptionManageView(LoginRequiredMixin, TemplateView):
    """Subscription management page for upgrading, downgrading, or cancelling."""
    template_name = 'subscriptions/subscription_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Manage Subscription'
        context['current_subscription'] = Subscription.objects.filter(
            user=self.request.user, status='active'
        ).select_related('plan').first()
        context['available_plans'] = SubscriptionPlan.objects.filter(is_active=True)
        context['all_subscriptions'] = Subscription.objects.filter(
            user=self.request.user
        ).select_related('plan').order_by('-created_at')
        return context
