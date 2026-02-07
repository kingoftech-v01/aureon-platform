"""
Tests for accounts app models.

Tests cover:
- User model creation and validation
- User role properties and permissions
- UserInvitation model
- ApiKey model
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# User Model Tests
# ============================================================================

@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model."""

    def test_create_user_with_email(self):
        """Test creating a user with email as primary identifier."""
        user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='SecurePass123!',
            first_name='Test',
            last_name='User',
        )

        assert user.email == 'test@example.com'
        assert user.check_password('SecurePass123!')
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_user_without_email_raises_error(self):
        """Test that creating a user without email raises an error."""
        with pytest.raises(ValueError):
            User.objects.create_user(
                username='empty',
                email='',
                password='SecurePass123!',
            )

    def test_create_superuser(self):
        """Test creating a superuser."""
        superuser = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@example.com',
            password='SuperPass123!',
            first_name='Super',
            last_name='Admin',
        )

        assert superuser.is_superuser is True
        assert superuser.is_staff is True
        assert superuser.is_active is True

    def test_user_string_representation(self, admin_user):
        """Test user string representation."""
        expected = f"{admin_user.get_full_name()} ({admin_user.email})"
        assert str(admin_user) == expected

    def test_get_full_name_with_full_name_field(self, admin_user):
        """Test get_full_name when full_name field is set."""
        admin_user.full_name = "Full Name Override"
        admin_user.save()

        assert admin_user.get_full_name() == "Full Name Override"

    def test_get_full_name_from_first_last(self, admin_user):
        """Test get_full_name when using first and last name."""
        admin_user.full_name = ""
        admin_user.save()

        assert admin_user.get_full_name() == f"{admin_user.first_name} {admin_user.last_name}"

    def test_get_short_name(self, admin_user):
        """Test get_short_name returns first name."""
        assert admin_user.get_short_name() == admin_user.first_name

    def test_get_short_name_fallback_to_email(self):
        """Test get_short_name falls back to email prefix."""
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='SecurePass123!',
            first_name='',
            last_name='',
        )

        assert user.get_short_name() == 'testuser'

    def test_auto_generate_username_from_email(self):
        """Test username is auto-generated from email."""
        user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='SecurePass123!',
        )

        assert user.username is not None
        assert user.username.startswith('newuser')

    def test_uuid_primary_key(self, admin_user):
        """Test that user has UUID primary key."""
        import uuid
        assert isinstance(admin_user.id, uuid.UUID)


# ============================================================================
# User Role and Permission Tests
# ============================================================================

@pytest.mark.django_db
class TestUserRoles:
    """Tests for user role properties."""

    def test_is_admin_for_admin_role(self, admin_user):
        """Test is_admin property for admin role."""
        assert admin_user.is_admin is True

    def test_is_admin_for_superuser(self, superuser):
        """Test is_admin property for superuser."""
        assert superuser.is_admin is True

    def test_is_admin_for_non_admin(self, contributor_user):
        """Test is_admin property for non-admin."""
        assert contributor_user.is_admin is False

    def test_is_manager_for_admin(self, admin_user):
        """Test is_manager property for admin."""
        assert admin_user.is_manager is True

    def test_is_manager_for_manager(self, manager_user):
        """Test is_manager property for manager."""
        assert manager_user.is_manager is True

    def test_is_manager_for_contributor(self, contributor_user):
        """Test is_manager property for contributor."""
        assert contributor_user.is_manager is False

    def test_is_client_user(self, client_user):
        """Test is_client_user property."""
        assert client_user.is_client_user is True

    def test_is_client_user_for_admin(self, admin_user):
        """Test is_client_user for admin is False."""
        assert admin_user.is_client_user is False

    def test_can_manage_contracts(self, admin_user, manager_user, contributor_user):
        """Test can_manage_contracts permission."""
        assert admin_user.can_manage_contracts() is True
        assert manager_user.can_manage_contracts() is True
        assert contributor_user.can_manage_contracts() is False

    def test_can_manage_invoices(self, admin_user, manager_user, contributor_user):
        """Test can_manage_invoices permission."""
        assert admin_user.can_manage_invoices() is True
        assert manager_user.can_manage_invoices() is True
        assert contributor_user.can_manage_invoices() is False

    def test_can_manage_users(self, admin_user, manager_user, contributor_user):
        """Test can_manage_users permission."""
        assert admin_user.can_manage_users() is True
        assert manager_user.can_manage_users() is False
        assert contributor_user.can_manage_users() is False

    def test_can_access_analytics(self, admin_user, manager_user, contributor_user):
        """Test can_access_analytics permission."""
        assert admin_user.can_access_analytics() is True
        assert manager_user.can_access_analytics() is True
        assert contributor_user.can_access_analytics() is False


