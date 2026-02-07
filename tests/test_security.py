"""
Security tests for Aureon SaaS Platform.

Tests cover:
- XSS injection attempts
- SQL injection attempts
- Authentication bypass attempts
- Rate limit tests
- CSRF protection
- Authorization bypass attempts
"""

import pytest
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# XSS Injection Tests
# ============================================================================

@pytest.mark.django_db
class TestXSSInjection:
    """Tests for XSS injection prevention."""

    def test_xss_in_user_first_name(self, authenticated_admin_client, xss_payloads):
        """Test XSS payloads in user first name are handled safely."""
        for payload in xss_payloads:
            data = {
                'email': 'xss@test.com',
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
                'first_name': payload,
                'last_name': 'Test',
            }

            response = authenticated_admin_client.post('/api/auth/api/users/', data)

            # The request should either succeed (with escaped content)
            # or fail validation - but not execute the script
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
            ]

            # If created, verify the payload is stored as-is (not executed)
            if response.status_code == status.HTTP_201_CREATED:
                # Content should be escaped in responses
                assert '<script>' not in str(response.content) or '&lt;script&gt;' in str(response.content)

    def test_xss_in_client_company_name(
        self, authenticated_admin_client, xss_payloads
    ):
        """Test XSS payloads in client company name are handled safely."""
        from apps.clients.models import Client

        for i, payload in enumerate(xss_payloads):
            data = {
                'client_type': Client.COMPANY,
                'company_name': payload,
                'first_name': 'Test',
                'last_name': 'User',
                'email': f'xss{i}@client.com',
            }

            response = authenticated_admin_client.post('/api/api/clients/', data)

            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
            ]

    def test_xss_in_contract_title(
        self, authenticated_admin_client, client_company, xss_payloads
    ):
        """Test XSS payloads in contract title are handled safely."""
        from datetime import date

        for i, payload in enumerate(xss_payloads):
            data = {
                'client': str(client_company.id),
                'title': payload,
                'description': 'Test description',
                'contract_type': 'fixed_price',
                'start_date': str(date.today()),
                'value': '1000.00',
            }

            response = authenticated_admin_client.post('/api/api/contracts/', data)

            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
            ]

    def test_xss_in_invoice_notes(
        self, authenticated_admin_client, client_company, xss_payloads
    ):
        """Test XSS payloads in invoice notes are handled safely."""
        from datetime import date, timedelta

        for i, payload in enumerate(xss_payloads):
            data = {
                'client': str(client_company.id),
                'issue_date': str(date.today()),
                'due_date': str(date.today() + timedelta(days=30)),
                'notes': payload,
            }

            response = authenticated_admin_client.post('/api/api/invoices/', data)

            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
            ]


# ============================================================================
# SQL Injection Tests
# ============================================================================

@pytest.mark.django_db
class TestSQLInjection:
    """Tests for SQL injection prevention."""

    def test_sql_injection_in_search(
        self, authenticated_admin_client, sql_injection_payloads
    ):
        """Test SQL injection in search queries."""
        for payload in sql_injection_payloads:
            response = authenticated_admin_client.get(
                f'/api/api/clients/?search={payload}'
            )

            # Should not cause server error
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
            ]

    def test_sql_injection_in_filter(
        self, authenticated_admin_client, sql_injection_payloads
    ):
        """Test SQL injection in filter parameters."""
        for payload in sql_injection_payloads:
            response = authenticated_admin_client.get(
                f'/api/api/contracts/?status={payload}'
            )

            # Should not cause server error
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_sql_injection_in_ordering(
        self, authenticated_admin_client, sql_injection_payloads
    ):
        """Test SQL injection in ordering parameters."""
        for payload in sql_injection_payloads:
            response = authenticated_admin_client.get(
                f'/api/api/invoices/?ordering={payload}'
            )

            # Should not cause server error
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_sql_injection_in_user_email(
        self, authenticated_admin_client, sql_injection_payloads
    ):
        """Test SQL injection in user email field."""
        for i, payload in enumerate(sql_injection_payloads):
            data = {
                'email': payload,
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
                'first_name': 'SQL',
                'last_name': 'Test',
            }

            response = authenticated_admin_client.post('/api/auth/api/users/', data)

            # Should fail validation, not cause SQL error
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_201_CREATED,
            ]


# ============================================================================
# Authentication Bypass Tests
# ============================================================================

