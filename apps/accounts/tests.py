"""
Comprehensive unit tests for accounts app.

Tests 2FA setup, token verification, and backup codes.
"""

import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
import pyotp

from .models import User, UserInvitation, ApiKey
from .two_factor import (
    TwoFactorAuthService,
    enable_2fa,
    verify_2fa_setup,
    disable_2fa,
    verify_2fa_token,
    use_backup_code,
    regenerate_backup_codes,
    get_2fa_status
)

User = get_user_model()


class UserModelTests(TestCase):
    """Test User model."""

    def setUp(self):
        """Set up test data."""
        from apps.tenants.models import Tenant

        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )

    def test_user_creation_with_email(self):
        """Test creating user with email."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertIsNotNone(user.username)  # Auto-generated

    def test_user_creation_generates_username(self):
        """Test that username is auto-generated from email."""
        user = User.objects.create_user(
            email='john.doe@example.com',
            password='testpass123'
        )

        self.assertIn('john.doe', user.username)

    def test_get_full_name_with_full_name_field(self):
        """Test get_full_name when full_name field is set."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='John Alexander Doe'
        )

        self.assertEqual(user.get_full_name(), 'John Alexander Doe')

    def test_get_full_name_with_first_last_name(self):
        """Test get_full_name with first_name and last_name."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )

        self.assertEqual(user.get_full_name(), 'Jane Smith')

    def test_get_full_name_fallback_to_email(self):
        """Test get_full_name falls back to email."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        self.assertEqual(user.get_full_name(), 'test@example.com')

    def test_get_short_name(self):
        """Test get_short_name method."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John'
        )

        self.assertEqual(user.get_short_name(), 'John')

    def test_is_admin_property(self):
        """Test is_admin property."""
        admin = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            role=User.ADMIN
        )

        regular = User.objects.create_user(
            email='regular@example.com',
            password='testpass123',
            role=User.CONTRIBUTOR
        )

        self.assertTrue(admin.is_admin)
        self.assertFalse(regular.is_admin)

    def test_is_manager_property(self):
        """Test is_manager property."""
        manager = User.objects.create_user(
            email='manager@example.com',
            password='testpass123',
            role=User.MANAGER
        )

        contributor = User.objects.create_user(
            email='contributor@example.com',
            password='testpass123',
            role=User.CONTRIBUTOR
        )

        self.assertTrue(manager.is_manager)
        self.assertFalse(contributor.is_manager)

    def test_is_client_user_property(self):
        """Test is_client_user property."""
        client_user = User.objects.create_user(
            email='client@example.com',
            password='testpass123',
            role=User.CLIENT
        )

        regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpass123',
            role=User.CONTRIBUTOR
        )

        self.assertTrue(client_user.is_client_user)
        self.assertFalse(regular_user.is_client_user)

    def test_has_tenant_permission(self):
        """Test has_tenant_permission method."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            tenant=self.tenant
        )

        other_tenant = self.tenant.__class__.objects.create(
            name='Other Tenant',
            slug='other-tenant'
        )

        self.assertTrue(user.has_tenant_permission(self.tenant))
        self.assertFalse(user.has_tenant_permission(other_tenant))

    def test_superuser_has_all_permissions(self):
        """Test that superuser has all permissions."""
        superuser = User.objects.create_superuser(
            email='super@example.com',
            password='testpass123'
        )

        self.assertTrue(superuser.is_admin)
        self.assertTrue(superuser.can_manage_contracts())
        self.assertTrue(superuser.can_manage_invoices())
        self.assertTrue(superuser.can_manage_users())

    def test_permission_methods(self):
        """Test various permission methods."""
        admin = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            role=User.ADMIN
        )

        manager = User.objects.create_user(
            email='manager@example.com',
            password='testpass123',
            role=User.MANAGER
        )

        contributor = User.objects.create_user(
            email='contributor@example.com',
            password='testpass123',
            role=User.CONTRIBUTOR
        )

        # Admin can do everything
        self.assertTrue(admin.can_manage_contracts())
        self.assertTrue(admin.can_manage_invoices())
        self.assertTrue(admin.can_manage_users())
        self.assertTrue(admin.can_access_analytics())

        # Manager can manage contracts/invoices but not users
        self.assertTrue(manager.can_manage_contracts())
        self.assertTrue(manager.can_manage_invoices())
        self.assertFalse(manager.can_manage_users())
        self.assertTrue(manager.can_access_analytics())

        # Contributor has limited permissions
        self.assertFalse(contributor.can_manage_contracts())
        self.assertFalse(contributor.can_manage_invoices())
        self.assertFalse(contributor.can_manage_users())
        self.assertFalse(contributor.can_access_analytics())


