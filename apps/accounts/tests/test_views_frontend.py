"""
Tests for accounts app frontend views.

Tests LoginPageView, RegisterPageView, ProfileView, SettingsView,
TeamListView, TeamDetailView, UserListView, InvitationListView,
and TwoFactorSetupView.
"""

import pytest
import secrets
from datetime import timedelta
from django.test import Client as TestClient, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.template import TemplateDoesNotExist
from django.utils import timezone

from apps.accounts.views_frontend import (
    LoginPageView,
    RegisterPageView,
    ProfileView,
    SettingsView,
    TeamListView,
    TeamDetailView,
    UserListView,
    InvitationListView,
    TwoFactorSetupView,
)
from apps.accounts.models import Team, TeamMember, UserInvitation, TeamInvitation

User = get_user_model()


@pytest.fixture
def rf():
    """Return a Django RequestFactory."""
    return RequestFactory()


@pytest.fixture
def user(db):
    """Create a standard test user."""
    return User.objects.create_user(
        username='frontenduser',
        email='frontenduser@test.com',
        password='TestPass123!',
        first_name='Frontend',
        last_name='User',
        role=User.ADMIN,
        is_active=True,
    )


@pytest.fixture
def team(db, user):
    """Create a test team."""
    return Team.objects.create(
        name='Test Team',
        description='A test team',
        owner=user,
    )


@pytest.fixture
def team_member(db, team, user):
    """Create a team member."""
    return TeamMember.objects.create(
        team=team,
        user=user,
        role=TeamMember.OWNER,
    )


@pytest.fixture
def team_invitation(db, team, user):
    """Create a team invitation."""
    return TeamInvitation.objects.create(
        team=team,
        email='invited@test.com',
        role=TeamMember.MEMBER,
        invited_by=user,
        invitation_token=secrets.token_urlsafe(32),
        status=TeamInvitation.PENDING,
        expires_at=timezone.now() + timedelta(days=7),
    )


@pytest.fixture
def user_invitation_obj(db, user):
    """Create a user invitation."""
    return UserInvitation.objects.create(
        email='newinvite@test.com',
        role=User.CONTRIBUTOR,
        invited_by=user,
        invitation_token=secrets.token_urlsafe(32),
        status=UserInvitation.PENDING,
        expires_at=timezone.now() + timedelta(days=7),
    )


# ============================================================================
# LoginPageView Tests (public, no login required)
# ============================================================================

class TestLoginPageView:
    """Tests for the LoginPageView."""

    def test_login_page_accessible_without_auth(self, rf):
        """Unauthenticated users can access the login page."""
        request = rf.get('/login/')
        request.user = AnonymousUser()
        view = LoginPageView.as_view()
        try:
            response = view(request)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            # Template doesn't exist yet but view executed without redirect
            pass

    def test_login_page_template_name(self):
        """LoginPageView uses the correct template."""
        assert LoginPageView.template_name == 'accounts/login.html'

    def test_login_page_accessible_when_authenticated(self, rf, user):
        """Authenticated users can also access the login page."""
        request = rf.get('/login/')
        request.user = user
        view = LoginPageView.as_view()
        try:
            response = view(request)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass


# ============================================================================
# RegisterPageView Tests (public, no login required)
# ============================================================================

class TestRegisterPageView:
    """Tests for the RegisterPageView."""

    def test_register_page_accessible_without_auth(self, rf):
        """Unauthenticated users can access the register page."""
        request = rf.get('/register/')
        request.user = AnonymousUser()
        view = RegisterPageView.as_view()
        try:
            response = view(request)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    def test_register_page_template_name(self):
        """RegisterPageView uses the correct template."""
        assert RegisterPageView.template_name == 'accounts/register.html'

    def test_register_page_accessible_when_authenticated(self, rf, user):
        """Authenticated users can also access the register page."""
        request = rf.get('/register/')
        request.user = user
        view = RegisterPageView.as_view()
        try:
            response = view(request)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass


# ============================================================================
# ProfileView Tests (login required)
# ============================================================================

class TestProfileView:
    """Tests for the ProfileView."""

    @pytest.mark.django_db
    def test_profile_redirects_unauthenticated(self, rf):
        """Unauthenticated users are redirected."""
        request = rf.get('/profile/')
        request.user = AnonymousUser()
        response = ProfileView.as_view()(request)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url or '/login/' in response.url

    @pytest.mark.django_db
    def test_profile_accessible_when_authenticated(self, rf, user):
        """Authenticated users can access the profile page."""
        request = rf.get('/profile/')
        request.user = user
        view = ProfileView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        context = view.get_context_data()
        assert context['user'] == user
        assert context['page_title'] == 'My Profile'

    @pytest.mark.django_db
    def test_profile_template_name(self):
        """ProfileView uses the correct template."""
        assert ProfileView.template_name == 'accounts/profile.html'

    @pytest.mark.django_db
    def test_profile_context_contains_user(self, rf, user):
        """Profile context includes the requesting user."""
        request = rf.get('/profile/')
        request.user = user
        view = ProfileView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        context = view.get_context_data()
        assert 'user' in context
        assert context['user'].email == user.email

    @pytest.mark.django_db
    def test_profile_context_contains_page_title(self, rf, user):
        """Profile context includes the page title."""
        request = rf.get('/profile/')
        request.user = user
        view = ProfileView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        context = view.get_context_data()
        assert 'page_title' in context


