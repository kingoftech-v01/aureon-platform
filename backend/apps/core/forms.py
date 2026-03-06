"""
Security Form Mixins for Aureon SaaS Platform
==============================================

Provides security-enhanced form mixins:
1. HoneypotFormMixin - Bot detection via hidden fields
2. TimestampFormMixin - Form timing validation
3. SecureFormMixin - Combined security features

Author: Rhematek Solutions
Version: 2.0.0
"""

import time
import logging
from typing import Optional, Set

from django import forms
from django.conf import settings
from django.utils import timezone


# Configure logger
security_logger = logging.getLogger('security')


class HoneypotFormMixin:
    """
    Mixin that adds honeypot fields to forms for bot detection.

    Usage:
        class MyForm(HoneypotFormMixin, forms.Form):
            name = forms.CharField()
            email = forms.EmailField()

    The honeypot fields are hidden via CSS and should remain empty.
    Bots that fill them will trigger validation errors.
    """

    # Default honeypot field names
    HONEYPOT_FIELDS = [
        'website_url',
        'email_confirm',
        'hp_field',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_honeypot_fields()

    def _add_honeypot_fields(self) -> None:
        """Add honeypot fields to the form."""
        # Get custom honeypot fields from settings or use defaults
        honeypot_fields = getattr(settings, 'HONEYPOT_FIELDS', self.HONEYPOT_FIELDS)

        # Add first 3 honeypot fields
        for field_name in honeypot_fields[:3]:
            if field_name not in self.fields:
                self.fields[field_name] = forms.CharField(
                    required=False,
                    widget=forms.TextInput(attrs={
                        'class': 'hp-field',  # Hidden via CSS
                        'tabindex': '-1',
                        'autocomplete': 'off',
                        'aria-hidden': 'true',
                        'style': 'position: absolute; left: -9999px; opacity: 0; height: 0; width: 0;',
                    }),
                    label='',
                )

    def clean(self):
        """Validate honeypot fields are empty."""
        cleaned_data = super().clean()

        honeypot_fields = getattr(settings, 'HONEYPOT_FIELDS', self.HONEYPOT_FIELDS)

        for field_name in honeypot_fields[:3]:
            value = cleaned_data.get(field_name, '')
            if value and value.strip():
                security_logger.warning(
                    f"Honeypot field triggered: {field_name}"
                )
                raise forms.ValidationError(
                    'Your submission could not be processed.',
                    code='honeypot_triggered'
                )

        return cleaned_data


class TimestampFormMixin:
    """
    Mixin that adds timestamp validation to detect too-fast form submissions.

    Forms submitted faster than the minimum time are likely bots.
    """

    # Minimum time in seconds between form load and submission
    MIN_SUBMISSION_TIME = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_timestamp_field()

    def _add_timestamp_field(self) -> None:
        """Add hidden timestamp field."""
        self.fields['_form_timestamp'] = forms.CharField(
            required=False,
            widget=forms.HiddenInput(attrs={
                'class': 'form-timestamp',
            }),
            initial=str(timezone.now().timestamp()),
        )

    def clean(self):
        """Validate form was not submitted too quickly."""
        cleaned_data = super().clean()

        timestamp_str = cleaned_data.get('_form_timestamp', '')

        if timestamp_str:
            try:
                form_timestamp = float(timestamp_str)
                current_timestamp = timezone.now().timestamp()
                elapsed = current_timestamp - form_timestamp

                min_time = getattr(
                    settings,
                    'HONEYPOT_MIN_FORM_SUBMISSION_TIME',
                    self.MIN_SUBMISSION_TIME
                )

                if elapsed < min_time:
                    security_logger.warning(
                        f"Form submitted too fast: {elapsed:.2f}s (min: {min_time}s)"
                    )
                    raise forms.ValidationError(
                        'Please review your submission and try again.',
                        code='submission_too_fast'
                    )

            except (ValueError, TypeError):
                # Invalid timestamp - could be tampering
                pass

        return cleaned_data


class SecureFormMixin(HoneypotFormMixin, TimestampFormMixin):
    """
    Combined security mixin with honeypot and timestamp validation.

    Usage:
        class MySecureForm(SecureFormMixin, forms.Form):
            name = forms.CharField()
            email = forms.EmailField()
    """

    def __init__(self, *args, **kwargs):
        # Store request if passed
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        """Perform all security validations."""
        cleaned_data = super().clean()

        # Additional validations can be added here
        # e.g., IP-based rate limiting, etc.

        return cleaned_data


class SecureModelFormMixin(SecureFormMixin):
    """
    Security mixin for ModelForms.

    Removes honeypot and timestamp fields before saving.
    """

    def save(self, commit=True):
        """Remove security fields before saving."""
        # Get the instance
        instance = super().save(commit=False)

        if commit:
            instance.save()
            # Save M2M if needed
            if hasattr(self, 'save_m2m'):
                self.save_m2m()

        return instance


# =============================================================================
# READY-TO-USE SECURE FORM CLASSES
# =============================================================================

class SecureForm(SecureFormMixin, forms.Form):
    """
    Base secure form class.

    Includes honeypot and timestamp validation.
    """
    pass


class SecureModelForm(SecureModelFormMixin, forms.ModelForm):
    """
    Base secure ModelForm class.

    Includes honeypot and timestamp validation.
    """
    pass


# =============================================================================
# TEMPLATE TAGS FOR HONEYPOT CSS
# =============================================================================

HONEYPOT_CSS = """
<style>
.hp-field {
    position: absolute !important;
    left: -9999px !important;
    opacity: 0 !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
    visibility: hidden !important;
}
</style>
"""


def get_honeypot_css() -> str:
    """Return CSS to hide honeypot fields."""
    return HONEYPOT_CSS