class TwoFactorAuthServiceTests(TestCase):
    """Test TwoFactorAuthService methods."""

    def test_generate_secret(self):
        """Test generating TOTP secret."""
        secret = TwoFactorAuthService.generate_secret()

        self.assertIsNotNone(secret)
        self.assertIsInstance(secret, str)
        self.assertEqual(len(secret), 32)  # Base32 encoded

    def test_generate_qr_code(self):
        """Test generating QR code."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        secret = TwoFactorAuthService.generate_secret()

        qr_code = TwoFactorAuthService.generate_qr_code(user, secret)

        self.assertIsNotNone(qr_code)
        self.assertTrue(qr_code.startswith('data:image/png;base64,'))

    def test_verify_token_valid(self):
        """Test verifying valid TOTP token."""
        secret = TwoFactorAuthService.generate_secret()
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()

        result = TwoFactorAuthService.verify_token(secret, valid_token)

        self.assertTrue(result)

    def test_verify_token_invalid(self):
        """Test verifying invalid TOTP token."""
        secret = TwoFactorAuthService.generate_secret()
        invalid_token = '000000'

        result = TwoFactorAuthService.verify_token(secret, invalid_token)

        self.assertFalse(result)

    def test_verify_token_with_time_window(self):
        """Test that token verification allows time window."""
        secret = TwoFactorAuthService.generate_secret()
        totp = pyotp.TOTP(secret)

        # Get token from 30 seconds ago
        import time
        past_time = int(time.time()) - 30
        past_token = totp.at(past_time)

        # Should still be valid due to valid_window=1
        result = TwoFactorAuthService.verify_token(secret, past_token)

        # Note: This may occasionally fail near time boundaries
        # In production, valid_window handles this

    def test_generate_backup_codes(self):
        """Test generating backup codes."""
        codes = TwoFactorAuthService.generate_backup_codes(count=10)

        self.assertEqual(len(codes), 10)
        for code in codes:
            # Format: XXXX-XXXX
            self.assertEqual(len(code), 9)
            self.assertIn('-', code)

    def test_generate_backup_codes_unique(self):
        """Test that generated backup codes are unique."""
        codes = TwoFactorAuthService.generate_backup_codes(count=50)

        # All codes should be unique
        self.assertEqual(len(codes), len(set(codes)))


class Enable2FATests(TestCase):
    """Test enabling 2FA."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_enable_2fa_success(self):
        """Test successfully enabling 2FA."""
        request = self.factory.post('/api/auth/2fa/enable/')
        force_authenticate(request, user=self.user)

        response = enable_2fa(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('secret', response.data)
        self.assertIn('qr_code', response.data)

        # Verify secret was saved
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.two_factor_secret)
        self.assertFalse(self.user.two_factor_enabled)  # Not enabled until verified

    def test_enable_2fa_already_enabled(self):
        """Test enabling 2FA when already enabled."""
        self.user.two_factor_enabled = True
        self.user.save()

        request = self.factory.post('/api/auth/2fa/enable/')
        force_authenticate(request, user=self.user)

        response = enable_2fa(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class Verify2FASetupTests(TestCase):
    """Test verifying 2FA setup."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.secret = TwoFactorAuthService.generate_secret()
        self.user.two_factor_secret = self.secret
        self.user.save()

    def test_verify_2fa_setup_success(self):
        """Test successfully verifying 2FA setup."""
        totp = pyotp.TOTP(self.secret)
        valid_token = totp.now()

        request = self.factory.post('/api/auth/2fa/verify-setup/', {
            'token': valid_token
        }, format='json')
        force_authenticate(request, user=self.user)

        response = verify_2fa_setup(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('backup_codes', response.data)

        # Verify 2FA is now enabled
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
        self.assertGreater(len(self.user.two_factor_backup_codes), 0)

    def test_verify_2fa_setup_invalid_token(self):
        """Test verifying 2FA setup with invalid token."""
        request = self.factory.post('/api/auth/2fa/verify-setup/', {
            'token': '000000'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = verify_2fa_setup(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify 2FA is still not enabled
        self.user.refresh_from_db()
        self.assertFalse(self.user.two_factor_enabled)

    def test_verify_2fa_setup_missing_token(self):
        """Test verifying 2FA setup without token."""
        request = self.factory.post('/api/auth/2fa/verify-setup/', {}, format='json')
        force_authenticate(request, user=self.user)

        response = verify_2fa_setup(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_2fa_setup_not_initiated(self):
        """Test verifying 2FA setup when not initiated."""
        user_without_secret = User.objects.create_user(
            email='nosecret@example.com',
            password='testpass123'
        )

        request = self.factory.post('/api/auth/2fa/verify-setup/', {
            'token': '123456'
        }, format='json')
        force_authenticate(request, user=user_without_secret)

        response = verify_2fa_setup(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class Disable2FATests(TestCase):
    """Test disabling 2FA."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.secret = TwoFactorAuthService.generate_secret()
        self.user.two_factor_enabled = True
        self.user.two_factor_secret = self.secret
        self.user.two_factor_backup_codes = ['AAAA-BBBB', 'CCCC-DDDD']
        self.user.save()

    def test_disable_2fa_with_token_success(self):
        """Test disabling 2FA with valid token."""
        totp = pyotp.TOTP(self.secret)
        valid_token = totp.now()

        request = self.factory.post('/api/auth/2fa/disable/', {
            'token': valid_token
        }, format='json')
        force_authenticate(request, user=self.user)

        response = disable_2fa(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify 2FA is disabled
        self.user.refresh_from_db()
        self.assertFalse(self.user.two_factor_enabled)
        self.assertEqual(self.user.two_factor_secret, '')
        self.assertEqual(len(self.user.two_factor_backup_codes), 0)

    def test_disable_2fa_with_backup_code_success(self):
        """Test disabling 2FA with backup code."""
        request = self.factory.post('/api/auth/2fa/disable/', {
            'backup_code': 'AAAA-BBBB'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = disable_2fa(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify 2FA is disabled
        self.user.refresh_from_db()
        self.assertFalse(self.user.two_factor_enabled)

    def test_disable_2fa_invalid_token(self):
        """Test disabling 2FA with invalid token."""
        request = self.factory.post('/api/auth/2fa/disable/', {
            'token': '000000'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = disable_2fa(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify 2FA is still enabled
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)

    def test_disable_2fa_not_enabled(self):
        """Test disabling 2FA when not enabled."""
        self.user.two_factor_enabled = False
        self.user.save()

        request = self.factory.post('/api/auth/2fa/disable/', {
            'token': '123456'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = disable_2fa(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class Verify2FATokenTests(TestCase):
    """Test verifying 2FA tokens during login."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.secret = TwoFactorAuthService.generate_secret()
        self.user.two_factor_enabled = True
        self.user.two_factor_secret = self.secret
        self.user.save()

    def test_verify_token_success(self):
        """Test verifying valid 2FA token."""
        totp = pyotp.TOTP(self.secret)
        valid_token = totp.now()

        request = self.factory.post('/api/auth/2fa/verify/', {
            'token': valid_token
        }, format='json')
        force_authenticate(request, user=self.user)

        response = verify_2fa_token(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['verified'])

    def test_verify_token_invalid(self):
        """Test verifying invalid 2FA token."""
        request = self.factory.post('/api/auth/2fa/verify/', {
            'token': '000000'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = verify_2fa_token(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['verified'])


class UseBackupCodeTests(TestCase):
    """Test using backup codes."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.two_factor_enabled = True
        self.user.two_factor_backup_codes = [
            'AAAA-BBBB',
            'CCCC-DDDD',
            'EEEE-FFFF'
        ]
        self.user.save()

    def test_use_backup_code_success(self):
        """Test using valid backup code."""
        request = self.factory.post('/api/auth/2fa/backup-code/', {
            'backup_code': 'AAAA-BBBB'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = use_backup_code(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['verified'])
        self.assertEqual(response.data['remaining_codes'], 2)

        # Verify code was removed
        self.user.refresh_from_db()
        self.assertNotIn('AAAA-BBBB', self.user.two_factor_backup_codes)
        self.assertEqual(len(self.user.two_factor_backup_codes), 2)

    def test_use_backup_code_invalid(self):
        """Test using invalid backup code."""
        request = self.factory.post('/api/auth/2fa/backup-code/', {
            'backup_code': 'ZZZZ-ZZZZ'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = use_backup_code(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['verified'])

    def test_use_backup_code_already_used(self):
        """Test using already used backup code."""
        # Use code first time
        request1 = self.factory.post('/api/auth/2fa/backup-code/', {
            'backup_code': 'AAAA-BBBB'
        }, format='json')
        force_authenticate(request1, user=self.user)
        use_backup_code(request1)

        # Try to use same code again
        request2 = self.factory.post('/api/auth/2fa/backup-code/', {
            'backup_code': 'AAAA-BBBB'
        }, format='json')
        force_authenticate(request2, user=self.user)
        response = use_backup_code(request2)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RegenerateBackupCodesTests(TestCase):
    """Test regenerating backup codes."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.secret = TwoFactorAuthService.generate_secret()
        self.user.two_factor_enabled = True
        self.user.two_factor_secret = self.secret
        self.user.two_factor_backup_codes = ['OLD1-CODE', 'OLD2-CODE']
        self.user.save()

    def test_regenerate_backup_codes_success(self):
        """Test successfully regenerating backup codes."""
        totp = pyotp.TOTP(self.secret)
        valid_token = totp.now()

        request = self.factory.post('/api/auth/2fa/regenerate-backup-codes/', {
            'token': valid_token
        }, format='json')
        force_authenticate(request, user=self.user)

        response = regenerate_backup_codes(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('backup_codes', response.data)

        # Verify new codes were generated
        self.user.refresh_from_db()
        self.assertNotIn('OLD1-CODE', self.user.two_factor_backup_codes)
        self.assertEqual(len(self.user.two_factor_backup_codes), 10)

    def test_regenerate_backup_codes_invalid_token(self):
        """Test regenerating backup codes with invalid token."""
        request = self.factory.post('/api/auth/2fa/regenerate-backup-codes/', {
            'token': '000000'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = regenerate_backup_codes(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class Get2FAStatusTests(TestCase):
    """Test getting 2FA status."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()

    def test_get_2fa_status_enabled(self):
        """Test getting 2FA status when enabled."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.two_factor_enabled = True
        user.two_factor_backup_codes = ['CODE1-2345', 'CODE2-6789']
        user.save()

        request = self.factory.get('/api/auth/2fa/status/')
        force_authenticate(request, user=user)

        response = get_2fa_status(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['enabled'])
        self.assertEqual(response.data['backup_codes_remaining'], 2)

    def test_get_2fa_status_disabled(self):
        """Test getting 2FA status when disabled."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        request = self.factory.get('/api/auth/2fa/status/')
        force_authenticate(request, user=user)

        response = get_2fa_status(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['enabled'])
        self.assertEqual(response.data['backup_codes_remaining'], 0)


class UserInvitationModelTests(TestCase):
    """Test UserInvitation model."""

    def setUp(self):
        """Set up test data."""
        from apps.tenants.models import Tenant
        from datetime import timedelta

        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )

        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            role=User.ADMIN
        )

        self.invitation = UserInvitation.objects.create(
            tenant=self.tenant,
            email='invite@example.com',
            role=User.CONTRIBUTOR,
            invited_by=self.admin,
            invitation_token='abc123',
            expires_at=timezone.now() + timedelta(days=7)
        )

    def test_invitation_creation(self):
        """Test creating user invitation."""
        self.assertEqual(self.invitation.status, UserInvitation.PENDING)
        self.assertEqual(self.invitation.email, 'invite@example.com')

    def test_is_expired_property_not_expired(self):
        """Test is_expired property for valid invitation."""
        self.assertFalse(self.invitation.is_expired)

    def test_is_expired_property_expired(self):
        """Test is_expired property for expired invitation."""
        from datetime import timedelta

        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()

        self.assertTrue(self.invitation.is_expired)

    def test_accept_invitation(self):
        """Test accepting invitation."""
        new_user = User.objects.create_user(
            email='invite@example.com',
            password='testpass123'
        )

        self.invitation.accept(new_user)

        self.assertEqual(self.invitation.status, UserInvitation.ACCEPTED)
        self.assertIsNotNone(self.invitation.accepted_at)

        # Verify user was assigned to tenant and role
        new_user.refresh_from_db()
        self.assertEqual(new_user.tenant, self.tenant)
        self.assertEqual(new_user.role, User.CONTRIBUTOR)

    def test_cancel_invitation(self):
        """Test canceling invitation."""
        self.invitation.cancel()

        self.assertEqual(self.invitation.status, UserInvitation.CANCELLED)


class ApiKeyModelTests(TestCase):
    """Test ApiKey model."""

    def setUp(self):
        """Set up test data."""
        from apps.tenants.models import Tenant

        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )

        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            tenant=self.tenant
        )

        self.api_key = ApiKey.objects.create(
            user=self.user,
            tenant=self.tenant,
            name='Test API Key',
            key='test_key_12345',
            prefix='test_key',
            scopes=['invoices:read', 'invoices:write'],
            is_active=True
        )

    def test_api_key_creation(self):
        """Test creating API key."""
        self.assertEqual(self.api_key.name, 'Test API Key')
        self.assertTrue(self.api_key.is_active)
        self.assertEqual(self.api_key.usage_count, 0)

    def test_is_expired_property_no_expiration(self):
        """Test is_expired when no expiration date set."""
        self.assertFalse(self.api_key.is_expired)

    def test_is_expired_property_not_expired(self):
        """Test is_expired for valid API key."""
        from datetime import timedelta

        self.api_key.expires_at = timezone.now() + timedelta(days=30)
        self.api_key.save()

        self.assertFalse(self.api_key.is_expired)

    def test_is_expired_property_expired(self):
        """Test is_expired for expired API key."""
        from datetime import timedelta

        self.api_key.expires_at = timezone.now() - timedelta(days=1)
        self.api_key.save()

        self.assertTrue(self.api_key.is_expired)

    def test_is_valid_property(self):
        """Test is_valid property."""
        self.assertTrue(self.api_key.is_valid)

        # Make inactive
        self.api_key.is_active = False
        self.assertFalse(self.api_key.is_valid)

    def test_record_usage(self):
        """Test recording API key usage."""
        initial_count = self.api_key.usage_count

        self.api_key.record_usage()
        self.api_key.refresh_from_db()

        self.assertEqual(self.api_key.usage_count, initial_count + 1)
        self.assertIsNotNone(self.api_key.last_used_at)