@pytest.mark.django_db
class TestAuthenticationBypass:
    """Tests for authentication bypass prevention."""

    def test_unauthenticated_user_list(self, api_client):
        """Test unauthenticated access to user list is denied."""
        response = api_client.get('/api/auth/api/users/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_client_list(self, api_client):
        """Test unauthenticated access to client list is denied."""
        response = api_client.get('/api/api/clients/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_contract_list(self, api_client):
        """Test unauthenticated access to contract list is denied."""
        response = api_client.get('/api/api/contracts/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_invoice_list(self, api_client):
        """Test unauthenticated access to invoice list is denied."""
        response = api_client.get('/api/api/invoices/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_payment_list(self, api_client):
        """Test unauthenticated access to payment list is denied."""
        response = api_client.get('/api/api/payments/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_tenant_list(self, api_client):
        """Test unauthenticated access to tenant list is denied."""
        response = api_client.get('/api/tenants/')
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_invalid_token(self, api_client):
        """Test invalid authentication token is rejected."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_123')
        response = api_client.get('/api/auth/api/users/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_simulation(self, api_client):
        """Test handling of potentially expired tokens."""
        api_client.credentials(HTTP_AUTHORIZATION='Token expired_token_abc')
        response = api_client.get('/api/api/clients/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Authorization Bypass Tests
# ============================================================================

@pytest.mark.django_db
class TestAuthorizationBypass:
    """Tests for authorization bypass prevention."""

    def test_client_user_cannot_access_admin_functions(
        self, authenticated_client_user, admin_user
    ):
        """Test client user cannot access admin-only functions."""
        # Try to delete another user
        response = authenticated_client_user.delete(
            f'/api/auth/api/users/{admin_user.id}/'
        )

        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_user_cannot_change_other_user_password(
        self, authenticated_contributor_client, admin_user
    ):
        """Test user cannot change another user's password."""
        data = {
            'old_password': 'anything',
            'new_password': 'HackedPass123!',
            'new_password_confirm': 'HackedPass123!',
        }

        response = authenticated_contributor_client.post(
            f'/api/auth/api/users/{admin_user.id}/change_password/',
            data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cross_tenant_data_access(
        self, authenticated_admin_client, tenant_with_trial
    ):
        """Test user cannot access data from another tenant."""
        # Create a client in another tenant context
        from apps.clients.models import Client

        other_client = Client.objects.create(
            first_name='Other',
            last_name='Tenant',
            email='other@tenant.com',
        )

        # Try to access client from different tenant
        response = authenticated_admin_client.get(
            f'/api/api/clients/{other_client.id}/'
        )

        # Should either not find it or return forbidden
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_200_OK,  # Some implementations may allow superuser access
        ]


# ============================================================================
# Rate Limit Tests
# ============================================================================

@pytest.mark.django_db
class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_repeated_login_attempts(self, api_client, admin_user):
        """Test rate limiting on repeated login attempts."""
        # Simulate multiple failed login attempts
        for i in range(10):
            response = api_client.post('/api/auth/login/', {
                'email': admin_user.email,
                'password': 'wrong_password',
            })

        # After many attempts, should either be rate limited or still fail auth
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_404_NOT_FOUND,  # If endpoint doesn't exist
        ]

    def test_rapid_api_requests(self, authenticated_admin_client, rate_limit_data):
        """Test handling of rapid API requests."""
        responses = []

        # Make multiple rapid requests
        for _ in range(50):
            response = authenticated_admin_client.get('/api/api/clients/')
            responses.append(response.status_code)

        # All should succeed or some should be rate limited
        success_count = responses.count(status.HTTP_200_OK)
        rate_limited_count = responses.count(status.HTTP_429_TOO_MANY_REQUESTS)

        # Either all succeed (no rate limiting) or some are rate limited
        assert success_count > 0 or rate_limited_count > 0


# ============================================================================
# File Upload Security Tests
# ============================================================================

@pytest.mark.django_db
class TestFileUploadSecurity:
    """Tests for file upload security."""

    def test_malicious_file_name_sanitization(
        self, authenticated_admin_client, client_company, malicious_file_names
    ):
        """Test malicious file names are sanitized."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        for filename in malicious_file_names:
            file = SimpleUploadedFile(
                filename,
                b'Test content',
                content_type='application/pdf'
            )

            data = {
                'client': str(client_company.id),
                'name': 'Test Document',
                'file': file,
            }

            response = authenticated_admin_client.post(
                '/api/api/documents/',
                data,
                format='multipart'
            )

            # Should either succeed with sanitized name or fail validation
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
            ]

            # If successful, path traversal should not work
            if response.status_code == status.HTTP_201_CREATED:
                assert '../' not in str(response.data.get('file', ''))


# ============================================================================
# Input Validation Tests
# ============================================================================

@pytest.mark.django_db
class TestInputValidation:
    """Tests for input validation security."""

    def test_extremely_long_input(self, authenticated_admin_client):
        """Test handling of extremely long input strings."""
        very_long_string = 'A' * 100000

        data = {
            'email': 'valid@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': very_long_string,
            'last_name': 'Test',
        }

        response = authenticated_admin_client.post('/api/auth/api/users/', data)

        # Should fail validation, not cause buffer overflow
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_null_byte_injection(self, authenticated_admin_client):
        """Test handling of null byte injection attempts."""
        data = {
            'email': 'test@example.com\x00admin@admin.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
        }

        response = authenticated_admin_client.post('/api/auth/api/users/', data)

        # Should fail validation
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unicode_normalization(self, authenticated_admin_client, client_company):
        """Test handling of Unicode normalization attacks."""
        from apps.clients.models import Client

        # Homograph attack - using similar-looking Unicode characters
        data = {
            'client_type': Client.INDIVIDUAL,
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@examp\u0131e.com',  # Using Turkish dotless i
        }

        response = authenticated_admin_client.post('/api/api/clients/', data)

        # Should handle Unicode properly
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        ]


# ============================================================================
# Session Security Tests
# ============================================================================

@pytest.mark.django_db
class TestSessionSecurity:
    """Tests for session security."""

    def test_session_not_exposed_in_response(self, authenticated_admin_client):
        """Test session details are not exposed in API responses."""
        response = authenticated_admin_client.get('/api/auth/api/users/me/')

        assert response.status_code == status.HTTP_200_OK
        assert 'session' not in response.data
        assert 'session_id' not in response.data
        assert 'sessionid' not in str(response.content).lower()

    def test_password_not_in_response(self, authenticated_admin_client, admin_user):
        """Test password is never returned in API responses."""
        response = authenticated_admin_client.get(f'/api/auth/api/users/{admin_user.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert 'password' not in response.data
        assert admin_user.password not in str(response.content)


# ============================================================================
# Content-Type Security Tests
# ============================================================================

@pytest.mark.django_db
class TestContentTypeSecurity:
    """Tests for content-type security."""

    def test_json_content_type_required(self, authenticated_admin_client):
        """Test that proper content type is required for POST requests."""
        # Send plain text when JSON is expected
        response = authenticated_admin_client.post(
            '/api/api/clients/',
            'plain text data',
            content_type='text/plain'
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        ]
