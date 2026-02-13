"""
Frontend views for the accounts app.

Provides class-based views for login, registration, profile management,
team management, user listing, invitations, and two-factor authentication setup.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView

from .models import User, Team, TeamMember, UserInvitation


class LoginPageView(TemplateView):
    """Public login page."""
    template_name = 'accounts/login.html'


class RegisterPageView(TemplateView):
    """Public registration page."""
    template_name = 'accounts/register.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile page showing current user details."""
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['page_title'] = 'My Profile'
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    """Account settings page for managing preferences and security."""
    template_name = 'accounts/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['page_title'] = 'Account Settings'
        return context


class TeamListView(LoginRequiredMixin, ListView):
    """List of teams the current user owns or belongs to."""
    template_name = 'accounts/team_list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        from django.db.models import Q
        return Team.objects.filter(
            Q(owner=self.request.user) | Q(members__user=self.request.user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Teams'
        return context


class TeamDetailView(LoginRequiredMixin, DetailView):
    """Detail view of a specific team with members and pending invitations."""
    template_name = 'accounts/team_detail.html'
    model = Team
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['members'] = self.object.members.select_related('user').all()
        context['invitations'] = self.object.invitations.filter(status='pending')
        context['page_title'] = f'Team: {self.object.name}'
        return context


class UserListView(LoginRequiredMixin, ListView):
    """List of all active users in the system."""
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Users'
        return context


class InvitationListView(LoginRequiredMixin, ListView):
    """List of all user invitations."""
    template_name = 'accounts/invitation_list.html'
    context_object_name = 'invitations'
    model = UserInvitation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Invitations'
        return context


class TwoFactorSetupView(LoginRequiredMixin, TemplateView):
    """Two-factor authentication setup and management page."""
    template_name = 'accounts/two_factor_setup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['two_factor_enabled'] = self.request.user.two_factor_enabled
        context['page_title'] = 'Two-Factor Authentication'
        return context