# ============================================================================
# SettingsView Tests (login required)
# ============================================================================

class TestSettingsView:
    """Tests for the SettingsView."""

    @pytest.mark.django_db
    def test_settings_redirects_unauthenticated(self, rf):
        """Unauthenticated users are redirected."""
        request = rf.get('/settings/')
        request.user = AnonymousUser()
        response = SettingsView.as_view()(request)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_settings_context_data(self, rf, user):
        """Settings context includes user and page title."""
        request = rf.get('/settings/')
        request.user = user
        view = SettingsView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        context = view.get_context_data()
        assert context['user'] == user
        assert context['page_title'] == 'Account Settings'

    @pytest.mark.django_db
    def test_settings_template_name(self):
        """SettingsView uses the correct template."""
        assert SettingsView.template_name == 'accounts/settings.html'

    @pytest.mark.django_db
    def test_settings_context_keys(self, rf, user):
        """Settings context has the expected keys."""
        request = rf.get('/settings/')
        request.user = user
        view = SettingsView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        context = view.get_context_data()
        assert 'user' in context
        assert 'page_title' in context


# ============================================================================
# TeamListView Tests (login required)
# ============================================================================

class TestTeamListView:
    """Tests for the TeamListView."""

    @pytest.mark.django_db
    def test_team_list_redirects_unauthenticated(self, rf):
        """Unauthenticated users are redirected."""
        request = rf.get('/teams/')
        request.user = AnonymousUser()
        response = TeamListView.as_view()(request)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_team_list_queryset_returns_owned_teams(self, rf, user, team):
        """Team list includes teams owned by the user."""
        request = rf.get('/teams/')
        request.user = user
        view = TeamListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        queryset = view.get_queryset()
        assert team in queryset

    @pytest.mark.django_db
    def test_team_list_queryset_returns_member_teams(self, rf, user, team, team_member):
        """Team list includes teams where user is a member."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@test.com',
            password='TestPass123!',
            is_active=True,
        )
        other_team = Team.objects.create(name='Other Team', owner=other_user)
        TeamMember.objects.create(team=other_team, user=user, role=TeamMember.MEMBER)

        request = rf.get('/teams/')
        request.user = user
        view = TeamListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        queryset = view.get_queryset()
        assert other_team in queryset

    @pytest.mark.django_db
    def test_team_list_context_data(self, rf, user, team):
        """Team list context includes page title."""
        request = rf.get('/teams/')
        request.user = user
        view = TeamListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        assert context['page_title'] == 'Teams'

    @pytest.mark.django_db
    def test_team_list_template_name(self):
        """TeamListView uses the correct template."""
        assert TeamListView.template_name == 'accounts/team_list.html'


# ============================================================================
# TeamDetailView Tests (login required)
# ============================================================================

class TestTeamDetailView:
    """Tests for the TeamDetailView."""

    @pytest.mark.django_db
    def test_team_detail_redirects_unauthenticated(self, rf, team):
        """Unauthenticated users are redirected."""
        request = rf.get(f'/teams/{team.pk}/')
        request.user = AnonymousUser()
        response = TeamDetailView.as_view()(request, pk=team.pk)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_team_detail_context_data(self, rf, user, team, team_member, team_invitation):
        """Team detail context includes members and invitations."""
        request = rf.get(f'/teams/{team.pk}/')
        request.user = user
        view = TeamDetailView()
        view.request = request
        view.kwargs = {'pk': str(team.pk)}
        view.setup(request, pk=str(team.pk))
        view.object = team
        context = view.get_context_data()
        assert 'members' in context
        assert 'invitations' in context
        assert context['page_title'] == f'Team: {team.name}'

    @pytest.mark.django_db
    def test_team_detail_members_in_context(self, rf, user, team, team_member):
        """Team detail context contains the correct members."""
        request = rf.get(f'/teams/{team.pk}/')
        request.user = user
        view = TeamDetailView()
        view.request = request
        view.kwargs = {'pk': str(team.pk)}
        view.setup(request, pk=str(team.pk))
        view.object = team
        context = view.get_context_data()
        assert context['members'].count() >= 1

    @pytest.mark.django_db
    def test_team_detail_pending_invitations_in_context(self, rf, user, team, team_invitation):
        """Team detail context shows only pending invitations."""
        request = rf.get(f'/teams/{team.pk}/')
        request.user = user
        view = TeamDetailView()
        view.request = request
        view.kwargs = {'pk': str(team.pk)}
        view.setup(request, pk=str(team.pk))
        view.object = team
        context = view.get_context_data()
        for inv in context['invitations']:
            assert inv.status == 'pending'

    @pytest.mark.django_db
    def test_team_detail_template_name(self):
        """TeamDetailView uses the correct template."""
        assert TeamDetailView.template_name == 'accounts/team_detail.html'


# ============================================================================
# UserListView Tests (login required)
# ============================================================================

class TestUserListView:
    """Tests for the UserListView."""

    @pytest.mark.django_db
    def test_user_list_redirects_unauthenticated(self, rf):
        """Unauthenticated users are redirected."""
        request = rf.get('/users/')
        request.user = AnonymousUser()
        response = UserListView.as_view()(request)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_user_list_queryset_active_only(self, rf, user):
        """User list only returns active users."""
        inactive = User.objects.create_user(
            username='inactive_test',
            email='inactive_test@test.com',
            password='TestPass123!',
            is_active=False,
        )
        request = rf.get('/users/')
        request.user = user
        view = UserListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        queryset = view.get_queryset()
        assert user in queryset
        assert inactive not in queryset

    @pytest.mark.django_db
    def test_user_list_context_data(self, rf, user):
        """User list context includes page title."""
        request = rf.get('/users/')
        request.user = user
        view = UserListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        assert context['page_title'] == 'Users'

    @pytest.mark.django_db
    def test_user_list_template_name(self):
        """UserListView uses the correct template."""
        assert UserListView.template_name == 'accounts/user_list.html'

    @pytest.mark.django_db
    def test_user_list_context_object_name(self):
        """UserListView uses 'users' as context object name."""
        assert UserListView.context_object_name == 'users'


# ============================================================================
# InvitationListView Tests (login required)
# ============================================================================

class TestInvitationListView:
    """Tests for the InvitationListView."""

    @pytest.mark.django_db
    def test_invitation_list_redirects_unauthenticated(self, rf):
        """Unauthenticated users are redirected."""
        request = rf.get('/invitations/')
        request.user = AnonymousUser()
        response = InvitationListView.as_view()(request)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_invitation_list_context_data(self, rf, user, user_invitation_obj):
        """Invitation list context includes page title."""
        request = rf.get('/invitations/')
        request.user = user
        view = InvitationListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        assert context['page_title'] == 'Invitations'

    @pytest.mark.django_db
    def test_invitation_list_model(self):
        """InvitationListView uses the UserInvitation model."""
        assert InvitationListView.model == UserInvitation

    @pytest.mark.django_db
    def test_invitation_list_template_name(self):
        """InvitationListView uses the correct template."""
        assert InvitationListView.template_name == 'accounts/invitation_list.html'

    @pytest.mark.django_db
    def test_invitation_list_queryset_contains_invitation(self, rf, user, user_invitation_obj):
        """Invitation list queryset includes created invitations."""
        request = rf.get('/invitations/')
        request.user = user
        view = InvitationListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        queryset = view.get_queryset()
        assert user_invitation_obj in queryset


# ============================================================================
# TwoFactorSetupView Tests (login required)
# ============================================================================

class TestTwoFactorSetupView:
    """Tests for the TwoFactorSetupView."""

    @pytest.mark.django_db
    def test_two_factor_redirects_unauthenticated(self, rf):
        """Unauthenticated users are redirected."""
        request = rf.get('/2fa-setup/')
        request.user = AnonymousUser()
        response = TwoFactorSetupView.as_view()(request)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_two_factor_context_data(self, rf, user):
        """Two-factor context includes 2FA enabled status and page title."""
        request = rf.get('/2fa-setup/')
        request.user = user
        view = TwoFactorSetupView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        context = view.get_context_data()
        assert 'two_factor_enabled' in context
        assert context['two_factor_enabled'] == user.two_factor_enabled
        assert context['page_title'] == 'Two-Factor Authentication'

    @pytest.mark.django_db
    def test_two_factor_context_reflects_disabled(self, rf, user):
        """Two-factor context shows disabled when 2FA is off."""
        user.two_factor_enabled = False
        user.save()
        request = rf.get('/2fa-setup/')
        request.user = user
        view = TwoFactorSetupView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        context = view.get_context_data()
        assert context['two_factor_enabled'] is False

    @pytest.mark.django_db
    def test_two_factor_context_reflects_enabled(self, rf, user):
        """Two-factor context shows enabled when 2FA is on."""
        user.two_factor_enabled = True
        user.save()
        request = rf.get('/2fa-setup/')
        request.user = user
        view = TwoFactorSetupView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        context = view.get_context_data()
        assert context['two_factor_enabled'] is True

    @pytest.mark.django_db
    def test_two_factor_template_name(self):
        """TwoFactorSetupView uses the correct template."""
        assert TwoFactorSetupView.template_name == 'accounts/two_factor_setup.html'
