"""
Tests for accounts admin module.

Covers:
- Admin site registration (User, UserInvitation, ApiKey)
- UserAdmin configuration (list_display, list_filter, search_fields, fieldsets)
- UserAdmin custom methods (role_badge, status_badge)
- UserInvitationAdmin configuration and custom methods
- ApiKeyAdmin configuration and custom methods
- Admin actions (cancel_invitations, deactivate_keys, activate_keys)
"""

import pytest
from unittest.mock import MagicMock, patch
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User, UserInvitation, ApiKey
from apps.accounts.admin import UserAdmin, UserInvitationAdmin, ApiKeyAdmin


# ============================================================================
# Admin Registration Tests
# ============================================================================


class TestAdminRegistration:
    """Tests for model registration in the admin site."""

    def test_user_model_is_registered(self):
        """User model is registered with the admin site."""
        assert User in admin.site._registry

    def test_user_invitation_model_is_registered(self):
        """UserInvitation model is registered with the admin site."""
        assert UserInvitation in admin.site._registry

    def test_api_key_model_is_registered(self):
        """ApiKey model is registered with the admin site."""
        assert ApiKey in admin.site._registry

    def test_user_admin_class(self):
        """User model uses UserAdmin for admin interface."""
        assert isinstance(admin.site._registry[User], UserAdmin)

    def test_user_invitation_admin_class(self):
        """UserInvitation model uses UserInvitationAdmin for admin interface."""
        assert isinstance(admin.site._registry[UserInvitation], UserInvitationAdmin)

    def test_api_key_admin_class(self):
        """ApiKey model uses ApiKeyAdmin for admin interface."""
        assert isinstance(admin.site._registry[ApiKey], ApiKeyAdmin)


# ============================================================================
# UserAdmin Configuration Tests
# ============================================================================


class TestUserAdminConfiguration:
    """Tests for UserAdmin configuration."""

    def test_list_display(self):
        """UserAdmin list_display includes expected fields."""
        expected = ['email', 'full_name', 'tenant', 'role_badge', 'status_badge', 'last_login']
        ua = UserAdmin(User, admin.site)
        assert ua.list_display == expected

    def test_list_filter(self):
        """UserAdmin list_filter includes expected fields."""
        ua = UserAdmin(User, admin.site)
        assert 'role' in ua.list_filter
        assert 'is_active' in ua.list_filter
        assert 'is_staff' in ua.list_filter
        assert 'is_verified' in ua.list_filter
        assert 'two_factor_enabled' in ua.list_filter
        assert 'date_joined' in ua.list_filter

    def test_search_fields(self):
        """UserAdmin search_fields includes expected fields."""
        ua = UserAdmin(User, admin.site)
        assert 'email' in ua.search_fields
        assert 'first_name' in ua.search_fields
        assert 'last_name' in ua.search_fields
        assert 'full_name' in ua.search_fields
        assert 'username' in ua.search_fields

    def test_readonly_fields(self):
        """UserAdmin readonly_fields includes expected fields."""
        ua = UserAdmin(User, admin.site)
        assert 'id' in ua.readonly_fields
        assert 'date_joined' in ua.readonly_fields
        assert 'last_login' in ua.readonly_fields
        assert 'verified_at' in ua.readonly_fields
        assert 'last_login_ip' in ua.readonly_fields

    def test_ordering(self):
        """UserAdmin is ordered by date_joined descending."""
        ua = UserAdmin(User, admin.site)
        assert ua.ordering == ('-date_joined',)

    def test_add_fieldsets(self):
        """UserAdmin add_fieldsets has correct fields."""
        ua = UserAdmin(User, admin.site)
        add_fields = ua.add_fieldsets[0][1]['fields']
        assert 'email' in add_fields
        assert 'password1' in add_fields
        assert 'password2' in add_fields
        assert 'tenant' in add_fields
        assert 'role' in add_fields

    def test_fieldsets_count(self):
        """UserAdmin has the expected number of fieldsets."""
        ua = UserAdmin(User, admin.site)
        assert len(ua.fieldsets) == 8  # Auth, Personal, Org, Perms, Prefs, Security, Dates, Meta


