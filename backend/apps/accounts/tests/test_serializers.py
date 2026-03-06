"""
Tests for accounts app serializers.

Tests cover:
- UserSerializer validation and output
- UserCreateSerializer validation
- UserUpdateSerializer
- ChangePasswordSerializer
- UserInvitationSerializer
- ApiKeySerializer
"""

import pytest
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model

from apps.accounts.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserInvitationSerializer,
    ApiKeySerializer,
)

User = get_user_model()


# ============================================================================
# UserSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestUserSerializer:
    """Tests for UserSerializer."""

    def test_serialize_user(self, admin_user):
        """Test serializing a user."""
        serializer = UserSerializer(admin_user)
        data = serializer.data

        assert data['email'] == admin_user.email
        assert data['id'] == str(admin_user.id)
        assert data['first_name'] == admin_user.first_name
        assert data['last_name'] == admin_user.last_name
        assert data['role'] == admin_user.role
        assert 'password' not in data

    def test_full_name_field(self, admin_user):
        """Test full_name serializer method field."""
        serializer = UserSerializer(admin_user)
        data = serializer.data

        assert data['full_name'] == admin_user.get_full_name()

    def test_is_admin_field(self, admin_user):
        """Test is_admin read-only field."""
        serializer = UserSerializer(admin_user)
        data = serializer.data

        assert data['is_admin'] is True

    def test_is_manager_field(self, manager_user):
        """Test is_manager read-only field."""
        serializer = UserSerializer(manager_user)
        data = serializer.data

        assert data['is_manager'] is True

    def test_read_only_fields(self, admin_user):
        """Test that read-only fields cannot be set via serializer."""
        serializer = UserSerializer()
        read_only = serializer.Meta.read_only_fields

        assert 'id' in read_only
        assert 'username' in read_only
        assert 'is_verified' in read_only
        assert 'last_login' in read_only
        assert 'date_joined' in read_only


# ============================================================================
# UserCreateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestUserCreateSerializer:
    """Tests for UserCreateSerializer."""

    def test_valid_user_creation(self):
        """Test valid user creation data."""
        data = {
            'email': 'newuser@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': User.CONTRIBUTOR,
        }

        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_password_mismatch(self):
        """Test password mismatch validation."""
        data = {
            'email': 'newuser@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass456!',
            'first_name': 'New',
            'last_name': 'User',
        }

        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_weak_password(self):
        """Test weak password validation."""
        data = {
            'email': 'newuser@test.com',
            'password': '123',
            'password_confirm': '123',
            'first_name': 'New',
            'last_name': 'User',
        }

        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_common_password(self):
        """Test common password validation."""
        data = {
            'email': 'newuser@test.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'New',
            'last_name': 'User',
        }

        serializer = UserCreateSerializer(data=data)
        # Common passwords should be rejected by Django's validators
        assert not serializer.is_valid()

    def test_create_user_via_serializer(self):
        """Test creating user through serializer."""
        data = {
            'email': 'created@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Created',
            'last_name': 'User',
            'role': User.CONTRIBUTOR,
        }

        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        user = serializer.save()
        assert user.email == 'created@test.com'
        assert user.check_password('SecurePass123!')
        assert user.role == User.CONTRIBUTOR

    def test_email_validation(self):
        """Test email format validation."""
        data = {
            'email': 'invalid-email',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
        }

        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_password_not_in_output(self):
        """Test password is not included in serializer output."""
        data = {
            'email': 'output@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Output',
            'last_name': 'User',
        }

        serializer = UserCreateSerializer(data=data)
        serializer.is_valid()

        # password and password_confirm should be write_only
        assert 'password' not in serializer.data
        assert 'password_confirm' not in serializer.data


