"""
Tests for emails app models.

Tests cover:
- Model creation and field defaults
- __str__ methods
- EmailTemplate.render() method
- EmailAttachment.save() file_size auto-population
- EmailAccount unique_together constraint
"""

import pytest
from django.db import IntegrityError
from apps.emails.models import EmailAccount, EmailMessage, EmailAttachment, EmailTemplate
from .factories import (
    UserFactory,
    EmailAccountFactory,
    EmailMessageFactory,
    EmailAttachmentFactory,
    EmailTemplateFactory,
)


# ============================================================================
# EmailAccount Model Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailAccountModel:
    """Tests for EmailAccount model."""

    def test_create_email_account(self):
        """Test creating an email account with defaults."""
        account = EmailAccountFactory()
        assert account.pk is not None
        assert account.is_active is True
        assert account.is_default is False
        assert account.provider == EmailAccount.SMTP
        assert account.created_at is not None
        assert account.updated_at is not None

    def test_str_representation(self):
        """Test __str__ returns display_name <email_address>."""
        account = EmailAccountFactory(
            display_name='John Doe',
            email_address='john@test.com',
        )
        assert str(account) == 'John Doe <john@test.com>'

    def test_provider_choices(self):
        """Test all provider choices can be set."""
        for provider_code, _ in EmailAccount.PROVIDER_CHOICES:
            account = EmailAccountFactory(provider=provider_code)
            assert account.provider == provider_code

    def test_unique_together_user_email_address(self):
        """Test unique_together constraint on user and email_address."""
        user = UserFactory()
        EmailAccountFactory(user=user, email_address='unique@test.com')

        with pytest.raises(IntegrityError):
            EmailAccountFactory(user=user, email_address='unique@test.com')

    def test_different_users_same_email_allowed(self):
        """Test different users can have the same email address."""
        user1 = UserFactory()
        user2 = UserFactory()
        EmailAccountFactory(user=user1, email_address='shared@test.com')
        account2 = EmailAccountFactory(user=user2, email_address='shared@test.com')
        assert account2.pk is not None

    def test_config_json_field(self):
        """Test config JSON field stores data correctly."""
        config = {'host': 'smtp.gmail.com', 'port': 465, 'use_ssl': True}
        account = EmailAccountFactory(config=config)
        assert account.config == config

    def test_ordering(self):
        """Test default ordering is [-is_default, -created_at]."""
        user = UserFactory()
        account1 = EmailAccountFactory(user=user, is_default=False)
        account2 = EmailAccountFactory(user=user, is_default=True)
        accounts = list(EmailAccount.objects.filter(user=user))
        assert accounts[0] == account2  # default first


# ============================================================================
# EmailMessage Model Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailMessageModel:
    """Tests for EmailMessage model."""

    def test_create_email_message(self):
        """Test creating an email message with defaults."""
        message = EmailMessageFactory()
        assert message.pk is not None
        assert message.status == EmailMessage.DRAFT
        assert message.direction == EmailMessage.OUTBOUND
        assert message.is_read is False
        assert message.opened_count == 0

    def test_str_representation(self):
        """Test __str__ returns subject - status."""
        message = EmailMessageFactory(
            subject='Test Subject',
            status=EmailMessage.SENT,
        )
        assert str(message) == 'Test Subject - sent'

    def test_direction_choices(self):
        """Test both direction choices."""
        inbound = EmailMessageFactory(direction=EmailMessage.INBOUND)
        outbound = EmailMessageFactory(direction=EmailMessage.OUTBOUND)
        assert inbound.direction == EmailMessage.INBOUND
        assert outbound.direction == EmailMessage.OUTBOUND

    def test_status_choices(self):
        """Test all status choices."""
        for status_code, _ in EmailMessage.STATUS_CHOICES:
            message = EmailMessageFactory(status=status_code)
            assert message.status == status_code

    def test_to_emails_json_field(self):
        """Test to_emails JSON field stores list correctly."""
        emails = ['a@test.com', 'b@test.com']
        message = EmailMessageFactory(to_emails=emails)
        assert message.to_emails == emails

    def test_cc_and_bcc_emails(self):
        """Test cc and bcc JSON fields."""
        cc = ['cc@test.com']
        bcc = ['bcc@test.com']
        message = EmailMessageFactory(cc_emails=cc, bcc_emails=bcc)
        assert message.cc_emails == cc
        assert message.bcc_emails == bcc

    def test_email_threading_in_reply_to(self):
        """Test in_reply_to self-referencing FK."""
        original = EmailMessageFactory()
        reply = EmailMessageFactory(in_reply_to=original, thread_id='thread-1')
        assert reply.in_reply_to == original
        assert reply.thread_id == 'thread-1'
        assert original.replies.first() == reply

    def test_metadata_json_field(self):
        """Test metadata JSON field."""
        meta = {'campaign': 'welcome', 'source': 'api'}
        message = EmailMessageFactory(metadata=meta)
        assert message.metadata == meta

    def test_client_fk_nullable(self):
        """Test client FK is nullable."""
        message = EmailMessageFactory(client=None)
        assert message.client is None

    def test_ordering(self):
        """Test default ordering is [-created_at]."""
        m1 = EmailMessageFactory()
        m2 = EmailMessageFactory()
        messages = list(EmailMessage.objects.all())
        assert messages[0] == m2  # most recent first