class TestUserAdminCustomMethods:
    """Tests for UserAdmin custom display methods."""

    @pytest.mark.django_db
    def test_role_badge_admin(self, admin_user):
        """role_badge returns red HTML for admin role."""
        ua = UserAdmin(User, admin.site)
        badge = ua.role_badge(admin_user)
        assert 'red' in badge
        assert admin_user.get_role_display() in badge

    @pytest.mark.django_db
    def test_role_badge_manager(self, manager_user):
        """role_badge returns orange HTML for manager role."""
        ua = UserAdmin(User, admin.site)
        badge = ua.role_badge(manager_user)
        assert 'orange' in badge

    @pytest.mark.django_db
    def test_role_badge_contributor(self, contributor_user):
        """role_badge returns blue HTML for contributor role."""
        ua = UserAdmin(User, admin.site)
        badge = ua.role_badge(contributor_user)
        assert 'blue' in badge

    @pytest.mark.django_db
    def test_role_badge_client(self, client_user):
        """role_badge returns gray HTML for client role."""
        ua = UserAdmin(User, admin.site)
        badge = ua.role_badge(client_user)
        assert 'gray' in badge

    @pytest.mark.django_db
    def test_role_badge_short_description(self):
        """role_badge has short_description set to 'Role'."""
        ua = UserAdmin(User, admin.site)
        assert ua.role_badge.short_description == 'Role'

    @pytest.mark.django_db
    def test_status_badge_active_user(self, admin_user):
        """status_badge shows 'Active' for an active user."""
        ua = UserAdmin(User, admin.site)
        badge = ua.status_badge(admin_user)
        assert 'Active' in badge
        assert 'green' in badge

    @pytest.mark.django_db
    def test_status_badge_inactive_user(self, inactive_user):
        """status_badge shows 'Inactive' for an inactive user."""
        ua = UserAdmin(User, admin.site)
        badge = ua.status_badge(inactive_user)
        assert 'Inactive' in badge
        assert 'red' in badge

    @pytest.mark.django_db
    def test_status_badge_verified_user(self, admin_user):
        """status_badge shows 'Verified' for a verified user."""
        admin_user.is_verified = True
        admin_user.save()

        ua = UserAdmin(User, admin.site)
        badge = ua.status_badge(admin_user)
        assert 'Verified' in badge

    @pytest.mark.django_db
    def test_status_badge_2fa_enabled(self, admin_user):
        """status_badge shows '2FA' when two-factor is enabled."""
        admin_user.two_factor_enabled = True
        admin_user.save()

        ua = UserAdmin(User, admin.site)
        badge = ua.status_badge(admin_user)
        assert '2FA' in badge
        assert 'blue' in badge

    @pytest.mark.django_db
    def test_status_badge_short_description(self):
        """status_badge has short_description set to 'Status'."""
        ua = UserAdmin(User, admin.site)
        assert ua.status_badge.short_description == 'Status'

    @pytest.mark.django_db
    def test_status_badge_multiple_badges(self, admin_user):
        """status_badge shows all applicable badges separated by pipes."""
        admin_user.is_active = True
        admin_user.is_verified = True
        admin_user.two_factor_enabled = True
        admin_user.save()

        ua = UserAdmin(User, admin.site)
        badge = ua.status_badge(admin_user)
        assert 'Active' in badge
        assert 'Verified' in badge
        assert '2FA' in badge
        assert '|' in badge


# ============================================================================
# UserInvitationAdmin Tests
# ============================================================================


class TestUserInvitationAdminConfiguration:
    """Tests for UserInvitationAdmin configuration."""

    def test_list_display(self):
        """UserInvitationAdmin list_display has expected fields."""
        ua = UserInvitationAdmin(UserInvitation, admin.site)
        expected = [
            'email', 'tenant', 'role', 'status_badge',
            'invited_by', 'created_at', 'expires_at',
        ]
        assert ua.list_display == expected

    def test_list_filter(self):
        """UserInvitationAdmin list_filter has expected fields."""
        ua = UserInvitationAdmin(UserInvitation, admin.site)
        assert 'status' in ua.list_filter
        assert 'role' in ua.list_filter
        assert 'created_at' in ua.list_filter
        assert 'tenant' in ua.list_filter

    def test_search_fields(self):
        """UserInvitationAdmin search_fields has expected fields."""
        ua = UserInvitationAdmin(UserInvitation, admin.site)
        assert 'email' in ua.search_fields
        assert 'tenant__name' in ua.search_fields
        assert 'invited_by__email' in ua.search_fields

    def test_readonly_fields(self):
        """UserInvitationAdmin readonly_fields has expected fields."""
        ua = UserInvitationAdmin(UserInvitation, admin.site)
        assert 'id' in ua.readonly_fields
        assert 'invitation_token' in ua.readonly_fields
        assert 'created_at' in ua.readonly_fields
        assert 'accepted_at' in ua.readonly_fields

    def test_actions(self):
        """UserInvitationAdmin has cancel_invitations action."""
        ua = UserInvitationAdmin(UserInvitation, admin.site)
        assert 'cancel_invitations' in ua.actions