# ============================================================================
# UserUpdateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestUserUpdateSerializer:
    """Tests for UserUpdateSerializer."""

    def test_update_user_fields(self, admin_user):
        """Test updating user fields."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'job_title': 'CTO',
            'timezone': 'America/Los_Angeles',
        }

        serializer = UserUpdateSerializer(admin_user, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors

        updated_user = serializer.save()
        assert updated_user.first_name == 'Updated'
        assert updated_user.job_title == 'CTO'

    def test_allowed_update_fields(self):
        """Test that only allowed fields can be updated."""
        serializer = UserUpdateSerializer()
        allowed_fields = serializer.Meta.fields

        assert 'first_name' in allowed_fields
        assert 'last_name' in allowed_fields
        assert 'full_name' in allowed_fields
        assert 'phone' in allowed_fields
        assert 'job_title' in allowed_fields
        assert 'timezone' in allowed_fields
        assert 'language' in allowed_fields
        # Sensitive fields should not be in update serializer
        assert 'email' not in allowed_fields
        assert 'password' not in allowed_fields
        assert 'role' not in allowed_fields

    def test_partial_update(self, admin_user):
        """Test partial update only changes specified fields."""
        original_last_name = admin_user.last_name
        data = {'first_name': 'OnlyFirst'}

        serializer = UserUpdateSerializer(admin_user, data=data, partial=True)
        assert serializer.is_valid()

        updated_user = serializer.save()
        assert updated_user.first_name == 'OnlyFirst'
        assert updated_user.last_name == original_last_name


# ============================================================================
# ChangePasswordSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestChangePasswordSerializer:
    """Tests for ChangePasswordSerializer."""

    def test_valid_password_change(self):
        """Test valid password change data."""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }

        serializer = ChangePasswordSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_password_mismatch(self):
        """Test new password mismatch."""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'DifferentPass789!',
        }

        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert 'new_password' in serializer.errors

    def test_weak_new_password(self):
        """Test weak new password."""
        data = {
            'old_password': 'OldPass123!',
            'new_password': '123',
            'new_password_confirm': '123',
        }

        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert 'new_password' in serializer.errors

    def test_missing_old_password(self):
        """Test missing old password."""
        data = {
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }

        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert 'old_password' in serializer.errors


# ============================================================================
# UserInvitationSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestUserInvitationSerializer:
    """Tests for UserInvitationSerializer."""

    def test_serialize_invitation(self, user_invitation):
        """Test serializing an invitation."""
        serializer = UserInvitationSerializer(user_invitation)
        data = serializer.data

        assert data['email'] == user_invitation.email
        assert data['role'] == user_invitation.role
        assert data['status'] == user_invitation.status
        assert 'invitation_token' not in data  # Should be excluded from output

    def test_is_expired_field(self, user_invitation):
        """Test is_expired computed field."""
        serializer = UserInvitationSerializer(user_invitation)
        data = serializer.data

        assert data['is_expired'] == user_invitation.is_expired

    def test_invited_by_email_field(self, user_invitation):
        """Test invited_by_email method field."""
        serializer = UserInvitationSerializer(user_invitation)
        data = serializer.data

        assert data['invited_by_email'] == user_invitation.invited_by.email

    def test_read_only_fields(self):
        """Test read-only fields are properly set."""
        serializer = UserInvitationSerializer()
        read_only = serializer.Meta.read_only_fields

        assert 'id' in read_only
        assert 'status' in read_only
        assert 'invitation_token' in read_only
        assert 'invited_by' in read_only
        assert 'created_at' in read_only
        assert 'accepted_at' in read_only


# ============================================================================
# ApiKeySerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestApiKeySerializer:
    """Tests for ApiKeySerializer."""

    def test_serialize_api_key(self, api_key):
        """Test serializing an API key."""
        serializer = ApiKeySerializer(api_key)
        data = serializer.data

        assert data['name'] == api_key.name
        assert data['prefix'] == api_key.prefix
        assert 'key' not in data  # Full key should not be in output

    def test_is_valid_field(self, api_key):
        """Test is_valid computed field."""
        serializer = ApiKeySerializer(api_key)
        data = serializer.data

        assert data['is_valid'] == api_key.is_valid

    def test_is_expired_field(self, api_key):
        """Test is_expired computed field."""
        serializer = ApiKeySerializer(api_key)
        data = serializer.data

        assert data['is_expired'] == api_key.is_expired

    def test_scopes_field(self, api_key):
        """Test scopes JSON field."""
        serializer = ApiKeySerializer(api_key)
        data = serializer.data

        assert data['scopes'] == api_key.scopes

    def test_read_only_fields(self):
        """Test read-only fields are properly set."""
        serializer = ApiKeySerializer()
        read_only = serializer.Meta.read_only_fields

        assert 'id' in read_only
        assert 'prefix' in read_only
        assert 'is_valid' in read_only
        assert 'is_expired' in read_only
        assert 'last_used_at' in read_only
        assert 'usage_count' in read_only
        assert 'created_at' in read_only

    def test_create_api_key_via_serializer(self):
        """Test creating API key via serializer."""
        data = {
            'name': 'Test Key',
            'scopes': ['read', 'write'],
        }

        serializer = ApiKeySerializer(data=data)
        assert serializer.is_valid(), serializer.errors


# ============================================================================
# Serializer Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestSerializerEdgeCases:
    """Edge case tests for serializers."""

    def test_empty_user_data(self):
        """Test serializer with empty data."""
        serializer = UserCreateSerializer(data={})
        assert not serializer.is_valid()

    def test_invitation_serializer_with_message(self, user_invitation):
        """Test invitation serializer includes message."""
        user_invitation.message = 'Welcome to the team!'
        user_invitation.save()

        serializer = UserInvitationSerializer(user_invitation)
        data = serializer.data

        assert data['message'] == 'Welcome to the team!'

    def test_api_key_serializer_with_expiry(self, api_key):
        """Test API key serializer with expiry date."""
        from django.utils import timezone
        from datetime import timedelta

        api_key.expires_at = timezone.now() + timedelta(days=30)
        api_key.save()

        serializer = ApiKeySerializer(api_key)
        data = serializer.data

        assert data['expires_at'] is not None
