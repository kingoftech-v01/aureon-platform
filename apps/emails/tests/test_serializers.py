"""
Tests for emails app serializers.

Tests cover:
- EmailAccountSerializer
- EmailMessageListSerializer (including attachments_count)
- EmailMessageDetailSerializer (including nested attachments)
- EmailMessageCreateSerializer
- EmailAttachmentSerializer
- EmailTemplateSerializer
"""

import pytest
from apps.emails.serializers import (
    EmailAccountSerializer,
    EmailMessageListSerializer,
    EmailMessageDetailSerializer,
    EmailMessageCreateSerializer,
    EmailAttachmentSerializer,
    EmailTemplateSerializer,
)
from .factories import (
    EmailAccountFactory,
    EmailMessageFactory,
    EmailAttachmentFactory,
    EmailTemplateFactory,
)


# ============================================================================
# EmailAccountSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailAccountSerializer:
    """Tests for EmailAccountSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        account = EmailAccountFactory()
        serializer = EmailAccountSerializer(account)
        data = serializer.data

        assert 'id' in data
        assert 'user' in data
        assert 'email_address' in data
        assert 'display_name' in data
        assert 'provider' in data
        assert 'config' in data
        assert 'is_active' in data
        assert 'is_default' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_read_only_fields(self):
        """Test id, created_at, updated_at are read-only."""
        account = EmailAccountFactory()
        serializer = EmailAccountSerializer(account)
        assert 'id' in serializer.Meta.read_only_fields
        assert 'created_at' in serializer.Meta.read_only_fields
        assert 'updated_at' in serializer.Meta.read_only_fields

    def test_valid_data(self):
        """Test serializer validates correct data."""
        account = EmailAccountFactory()
        data = {
            'user': str(account.user.id),
            'email_address': 'new@test.com',
            'display_name': 'New Account',
            'provider': 'gmail',
            'is_active': True,
            'is_default': False,
            'config': {},
        }
        serializer = EmailAccountSerializer(data=data)
        assert serializer.is_valid(), serializer.errors


# ============================================================================
# EmailMessageListSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailMessageListSerializer:
    """Tests for EmailMessageListSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns list-appropriate fields."""
        message = EmailMessageFactory()
        serializer = EmailMessageListSerializer(message)
        data = serializer.data

        assert 'id' in data
        assert 'account' in data
        assert 'direction' in data
        assert 'from_email' in data
        assert 'to_emails' in data
        assert 'subject' in data
        assert 'status' in data
        assert 'is_read' in data
        assert 'attachments_count' in data

    def test_attachments_count_zero(self):
        """Test attachments_count is 0 when no attachments."""
        message = EmailMessageFactory()
        serializer = EmailMessageListSerializer(message)
        assert serializer.data['attachments_count'] == 0

    def test_attachments_count_with_attachments(self):
        """Test attachments_count reflects actual count."""
        message = EmailMessageFactory()
        EmailAttachmentFactory(email=message)
        EmailAttachmentFactory(email=message)

        serializer = EmailMessageListSerializer(message)
        assert serializer.data['attachments_count'] == 2

    def test_body_fields_excluded(self):
        """Test body_text and body_html are excluded from list serializer."""
        message = EmailMessageFactory()
        serializer = EmailMessageListSerializer(message)
        data = serializer.data
        assert 'body_text' not in data
        assert 'body_html' not in data


# ============================================================================
# EmailMessageDetailSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailMessageDetailSerializer:
    """Tests for EmailMessageDetailSerializer."""

    def test_serializer_includes_all_fields(self):
        """Test detail serializer includes all model fields."""
        message = EmailMessageFactory()
        serializer = EmailMessageDetailSerializer(message)
        data = serializer.data

        assert 'id' in data
        assert 'body_text' in data
        assert 'body_html' in data
        assert 'metadata' in data
        assert 'attachments' in data

    def test_nested_attachments(self):
        """Test attachments are serialized as nested objects."""
        message = EmailMessageFactory()
        EmailAttachmentFactory(email=message, file_name='doc.pdf')

        serializer = EmailMessageDetailSerializer(message)
        assert len(serializer.data['attachments']) == 1
        assert serializer.data['attachments'][0]['file_name'] == 'doc.pdf'

    def test_read_only_fields(self):
        """Test read-only fields."""
        assert 'id' in EmailMessageDetailSerializer.Meta.read_only_fields
        assert 'created_at' in EmailMessageDetailSerializer.Meta.read_only_fields
        assert 'updated_at' in EmailMessageDetailSerializer.Meta.read_only_fields


# ============================================================================
# EmailMessageCreateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailMessageCreateSerializer:
    """Tests for EmailMessageCreateSerializer."""

    def test_valid_data(self):
        """Test serializer validates correct create data."""
        account = EmailAccountFactory()
        data = {
            'account': str(account.id),
            'to_emails': ['recipient@test.com'],
            'subject': 'Test Subject',
            'body_text': 'Hello World',
        }
        serializer = EmailMessageCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_fields_included(self):
        """Test create serializer includes correct fields."""
        expected_fields = [
            'account', 'to_emails', 'cc_emails', 'bcc_emails',
            'subject', 'body_text', 'body_html', 'client',
            'contract', 'invoice', 'in_reply_to',
        ]
        for field in expected_fields:
            assert field in EmailMessageCreateSerializer.Meta.fields

    def test_missing_account_invalid(self):
        """Test missing account fails validation."""
        data = {
            'to_emails': ['recipient@test.com'],
            'subject': 'Test',
        }
        serializer = EmailMessageCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'account' in serializer.errors


# ============================================================================
# EmailAttachmentSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailAttachmentSerializer:
    """Tests for EmailAttachmentSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        attachment = EmailAttachmentFactory()
        serializer = EmailAttachmentSerializer(attachment)
        data = serializer.data

        assert 'id' in data
        assert 'email' in data
        assert 'file' in data
        assert 'file_name' in data
        assert 'file_size' in data
        assert 'file_type' in data

    def test_read_only_fields(self):
        """Test file_size is read-only."""
        assert 'file_size' in EmailAttachmentSerializer.Meta.read_only_fields
        assert 'id' in EmailAttachmentSerializer.Meta.read_only_fields


# ============================================================================
# EmailTemplateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailTemplateSerializer:
    """Tests for EmailTemplateSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        template = EmailTemplateFactory()
        serializer = EmailTemplateSerializer(template)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'subject' in data
        assert 'body_text' in data
        assert 'body_html' in data
        assert 'category' in data
        assert 'available_variables' in data
        assert 'is_active' in data
        assert 'owner' in data

    def test_read_only_fields(self):
        """Test read-only fields."""
        assert 'id' in EmailTemplateSerializer.Meta.read_only_fields
        assert 'created_at' in EmailTemplateSerializer.Meta.read_only_fields
        assert 'updated_at' in EmailTemplateSerializer.Meta.read_only_fields

    def test_valid_data(self):
        """Test serializer validates correct data."""
        user = EmailAccountFactory().user
        data = {
            'name': 'New Template',
            'subject': 'Welcome $name',
            'body_text': 'Hello $name',
            'body_html': '<p>Hello $name</p>',
            'category': 'welcome',
            'is_active': True,
            'owner': str(user.id),
            'available_variables': ['name'],
        }
        serializer = EmailTemplateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