class TestUserInvitationAdminMethods:
    """Tests for UserInvitationAdmin custom methods."""

    @pytest.mark.django_db
    def test_status_badge_pending(self, user_invitation):
        """status_badge returns orange for pending invitation."""
        ua = UserInvitationAdmin(UserInvitation, admin.site)
        badge = ua.status_badge(user_invitation)
        assert 'orange' in badge

    @pytest.mark.django_db
    def test_status_badge_accepted(self, user_invitation):
        """status_badge returns green for accepted invitation."""
        user_invitation.status = UserInvitation.ACCEPTED
        user_invitation.save()

        ua = UserInvitationAdmin(UserInvitation, admin.site)
        badge = ua.status_badge(user_invitation)
        assert 'green' in badge

    @pytest.mark.django_db
    def test_status_badge_expired(self, user_invitation):
        """status_badge returns gray for expired invitation."""
        user_invitation.status = UserInvitation.EXPIRED
        user_invitation.save()

        ua = UserInvitationAdmin(UserInvitation, admin.site)
        badge = ua.status_badge(user_invitation)
        assert 'gray' in badge

    @pytest.mark.django_db
    def test_status_badge_cancelled(self, user_invitation):
        """status_badge returns red for cancelled invitation."""
        user_invitation.status = UserInvitation.CANCELLED
        user_invitation.save()

        ua = UserInvitationAdmin(UserInvitation, admin.site)
        badge = ua.status_badge(user_invitation)
        assert 'red' in badge

    def test_status_badge_short_description(self):
        """status_badge has short_description set to 'Status'."""
        ua = UserInvitationAdmin(UserInvitation, admin.site)
        assert ua.status_badge.short_description == 'Status'

    @pytest.mark.django_db
    def test_cancel_invitations_action(self, user_invitation, tenant, admin_user):
        """cancel_invitations action cancels pending invitations."""
        import secrets as secrets_mod

        # Create additional pending invitations
        inv2 = UserInvitation.objects.create(
            tenant=tenant,
            email='inv2@example.com',
            role=User.CONTRIBUTOR,
            invited_by=admin_user,
            invitation_token=secrets_mod.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(days=7),
            status=UserInvitation.PENDING,
        )

        ua = UserInvitationAdmin(UserInvitation, admin.site)
        request = RequestFactory().get('/admin/')
        request.user = admin_user

        queryset = UserInvitation.objects.filter(
            id__in=[user_invitation.id, inv2.id]
        )
        ua.cancel_invitations(request, queryset)

        user_invitation.refresh_from_db()
        inv2.refresh_from_db()
        assert user_invitation.status == UserInvitation.CANCELLED
        assert inv2.status == UserInvitation.CANCELLED

    @pytest.mark.django_db
    def test_cancel_invitations_skips_non_pending(self, user_invitation, admin_user):
        """cancel_invitations only cancels pending invitations."""
        user_invitation.status = UserInvitation.ACCEPTED
        user_invitation.save()

        ua = UserInvitationAdmin(UserInvitation, admin.site)
        request = RequestFactory().get('/admin/')
        request.user = admin_user

        queryset = UserInvitation.objects.filter(id=user_invitation.id)
        ua.cancel_invitations(request, queryset)

        user_invitation.refresh_from_db()
        # Status should remain ACCEPTED, not changed to CANCELLED
        assert user_invitation.status == UserInvitation.ACCEPTED

    def test_cancel_invitations_short_description(self):
        """cancel_invitations has short_description set."""
        ua = UserInvitationAdmin(UserInvitation, admin.site)
        assert ua.cancel_invitations.short_description == 'Cancel selected invitations'


# ============================================================================
# ApiKeyAdmin Tests
# ============================================================================


