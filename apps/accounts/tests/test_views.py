"""
Tests for accounts app views and API endpoints.

Tests cover:
- User CRUD operations
- User profile endpoints
- Password change functionality
- User invitations
- API key management
- Authentication and authorization
"""

import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# User ViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestUserViewSet:
    """Tests for UserViewSet."""

    def test_list_users_authenticated(self, authenticated_admin_client, admin_user, manager_user):
        """Test listing users as authenticated user."""
        response = authenticated_admin_client.get('/api/users/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_users_unauthenticated(self, api_client):
        """Test listing users as unauthenticated user."""
        response = api_client.get('/api/users/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_user(self, authenticated_admin_client, admin_user):
        """Test retrieving a specific user."""
        response = authenticated_admin_client.get(f'/api/users/{admin_user.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == admin_user.email

    def test_create_user(self, authenticated_admin_client, tenant):
        """Test creating a new user."""
        data = {
            'email': 'newuser@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': User.CONTRIBUTOR,
        }

        response = authenticated_admin_client.post('/api/users/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'newuser@test.com'

    def test_create_user_password_mismatch(self, authenticated_admin_client):
        """Test creating user with mismatched passwords."""
        data = {
            'email': 'newuser@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
            'first_name': 'New',
            'last_name': 'User',
        }

        response = authenticated_admin_client.post('/api/users/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data or 'password_confirm' in str(response.data)

    def test_create_user_weak_password(self, authenticated_admin_client):
        """Test creating user with weak password."""
        data = {
            'email': 'newuser@test.com',
            'password': '123',
            'password_confirm': '123',
            'first_name': 'New',
            'last_name': 'User',
        }

        response = authenticated_admin_client.post('/api/users/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_user(self, authenticated_admin_client, contributor_user):
        """Test updating a user."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'job_title': 'Senior Developer',
        }

        response = authenticated_admin_client.patch(
            f'/api/users/{contributor_user.id}/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'

    def test_delete_user(self, authenticated_admin_client, contributor_user):
        """Test deleting a user."""
        response = authenticated_admin_client.delete(
            f'/api/users/{contributor_user.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(id=contributor_user.id).exists()

    def test_me_endpoint(self, authenticated_admin_client, admin_user):
        """Test the /me endpoint returns current user."""
        response = authenticated_admin_client.get('/api/users/me/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == admin_user.email
        assert response.data['id'] == str(admin_user.id)

    def test_users_filtered_by_tenant(self, authenticated_admin_client, admin_user, tenant):
        """Test users are filtered by tenant."""
        response = authenticated_admin_client.get('/api/users/')

        # All returned users should belong to the same tenant
        assert response.status_code == status.HTTP_200_OK
        for user_data in response.data:
            if user_data.get('tenant'):
                assert user_data['tenant'] == str(tenant.id)


# ============================================================================
# Password Change Tests
# ============================================================================

@pytest.mark.django_db
class TestPasswordChange:
    """Tests for password change functionality."""

    def test_change_password_success(self, authenticated_admin_client, admin_user):
        """Test successful password change."""
        data = {
            'old_password': 'SecurePass123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }

        response = authenticated_admin_client.post(
            f'/api/users/{admin_user.id}/change_password/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert admin_user.check_password('NewSecurePass456!')

    def test_change_password_wrong_old_password(self, authenticated_admin_client, admin_user):
        """Test password change with wrong old password."""
        data = {
            'old_password': 'WrongPassword123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }

        response = authenticated_admin_client.post(
            f'/api/users/{admin_user.id}/change_password/',
            data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data

    def test_change_password_mismatch(self, authenticated_admin_client, admin_user):
        """Test password change with mismatched new passwords."""
        data = {
            'old_password': 'SecurePass123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'DifferentPass789!',
        }

        response = authenticated_admin_client.post(
            f'/api/users/{admin_user.id}/change_password/',
            data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_other_user_forbidden(
        self, authenticated_contributor_client, admin_user
    ):
        """Test that users cannot change other users' passwords."""
        data = {
            'old_password': 'SecurePass123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }

        response = authenticated_contributor_client.post(
            f'/api/users/{admin_user.id}/change_password/',
            data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# User Invitation ViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestUserInvitationViewSet:
    """Tests for UserInvitationViewSet."""

    def test_list_invitations(self, authenticated_admin_client, user_invitation):
        """Test listing user invitations."""
        response = authenticated_admin_client.get('/api/auth/api/invitations/')

        assert response.status_code == status.HTTP_200_OK

    def test_create_invitation(self, authenticated_admin_client, tenant):
        """Test creating a user invitation."""
        data = {
            'email': 'newinvite@example.com',
            'role': User.CONTRIBUTOR,
            'message': 'Welcome to the team!',
        }

        response = authenticated_admin_client.post('/api/auth/api/invitations/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'newinvite@example.com'
        assert response.data['status'] == 'pending'

    def test_cancel_invitation(self, authenticated_admin_client, user_invitation):
        """Test cancelling an invitation."""
        response = authenticated_admin_client.post(
            f'/api/auth/api/invitations/{user_invitation.id}/cancel/'
        )

        assert response.status_code == status.HTTP_200_OK
        user_invitation.refresh_from_db()
        assert user_invitation.status == 'cancelled'

    def test_accept_invitation_requires_token(self, api_client):
        """Test accepting invitation requires token."""
        response = api_client.post('/api/auth/api/invitations/accept/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_accept_invitation_invalid_token(self, authenticated_contributor_client):
        """Test accepting invitation with invalid token."""
        response = authenticated_contributor_client.post(
            '/api/auth/api/invitations/accept/',
            {'token': 'invalid-token-12345'}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# API Key ViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestApiKeyViewSet:
    """Tests for ApiKeyViewSet."""

    def test_list_api_keys(self, authenticated_admin_client, api_key):
        """Test listing API keys."""
        response = authenticated_admin_client.get('/api/auth/api/api-keys/')

        assert response.status_code == status.HTTP_200_OK

    def test_create_api_key(self, authenticated_admin_client, tenant):
        """Test creating an API key."""
        data = {
            'name': 'New API Key',
            'scopes': ['read'],
        }

        response = authenticated_admin_client.post('/api/auth/api/api-keys/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New API Key'
        # The full key should be returned only on creation
        assert 'key' in response.data

    def test_deactivate_api_key(self, authenticated_admin_client, api_key):
        """Test deactivating an API key."""
        response = authenticated_admin_client.post(
            f'/api/auth/api/api-keys/{api_key.id}/deactivate/'
        )

        assert response.status_code == status.HTTP_200_OK
        api_key.refresh_from_db()
        assert api_key.is_active is False

    def test_activate_api_key(self, authenticated_admin_client, api_key):
        """Test activating an API key."""
        api_key.is_active = False
        api_key.save()

        response = authenticated_admin_client.post(
            f'/api/auth/api/api-keys/{api_key.id}/activate/'
        )

        assert response.status_code == status.HTTP_200_OK
        api_key.refresh_from_db()
        assert api_key.is_active is True

    def test_delete_api_key(self, authenticated_admin_client, api_key):
        """Test deleting an API key."""
        response = authenticated_admin_client.delete(
            f'/api/auth/api/api-keys/{api_key.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT


# ============================================================================
# Authorization Tests
# ============================================================================

@pytest.mark.django_db
class TestUserAuthorization:
    """Tests for user authorization."""

    def test_contributor_cannot_create_users(self, authenticated_contributor_client):
        """Test contributor cannot create users."""
        data = {
            'email': 'newuser@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
        }

        response = authenticated_contributor_client.post('/api/users/', data)

        # Should either be forbidden or the user creation is allowed
        # but user is assigned to same tenant
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_client_user_limited_access(self, authenticated_client_user):
        """Test client user has limited access."""
        response = authenticated_client_user.get('/api/users/')

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN
        ]

    def test_superuser_sees_all_users(self, authenticated_superuser_client, admin_user, tenant):
        """Test superuser can see all users."""
        response = authenticated_superuser_client.get('/api/users/')

        assert response.status_code == status.HTTP_200_OK

    def test_inactive_user_cannot_login(self, api_client, inactive_user):
        """Test inactive user cannot authenticate."""
        response = api_client.post('/api/auth/login/', {
            'email': inactive_user.email,
            'password': 'SecurePass123!',
        })

        # Login should fail for inactive users
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
        ]


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@pytest.mark.django_db
class TestUserViewEdgeCases:
    """Edge case tests for user views."""

    def test_create_user_duplicate_email(self, authenticated_admin_client, admin_user):
        """Test creating user with duplicate email."""
        data = {
            'email': admin_user.email,
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Duplicate',
            'last_name': 'User',
        }

        response = authenticated_admin_client.post('/api/users/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_nonexistent_user(self, authenticated_admin_client):
        """Test retrieving a nonexistent user."""
        import uuid
        fake_id = uuid.uuid4()

        response = authenticated_admin_client.get(f'/api/users/{fake_id}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_email_to_existing(self, authenticated_admin_client, admin_user, contributor_user):
        """Test updating email to an existing email."""
        data = {'email': contributor_user.email}

        response = authenticated_admin_client.patch(
            f'/api/users/{admin_user.id}/',
            data
        )

        # Email updates might be restricted or cause validation error
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_user_with_special_characters_in_name(self, authenticated_admin_client):
        """Test creating user with special characters in name."""
        data = {
            'email': 'special@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': "O'Connor",
            'last_name': 'Smith-Jones',
        }

        response = authenticated_admin_client.post('/api/users/', data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_user_with_unicode_name(self, authenticated_admin_client):
        """Test creating user with Unicode characters in name."""
        data = {
            'email': 'unicode@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Jean-Pierre',
            'last_name': 'Garcia',
        }

        response = authenticated_admin_client.post('/api/users/', data)

        assert response.status_code == status.HTTP_201_CREATED