# ============================================================================
# User Two-Factor Authentication Tests
# ============================================================================

@pytest.mark.django_db
class TestUserTwoFactor:
    """Tests for user two-factor authentication."""

    def test_two_factor_disabled_by_default(self, admin_user):
        """Test 2FA is disabled by default."""
        assert admin_user.two_factor_enabled is False

    def test_two_factor_secret_empty_by_default(self, admin_user):
        """Test 2FA secret is empty by default."""
        assert admin_user.two_factor_secret == ''

    def test_two_factor_backup_codes_empty_by_default(self, admin_user):
        """Test 2FA backup codes is empty list by default."""
        assert admin_user.two_factor_backup_codes == []

    def test_enable_two_factor(self, admin_user):
        """Test enabling two-factor authentication."""
        admin_user.two_factor_enabled = True
        admin_user.two_factor_secret = 'JBSWY3DPEHPK3PXP'
        admin_user.two_factor_backup_codes = ['123456', '654321']
        admin_user.save()

        admin_user.refresh_from_db()
        assert admin_user.two_factor_enabled is True
        assert admin_user.two_factor_secret == 'JBSWY3DPEHPK3PXP'
        assert len(admin_user.two_factor_backup_codes) == 2


# ============================================================================
# UserInvitation Model Tests
# ============================================================================

@pytest.mark.django_db
class TestUserInvitationModel:
    """Tests for the UserInvitation model."""

    def test_create_invitation(self, admin_user):
        """Test creating a user invitation."""
        from apps.accounts.models import UserInvitation
        import secrets

        invitation = UserInvitation.objects.create(
            email='newinvite@example.com',
            role=User.CONTRIBUTOR,
            invited_by=admin_user,
            invitation_token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(days=7),
        )

        assert invitation.email == 'newinvite@example.com'
        assert invitation.role == User.CONTRIBUTOR
        assert invitation.status == UserInvitation.PENDING

    def test_invitation_string_representation(self, user_invitation):
        """Test invitation string representation."""
        expected = f"Invitation to {user_invitation.email} ({user_invitation.status})"
        assert str(user_invitation) == expected

    def test_is_expired_property_not_expired(self, user_invitation):
        """Test is_expired property when not expired."""
        assert user_invitation.is_expired is False

    def test_is_expired_property_expired(self, user_invitation):
        """Test is_expired property when expired."""
        user_invitation.expires_at = timezone.now() - timedelta(days=1)
        user_invitation.save()

        assert user_invitation.is_expired is True

    def test_is_expired_accepted_invitation(self, user_invitation):
        """Test is_expired for already accepted invitation."""
        user_invitation.status = 'accepted'
        user_invitation.save()

        # Even if past expiry date, accepted invitations are not "expired"
        user_invitation.expires_at = timezone.now() - timedelta(days=1)
        assert user_invitation.is_expired is False

    def test_accept_invitation(self, user_invitation, contributor_user):
        """Test accepting an invitation."""
        from apps.accounts.models import UserInvitation

        user_invitation.accept(contributor_user)

        assert user_invitation.status == UserInvitation.ACCEPTED
        assert user_invitation.accepted_at is not None
        assert contributor_user.role == user_invitation.role

    def test_cancel_invitation(self, user_invitation):
        """Test cancelling an invitation."""
        from apps.accounts.models import UserInvitation

        user_invitation.cancel()

        assert user_invitation.status == UserInvitation.CANCELLED


# ============================================================================
# ApiKey Model Tests
# ============================================================================

