"""
Tests for accounts two_factor module.

Covers:
- TwoFactorAuthService.generate_secret
- TwoFactorAuthService.generate_qr_code
- TwoFactorAuthService.verify_token (valid, invalid, expired)
- TwoFactorAuthService.generate_backup_codes (format, uniqueness, count)
- enable_2fa view (success, already enabled)
- verify_2fa_setup (success, missing token, invalid token, no secret)
- disable_2fa (with token, with backup code, not enabled, invalid)
- verify_2fa_token (valid, invalid, not enabled)
- use_backup_code (valid, invalid, not enabled, last code)
- regenerate_backup_codes (success, invalid token, not enabled)
- get_2fa_status (enabled, disabled)
"""

import re
import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.two_factor import TwoFactorAuthService

User = get_user_model()

AUTH_URL_PREFIX = "/api/auth/"


# ============================================================================
# TwoFactorAuthService Unit Tests
# ============================================================================


class TestTwoFactorAuthServiceGenerateSecret:
    """Tests for TwoFactorAuthService.generate_secret."""

    def test_generate_secret_returns_string(self):
        """generate_secret returns a string."""
        secret = TwoFactorAuthService.generate_secret()
        assert isinstance(secret, str)

    def test_generate_secret_not_empty(self):
        """generate_secret returns a non-empty string."""
        secret = TwoFactorAuthService.generate_secret()
        assert len(secret) > 0

    def test_generate_secret_is_base32(self):
        """generate_secret returns a valid base32-encoded string."""
        secret = TwoFactorAuthService.generate_secret()
        # Base32 characters: A-Z and 2-7
        assert re.match(r'^[A-Z2-7]+=*$', secret), f"Not valid base32: {secret}"

    def test_generate_secret_unique(self):
        """generate_secret produces unique secrets across calls."""
        secrets_set = {TwoFactorAuthService.generate_secret() for _ in range(50)}
        assert len(secrets_set) == 50

    @patch('apps.accounts.two_factor.pyotp.random_base32')
    def test_generate_secret_calls_pyotp(self, mock_random_base32):
        """generate_secret delegates to pyotp.random_base32."""
        mock_random_base32.return_value = 'JBSWY3DPEHPK3PXP'
        secret = TwoFactorAuthService.generate_secret()
        mock_random_base32.assert_called_once()
        assert secret == 'JBSWY3DPEHPK3PXP'


class TestTwoFactorAuthServiceGenerateQrCode:
    """Tests for TwoFactorAuthService.generate_qr_code."""

    @pytest.mark.django_db
    def test_generate_qr_code_returns_data_uri(self, admin_user):
        """generate_qr_code returns a data URI with base64 PNG content."""
        secret = 'JBSWY3DPEHPK3PXP'
        qr_code = TwoFactorAuthService.generate_qr_code(admin_user, secret)

        assert qr_code.startswith("data:image/png;base64,")

    @pytest.mark.django_db
    def test_generate_qr_code_contains_base64_data(self, admin_user):
        """generate_qr_code returns valid base64-encoded data after the prefix."""
        import base64

        secret = 'JBSWY3DPEHPK3PXP'
        qr_code = TwoFactorAuthService.generate_qr_code(admin_user, secret)

        # Extract and decode the base64 portion
        base64_data = qr_code.split(",")[1]
        decoded = base64.b64decode(base64_data)
        # PNG magic bytes
        assert decoded[:4] == b'\x89PNG'

    @pytest.mark.django_db
    @patch('apps.accounts.two_factor.pyotp.TOTP')
    def test_generate_qr_code_uses_correct_issuer(self, mock_totp_cls, admin_user):
        """generate_qr_code creates provisioning URI with correct issuer name."""
        mock_totp_instance = MagicMock()
        mock_totp_instance.provisioning_uri.return_value = (
            'otpauth://totp/Aureon%20Platform:admin@testorg.com?secret=JBSWY3DPEHPK3PXP&issuer=Aureon+Platform'
        )
        mock_totp_cls.return_value = mock_totp_instance

        secret = 'JBSWY3DPEHPK3PXP'
        TwoFactorAuthService.generate_qr_code(admin_user, secret)

        mock_totp_instance.provisioning_uri.assert_called_once_with(
            name=admin_user.email,
            issuer_name='Aureon Platform'
        )