# ============================================================================
# EmailAttachment Model Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailAttachmentModel:
    """Tests for EmailAttachment model."""

    def test_create_attachment(self):
        """Test creating an email attachment."""
        attachment = EmailAttachmentFactory()
        assert attachment.pk is not None
        assert attachment.file_name is not None
        assert attachment.file_type == 'application/pdf'

    def test_str_representation(self):
        """Test __str__ returns file_name."""
        attachment = EmailAttachmentFactory(file_name='report.pdf')
        assert str(attachment) == 'report.pdf'

    def test_save_sets_file_size(self):
        """Test save() automatically sets file_size from file."""
        attachment = EmailAttachmentFactory()
        assert attachment.file_size is not None
        assert attachment.file_size > 0

    def test_save_without_file_no_error(self):
        """Test save() handles missing file gracefully."""
        message = EmailMessageFactory()
        attachment = EmailAttachment(
            email=message,
            file_name='empty.pdf',
            file_type='application/pdf',
        )
        # file is not set, save should not error
        attachment.save()
        assert attachment.pk is not None

    def test_attachment_belongs_to_email(self):
        """Test attachment FK to email message."""
        message = EmailMessageFactory()
        attachment = EmailAttachmentFactory(email=message)
        assert attachment.email == message
        assert message.attachments.count() == 1


# ============================================================================
# EmailTemplate Model Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailTemplateModel:
    """Tests for EmailTemplate model."""

    def test_create_template(self):
        """Test creating an email template with defaults."""
        template = EmailTemplateFactory()
        assert template.pk is not None
        assert template.is_active is True
        assert template.category == EmailTemplate.GENERAL

    def test_str_representation(self):
        """Test __str__ returns template name."""
        template = EmailTemplateFactory(name='Welcome Email')
        assert str(template) == 'Welcome Email'

    def test_category_choices(self):
        """Test all category choices."""
        for cat_code, _ in EmailTemplate.CATEGORY_CHOICES:
            template = EmailTemplateFactory(category=cat_code)
            assert template.category == cat_code

    def test_render_with_context(self):
        """Test render() substitutes variables correctly."""
        template = EmailTemplateFactory(
            subject='Hello $client_name',
            body_text='Dear $client_name, your project $project_name is ready.',
            body_html='<p>Dear $client_name, your project $project_name is ready.</p>',
        )
        context = {'client_name': 'Alice', 'project_name': 'Website'}
        result = template.render(context)

        assert result['subject'] == 'Hello Alice'
        assert 'Dear Alice' in result['body_text']
        assert 'Website' in result['body_text']
        assert '<p>Dear Alice' in result['body_html']
        assert 'Website' in result['body_html']

    def test_render_with_missing_variables(self):
        """Test render() uses safe_substitute (missing vars kept as-is)."""
        template = EmailTemplateFactory(
            subject='Hello $client_name',
            body_text='About $project_name',
            body_html='<p>About $project_name</p>',
        )
        result = template.render({'client_name': 'Bob'})

        assert result['subject'] == 'Hello Bob'
        assert '$project_name' in result['body_text']

    def test_render_with_empty_context(self):
        """Test render() with empty context returns template strings with vars."""
        template = EmailTemplateFactory(
            subject='Hello $name',
            body_text='$message',
            body_html='<p>$message</p>',
        )
        result = template.render({})

        assert '$name' in result['subject']
        assert '$message' in result['body_text']

    def test_available_variables_field(self):
        """Test available_variables JSON field."""
        vars_list = ['name', 'date', 'amount']
        template = EmailTemplateFactory(available_variables=vars_list)
        assert template.available_variables == vars_list

    def test_ordering(self):
        """Test default ordering by name."""
        t_b = EmailTemplateFactory(name='B Template')
        t_a = EmailTemplateFactory(name='A Template')
        templates = list(EmailTemplate.objects.all())
        assert templates[0] == t_a
        assert templates[1] == t_b

    def test_owner_nullable(self):
        """Test owner FK is nullable."""
        template = EmailTemplateFactory(owner=None)
        assert template.owner is None
        assert template.pk is not None