@pytest.mark.django_db
class TestApiKeyModel:
    """Tests for the ApiKey model."""

    def test_create_api_key(self, admin_user):
        """Test creating an API key."""
        from apps.accounts.models import ApiKey
        import secrets

        key = secrets.token_urlsafe(32)
        api_key = ApiKey.objects.create(
            user=admin_user,
            name='Test Key',
            key=key,
            prefix=key[:8],
            scopes=['read', 'write'],
        )

        assert api_key.name == 'Test Key'
        assert api_key.key == key
        assert api_key.is_active is True
        assert api_key.usage_count == 0

    def test_api_key_string_representation(self, api_key):
        """Test API key string representation."""
        expected = f"{api_key.name} ({api_key.prefix}***)"
        assert str(api_key) == expected

    def test_is_expired_no_expiry(self, api_key):
        """Test is_expired when no expiry set."""
        api_key.expires_at = None
        api_key.save()

        assert api_key.is_expired is False

    def test_is_expired_future_expiry(self, api_key):
        """Test is_expired when expiry is in future."""
        api_key.expires_at = timezone.now() + timedelta(days=30)
        api_key.save()

        assert api_key.is_expired is False

    def test_is_expired_past_expiry(self, api_key):
        """Test is_expired when expiry is in past."""
        api_key.expires_at = timezone.now() - timedelta(days=1)
        api_key.save()

        assert api_key.is_expired is True

    def test_is_valid_active_not_expired(self, api_key):
        """Test is_valid when active and not expired."""
        assert api_key.is_valid is True

    def test_is_valid_inactive(self, api_key):
        """Test is_valid when inactive."""
        api_key.is_active = False
        api_key.save()

        assert api_key.is_valid is False

    def test_is_valid_expired(self, api_key):
        """Test is_valid when expired."""
        api_key.expires_at = timezone.now() - timedelta(days=1)
        api_key.save()

        assert api_key.is_valid is False

    def test_record_usage(self, api_key):
        """Test recording API key usage."""
        initial_count = api_key.usage_count
        initial_used_at = api_key.last_used_at

        api_key.record_usage()

        assert api_key.usage_count == initial_count + 1
        assert api_key.last_used_at is not None
        if initial_used_at:
            assert api_key.last_used_at > initial_used_at

    def test_record_usage_increments_count(self, api_key):
        """Test that record_usage properly increments usage count."""
        api_key.record_usage()
        api_key.record_usage()
        api_key.record_usage()

        api_key.refresh_from_db()
        assert api_key.usage_count == 3


# ============================================================================
# User Model Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestUserModelEdgeCases:
    """Edge case tests for User model."""

    def test_user_metadata_field(self, admin_user):
        """Test user metadata JSON field."""
        admin_user.metadata = {'custom': 'data', 'nested': {'key': 'value'}}
        admin_user.save()

        admin_user.refresh_from_db()
        assert admin_user.metadata['custom'] == 'data'
        assert admin_user.metadata['nested']['key'] == 'value'

    def test_user_timezone_default(self):
        """Test user timezone default value."""
        user = User.objects.create_user(
            username='timezone',
            email='timezone@test.com',
            password='Pass123!',
        )
        assert user.timezone == 'UTC'

    def test_user_language_default(self):
        """Test user language default value."""
        user = User.objects.create_user(
            username='lang',
            email='lang@test.com',
            password='Pass123!',
        )
        assert user.language == 'en'

    def test_user_notification_preferences_defaults(self):
        """Test user notification preferences defaults."""
        user = User.objects.create_user(
            username='notif',
            email='notif@test.com',
            password='Pass123!',
        )
        assert user.email_notifications is True
        assert user.sms_notifications is False

    def test_user_role_choices(self):
        """Test that all role choices are valid."""
        valid_roles = [User.ADMIN, User.MANAGER, User.CONTRIBUTOR, User.CLIENT]
        for role in valid_roles:
            assert role in dict(User.ROLE_CHOICES)

    def test_user_verified_status(self):
        """Test user verified status fields."""
        user = User.objects.create_user(
            username='unverified',
            email='unverified@test.com',
            password='Pass123!',
        )
        assert user.is_verified is False
        assert user.verified_at is None

        user.is_verified = True
        user.verified_at = timezone.now()
        user.save()

        user.refresh_from_db()
        assert user.is_verified is True
        assert user.verified_at is not None

    def test_user_last_login_ip(self, admin_user):
        """Test last login IP field."""
        admin_user.last_login_ip = '192.168.1.1'
        admin_user.save()

        admin_user.refresh_from_db()
        assert admin_user.last_login_ip == '192.168.1.1'
