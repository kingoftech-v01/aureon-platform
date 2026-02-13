"""
Frontend views for the notifications app.

Provides class-based views for notification listing, notification settings,
and notification template management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView

from .models import Notification, NotificationTemplate


class NotificationListView(LoginRequiredMixin, ListView):
    """List all notifications for the current user."""
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        channel = self.request.GET.get('channel')
        if channel:
            queryset = queryset.filter(channel=channel)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Notifications'
        context['status_choices'] = Notification.STATUS_CHOICES
        context['channel_choices'] = NotificationTemplate.CHANNEL_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_channel'] = self.request.GET.get('channel', '')
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user
        ).exclude(status=Notification.READ).count()
        context['total_count'] = Notification.objects.filter(
            user=self.request.user
        ).count()
        return context


class NotificationSettingsView(LoginRequiredMixin, TemplateView):
    """Notification preferences and settings page for the current user."""
    template_name = 'notifications/notification_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Notification Settings'
        context['user'] = self.request.user
        context['email_notifications'] = self.request.user.email_notifications
        context['sms_notifications'] = self.request.user.sms_notifications
        context['templates'] = NotificationTemplate.objects.filter(is_active=True)
        return context


class NotificationTemplateListView(LoginRequiredMixin, ListView):
    """List all notification templates for management."""
    template_name = 'notifications/notification_template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return NotificationTemplate.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Notification Templates'
        context['template_type_choices'] = NotificationTemplate.TEMPLATE_TYPE_CHOICES
        context['channel_choices'] = NotificationTemplate.CHANNEL_CHOICES
        context['active_count'] = NotificationTemplate.objects.filter(is_active=True).count()
        context['total_count'] = NotificationTemplate.objects.count()
        return context
