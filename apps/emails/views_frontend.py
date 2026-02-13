"""
Frontend views for the emails app.

Provides class-based views for email inbox, detail, compose,
account settings, and email template management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Q

from .models import EmailAccount, EmailMessage, EmailAttachment, EmailTemplate


class EmailInboxView(LoginRequiredMixin, ListView):
    """Email inbox view showing all messages for the current user's accounts."""
    template_name = 'emails/email_inbox.html'
    context_object_name = 'emails'

    def get_queryset(self):
        user_accounts = EmailAccount.objects.filter(user=self.request.user)
        queryset = EmailMessage.objects.filter(
            account__in=user_accounts
        ).select_related('account', 'client')
        direction = self.request.GET.get('direction')
        if direction:
            queryset = queryset.filter(direction=direction)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(subject__icontains=search) |
                Q(from_email__icontains=search) |
                Q(body_text__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Email Inbox'
        context['direction_choices'] = EmailMessage.DIRECTION_CHOICES
        context['status_choices'] = EmailMessage.STATUS_CHOICES
        context['current_direction'] = self.request.GET.get('direction', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        user_accounts = EmailAccount.objects.filter(user=self.request.user)
        context['accounts'] = user_accounts
        context['unread_count'] = EmailMessage.objects.filter(
            account__in=user_accounts, is_read=False, direction=EmailMessage.INBOUND
        ).count()
        return context


class EmailDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single email message with attachments."""
    template_name = 'emails/email_detail.html'
    model = EmailMessage
    context_object_name = 'email'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Email: {self.object.subject}'
        context['attachments'] = self.object.attachments.all()
        context['replies'] = self.object.replies.all()
        context['client'] = self.object.client
        context['contract'] = self.object.contract
        context['invoice'] = self.object.invoice
        context['is_read'] = self.object.is_read
        context['from_email'] = self.object.from_email
        context['to_emails'] = self.object.to_emails
        context['cc_emails'] = self.object.cc_emails
        return context


class EmailComposeView(LoginRequiredMixin, TemplateView):
    """Email compose view for creating and sending new emails."""
    template_name = 'emails/email_compose.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Compose Email'
        context['accounts'] = EmailAccount.objects.filter(
            user=self.request.user, is_active=True
        )
        context['templates'] = EmailTemplate.objects.filter(is_active=True)
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        # If replying to an email, include the original
        reply_to_id = self.request.GET.get('reply_to')
        if reply_to_id:
            context['reply_to'] = EmailMessage.objects.get(pk=reply_to_id)
        return context


class EmailAccountSettingsView(LoginRequiredMixin, ListView):
    """Email account settings showing all configured email accounts."""
    template_name = 'emails/email_account_settings.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return EmailAccount.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Email Account Settings'
        context['provider_choices'] = EmailAccount.PROVIDER_CHOICES
        context['total_accounts'] = EmailAccount.objects.filter(
            user=self.request.user
        ).count()
        context['default_account'] = EmailAccount.objects.filter(
            user=self.request.user, is_default=True
        ).first()
        return context


class EmailTemplateListView(LoginRequiredMixin, ListView):
    """List all email templates for management and reuse."""
    template_name = 'emails/email_template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return EmailTemplate.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Email Templates'
        context['category_choices'] = EmailTemplate.CATEGORY_CHOICES
        context['active_count'] = EmailTemplate.objects.filter(is_active=True).count()
        context['total_count'] = EmailTemplate.objects.count()
        return context
