"""
Input Validators for Aureon SaaS Platform
==========================================

Comprehensive validation utilities:
1. Regex validators for all input types (email, phone, UUID, URL)
2. File upload validators (size, type, virus scan hook)
3. Sanitization functions

Author: Rhematek Solutions
Version: 2.0.0
"""

import re
import os
import magic
import hashlib
import logging
from typing import Optional, List, Set, Tuple
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import (
    RegexValidator,
    EmailValidator,
    URLValidator as DjangoURLValidator,
)
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# Configure logger
logger = logging.getLogger('security.validation')


# =============================================================================
# REGEX VALIDATORS
# =============================================================================

class StrictEmailValidator(EmailValidator):
    """
    Enhanced email validator with additional security checks.

    Prevents:
    - Disposable email addresses
    - Email addresses with suspicious patterns
    - Excessively long local parts
    """

    # Disposable email domains (partial list - extend as needed)
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'throwaway.email', '10minutemail.com', 'guerrillamail.com',
        'mailinator.com', 'yopmail.com', 'trashmail.com', 'fakeinbox.com',
        'temp-mail.org', 'tempail.com', 'maildrop.cc', 'dispostable.com',
        'getnada.com', 'mohmal.com', 'sharklasers.com', 'guerrillamail.info',
    }

    # Maximum length for local part
    MAX_LOCAL_PART_LENGTH = 64

    def __init__(self, allow_disposable: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.allow_disposable = allow_disposable

    def __call__(self, value: str) -> None:
        # Run parent validation first
        super().__call__(value)

        # Additional checks
        value = value.lower().strip()

        # Check local part length
        local_part = value.split('@')[0]
        if len(local_part) > self.MAX_LOCAL_PART_LENGTH:
            raise ValidationError(
                _('Email local part is too long.'),
                code='email_local_too_long'
            )

        # Check for disposable domains
        if not self.allow_disposable:
            domain = value.split('@')[1]
            if domain in self.DISPOSABLE_DOMAINS:
                raise ValidationError(
                    _('Please use a permanent email address.'),
                    code='disposable_email'
                )

        # Check for suspicious patterns
        suspicious_patterns = [
            r'^test[0-9]*@',
            r'^fake[0-9]*@',
            r'^spam[0-9]*@',
            r'^[0-9]{10,}@',  # Long number sequences
        ]

        for pattern in suspicious_patterns:
            if re.match(pattern, value):
                raise ValidationError(
                    _('Please provide a valid email address.'),
                    code='suspicious_email'
                )


class PhoneNumberValidator(RegexValidator):
    """
    International phone number validator.

    Supports:
    - E.164 format (+1234567890)
    - National formats with various separators
    - Extension numbers
    """

    # E.164 and common formats
    regex = r'^(\+?[1-9]\d{0,2})?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}(\s*(ext|x|extension)\s*\d{1,5})?$'
    message = _('Enter a valid phone number.')
    code = 'invalid_phone'

    def __call__(self, value: str) -> None:
        # Remove all whitespace for validation
        cleaned = re.sub(r'\s+', '', value)

        # Check length (E.164 max is 15 digits)
        digits_only = re.sub(r'\D', '', cleaned)
        if len(digits_only) > 15:
            raise ValidationError(
                _('Phone number is too long.'),
                code='phone_too_long'
            )

        if len(digits_only) < 7:
            raise ValidationError(
                _('Phone number is too short.'),
                code='phone_too_short'
            )

        super().__call__(value)


class UUIDValidator(RegexValidator):
    """
    UUID validator supporting versions 1-5.
    """

    regex = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    message = _('Enter a valid UUID.')
    code = 'invalid_uuid'
    flags = re.IGNORECASE


class SafeURLValidator(DjangoURLValidator):
    """
    Enhanced URL validator with security checks.

    Prevents:
    - Local/private IP addresses
    - Dangerous protocols
    - URL injection patterns
    """

    # Blocked URL patterns
    BLOCKED_PATTERNS = [
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'file:',
        r'about:',
    ]

    # Private IP ranges
    PRIVATE_IP_PATTERNS = [
        r'^127\.',
        r'^10\.',
        r'^172\.(1[6-9]|2[0-9]|3[01])\.',
        r'^192\.168\.',
        r'^169\.254\.',
        r'^::1$',
        r'^fc00:',
        r'^fe80:',
        r'^localhost$',
    ]

    def __init__(self, allow_private: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.allow_private = allow_private

    def __call__(self, value: str) -> None:
        # Check for blocked patterns
        value_lower = value.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if re.match(pattern, value_lower):
                raise ValidationError(
                    _('This URL scheme is not allowed.'),
                    code='blocked_scheme'
                )

        # Run parent validation
        super().__call__(value)

        # Check for private IPs
        if not self.allow_private:
            parsed = urlparse(value)
            host = parsed.hostname or ''

            for pattern in self.PRIVATE_IP_PATTERNS:
                if re.match(pattern, host, re.IGNORECASE):
                    raise ValidationError(
                        _('Private or local URLs are not allowed.'),
                        code='private_url'
                    )


class UsernameValidator(RegexValidator):
    """
    Username validator with security constraints.
    """

    regex = r'^[a-zA-Z][a-zA-Z0-9_]{2,29}$'
    message = _(
        'Username must start with a letter, contain only letters, '
        'numbers, and underscores, and be 3-30 characters long.'
    )
    code = 'invalid_username'

    # Reserved usernames
    RESERVED = {
        'admin', 'administrator', 'root', 'system', 'user', 'test',
        'support', 'help', 'info', 'contact', 'sales', 'billing',
        'api', 'www', 'mail', 'email', 'ftp', 'ssh', 'login',
    }

    def __call__(self, value: str) -> None:
        super().__call__(value)

        # Check reserved names
        if value.lower() in self.RESERVED:
            raise ValidationError(
                _('This username is reserved.'),
                code='reserved_username'
            )


class PasswordStrengthValidator:
    """
    Password strength validator with comprehensive rules.
    """

    def __init__(
        self,
        min_length: int = 12,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
    ):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special

    def validate(self, password: str, user=None) -> None:
        errors = []

        if len(password) < self.min_length:
            errors.append(
                ValidationError(
                    _('Password must be at least %(min_length)d characters.'),
                    code='password_too_short',
                    params={'min_length': self.min_length}
                )
            )

        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append(
                ValidationError(
                    _('Password must contain at least one uppercase letter.'),
                    code='password_no_upper'
                )
            )

        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append(
                ValidationError(
                    _('Password must contain at least one lowercase letter.'),
                    code='password_no_lower'
                )
            )

        if self.require_digit and not re.search(r'\d', password):
            errors.append(
                ValidationError(
                    _('Password must contain at least one digit.'),
                    code='password_no_digit'
                )
            )

        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(
                ValidationError(
                    _('Password must contain at least one special character.'),
                    code='password_no_special'
                )
            )

        # Check for common patterns
        common_patterns = [
            r'(.)\1{2,}',  # Repeated characters
            r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
            r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
        ]

        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                errors.append(
                    ValidationError(
                        _('Password contains predictable patterns.'),
                        code='password_pattern'
                    )
                )
                break

        if errors:
            raise ValidationError(errors)

    def get_help_text(self) -> str:
        requirements = [f'at least {self.min_length} characters']
        if self.require_uppercase:
            requirements.append('one uppercase letter')
        if self.require_lowercase:
            requirements.append('one lowercase letter')
        if self.require_digit:
            requirements.append('one digit')
        if self.require_special:
            requirements.append('one special character')

        return _('Your password must contain: ') + ', '.join(requirements) + '.'


# =============================================================================
# FILE UPLOAD VALIDATORS
# =============================================================================

class FileUploadValidator:
    """
    Comprehensive file upload validator.

    Validates:
    - File size
    - File extension
    - MIME type (magic number verification)
    - Filename security
    - Virus scanning hook
    """

    # Default allowed extensions by category
    ALLOWED_EXTENSIONS = {
        'image': {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'},
        'document': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'odt', 'ods'},
        'archive': {'zip', 'tar', 'gz', '7z'},
    }

    # MIME type mapping
    MIME_TYPES = {
        'jpg': ['image/jpeg'],
        'jpeg': ['image/jpeg'],
        'png': ['image/png'],
        'gif': ['image/gif'],
        'webp': ['image/webp'],
        'svg': ['image/svg+xml'],
        'pdf': ['application/pdf'],
        'doc': ['application/msword'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'xls': ['application/vnd.ms-excel'],
        'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'ppt': ['application/vnd.ms-powerpoint'],
        'pptx': ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
        'txt': ['text/plain'],
        'rtf': ['application/rtf', 'text/rtf'],
        'odt': ['application/vnd.oasis.opendocument.text'],
        'ods': ['application/vnd.oasis.opendocument.spreadsheet'],
        'zip': ['application/zip', 'application/x-zip-compressed'],
        'tar': ['application/x-tar'],
        'gz': ['application/gzip', 'application/x-gzip'],
        '7z': ['application/x-7z-compressed'],
    }

    # Dangerous file patterns
    DANGEROUS_PATTERNS = [
        r'\.php[0-9]?$',
        r'\.phtml$',
        r'\.exe$',
        r'\.bat$',
        r'\.cmd$',
        r'\.sh$',
        r'\.ps1$',
        r'\.vbs$',
        r'\.js$',
        r'\.jar$',
        r'\.msi$',
        r'\.dll$',
        r'\.scr$',
        r'\.hta$',
        r'\.cpl$',
    ]

    def __init__(
        self,
        max_size: Optional[int] = None,
        allowed_extensions: Optional[Set[str]] = None,
        allowed_categories: Optional[List[str]] = None,
        check_mime: bool = True,
        virus_scan: bool = False,
    ):
        # Default to settings or 10MB
        self.max_size = max_size or getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)

        # Build allowed extensions set
        self.allowed_extensions = set()
        if allowed_extensions:
            self.allowed_extensions = {ext.lower().lstrip('.') for ext in allowed_extensions}
        elif allowed_categories:
            for category in allowed_categories:
                self.allowed_extensions.update(self.ALLOWED_EXTENSIONS.get(category, set()))
        else:
            # Default: allow images and documents
            for category in ['image', 'document']:
                self.allowed_extensions.update(self.ALLOWED_EXTENSIONS.get(category, set()))

        self.check_mime = check_mime
        self.virus_scan = virus_scan

    def __call__(self, file) -> None:
        """Validate uploaded file."""
        self.validate_size(file)
        self.validate_filename(file.name)
        self.validate_extension(file.name)

        if self.check_mime:
            self.validate_mime_type(file)

        if self.virus_scan:
            self.scan_for_viruses(file)

    def validate_size(self, file) -> None:
        """Validate file size."""
        if file.size > self.max_size:
            raise ValidationError(
                _('File size must be under %(max_size)s MB.'),
                code='file_too_large',
                params={'max_size': self.max_size // (1024 * 1024)}
            )

    def validate_filename(self, filename: str) -> None:
        """Validate filename for security issues."""
        # Check for null bytes
        if '\x00' in filename:
            raise ValidationError(
                _('Invalid filename.'),
                code='invalid_filename'
            )

        # Check for path traversal
        if '..' in filename or filename.startswith('/'):
            raise ValidationError(
                _('Invalid filename.'),
                code='path_traversal'
            )

        # Check for dangerous patterns
        filename_lower = filename.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, filename_lower):
                raise ValidationError(
                    _('This file type is not allowed.'),
                    code='dangerous_file'
                )

    def validate_extension(self, filename: str) -> None:
        """Validate file extension."""
        ext = os.path.splitext(filename)[1].lower().lstrip('.')

        if not ext:
            raise ValidationError(
                _('File must have an extension.'),
                code='no_extension'
            )

        if ext not in self.allowed_extensions:
            raise ValidationError(
                _('File type .%(extension)s is not allowed.'),
                code='invalid_extension',
                params={'extension': ext}
            )

    def validate_mime_type(self, file) -> None:
        """Validate MIME type using magic numbers."""
        ext = os.path.splitext(file.name)[1].lower().lstrip('.')

        # Read file header
        file.seek(0)
        header = file.read(2048)
        file.seek(0)

        try:
            detected_mime = magic.from_buffer(header, mime=True)
        except Exception:
            # If magic fails, allow but log
            logger.warning(f"Could not detect MIME type for {file.name}")
            return

        # Check against expected MIME types
        expected_mimes = self.MIME_TYPES.get(ext, [])

        if expected_mimes and detected_mime not in expected_mimes:
            # Special handling for some edge cases
            if not self._is_mime_compatible(detected_mime, expected_mimes):
                raise ValidationError(
                    _('File content does not match extension.'),
                    code='mime_mismatch'
                )

    def _is_mime_compatible(self, detected: str, expected: List[str]) -> bool:
        """Check if detected MIME is compatible with expected."""
        # Handle text files with various encodings
        if 'text/plain' in expected and detected.startswith('text/'):
            return True

        # Handle application/octet-stream as generic
        if detected == 'application/octet-stream':
            return True

        return False

    def scan_for_viruses(self, file) -> None:
        """
        Virus scanning hook.

        This is a placeholder for virus scanning integration.
        Implement with ClamAV or cloud-based scanning service.
        """
        virus_scanner = getattr(settings, 'VIRUS_SCANNER', None)

        if virus_scanner:
            try:
                # Hook for external virus scanning
                result = virus_scanner.scan(file)
                if not result['clean']:
                    logger.error(f"Virus detected in upload: {file.name}")
                    raise ValidationError(
                        _('File failed security scan.'),
                        code='virus_detected'
                    )
            except Exception as e:
                logger.error(f"Virus scan error: {e}")
                # Depending on policy, either block or allow
                if getattr(settings, 'BLOCK_ON_SCAN_ERROR', True):
                    raise ValidationError(
                        _('File could not be verified.'),
                        code='scan_error'
                    )


class ImageUploadValidator(FileUploadValidator):
    """
    Specialized validator for image uploads.
    """

    def __init__(self, max_size: Optional[int] = None, **kwargs):
        super().__init__(
            max_size=max_size or 5 * 1024 * 1024,  # 5MB default for images
            allowed_categories=['image'],
            **kwargs
        )

    def __call__(self, file) -> None:
        super().__call__(file)
        self.validate_image_dimensions(file)

    def validate_image_dimensions(self, file) -> None:
        """Validate image dimensions."""
        try:
            from PIL import Image

            file.seek(0)
            img = Image.open(file)

            max_dimension = getattr(settings, 'MAX_IMAGE_DIMENSION', 4096)

            if img.width > max_dimension or img.height > max_dimension:
                raise ValidationError(
                    _('Image dimensions must not exceed %(max)d pixels.'),
                    code='image_too_large',
                    params={'max': max_dimension}
                )

            file.seek(0)
        except ImportError:
            logger.warning("PIL not installed, skipping dimension check")
        except Exception as e:
            logger.warning(f"Could not validate image dimensions: {e}")


class DocumentUploadValidator(FileUploadValidator):
    """
    Specialized validator for document uploads.
    """

    def __init__(self, max_size: Optional[int] = None, **kwargs):
        super().__init__(
            max_size=max_size or 25 * 1024 * 1024,  # 25MB default for documents
            allowed_categories=['document'],
            **kwargs
        )


# =============================================================================
# SANITIZATION FUNCTIONS
# =============================================================================

def sanitize_html(value: str, allowed_tags: Optional[Set[str]] = None) -> str:
    """
    Sanitize HTML content, allowing only safe tags.

    Args:
        value: HTML string to sanitize
        allowed_tags: Set of allowed HTML tags (default: basic formatting)

    Returns:
        Sanitized HTML string
    """
    import bleach

    if allowed_tags is None:
        allowed_tags = {'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li'}

    allowed_attrs = {
        'a': ['href', 'title'],
    }

    # Strip dangerous content
    cleaned = bleach.clean(
        value,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True,
        strip_comments=True,
    )

    # Additional link sanitization
    cleaned = bleach.linkify(cleaned, parse_email=False)

    return cleaned


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    # Get extension
    name, ext = os.path.splitext(filename)

    # Remove/replace dangerous characters
    safe_name = re.sub(r'[^\w\s\-.]', '', name)
    safe_name = re.sub(r'\s+', '_', safe_name)
    safe_name = safe_name.strip('._')

    # Limit length
    if len(safe_name) > 100:
        safe_name = safe_name[:100]

    # Ensure we have a name (using md5 for non-security filename generation)
    if not safe_name:
        safe_name = hashlib.md5(filename.encode(), usedforsecurity=False).hexdigest()[:12]

    return f"{safe_name}{ext.lower()}"


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Basic string sanitization.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    import html

    # Limit length
    value = value[:max_length]

    # HTML encode
    value = html.escape(value)

    # Remove null bytes
    value = value.replace('\x00', '')

    # Normalize whitespace
    value = ' '.join(value.split())

    return value


def sanitize_sql_like(value: str) -> str:
    """
    Escape special characters for SQL LIKE queries.

    Args:
        value: Search value

    Returns:
        Escaped value safe for LIKE queries
    """
    # Escape SQL LIKE special characters
    value = value.replace('\\', '\\\\')
    value = value.replace('%', '\\%')
    value = value.replace('_', '\\_')
    value = value.replace('[', '\\[')

    return value


def validate_json_schema(data: dict, schema: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate JSON data against a schema.

    Args:
        data: JSON data to validate
        schema: JSON schema

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import jsonschema

        jsonschema.validate(data, schema)
        return True, None
    except jsonschema.ValidationError as e:
        return False, str(e.message)
    except Exception as e:
        return False, str(e)


# =============================================================================
# CONVENIENCE VALIDATORS
# =============================================================================

# Pre-configured validators for common use cases
email_validator = StrictEmailValidator()
phone_validator = PhoneNumberValidator()
uuid_validator = UUIDValidator()
url_validator = SafeURLValidator()
username_validator = UsernameValidator()
password_validator = PasswordStrengthValidator()
file_validator = FileUploadValidator()
image_validator = ImageUploadValidator()
document_validator = DocumentUploadValidator()


def validate_email(value: str) -> str:
    """Validate and return cleaned email."""
    email_validator(value)
    return value.lower().strip()


def validate_phone(value: str) -> str:
    """Validate and return cleaned phone number."""
    phone_validator(value)
    return value.strip()


def validate_uuid(value: str) -> str:
    """Validate UUID string."""
    uuid_validator(value)
    return value.lower()


def validate_url(value: str) -> str:
    """Validate and return URL."""
    url_validator(value)
    return value


def validate_username(value: str) -> str:
    """Validate username."""
    username_validator(value)
    return value
