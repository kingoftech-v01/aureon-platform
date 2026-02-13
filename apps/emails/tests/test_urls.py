"""
Tests for emails app URL configuration.

Tests cover:
- URL resolution for all registered ViewSet routes
- Router URL names and patterns
"""

import pytest
from django.urls import reverse, resolve


@pytest.mark.django_db
class TestEmailURLs:
    """Tests for emails app URL configuration."""

    def test_email_account_list_url(self):
        """Test email-account-list URL resolves."""
        url = '/api/emails/api/email-accounts/'
        match = resolve(url)
        assert match.url_name == 'email-account-list'

    def test_email_account_detail_url(self):
        """Test email-account-detail URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = f'/api/emails/api/email-accounts/{pk}/'
        match = resolve(url)
        assert match.url_name == 'email-account-detail'

    def test_email_account_set_default_url(self):
        """Test email-account set_default URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = f'/api/emails/api/email-accounts/{pk}/set_default/'
        match = resolve(url)
        assert match.url_name == 'email-account-set-default'

    def test_email_account_test_connection_url(self):
        """Test email-account test_connection URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = f'/api/emails/api/email-accounts/{pk}/test_connection/'
        match = resolve(url)
        assert match.url_name == 'email-account-test-connection'

    def test_email_message_list_url(self):
        """Test email-list URL resolves."""
        url = '/api/emails/api/emails/'
        match = resolve(url)
        assert match.url_name == 'email-list'

    def test_email_message_detail_url(self):
        """Test email-detail URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = f'/api/emails/api/emails/{pk}/'
        match = resolve(url)
        assert match.url_name == 'email-detail'

    def test_email_message_send_url(self):
        """Test email send URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = f'/api/emails/api/emails/{pk}/send/'
        match = resolve(url)
        assert match.url_name == 'email-send'

    def test_email_message_mark_read_url(self):
        """Test email mark_read URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = f'/api/emails/api/emails/{pk}/mark_read/'
        match = resolve(url)
        assert match.url_name == 'email-mark-read'

    def test_email_message_mark_unread_url(self):
        """Test email mark_unread URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = f'/api/emails/api/emails/{pk}/mark_unread/'
        match = resolve(url)
        assert match.url_name == 'email-mark-unread'

    def test_email_message_stats_url(self):
        """Test email stats URL resolves."""
        url = '/api/emails/api/emails/stats/'
        match = resolve(url)
        assert match.url_name == 'email-stats'

    def test_email_attachment_list_url(self):
        """Test email-attachment-list URL resolves."""
        url = '/api/emails/api/email-attachments/'
        match = resolve(url)
        assert match.url_name == 'email-attachment-list'

    def test_email_template_list_url(self):
        """Test email-template-list URL resolves."""
        url = '/api/emails/api/email-templates/'
        match = resolve(url)
        assert match.url_name == 'email-template-list'

    def test_email_template_preview_url(self):
        """Test email-template preview URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = f'/api/emails/api/email-templates/{pk}/preview/'
        match = resolve(url)
        assert match.url_name == 'email-template-preview'