class TestTwoFactorAuthServiceVerifyToken:
    """Tests for TwoFactorAuthService.verify_token."""

    @patch('apps.accounts.two_factor.pyotp.TOTP')
    def test_verify_token_valid(self, mock_totp_cls):
        """verify_token returns True for a valid token."""
        mock_totp_instance = MagicMock()
        mock_totp_instance.verify.return_value = True
        mock_totp_cls.return_value = mock_totp_instance

        result = TwoFactorAuthService.verify_token('JBSWY3DPEHPK3PXP', '123456')

        assert result is True
        mock_totp_instance.verify.assert_called_once_with('123456', valid_window=1)

    @patch('apps.accounts.two_factor.pyotp.TOTP')
    def test_verify_token_invalid(self, mock_totp_cls):
        """verify_token returns False for an invalid token."""
        mock_totp_instance = MagicMock()
        mock_totp_instance.verify.return_value = False
        mock_totp_cls.return_value = mock_totp_instance

        result = TwoFactorAuthService.verify_token('JBSWY3DPEHPK3PXP', '000000')

        assert result is False

    @patch('apps.accounts.two_factor.pyotp.TOTP')
    def test_verify_token_uses_valid_window(self, mock_totp_cls):
        """verify_token allows 1 time step tolerance."""
        mock_totp_instance = MagicMock()
        mock_totp_instance.verify.return_value = True
        mock_totp_cls.return_value = mock_totp_instance

        TwoFactorAuthService.verify_token('SECRET', '123456')

        mock_totp_instance.verify.assert_called_with('123456', valid_window=1)


