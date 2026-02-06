"""
Tests for core app forms (security form mixins).

Covers:
- HoneypotFormMixin: hidden honeypot fields, bot detection
- TimestampFormMixin: form timing validation
- SecureFormMixin: combined security features
- SecureModelFormMixin: model form security
- SecureForm / SecureModelForm: ready-to-use classes
- get_honeypot_css helper
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from django import forms
from django.conf import settings
from django.test import override_settings
from django.utils import timezone

from apps.core.forms import (
    HoneypotFormMixin,
    TimestampFormMixin,
    SecureFormMixin,
    SecureModelFormMixin,
    SecureForm,
    SecureModelForm,
    get_honeypot_css,
    HONEYPOT_CSS,
)


# ---------------------------------------------------------------------------
# Helper: get the first 3 honeypot field names used at runtime
# ---------------------------------------------------------------------------

def _active_honeypot_fields():
    """Return the first 3 honeypot field names that the mixin will actually use."""
    return getattr(settings, 'HONEYPOT_FIELDS', HoneypotFormMixin.HONEYPOT_FIELDS)[:3]


# ---------------------------------------------------------------------------
# Concrete form classes for testing mixins
# ---------------------------------------------------------------------------

class HoneypotTestForm(HoneypotFormMixin, forms.Form):
    name = forms.CharField()
    email = forms.EmailField()


class TimestampTestForm(TimestampFormMixin, forms.Form):
    name = forms.CharField()


class SecureMixinTestForm(SecureFormMixin, forms.Form):
    name = forms.CharField()
    email = forms.EmailField()


# ---------------------------------------------------------------------------
# HoneypotFormMixin
# ---------------------------------------------------------------------------

class TestHoneypotFormMixin:
    """Tests for HoneypotFormMixin."""

    def test_honeypot_fields_added(self):
        """Honeypot fields should be added to the form."""
        form = HoneypotTestForm()
        for field_name in _active_honeypot_fields():
            assert field_name in form.fields, f"Missing honeypot field: {field_name}"

    def test_honeypot_fields_not_required(self):
        """Honeypot fields should not be required."""
        form = HoneypotTestForm()
        for field_name in _active_honeypot_fields():
            assert not form.fields[field_name].required

    def test_honeypot_field_widget_attributes(self):
        """Honeypot field widgets should have hidden attributes."""
        form = HoneypotTestForm()
        first_hp = _active_honeypot_fields()[0]
        field = form.fields[first_hp]
        attrs = field.widget.attrs
        assert attrs['tabindex'] == '-1'
        assert attrs['autocomplete'] == 'off'
        assert attrs['aria-hidden'] == 'true'
        assert 'hp-field' in attrs['class']

    def test_clean_passes_when_honeypot_empty(self):
        """Form should validate when honeypot fields are empty."""
        data = {
            'name': 'Test User',
            'email': 'user@example.com',
        }
        for field_name in _active_honeypot_fields():
            data[field_name] = ''
        form = HoneypotTestForm(data=data)
        assert form.is_valid(), form.errors

    def test_clean_fails_when_first_honeypot_filled(self):
        """Form should reject submission when the first honeypot field is filled."""
        data = {
            'name': 'Test User',
            'email': 'user@example.com',
        }
        hp_fields = _active_honeypot_fields()
        for field_name in hp_fields:
            data[field_name] = ''
        data[hp_fields[0]] = 'http://spam.com'
        form = HoneypotTestForm(data=data)
        assert not form.is_valid()
        assert '__all__' in form.errors
        assert 'could not be processed' in form.errors['__all__'][0]

    def test_clean_fails_when_second_honeypot_filled(self):
        """Should catch the second honeypot field being filled."""
        data = {
            'name': 'Test User',
            'email': 'user@example.com',
        }
        hp_fields = _active_honeypot_fields()
        for field_name in hp_fields:
            data[field_name] = ''
        data[hp_fields[1]] = 'trap@spam.com'
        form = HoneypotTestForm(data=data)
        assert not form.is_valid()

    def test_clean_fails_when_third_honeypot_filled(self):
        """Should catch the third honeypot field being filled."""
        data = {
            'name': 'Test User',
            'email': 'user@example.com',
        }
        hp_fields = _active_honeypot_fields()
        for field_name in hp_fields:
            data[field_name] = ''
        data[hp_fields[2]] = 'gotcha'
        form = HoneypotTestForm(data=data)
        assert not form.is_valid()

    def test_honeypot_whitespace_only_passes(self):
        """Whitespace-only honeypot values should pass (stripped to empty)."""
        data = {
            'name': 'Test User',
            'email': 'user@example.com',
        }
        hp_fields = _active_honeypot_fields()
        for field_name in hp_fields:
            data[field_name] = '   '
        form = HoneypotTestForm(data=data)
        assert form.is_valid()

    @override_settings(HONEYPOT_FIELDS=['custom_hp_1', 'custom_hp_2'])
    def test_custom_honeypot_fields_from_settings(self):
        """Should use custom honeypot field names from settings."""
        form = HoneypotTestForm()
        assert 'custom_hp_1' in form.fields
        assert 'custom_hp_2' in form.fields

    @override_settings(HONEYPOT_FIELDS=['a', 'b', 'c', 'd', 'e'])
    def test_only_first_three_honeypot_fields_added(self):
        """Should only add at most 3 honeypot fields."""
        form = HoneypotTestForm()
        assert 'a' in form.fields
        assert 'b' in form.fields
        assert 'c' in form.fields
        assert 'd' not in form.fields
        assert 'e' not in form.fields

    def test_honeypot_does_not_override_existing_fields(self):
        """Honeypot should not override a real form field with the same name."""

        class FormWithConflict(HoneypotFormMixin, forms.Form):
            website_url = forms.CharField(required=True)

        form = FormWithConflict()
        # The original field should remain required (not overwritten)
        assert form.fields['website_url'].required

    def test_security_logger_called_on_honeypot_trigger(self):
        """Security logger should warn when honeypot is triggered."""
        data = {
            'name': 'Test',
            'email': 'user@example.com',
        }
        hp_fields = _active_honeypot_fields()
        for field_name in hp_fields:
            data[field_name] = ''
        data[hp_fields[0]] = 'bot-value'
        with patch('apps.core.forms.security_logger') as mock_logger:
            form = HoneypotTestForm(data=data)
            form.is_valid()
            mock_logger.warning.assert_called_once()
            assert 'Honeypot' in mock_logger.warning.call_args[0][0]


# ---------------------------------------------------------------------------
# TimestampFormMixin
# ---------------------------------------------------------------------------

class TestTimestampFormMixin:
    """Tests for TimestampFormMixin."""

    def test_timestamp_field_added(self):
        """Hidden timestamp field should be present."""
        form = TimestampTestForm()
        assert '_form_timestamp' in form.fields

    def test_timestamp_field_is_hidden(self):
        """Timestamp field should use HiddenInput widget."""
        form = TimestampTestForm()
        assert isinstance(form.fields['_form_timestamp'].widget, forms.HiddenInput)

    def test_timestamp_field_not_required(self):
        """Timestamp field should not be required."""
        form = TimestampTestForm()
        assert not form.fields['_form_timestamp'].required

    def test_valid_submission_with_elapsed_time(self):
        """Form submitted after sufficient time should pass."""
        past = str(timezone.now().timestamp() - 10)
        data = {'name': 'Test', '_form_timestamp': past}
        form = TimestampTestForm(data=data)
        assert form.is_valid()

    def test_submission_too_fast_fails(self):
        """Form submitted too quickly should fail validation."""
        now_ts = str(timezone.now().timestamp())
        data = {'name': 'Test', '_form_timestamp': now_ts}
        form = TimestampTestForm(data=data)
        assert not form.is_valid()
        errors = form.errors.get('__all__', [])
        assert any('review your submission' in str(e) or 'submission_too_fast' in str(e)
                    for e in errors)

    def test_missing_timestamp_passes(self):
        """Missing timestamp should not block form submission."""
        data = {'name': 'Test', '_form_timestamp': ''}
        form = TimestampTestForm(data=data)
        assert form.is_valid()

    def test_invalid_timestamp_passes(self):
        """Invalid (non-numeric) timestamp should pass gracefully."""
        data = {'name': 'Test', '_form_timestamp': 'not-a-timestamp'}
        form = TimestampTestForm(data=data)
        assert form.is_valid()

    @override_settings(HONEYPOT_MIN_FORM_SUBMISSION_TIME=5)
    def test_custom_min_submission_time(self):
        """Should respect custom minimum submission time from settings."""
        past = str(timezone.now().timestamp() - 3)
        data = {'name': 'Test', '_form_timestamp': past}
        form = TimestampTestForm(data=data)
        assert not form.is_valid()

    @override_settings(HONEYPOT_MIN_FORM_SUBMISSION_TIME=5)
    def test_custom_min_submission_time_passes(self):
        """Submission after the custom threshold should pass."""
        past = str(timezone.now().timestamp() - 10)
        data = {'name': 'Test', '_form_timestamp': past}
        form = TimestampTestForm(data=data)
        assert form.is_valid()

    def test_security_logger_called_on_fast_submission(self):
        """Security logger should warn on too-fast submissions."""
        now_ts = str(timezone.now().timestamp())
        data = {'name': 'Test', '_form_timestamp': now_ts}
        with patch('apps.core.forms.security_logger') as mock_logger:
            form = TimestampTestForm(data=data)
            form.is_valid()
            mock_logger.warning.assert_called_once()
            assert 'too fast' in mock_logger.warning.call_args[0][0]


# ---------------------------------------------------------------------------
# SecureFormMixin
# ---------------------------------------------------------------------------

class TestSecureFormMixin:
    """Tests for SecureFormMixin (combined honeypot + timestamp)."""

    def test_has_both_honeypot_and_timestamp(self):
        """Should include both honeypot fields and a timestamp field."""
        form = SecureMixinTestForm()
        assert _active_honeypot_fields()[0] in form.fields
        assert '_form_timestamp' in form.fields

    def test_request_stored(self):
        """Request object passed via kwargs should be stored."""
        mock_request = MagicMock()
        form = SecureMixinTestForm(request=mock_request)
        assert form.request is mock_request

    def test_request_defaults_to_none(self):
        """Request should default to None when not passed."""
        form = SecureMixinTestForm()
        assert form.request is None

    def test_valid_clean_data(self):
        """Full valid submission should pass all checks."""
        past = str(timezone.now().timestamp() - 5)
        data = {
            'name': 'Test',
            'email': 'test@example.com',
            '_form_timestamp': past,
        }
        for field_name in _active_honeypot_fields():
            data[field_name] = ''
        form = SecureMixinTestForm(data=data)
        assert form.is_valid(), form.errors

    def test_honeypot_trigger_blocks_in_combined(self):
        """Honeypot trigger should still work in combined mixin."""
        past = str(timezone.now().timestamp() - 5)
        data = {
            'name': 'Test',
            'email': 'test@example.com',
            '_form_timestamp': past,
        }
        hp_fields = _active_honeypot_fields()
        for field_name in hp_fields:
            data[field_name] = ''
        data[hp_fields[0]] = 'spam'
        form = SecureMixinTestForm(data=data)
        assert not form.is_valid()

    def test_fast_submission_blocks_in_combined(self):
        """Fast submission should still work in combined mixin."""
        now_ts = str(timezone.now().timestamp())
        data = {
            'name': 'Test',
            'email': 'test@example.com',
            '_form_timestamp': now_ts,
        }
        for field_name in _active_honeypot_fields():
            data[field_name] = ''
        form = SecureMixinTestForm(data=data)
        assert not form.is_valid()


# ---------------------------------------------------------------------------
# SecureForm (ready-to-use class)
# ---------------------------------------------------------------------------

class TestSecureForm:
    """Tests for the concrete SecureForm class."""

    def test_inherits_form(self):
        """SecureForm should be a subclass of forms.Form."""
        assert issubclass(SecureForm, forms.Form)

    def test_inherits_secure_mixin(self):
        """SecureForm should include SecureFormMixin."""
        assert issubclass(SecureForm, SecureFormMixin)

    def test_can_add_fields_via_subclass(self):
        """Subclassing SecureForm should add security fields automatically."""

        class MyForm(SecureForm):
            username = forms.CharField()

        form = MyForm()
        assert 'username' in form.fields
        assert _active_honeypot_fields()[0] in form.fields
        assert '_form_timestamp' in form.fields


# ---------------------------------------------------------------------------
# SecureModelFormMixin / SecureModelForm
# ---------------------------------------------------------------------------

class TestSecureModelFormMixin:
    """Tests for SecureModelFormMixin save() behaviour."""

    def test_save_with_commit_true(self):
        """save(commit=True) should persist the instance."""
        with patch.object(SecureModelFormMixin, '__init__', lambda self, *a, **kw: None):
            mixin = SecureModelFormMixin()

        mock_instance = MagicMock()
        with patch('apps.core.forms.SecureFormMixin.save', return_value=mock_instance):
            mixin.save_m2m = MagicMock()
            result = SecureModelFormMixin.save(mixin, commit=True)

        mock_instance.save.assert_called_once()
        mixin.save_m2m.assert_called_once()
        assert result is mock_instance

    def test_save_with_commit_false(self):
        """save(commit=False) should return unsaved instance."""
        with patch.object(SecureModelFormMixin, '__init__', lambda self, *a, **kw: None):
            mixin = SecureModelFormMixin()

        mock_instance = MagicMock()
        with patch('apps.core.forms.SecureFormMixin.save', return_value=mock_instance):
            result = SecureModelFormMixin.save(mixin, commit=False)

        mock_instance.save.assert_not_called()
        assert result is mock_instance


class TestSecureModelForm:
    """Tests for SecureModelForm."""

    def test_inherits_model_form(self):
        """SecureModelForm should be a subclass of forms.ModelForm."""
        assert issubclass(SecureModelForm, forms.ModelForm)

    def test_inherits_secure_model_form_mixin(self):
        """SecureModelForm should include SecureModelFormMixin."""
        assert issubclass(SecureModelForm, SecureModelFormMixin)


# ---------------------------------------------------------------------------
# get_honeypot_css
# ---------------------------------------------------------------------------

class TestGetHoneypotCSS:
    """Tests for the CSS helper."""

    def test_returns_style_tag(self):
        """Should return a <style> block."""
        css = get_honeypot_css()
        assert '<style>' in css
        assert '</style>' in css

    def test_contains_hp_field_class(self):
        """Should reference the .hp-field class."""
        css = get_honeypot_css()
        assert '.hp-field' in css

    def test_matches_module_constant(self):
        """Should return the module-level HONEYPOT_CSS constant."""
        assert get_honeypot_css() == HONEYPOT_CSS
