"""
Two-Factor Authentication (2FA) implementation.

Provides TOTP-based 2FA using Google Authenticator-compatible apps.
"""

import logging
import pyotp
import qrcode
import io
import base64
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

User = get_user_model()
logger = logging.getLogger(__name__)


class TwoFactorAuthService:
    """Service for handling 2FA operations."""

    @staticmethod
    def generate_secret():
        """
        Generate a new TOTP secret.

        Returns:
            str: Base32-encoded secret key
        """
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code(user, secret):
        """
        Generate QR code for authenticator app setup.

        Args:
            user: User instance
            secret: TOTP secret key

        Returns:
            str: Base64-encoded QR code image
        """
        # Create provisioning URI for authenticator apps
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name='Aureon Platform'
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def verify_token(secret, token):
        """
        Verify a TOTP token.

        Args:
            secret: TOTP secret key
            token: 6-digit token from authenticator app

        Returns:
            bool: True if token is valid
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Allow 1 time step tolerance

    @staticmethod
    def generate_backup_codes(count=10):
        """
        Generate backup codes for account recovery.

        Args:
            count: Number of backup codes to generate

        Returns:
            list: List of backup codes
        """
        import secrets
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            # Format as XXXX-XXXX for readability
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        return codes


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enable_2fa(request):
    """
    Enable 2FA for the current user.

    POST /api/auth/2fa/enable/

    Returns QR code and secret for setting up authenticator app.
    """
    user = request.user

    if user.two_factor_enabled:
        return Response(
            {'error': '2FA is already enabled for this account.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate new secret
    secret = TwoFactorAuthService.generate_secret()

    # Generate QR code
    qr_code = TwoFactorAuthService.generate_qr_code(user, secret)

    # Store secret temporarily (will be confirmed on verification)
    user.two_factor_secret = secret
    user.save(update_fields=['two_factor_secret'])

    return Response({
        'secret': secret,
        'qr_code': qr_code,
        'message': 'Scan the QR code with your authenticator app, then verify with a token.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_2fa_setup(request):
    """
    Verify and confirm 2FA setup.

    POST /api/auth/2fa/verify-setup/
    Body: {"token": "123456"}

    Confirms the 2FA setup by verifying a token from the authenticator app.
    """
    user = request.user
    token = request.data.get('token')

    if not token:
        return Response(
            {'error': 'Token is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.two_factor_secret:
        return Response(
            {'error': '2FA setup not initiated. Call /enable/ first.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify token
    if not TwoFactorAuthService.verify_token(user.two_factor_secret, token):
        return Response(
            {'error': 'Invalid token. Please try again.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate backup codes
    backup_codes = TwoFactorAuthService.generate_backup_codes()

    # Enable 2FA
    user.two_factor_enabled = True
    user.two_factor_backup_codes = backup_codes
    user.save(update_fields=['two_factor_enabled', 'two_factor_backup_codes'])

    logger.info(f"2FA enabled for user {user.email}")

    return Response({
        'message': '2FA successfully enabled!',
        'backup_codes': backup_codes,
        'warning': 'Save these backup codes in a secure location. They can be used if you lose access to your authenticator app.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_2fa(request):
    """
    Disable 2FA for the current user.

    POST /api/auth/2fa/disable/
    Body: {"token": "123456"} or {"backup_code": "XXXX-XXXX"}

    Requires current token or backup code for security.
    """
    user = request.user
    token = request.data.get('token')
    backup_code = request.data.get('backup_code')

    if not user.two_factor_enabled:
        return Response(
            {'error': '2FA is not enabled for this account.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify token or backup code
    verified = False

    if token:
        verified = TwoFactorAuthService.verify_token(user.two_factor_secret, token)
    elif backup_code:
        if backup_code in user.two_factor_backup_codes:
            verified = True
            # Remove used backup code
            user.two_factor_backup_codes.remove(backup_code)

    if not verified:
        return Response(
            {'error': 'Invalid token or backup code.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Disable 2FA
    user.two_factor_enabled = False
    user.two_factor_secret = ''
    user.two_factor_backup_codes = []
    user.save(update_fields=['two_factor_enabled', 'two_factor_secret', 'two_factor_backup_codes'])

    logger.warning(f"2FA disabled for user {user.email}")

    return Response({
        'message': '2FA successfully disabled.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_2fa_token(request):
    """
    Verify a 2FA token.

    POST /api/auth/2fa/verify/
    Body: {"token": "123456"}

    Used during login flow to verify 2FA token.
    """
    user = request.user
    token = request.data.get('token')

    if not token:
        return Response(
            {'error': 'Token is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.two_factor_enabled:
        return Response(
            {'error': '2FA is not enabled for this account.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify token
    if TwoFactorAuthService.verify_token(user.two_factor_secret, token):
        return Response({
            'verified': True,
            'message': 'Token verified successfully.'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'verified': False,
            'error': 'Invalid token.'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def use_backup_code(request):
    """
    Use a backup code for 2FA.

    POST /api/auth/2fa/backup-code/
    Body: {"backup_code": "XXXX-XXXX"}

    Verifies and consumes a backup code.
    """
    user = request.user
    backup_code = request.data.get('backup_code')

    if not backup_code:
        return Response(
            {'error': 'Backup code is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.two_factor_enabled:
        return Response(
            {'error': '2FA is not enabled for this account.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if backup_code in user.two_factor_backup_codes:
        # Remove used backup code
        user.two_factor_backup_codes.remove(backup_code)
        user.save(update_fields=['two_factor_backup_codes'])

        remaining_codes = len(user.two_factor_backup_codes)

        logger.info(f"Backup code used for user {user.email}. {remaining_codes} codes remaining.")

        return Response({
            'verified': True,
            'message': 'Backup code verified successfully.',
            'remaining_codes': remaining_codes,
            'warning': 'This backup code has been consumed and cannot be used again.' if remaining_codes > 0 else 'This was your last backup code. Please generate new ones.'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'verified': False,
            'error': 'Invalid or already used backup code.'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_backup_codes(request):
    """
    Regenerate backup codes.

    POST /api/auth/2fa/regenerate-backup-codes/
    Body: {"token": "123456"}

    Generates new backup codes (requires current token for security).
    """
    user = request.user
    token = request.data.get('token')

    if not token:
        return Response(
            {'error': 'Token is required for security.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.two_factor_enabled:
        return Response(
            {'error': '2FA is not enabled for this account.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify token
    if not TwoFactorAuthService.verify_token(user.two_factor_secret, token):
        return Response(
            {'error': 'Invalid token.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate new backup codes
    backup_codes = TwoFactorAuthService.generate_backup_codes()
    user.two_factor_backup_codes = backup_codes
    user.save(update_fields=['two_factor_backup_codes'])

    logger.info(f"Backup codes regenerated for user {user.email}")

    return Response({
        'message': 'New backup codes generated successfully!',
        'backup_codes': backup_codes,
        'warning': 'Old backup codes are no longer valid. Save these new codes securely.'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_2fa_status(request):
    """
    Get 2FA status for current user.

    GET /api/auth/2fa/status/

    Returns whether 2FA is enabled and backup code count.
    """
    user = request.user

    return Response({
        'enabled': user.two_factor_enabled,
        'backup_codes_remaining': len(user.two_factor_backup_codes) if user.two_factor_enabled else 0,
        'email': user.email
    }, status=status.HTTP_200_OK)