class TestTwoFactorAuthServiceGenerateBackupCodes:
    """Tests for TwoFactorAuthService.generate_backup_codes."""

    def test_generate_backup_codes_default_count(self):
        """generate_backup_codes returns 10 codes by default."""
        codes = TwoFactorAuthService.generate_backup_codes()
        assert len(codes) == 10

    def test_generate_backup_codes_custom_count(self):
        """generate_backup_codes returns the specified number of codes."""
        codes = TwoFactorAuthService.generate_backup_codes(count=5)
        assert len(codes) == 5

        codes = TwoFactorAuthService.generate_backup_codes(count=20)
        assert len(codes) == 20

    def test_generate_backup_codes_format(self):
        """Each backup code has the XXXX-XXXX format."""
        codes = TwoFactorAuthService.generate_backup_codes()
        pattern = re.compile(r'^[A-Z2-9]{4}-[A-Z2-9]{4}$')

        for code in codes:
            assert pattern.match(code), f"Code '{code}' does not match XXXX-XXXX format"

    def test_generate_backup_codes_uniqueness(self):
        """All generated backup codes are unique."""
        codes = TwoFactorAuthService.generate_backup_codes(count=100)
        assert len(set(codes)) == len(codes)

    def test_generate_backup_codes_character_set(self):
        """Backup codes only use uppercase letters (excluding I, O) and digits 2-9."""
        allowed_chars = set('ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
        codes = TwoFactorAuthService.generate_backup_codes(count=50)

        for code in codes:
            # Remove the dash
            raw = code.replace('-', '')
            for char in raw:
                assert char in allowed_chars, f"Unexpected character '{char}' in code '{code}'"

    def test_generate_backup_codes_no_ambiguous_characters(self):
        """Backup codes do not contain ambiguous characters (I, O, 0, 1)."""
        codes = TwoFactorAuthService.generate_backup_codes(count=100)
        ambiguous = set('IO01')

        for code in codes:
            raw = code.replace('-', '')
            for char in raw:
                assert char not in ambiguous, (
                    f"Ambiguous character '{char}' found in code '{code}'"
                )

    def test_generate_backup_codes_zero_count(self):
        """generate_backup_codes with count=0 returns empty list."""
        codes = TwoFactorAuthService.generate_backup_codes(count=0)
        assert codes == []


# ============================================================================
# enable_2fa View Tests
# ============================================================================


class TestEnable2FA:
    """Tests for the enable_2fa view."""

    ENABLE_URL = f"{AUTH_URL_PREFIX}2fa/enable/"

    @pytest.mark.django_db
    @patch('apps.accounts.two_factor.TwoFactorAuthService.generate_qr_code')
    @patch('apps.accounts.two_factor.TwoFactorAuthService.generate_secret')
    def test_enable_2fa_success(
        self, mock_generate_secret, mock_generate_qr_code,
        authenticated_admin_client, admin_user
    ):
        """Enabling 2FA returns secret and QR code."""
        mock_generate_secret.return_value = 'TESTSECRET123456'
        mock_generate_qr_code.return_value = 'data:image/png;base64,abc123'

        response = authenticated_admin_client.post(self.ENABLE_URL, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["secret"] == 'TESTSECRET123456'
        assert response.data["qr_code"] == 'data:image/png;base64,abc123'
        assert "message" in response.data

        # Verify secret was saved to user
        admin_user.refresh_from_db()
        assert admin_user.two_factor_secret == 'TESTSECRET123456'

    @pytest.mark.django_db
    def test_enable_2fa_already_enabled(self, authenticated_admin_client, admin_user):
        """Enabling 2FA when already enabled returns 400."""
        admin_user.two_factor_enabled = True
        admin_user.two_factor_secret = 'EXISTINGSECRET'
        admin_user.save()

        response = authenticated_admin_client.post(self.ENABLE_URL, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already enabled" in response.data["error"]

    @pytest.mark.django_db
    def test_enable_2fa_unauthenticated(self, api_client):
        """Unauthenticated users cannot enable 2FA."""
        response = api_client.post(self.ENABLE_URL, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# verify_2fa_setup View Tests
# ============================================================================


class TestVerify2FASetup:
    """Tests for the verify_2fa_setup view."""

    VERIFY_SETUP_URL = f"{AUTH_URL_PREFIX}2fa/verify-setup/"

    @pytest.mark.django_db
    @patch('apps.accounts.two_factor.TwoFactorAuthService.verify_token')
    @patch('apps.accounts.two_factor.TwoFactorAuthService.generate_backup_codes')
    def test_verify_2fa_setup_success(
        self, mock_generate_backup, mock_verify_token,
        authenticated_admin_client, admin_user
    ):
        """Successful 2FA verification enables 2FA and returns backup codes."""
        admin_user.two_factor_secret = 'TESTSECRET123456'
        admin_user.save()

        mock_verify_token.return_value = True
        mock_generate_backup.return_value = [
            'ABCD-EFGH', 'IJKL-MNOP', 'QRST-UVWX',
        ]

        response = authenticated_admin_client.post(
            self.VERIFY_SETUP_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "backup_codes" in response.data
        assert len(response.data["backup_codes"]) == 3
        assert "warning" in response.data

        # Verify 2FA is now enabled
        admin_user.refresh_from_db()
        assert admin_user.two_factor_enabled is True
        assert admin_user.two_factor_backup_codes == ['ABCD-EFGH', 'IJKL-MNOP', 'QRST-UVWX']

    @pytest.mark.django_db
    def test_verify_2fa_setup_missing_token(self, authenticated_admin_client, admin_user):
        """verify_2fa_setup fails when token is missing."""
        admin_user.two_factor_secret = 'TESTSECRET123456'
        admin_user.save()

        response = authenticated_admin_client.post(
            self.VERIFY_SETUP_URL, {}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Token is required" in response.data["error"]

    @pytest.mark.django_db
    @patch('apps.accounts.two_factor.TwoFactorAuthService.verify_token')
    def test_verify_2fa_setup_invalid_token(
        self, mock_verify_token, authenticated_admin_client, admin_user
    ):
        """verify_2fa_setup fails when token is invalid."""
        admin_user.two_factor_secret = 'TESTSECRET123456'
        admin_user.save()

        mock_verify_token.return_value = False

        response = authenticated_admin_client.post(
            self.VERIFY_SETUP_URL, {"token": "000000"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid token" in response.data["error"]

        # 2FA should not be enabled
        admin_user.refresh_from_db()
        assert admin_user.two_factor_enabled is False

    @pytest.mark.django_db
    def test_verify_2fa_setup_no_secret(self, authenticated_admin_client, admin_user):
        """verify_2fa_setup fails when no secret has been generated (enable not called)."""
        # Ensure no secret is set
        admin_user.two_factor_secret = ''
        admin_user.save()

        response = authenticated_admin_client.post(
            self.VERIFY_SETUP_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not initiated" in response.data["error"]

    @pytest.mark.django_db
    def test_verify_2fa_setup_unauthenticated(self, api_client):
        """Unauthenticated users cannot verify 2FA setup."""
        response = api_client.post(
            self.VERIFY_SETUP_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# disable_2fa View Tests
# ============================================================================


class TestDisable2FA:
    """Tests for the disable_2fa view."""

    DISABLE_URL = f"{AUTH_URL_PREFIX}2fa/disable/"

    def _setup_2fa_user(self, user, secret='TESTSECRET123456', backup_codes=None):
        """Helper to set up a user with 2FA enabled."""
        user.two_factor_enabled = True
        user.two_factor_secret = secret
        user.two_factor_backup_codes = backup_codes or ['ABCD-EFGH', 'IJKL-MNOP']
        user.save()

    @pytest.mark.django_db
    @patch('apps.accounts.two_factor.TwoFactorAuthService.verify_token')
    def test_disable_2fa_with_token(
        self, mock_verify_token, authenticated_admin_client, admin_user
    ):
        """Disable 2FA with a valid TOTP token."""
        self._setup_2fa_user(admin_user)
        mock_verify_token.return_value = True

        response = authenticated_admin_client.post(
            self.DISABLE_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "disabled" in response.data["message"]

        admin_user.refresh_from_db()
        assert admin_user.two_factor_enabled is False
        assert admin_user.two_factor_secret == ''
        assert admin_user.two_factor_backup_codes == []

    @pytest.mark.django_db
    def test_disable_2fa_with_backup_code(self, authenticated_admin_client, admin_user):
        """Disable 2FA with a valid backup code."""
        self._setup_2fa_user(admin_user, backup_codes=['ABCD-EFGH', 'IJKL-MNOP'])

        response = authenticated_admin_client.post(
            self.DISABLE_URL, {"backup_code": "ABCD-EFGH"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "disabled" in response.data["message"]

        admin_user.refresh_from_db()
        assert admin_user.two_factor_enabled is False

    @pytest.mark.django_db
    def test_disable_2fa_not_enabled(self, authenticated_admin_client, admin_user):
        """Disabling 2FA when not enabled returns 400."""
        admin_user.two_factor_enabled = False
        admin_user.save()

        response = authenticated_admin_client.post(
            self.DISABLE_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not enabled" in response.data["error"]

    @pytest.mark.django_db
    @patch('apps.accounts.two_factor.TwoFactorAuthService.verify_token')
    def test_disable_2fa_invalid_token(
        self, mock_verify_token, authenticated_admin_client, admin_user
    ):
        """Disabling 2FA with an invalid token fails."""
        self._setup_2fa_user(admin_user)
        mock_verify_token.return_value = False

        response = authenticated_admin_client.post(
            self.DISABLE_URL, {"token": "000000"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid token or backup code" in response.data["error"]

        # 2FA should still be enabled
        admin_user.refresh_from_db()
        assert admin_user.two_factor_enabled is True

    @pytest.mark.django_db
    def test_disable_2fa_invalid_backup_code(self, authenticated_admin_client, admin_user):
        """Disabling 2FA with an invalid backup code fails."""
        self._setup_2fa_user(admin_user, backup_codes=['ABCD-EFGH'])

        response = authenticated_admin_client.post(
            self.DISABLE_URL, {"backup_code": "XXXX-YYYY"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid token or backup code" in response.data["error"]

    @pytest.mark.django_db
    def test_disable_2fa_no_token_no_backup(self, authenticated_admin_client, admin_user):
        """Disabling 2FA without token or backup code fails."""
        self._setup_2fa_user(admin_user)

        response = authenticated_admin_client.post(
            self.DISABLE_URL, {}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_disable_2fa_unauthenticated(self, api_client):
        """Unauthenticated users cannot disable 2FA."""
        response = api_client.post(
            self.DISABLE_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# verify_2fa_token View Tests
# ============================================================================


class TestVerify2FAToken:
    """Tests for the verify_2fa_token view."""

    VERIFY_URL = f"{AUTH_URL_PREFIX}2fa/verify/"

    @pytest.mark.django_db
    @patch('apps.accounts.two_factor.TwoFactorAuthService.verify_token')
    def test_verify_2fa_token_valid(
        self, mock_verify_token, authenticated_admin_client, admin_user
    ):
        """Verify a valid 2FA token succeeds."""
        admin_user.two_factor_enabled = True
        admin_user.two_factor_secret = 'TESTSECRET123456'
        admin_user.save()

        mock_verify_token.return_value = True

        response = authenticated_admin_client.post(
            self.VERIFY_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["verified"] is True
        assert "verified successfully" in response.data["message"]

    @pytest.mark.django_db
    @patch('apps.accounts.two_factor.TwoFactorAuthService.verify_token')
    def test_verify_2fa_token_invalid(
        self, mock_verify_token, authenticated_admin_client, admin_user
    ):
        """Verify an invalid 2FA token returns error."""
        admin_user.two_factor_enabled = True
        admin_user.two_factor_secret = 'TESTSECRET123456'
        admin_user.save()

        mock_verify_token.return_value = False

        response = authenticated_admin_client.post(
            self.VERIFY_URL, {"token": "000000"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["verified"] is False
        assert "Invalid token" in response.data["error"]

    @pytest.mark.django_db
    def test_verify_2fa_token_not_enabled(self, authenticated_admin_client, admin_user):
        """Verifying 2FA token when 2FA is not enabled returns error."""
        admin_user.two_factor_enabled = False
        admin_user.save()

        response = authenticated_admin_client.post(
            self.VERIFY_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not enabled" in response.data["error"]

    @pytest.mark.django_db
    def test_verify_2fa_token_missing_token(self, authenticated_admin_client, admin_user):
        """Verifying without providing a token returns error."""
        admin_user.two_factor_enabled = True
        admin_user.two_factor_secret = 'TESTSECRET123456'
        admin_user.save()

        response = authenticated_admin_client.post(
            self.VERIFY_URL, {}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Token is required" in response.data["error"]

    @pytest.mark.django_db
    def test_verify_2fa_token_unauthenticated(self, api_client):
        """Unauthenticated users cannot verify 2FA tokens."""
        response = api_client.post(
            self.VERIFY_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# use_backup_code View Tests
# ============================================================================


class TestUseBackupCode:
    """Tests for the use_backup_code view."""

    BACKUP_URL = f"{AUTH_URL_PREFIX}2fa/backup-code/"

    def _setup_2fa_user(self, user, backup_codes=None):
        """Helper to set up a user with 2FA and backup codes."""
        user.two_factor_enabled = True
        user.two_factor_secret = 'TESTSECRET123456'
        user.two_factor_backup_codes = backup_codes or [
            'ABCD-EFGH', 'IJKL-MNOP', 'QRST-UVWX',
        ]
        user.save()

    @pytest.mark.django_db
    def test_use_backup_code_valid(self, authenticated_admin_client, admin_user):
        """Using a valid backup code succeeds and removes it."""
        self._setup_2fa_user(admin_user, ['ABCD-EFGH', 'IJKL-MNOP', 'QRST-UVWX'])

        response = authenticated_admin_client.post(
            self.BACKUP_URL, {"backup_code": "ABCD-EFGH"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["verified"] is True
        assert response.data["remaining_codes"] == 2

        # Verify code was consumed
        admin_user.refresh_from_db()
        assert 'ABCD-EFGH' not in admin_user.two_factor_backup_codes
        assert len(admin_user.two_factor_backup_codes) == 2

    @pytest.mark.django_db
    def test_use_backup_code_invalid(self, authenticated_admin_client, admin_user):
        """Using an invalid backup code fails."""
        self._setup_2fa_user(admin_user, ['ABCD-EFGH'])

        response = authenticated_admin_client.post(
            self.BACKUP_URL, {"backup_code": "XXXX-YYYY"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["verified"] is False
        assert "Invalid or already used" in response.data["error"]

    @pytest.mark.django_db
    def test_use_backup_code_not_enabled(self, authenticated_admin_client, admin_user):
        """Using backup code when 2FA is not enabled returns error."""
        admin_user.two_factor_enabled = False
        admin_user.save()

        response = authenticated_admin_client.post(
            self.BACKUP_URL, {"backup_code": "ABCD-EFGH"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not enabled" in response.data["error"]

    @pytest.mark.django_db
    def test_use_backup_code_last_code(self, authenticated_admin_client, admin_user):
        """Using the last backup code returns appropriate warning."""
        self._setup_2fa_user(admin_user, ['LAST-CODE'])

        response = authenticated_admin_client.post(
            self.BACKUP_URL, {"backup_code": "LAST-CODE"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["verified"] is True
        assert response.data["remaining_codes"] == 0
        assert "last backup code" in response.data["warning"]

    @pytest.mark.django_db
    def test_use_backup_code_missing_code(self, authenticated_admin_client, admin_user):
        """Using backup code without providing a code returns error."""
        self._setup_2fa_user(admin_user)

        response = authenticated_admin_client.post(
            self.BACKUP_URL, {}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Backup code is required" in response.data["error"]

    @pytest.mark.django_db
    def test_use_backup_code_already_used(self, authenticated_admin_client, admin_user):
        """A backup code cannot be used twice."""
        self._setup_2fa_user(admin_user, ['ABCD-EFGH', 'IJKL-MNOP'])

        # Use code once
        authenticated_admin_client.post(
            self.BACKUP_URL, {"backup_code": "ABCD-EFGH"}, format="json"
        )

        # Try again
        response = authenticated_admin_client.post(
            self.BACKUP_URL, {"backup_code": "ABCD-EFGH"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["verified"] is False

    @pytest.mark.django_db
    def test_use_backup_code_unauthenticated(self, api_client):
        """Unauthenticated users cannot use backup codes."""
        response = api_client.post(
            self.BACKUP_URL, {"backup_code": "ABCD-EFGH"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_use_backup_code_remaining_with_multiple_codes(
        self, authenticated_admin_client, admin_user
    ):
        """Remaining codes warning is appropriate when more than 0 remain."""
        self._setup_2fa_user(admin_user, ['CODE-AAAA', 'CODE-BBBB', 'CODE-CCCC'])

        response = authenticated_admin_client.post(
            self.BACKUP_URL, {"backup_code": "CODE-AAAA"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["remaining_codes"] == 2
        assert "consumed and cannot be used again" in response.data["warning"]


# ============================================================================
# regenerate_backup_codes View Tests
# ============================================================================


class TestRegenerateBackupCodes:
    """Tests for the regenerate_backup_codes view."""

    REGENERATE_URL = f"{AUTH_URL_PREFIX}2fa/regenerate-backup-codes/"

    def _setup_2fa_user(self, user):
        """Helper to set up a user with 2FA enabled."""
        user.two_factor_enabled = True
        user.two_factor_secret = 'TESTSECRET123456'
        user.two_factor_backup_codes = ['OLD1-CODE', 'OLD2-CODE']
        user.save()

    @pytest.mark.django_db
    @patch('apps.accounts.two_factor.TwoFactorAuthService.verify_token')
    @patch('apps.accounts.two_factor.TwoFactorAuthService.generate_backup_codes')
    def test_regenerate_backup_codes_success(
        self, mock_generate, mock_verify,
        authenticated_admin_client, admin_user
    ):
        """Regenerating backup codes with valid token returns new codes."""
        self._setup_2fa_user(admin_user)
        mock_verify.return_value = True
        mock_generate.return_value = ['NEW1-CODE', 'NEW2-CODE', 'NEW3-CODE']

        response = authenticated_admin_client.post(
            self.REGENERATE_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["backup_codes"] == ['NEW1-CODE', 'NEW2-CODE', 'NEW3-CODE']
        assert "warning" in response.data

        admin_user.refresh_from_db()
        assert admin_user.two_factor_backup_codes == ['NEW1-CODE', 'NEW2-CODE', 'NEW3-CODE']

    @pytest.mark.django_db
    @patch('apps.accounts.two_factor.TwoFactorAuthService.verify_token')
    def test_regenerate_backup_codes_invalid_token(
        self, mock_verify, authenticated_admin_client, admin_user
    ):
        """Regenerating backup codes with invalid token fails."""
        self._setup_2fa_user(admin_user)
        mock_verify.return_value = False

        response = authenticated_admin_client.post(
            self.REGENERATE_URL, {"token": "000000"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid token" in response.data["error"]

    @pytest.mark.django_db
    def test_regenerate_backup_codes_not_enabled(
        self, authenticated_admin_client, admin_user
    ):
        """Regenerating backup codes when 2FA is not enabled fails."""
        admin_user.two_factor_enabled = False
        admin_user.save()

        response = authenticated_admin_client.post(
            self.REGENERATE_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not enabled" in response.data["error"]

    @pytest.mark.django_db
    def test_regenerate_backup_codes_missing_token(
        self, authenticated_admin_client, admin_user
    ):
        """Regenerating backup codes without token fails."""
        self._setup_2fa_user(admin_user)

        response = authenticated_admin_client.post(
            self.REGENERATE_URL, {}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Token is required" in response.data["error"]

    @pytest.mark.django_db
    def test_regenerate_backup_codes_unauthenticated(self, api_client):
        """Unauthenticated users cannot regenerate backup codes."""
        response = api_client.post(
            self.REGENERATE_URL, {"token": "123456"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# get_2fa_status View Tests
# ============================================================================


class TestGet2FAStatus:
    """Tests for the get_2fa_status view."""

    STATUS_URL = f"{AUTH_URL_PREFIX}2fa/status/"

    @pytest.mark.django_db
    def test_get_2fa_status_enabled(self, authenticated_admin_client, admin_user):
        """Status returns enabled=True with backup code count when 2FA is enabled."""
        admin_user.two_factor_enabled = True
        admin_user.two_factor_backup_codes = ['CODE-AAAA', 'CODE-BBBB', 'CODE-CCCC']
        admin_user.save()

        response = authenticated_admin_client.get(self.STATUS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["enabled"] is True
        assert response.data["backup_codes_remaining"] == 3
        assert response.data["email"] == admin_user.email

    @pytest.mark.django_db
    def test_get_2fa_status_disabled(self, authenticated_admin_client, admin_user):
        """Status returns enabled=False with 0 backup codes when 2FA is disabled."""
        admin_user.two_factor_enabled = False
        admin_user.save()

        response = authenticated_admin_client.get(self.STATUS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["enabled"] is False
        assert response.data["backup_codes_remaining"] == 0
        assert response.data["email"] == admin_user.email

    @pytest.mark.django_db
    def test_get_2fa_status_unauthenticated(self, api_client):
        """Unauthenticated users cannot check 2FA status."""
        response = api_client.get(self.STATUS_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_get_2fa_status_post_not_allowed(self, authenticated_admin_client):
        """2FA status endpoint only accepts GET."""
        response = authenticated_admin_client.post(self.STATUS_URL, {}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.django_db
    def test_get_2fa_status_no_backup_codes(self, authenticated_admin_client, admin_user):
        """Status with 2FA enabled but no backup codes shows 0 remaining."""
        admin_user.two_factor_enabled = True
        admin_user.two_factor_backup_codes = []
        admin_user.save()

        response = authenticated_admin_client.get(self.STATUS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["enabled"] is True
        assert response.data["backup_codes_remaining"] == 0
