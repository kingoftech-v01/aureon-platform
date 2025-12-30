from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SubscriptionPlan, Subscription


class SubscriptionPlanListView(ListView):
    """List available subscription plans."""
    model = SubscriptionPlan
    template_name = 'subscriptions/plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_active=True)


class UserSubscriptionView(LoginRequiredMixin, DetailView):
    """View user's current subscription."""
    model = Subscription
    template_name = 'subscriptions/subscription_detail.html'
    context_object_name = 'subscription'

    def get_object(self):
        return Subscription.objects.filter(
            user=self.request.user,
            status='active'
        ).first()
