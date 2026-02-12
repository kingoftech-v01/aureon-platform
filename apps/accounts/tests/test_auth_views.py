"""
Tests for accounts auth_views module.

Covers:
- register endpoint (success, password mismatch, duplicate email, missing fields, etc.)
- login endpoint via CustomTokenObtainPairView (success, wrong password, inactive user)
- get_current_user (authenticated, unauthenticated)
- logout endpoint
- CustomTokenObtainPairSerializer (user data in token response)
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

# Base path for all auth endpoints
AUTH_URL_PREFIX = "/api/auth/"


# ============================================================================
# Register Endpoint Tests
# ============================================================================


class TestRegisterEndpoint:
    """Tests for the register view."""

    REGISTER_URL = f"{AUTH_URL_PREFIX}register/"

    @pytest.mark.django_db
    def test_register_success(self, api_client):
        """Registration with valid data creates user and returns tokens."""
        data = {
            "email": "newuser@example.com",
            "password": "V3ryS3cureP@ss!",
            "password_confirm": "V3ryS3cureP@ss!",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == "newuser@example.com"
        assert response.data["user"]["first_name"] == "New"
        assert response.data["user"]["last_name"] == "User"

        # Verify user exists in the database
        assert User.objects.filter(email="newuser@example.com").exists()

    @pytest.mark.django_db
    def test_register_success_minimal_fields(self, api_client):
        """Registration succeeds with only required fields (email, passwords)."""
        data = {
            "email": "minimal@example.com",
            "password": "V3ryS3cureP@ss!",
            "password_confirm": "V3ryS3cureP@ss!",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["email"] == "minimal@example.com"
        # Default role should be CONTRIBUTOR
        assert response.data["user"]["role"] == User.CONTRIBUTOR

    @pytest.mark.django_db
    def test_register_with_role(self, api_client):
        """Registration with explicit role sets the role correctly."""
        data = {
            "email": "manager@example.com",
            "password": "V3ryS3cureP@ss!",
            "password_confirm": "V3ryS3cureP@ss!",
            "first_name": "Manager",
            "last_name": "Test",
            "role": User.MANAGER,
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["role"] == User.MANAGER

    @pytest.mark.django_db
    def test_register_password_mismatch(self, api_client):
        """Registration fails when passwords do not match."""
        data = {
            "email": "mismatch@example.com",
            "password": "V3ryS3cureP@ss!",
            "password_confirm": "DifferentPassword123!",
            "first_name": "Mismatch",
            "last_name": "User",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    @pytest.mark.django_db
    def test_register_duplicate_email(self, api_client, admin_user):
        """Registration fails when email already exists."""
        data = {
            "email": admin_user.email,
            "password": "V3ryS3cureP@ss!",
            "password_confirm": "V3ryS3cureP@ss!",
            "first_name": "Duplicate",
            "last_name": "User",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    @pytest.mark.django_db
    def test_register_missing_email(self, api_client):
        """Registration fails when email is missing."""
        data = {
            "password": "V3ryS3cureP@ss!",
            "password_confirm": "V3ryS3cureP@ss!",
            "first_name": "No",
            "last_name": "Email",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    @pytest.mark.django_db
    def test_register_missing_password(self, api_client):
        """Registration fails when password is missing."""
        data = {
            "email": "nopass@example.com",
            "password_confirm": "V3ryS3cureP@ss!",
            "first_name": "No",
            "last_name": "Password",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    @pytest.mark.django_db
    def test_register_missing_password_confirm(self, api_client):
        """Registration fails when password_confirm is missing."""
        data = {
            "email": "noconfirm@example.com",
            "password": "V3ryS3cureP@ss!",
            "first_name": "No",
            "last_name": "Confirm",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data

    @pytest.mark.django_db
    def test_register_weak_password(self, api_client):
        """Registration fails with a weak password (Django password validators)."""
        data = {
            "email": "weakpass@example.com",
            "password": "123",
            "password_confirm": "123",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    @pytest.mark.django_db
    def test_register_invalid_email_format(self, api_client):
        """Registration fails with an invalid email format."""
        data = {
            "email": "not-an-email",
            "password": "V3ryS3cureP@ss!",
            "password_confirm": "V3ryS3cureP@ss!",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    @pytest.mark.django_db
    def test_register_empty_body(self, api_client):
        """Registration fails with empty request body."""
        response = api_client.post(self.REGISTER_URL, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_register_returns_jwt_tokens(self, api_client):
        """Registration returns valid JWT access and refresh tokens."""
        data = {
            "email": "jwt@example.com",
            "password": "V3ryS3cureP@ss!",
            "password_confirm": "V3ryS3cureP@ss!",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        # JWT tokens are non-empty strings
        assert isinstance(response.data["access"], str)
        assert len(response.data["access"]) > 0
        assert isinstance(response.data["refresh"], str)
        assert len(response.data["refresh"]) > 0

    @pytest.mark.django_db
    def test_register_get_method_not_allowed(self, api_client):
        """Register endpoint only accepts POST."""
        response = api_client.get(self.REGISTER_URL)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.django_db
    def test_register_user_data_in_response(self, api_client):
        """Registration response includes serialized user data."""
        data = {
            "email": "userdata@example.com",
            "password": "V3ryS3cureP@ss!",
            "password_confirm": "V3ryS3cureP@ss!",
            "first_name": "Data",
            "last_name": "Check",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        user_data = response.data["user"]
        assert "id" in user_data
        assert "email" in user_data
        assert "first_name" in user_data
        assert "last_name" in user_data
        assert "role" in user_data
        assert "is_active" in user_data


# ============================================================================
# Login Endpoint Tests (CustomTokenObtainPairView)
# ============================================================================


class TestLoginEndpoint:
    """Tests for the login (CustomTokenObtainPairView) view."""

    LOGIN_URL = f"{AUTH_URL_PREFIX}login/"

    @pytest.mark.django_db
    def test_login_success(self, api_client, admin_user):
        """Login with correct credentials returns tokens and user data."""
        data = {
            "email": admin_user.email,
            "password": "SecurePass123!",
        }
        response = api_client.post(self.LOGIN_URL, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == admin_user.email

    @pytest.mark.django_db
    def test_login_returns_user_data(self, api_client, admin_user):
        """Login response includes serialized user data from CustomTokenObtainPairSerializer."""
        data = {
            "email": admin_user.email,
            "password": "SecurePass123!",
        }
        response = api_client.post(self.LOGIN_URL, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        user_data = response.data["user"]
        assert user_data["email"] == admin_user.email
        assert user_data["first_name"] == admin_user.first_name
        assert user_data["last_name"] == admin_user.last_name
        assert user_data["role"] == admin_user.role
        assert "id" in user_data

    @pytest.mark.django_db
    def test_login_wrong_password(self, api_client, admin_user):
        """Login with wrong password fails."""
        data = {
            "email": admin_user.email,
            "password": "WrongPassword123!",
        }
        response = api_client.post(self.LOGIN_URL, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_login_nonexistent_email(self, api_client):
        """Login with non-existent email fails."""
        data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        }
        response = api_client.post(self.LOGIN_URL, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_login_inactive_user(self, api_client, inactive_user):
        """Login with inactive user account fails."""
        data = {
            "email": inactive_user.email,
            "password": "SecurePass123!",
        }
        response = api_client.post(self.LOGIN_URL, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_login_missing_email(self, api_client):
        """Login fails when email is missing."""
        data = {
            "password": "SecurePass123!",
        }
        response = api_client.post(self.LOGIN_URL, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_login_missing_password(self, api_client):
        """Login fails when password is missing."""
        data = {
            "email": "admin@testorg.com",
        }
        response = api_client.post(self.LOGIN_URL, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_login_empty_body(self, api_client):
        """Login fails with empty request body."""
        response = api_client.post(self.LOGIN_URL, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_login_get_method_not_allowed(self, api_client):
        """Login endpoint only accepts POST."""
        response = api_client.get(self.LOGIN_URL)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.django_db
    def test_login_different_roles(self, api_client, manager_user, contributor_user, client_user):
        """Login works for all user roles."""
        for user in [manager_user, contributor_user, client_user]:
            client = APIClient()
            client.defaults['HTTP_ORIGIN'] = 'http://testserver'
            client.defaults['SERVER_NAME'] = 'testserver'
            data = {
                "email": user.email,
                "password": "SecurePass123!",
            }
            response = client.post(self.LOGIN_URL, data, format="json")

            assert response.status_code == status.HTTP_200_OK
            assert response.data["user"]["role"] == user.role


# ============================================================================
# Get Current User Endpoint Tests
# ============================================================================


class TestGetCurrentUser:
    """Tests for the get_current_user view."""

    USER_URL = f"{AUTH_URL_PREFIX}user/"

    @pytest.mark.django_db
    def test_get_current_user_authenticated(self, authenticated_admin_client, admin_user):
        """Authenticated user can retrieve their own data."""
        response = authenticated_admin_client.get(self.USER_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == admin_user.email
        assert response.data["first_name"] == admin_user.first_name
        assert response.data["last_name"] == admin_user.last_name
        assert response.data["role"] == admin_user.role

    @pytest.mark.django_db
    def test_get_current_user_unauthenticated(self, api_client):
        """Unauthenticated request to get current user fails with 401."""
        response = api_client.get(self.USER_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # DRF's default IsAuthenticated permission returns this message
        # before the view's own check is reached.
        assert "not_authenticated" in str(response.data["detail"].code) or \
            "Authentication credentials were not provided" in str(response.data["detail"])

    @pytest.mark.django_db
    def test_get_current_user_returns_full_data(self, authenticated_admin_client, admin_user):
        """Authenticated user response includes all expected fields."""
        response = authenticated_admin_client.get(self.USER_URL)

        assert response.status_code == status.HTTP_200_OK
        expected_fields = [
            "id", "email", "first_name", "last_name", "role",
            "is_active", "is_admin", "is_manager",
            "two_factor_enabled", "timezone", "language",
        ]
        for field in expected_fields:
            assert field in response.data, f"Missing field: {field}"

    @pytest.mark.django_db
    def test_get_current_user_admin_properties(self, authenticated_admin_client):
        """Admin user response shows is_admin=True and is_manager=True."""
        response = authenticated_admin_client.get(self.USER_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_admin"] is True
        assert response.data["is_manager"] is True

    @pytest.mark.django_db
    def test_get_current_user_contributor_properties(
        self, authenticated_contributor_client, contributor_user
    ):
        """Contributor user response shows is_admin=False and is_manager=False."""
        response = authenticated_contributor_client.get(self.USER_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_admin"] is False
        assert response.data["is_manager"] is False
        assert response.data["role"] == User.CONTRIBUTOR

    @pytest.mark.django_db
    def test_get_current_user_post_not_allowed(self, authenticated_admin_client):
        """Current user endpoint only accepts GET."""
        response = authenticated_admin_client.post(self.USER_URL, {}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ============================================================================
# Logout Endpoint Tests
# ============================================================================


class TestLogoutEndpoint:
    """Tests for the logout view."""

    LOGOUT_URL = f"{AUTH_URL_PREFIX}logout/"

    @pytest.mark.django_db
    def test_logout_success(self, api_client):
        """Logout returns success message."""
        response = api_client.post(self.LOGOUT_URL, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Successfully logged out."

    @pytest.mark.django_db
    def test_logout_authenticated_user(self, authenticated_admin_client):
        """Authenticated user can log out successfully."""
        response = authenticated_admin_client.post(self.LOGOUT_URL, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Successfully logged out."

    @pytest.mark.django_db
    def test_logout_unauthenticated_user(self, api_client):
        """Unauthenticated user can also call logout (AllowAny)."""
        response = api_client.post(self.LOGOUT_URL, format="json")

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_logout_get_method_not_allowed(self, api_client):
        """Logout endpoint only accepts POST."""
        response = api_client.get(self.LOGOUT_URL)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.django_db
    def test_logout_idempotent(self, api_client):
        """Calling logout multiple times always succeeds."""
        for _ in range(3):
            response = api_client.post(self.LOGOUT_URL, format="json")
            assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Token Refresh Endpoint Tests
# ============================================================================


class TestTokenRefresh:
    """Tests for the token refresh view."""

    REFRESH_URL = f"{AUTH_URL_PREFIX}token/refresh/"
    LOGIN_URL = f"{AUTH_URL_PREFIX}login/"

    @pytest.mark.django_db
    def test_token_refresh_success(self, api_client, admin_user):
        """Valid refresh token returns a new access token."""
        # First login to get tokens
        login_data = {
            "email": admin_user.email,
            "password": "SecurePass123!",
        }
        login_response = api_client.post(self.LOGIN_URL, login_data, format="json")
        refresh_token = login_response.data["refresh"]

        # Use refresh token
        response = api_client.post(
            self.REFRESH_URL, {"refresh": refresh_token}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    @pytest.mark.django_db
    def test_token_refresh_invalid_token(self, api_client):
        """Invalid refresh token is rejected."""
        response = api_client.post(
            self.REFRESH_URL, {"refresh": "invalid-token"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_token_refresh_missing_token(self, api_client):
        """Missing refresh token returns error."""
        response = api_client.post(self.REFRESH_URL, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# get_current_user unauthenticated branch (covers line 86)
# ============================================================================


class TestGetCurrentUserInternalCheck:
    """Tests for the internal is_authenticated check in get_current_user (line 86)."""

    @pytest.mark.django_db
    def test_get_current_user_unauthenticated_internal_check(self):
        """Bypass DRF permission to exercise the view's own is_authenticated check."""
        from unittest.mock import patch as mock_patch, MagicMock
        from django.contrib.auth.models import AnonymousUser

        client = APIClient()

        # Override default permission classes to allow the request through
        with mock_patch(
            'apps.accounts.auth_views.permission_classes',
        ) as mock_perms:
            # Override the view's permissions at the DRF level
            with mock_patch(
                'rest_framework.views.APIView.check_permissions',
                return_value=None,
            ):
                # Force the request user to be AnonymousUser
                with mock_patch(
                    'rest_framework.views.APIView.perform_authentication',
                    return_value=None,
                ):
                    response = client.get(f"{AUTH_URL_PREFIX}user/")

        # Either the DRF default permission or the view's own check returns 401
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