class TestApiKeyAdminConfiguration:
    """Tests for ApiKeyAdmin configuration."""

    def test_list_display(self):
        """ApiKeyAdmin list_display has expected fields."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        expected = [
            'name', 'prefix_display', 'user', 'tenant',
            'status_badge', 'usage_count', 'last_used_at', 'created_at',
        ]
        assert ua.list_display == expected

    def test_list_filter(self):
        """ApiKeyAdmin list_filter has expected fields."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        assert 'is_active' in ua.list_filter
        assert 'created_at' in ua.list_filter
        assert 'tenant' in ua.list_filter

    def test_search_fields(self):
        """ApiKeyAdmin search_fields has expected fields."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        assert 'name' in ua.search_fields
        assert 'prefix' in ua.search_fields
        assert 'user__email' in ua.search_fields
        assert 'tenant__name' in ua.search_fields

    def test_readonly_fields(self):
        """ApiKeyAdmin readonly_fields has expected fields."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        assert 'id' in ua.readonly_fields
        assert 'key' in ua.readonly_fields
        assert 'prefix' in ua.readonly_fields
        assert 'created_at' in ua.readonly_fields
        assert 'last_used_at' in ua.readonly_fields
        assert 'usage_count' in ua.readonly_fields

    def test_actions(self):
        """ApiKeyAdmin has deactivate and activate actions."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        assert 'deactivate_keys' in ua.actions
        assert 'activate_keys' in ua.actions


class TestApiKeyAdminMethods:
    """Tests for ApiKeyAdmin custom methods."""

    @pytest.mark.django_db
    def test_prefix_display(self, api_key):
        """prefix_display shows prefix followed by asterisks."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        display = ua.prefix_display(api_key)
        assert display == f"{api_key.prefix}***"

    def test_prefix_display_short_description(self):
        """prefix_display has short_description set to 'Key'."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        assert ua.prefix_display.short_description == 'Key'

    @pytest.mark.django_db
    def test_status_badge_active(self, api_key):
        """status_badge returns green for active, non-expired key."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        badge = ua.status_badge(api_key)
        assert 'Active' in badge
        assert 'green' in badge

    @pytest.mark.django_db
    def test_status_badge_expired(self, api_key):
        """status_badge returns orange for expired key."""
        api_key.expires_at = timezone.now() - timedelta(days=1)
        api_key.save()

        ua = ApiKeyAdmin(ApiKey, admin.site)
        badge = ua.status_badge(api_key)
        assert 'Expired' in badge
        assert 'orange' in badge

    @pytest.mark.django_db
    def test_status_badge_inactive(self, api_key):
        """status_badge returns red for inactive key."""
        api_key.is_active = False
        api_key.save()

        ua = ApiKeyAdmin(ApiKey, admin.site)
        badge = ua.status_badge(api_key)
        assert 'Invalid' in badge
        assert 'red' in badge

    def test_status_badge_short_description(self):
        """status_badge has short_description set to 'Status'."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        assert ua.status_badge.short_description == 'Status'

    @pytest.mark.django_db
    def test_deactivate_keys_action(self, api_key, admin_user):
        """deactivate_keys action sets is_active=False."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        request = RequestFactory().get('/admin/')
        request.user = admin_user

        queryset = ApiKey.objects.filter(id=api_key.id)
        ua.deactivate_keys(request, queryset)

        api_key.refresh_from_db()
        assert api_key.is_active is False

    @pytest.mark.django_db
    def test_activate_keys_action(self, api_key, admin_user):
        """activate_keys action sets is_active=True."""
        api_key.is_active = False
        api_key.save()

        ua = ApiKeyAdmin(ApiKey, admin.site)
        request = RequestFactory().get('/admin/')
        request.user = admin_user

        queryset = ApiKey.objects.filter(id=api_key.id)
        ua.activate_keys(request, queryset)

        api_key.refresh_from_db()
        assert api_key.is_active is True

    def test_deactivate_keys_short_description(self):
        """deactivate_keys has correct short_description."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        assert ua.deactivate_keys.short_description == 'Deactivate selected keys'

    def test_activate_keys_short_description(self):
        """activate_keys has correct short_description."""
        ua = ApiKeyAdmin(ApiKey, admin.site)
        assert ua.activate_keys.short_description == 'Activate selected keys'
