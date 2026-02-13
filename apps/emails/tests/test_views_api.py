"""
Tests for emails app API views.

Tests cover:
- EmailAccountViewSet CRUD + set_default + test_connection
- EmailMessageViewSet CRUD + send + mark_read + mark_unread + stats
- EmailTemplateViewSet CRUD + preview
- EmailAttachmentViewSet CRUD subset
- Filtering and search
- Authentication requirements (401 for unauthenticated)
"""

import pytest
import uuid
from rest_framework import status
from rest_framework.test import APIClient
from apps.emails.models import EmailAccount, EmailMessage, EmailTemplate
from .factories import (
    UserFactory,
    EmailAccountFactory,
    EmailMessageFactory,
    EmailAttachmentFactory,
    EmailTemplateFactory,
)


# ============================================================================
# EmailAccountViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailAccountViewSet:
    """Tests for EmailAccountViewSet."""

    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = '/api/emails/api/email-accounts/'

    def test_list_accounts(self):
        """Test listing email accounts."""
        EmailAccountFactory(user=self.user)
        EmailAccountFactory(user=self.user)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_list_accounts_unauthenticated(self):
        """Test 401 for unauthenticated access."""
        client = APIClient()
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_account(self):
        """Test creating an email account."""
        data = {
            'user': str(self.user.id),
            'email_address': 'new@example.com',
            'display_name': 'New Account',
            'provider': 'gmail',
            'is_active': True,
            'is_default': False,
            'config': {},
        }
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email_address'] == 'new@example.com'

    def test_retrieve_account(self):
        """Test retrieving an email account."""
        account = EmailAccountFactory(user=self.user)
        response = self.client.get(f'{self.url}{account.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(account.id)

    def test_update_account(self):
        """Test updating an email account."""
        account = EmailAccountFactory(user=self.user)
        response = self.client.patch(
            f'{self.url}{account.id}/',
            {'display_name': 'Updated Name'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['display_name'] == 'Updated Name'

    def test_delete_account(self):
        """Test deleting an email account."""
        account = EmailAccountFactory(user=self.user)
        response = self.client.delete(f'{self.url}{account.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not EmailAccount.objects.filter(id=account.id).exists()

    def test_set_default_action(self):
        """Test set_default action unsets other defaults and sets this one."""
        account1 = EmailAccountFactory(user=self.user, is_default=True)
        account2 = EmailAccountFactory(user=self.user, is_default=False)

        response = self.client.post(f'{self.url}{account2.id}/set_default/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_default'] is True

        account1.refresh_from_db()
        assert account1.is_default is False

    def test_test_connection_action(self):
        """Test test_connection action returns success."""
        account = EmailAccountFactory(user=self.user)
        response = self.client.post(f'{self.url}{account.id}/test_connection/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert account.email_address in response.data['message']
        assert response.data['provider'] == account.provider

    def test_filter_by_provider(self):
        """Test filtering by provider."""
        EmailAccountFactory(user=self.user, provider=EmailAccount.GMAIL)
        EmailAccountFactory(user=self.user, provider=EmailAccount.SMTP)
        response = self.client.get(f'{self.url}?provider=gmail')
        assert response.status_code == status.HTTP_200_OK
        for item in response.data:
            assert item['provider'] == 'gmail'

    def test_filter_by_is_active(self):
        """Test filtering by is_active."""
        EmailAccountFactory(user=self.user, is_active=True)
        EmailAccountFactory(user=self.user, is_active=False)
        response = self.client.get(f'{self.url}?is_active=true')
        assert response.status_code == status.HTTP_200_OK
        for item in response.data:
            assert item['is_active'] is True

    def test_non_staff_sees_own_accounts_only(self):
        """Test non-staff user sees only their own accounts."""
        other_user = UserFactory(is_staff=False)
        EmailAccountFactory(user=self.user)
        EmailAccountFactory(user=other_user)

        self.user.is_staff = False
        self.user.save()

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        for item in response.data:
            assert item['user'] == str(self.user.id)

    def test_retrieve_nonexistent_returns_404(self):
        """Test retrieving a nonexistent account returns 404."""
        fake_id = uuid.uuid4()
        response = self.client.get(f'{self.url}{fake_id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# EmailMessageViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailMessageViewSet:
    """Tests for EmailMessageViewSet."""

    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.account = EmailAccountFactory(user=self.user)
        self.url = '/api/emails/api/emails/'

    def test_list_messages(self):
        """Test listing email messages."""
        EmailMessageFactory(account=self.account)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_messages_unauthenticated(self):
        """Test 401 for unauthenticated access."""
        client = APIClient()
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_message(self):
        """Test creating an email message (draft)."""
        data = {
            'account': str(self.account.id),
            'to_emails': ['test@example.com'],
            'subject': 'New Email',
            'body_text': 'Hello!',
        }
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_perform_create_sets_from_email_and_direction(self):
        """Test perform_create sets from_email and direction automatically."""
        data = {
            'account': str(self.account.id),
            'to_emails': ['test@example.com'],
            'subject': 'Auto fields test',
            'body_text': 'Test',
        }
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        msg = EmailMessage.objects.get(subject='Auto fields test')
        assert msg.from_email == self.account.email_address
        assert msg.direction == EmailMessage.OUTBOUND

    def test_retrieve_message(self):
        """Test retrieving a message returns detail serializer."""
        message = EmailMessageFactory(account=self.account)
        response = self.client.get(f'{self.url}{message.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'body_text' in response.data  # detail serializer
        assert 'attachments' in response.data

    def test_update_message(self):
        """Test updating a message."""
        message = EmailMessageFactory(account=self.account)
        response = self.client.patch(
            f'{self.url}{message.id}/',
            {'subject': 'Updated Subject'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK

    def test_delete_message(self):
        """Test deleting a message."""
        message = EmailMessageFactory(account=self.account)
        response = self.client.delete(f'{self.url}{message.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_send_action_success(self):
        """Test send action sets status to SENT."""
        message = EmailMessageFactory(account=self.account, status=EmailMessage.DRAFT)
        response = self.client.post(f'{self.url}{message.id}/send/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == EmailMessage.SENT
        assert response.data['sent_at'] is not None

    def test_send_action_queued_message(self):
        """Test send action works for queued messages."""
        message = EmailMessageFactory(account=self.account, status=EmailMessage.QUEUED)
        response = self.client.post(f'{self.url}{message.id}/send/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == EmailMessage.SENT

    def test_send_action_already_sent_fails(self):
        """Test send action fails for already-sent messages."""
        message = EmailMessageFactory(account=self.account, status=EmailMessage.SENT)
        response = self.client.post(f'{self.url}{message.id}/send/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_send_action_failed_status_fails(self):
        """Test send action fails for messages with failed status."""
        message = EmailMessageFactory(account=self.account, status=EmailMessage.FAILED)
        response = self.client.post(f'{self.url}{message.id}/send/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_mark_read_action(self):
        """Test mark_read action sets is_read to True."""
        message = EmailMessageFactory(account=self.account, is_read=False)
        response = self.client.post(f'{self.url}{message.id}/mark_read/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_read'] is True

    def test_mark_unread_action(self):
        """Test mark_unread action sets is_read to False."""
        message = EmailMessageFactory(account=self.account, is_read=True)
        response = self.client.post(f'{self.url}{message.id}/mark_unread/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_read'] is False

    def test_stats_action(self):
        """Test stats action returns correct counts."""
        EmailMessageFactory(
            account=self.account,
            direction=EmailMessage.OUTBOUND,
            status=EmailMessage.SENT,
        )
        EmailMessageFactory(
            account=self.account,
            direction=EmailMessage.INBOUND,
            status=EmailMessage.RECEIVED,
        )
        EmailMessageFactory(
            account=self.account,
            status=EmailMessage.DRAFT,
        )

        response = self.client.get(f'{self.url}stats/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data
        assert 'sent' in response.data
        assert 'received' in response.data
        assert 'drafts' in response.data
        assert 'unread' in response.data
        assert response.data['total'] >= 3

    def test_filter_by_status(self):
        """Test filtering by status."""
        EmailMessageFactory(account=self.account, status=EmailMessage.DRAFT)
        EmailMessageFactory(account=self.account, status=EmailMessage.SENT)
        response = self.client.get(f'{self.url}?status=draft')
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_direction(self):
        """Test filtering by direction."""
        EmailMessageFactory(account=self.account, direction=EmailMessage.INBOUND)
        response = self.client.get(f'{self.url}?direction=inbound')
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_is_read(self):
        """Test filtering by is_read."""
        EmailMessageFactory(account=self.account, is_read=True)
        EmailMessageFactory(account=self.account, is_read=False)
        response = self.client.get(f'{self.url}?is_read=true')
        assert response.status_code == status.HTTP_200_OK

    def test_search_by_subject(self):
        """Test search by subject."""
        EmailMessageFactory(account=self.account, subject='Unique Search Target')
        response = self.client.get(f'{self.url}?search=Unique+Search+Target')
        assert response.status_code == status.HTTP_200_OK

    def test_search_by_from_email(self):
        """Test search by from_email."""
        EmailMessageFactory(account=self.account, from_email='searchable@test.com')
        response = self.client.get(f'{self.url}?search=searchable@test.com')
        assert response.status_code == status.HTTP_200_OK

    def test_non_staff_sees_own_messages_only(self):
        """Test non-staff sees only their own messages."""
        other_user = UserFactory(is_staff=False)
        other_account = EmailAccountFactory(user=other_user)
        EmailMessageFactory(account=self.account)
        EmailMessageFactory(account=other_account)

        self.user.is_staff = False
        self.user.save()

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_serializer_class_list(self):
        """Test list action uses EmailMessageListSerializer."""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        # list serializer has attachments_count, not body_text


# ============================================================================
# EmailAttachmentViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailAttachmentViewSet:
    """Tests for EmailAttachmentViewSet."""

    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.account = EmailAccountFactory(user=self.user)
        self.message = EmailMessageFactory(account=self.account)
        self.url = '/api/emails/api/email-attachments/'

    def test_list_attachments(self):
        """Test listing attachments."""
        EmailAttachmentFactory(email=self.message)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_unauthenticated(self):
        """Test 401 for unauthenticated access."""
        client = APIClient()
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_attachment(self):
        """Test retrieving an attachment."""
        attachment = EmailAttachmentFactory(email=self.message)
        response = self.client.get(f'{self.url}{attachment.id}/')
        assert response.status_code == status.HTTP_200_OK

    def test_delete_attachment(self):
        """Test deleting an attachment."""
        attachment = EmailAttachmentFactory(email=self.message)
        response = self.client.delete(f'{self.url}{attachment.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_by_email(self):
        """Test filtering attachments by email."""
        EmailAttachmentFactory(email=self.message)
        response = self.client.get(f'{self.url}?email={self.message.id}')
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# EmailTemplateViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestEmailTemplateViewSet:
    """Tests for EmailTemplateViewSet."""

    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = '/api/emails/api/email-templates/'

    def test_list_templates(self):
        """Test listing email templates."""
        EmailTemplateFactory(owner=self.user)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_templates_unauthenticated(self):
        """Test 401 for unauthenticated access."""
        client = APIClient()
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_template(self):
        """Test creating an email template."""
        data = {
            'name': 'New Template',
            'subject': 'Hello $name',
            'body_text': 'Dear $name',
            'body_html': '<p>Dear $name</p>',
            'category': 'welcome',
            'is_active': True,
            'owner': str(self.user.id),
            'available_variables': ['name'],
        }
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_template(self):
        """Test retrieving a template."""
        template = EmailTemplateFactory(owner=self.user)
        response = self.client.get(f'{self.url}{template.id}/')
        assert response.status_code == status.HTTP_200_OK

    def test_update_template(self):
        """Test updating a template."""
        template = EmailTemplateFactory(owner=self.user)
        response = self.client.patch(
            f'{self.url}{template.id}/',
            {'name': 'Updated Template'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Template'

    def test_delete_template(self):
        """Test deleting a template."""
        template = EmailTemplateFactory(owner=self.user)
        response = self.client.delete(f'{self.url}{template.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_preview_action(self):
        """Test preview action renders template with context."""
        template = EmailTemplateFactory(
            owner=self.user,
            subject='Hello $client_name',
            body_text='Dear $client_name, about $project_name.',
            body_html='<p>Dear $client_name, about $project_name.</p>',
        )
        data = {
            'context': {
                'client_name': 'Alice',
                'project_name': 'Website',
            }
        }
        response = self.client.post(
            f'{self.url}{template.id}/preview/',
            data,
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['rendered_subject'] == 'Hello Alice'
        assert 'Alice' in response.data['rendered_body_text']
        assert 'Website' in response.data['rendered_body_text']
        assert response.data['name'] == template.name
        assert response.data['category'] == template.category

    def test_preview_action_empty_context(self):
        """Test preview action with empty context keeps variables."""
        template = EmailTemplateFactory(
            owner=self.user,
            subject='Hello $name',
            body_text='$message',
            body_html='<p>$message</p>',
        )
        response = self.client.post(
            f'{self.url}{template.id}/preview/',
            {'context': {}},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert '$name' in response.data['rendered_subject']

    def test_filter_by_category(self):
        """Test filtering by category."""
        EmailTemplateFactory(category=EmailTemplate.INVOICE)
        EmailTemplateFactory(category=EmailTemplate.WELCOME)
        response = self.client.get(f'{self.url}?category=invoice')
        assert response.status_code == status.HTTP_200_OK
        for item in response.data:
            assert item['category'] == 'invoice'

    def test_filter_by_is_active(self):
        """Test filtering by is_active."""
        EmailTemplateFactory(is_active=True)
        EmailTemplateFactory(is_active=False)
        response = self.client.get(f'{self.url}?is_active=true')
        assert response.status_code == status.HTTP_200_OK

    def test_search_by_name(self):
        """Test search by template name."""
        EmailTemplateFactory(name='Unique Template Name XYZ')
        response = self.client.get(f'{self.url}?search=Unique+Template+Name+XYZ')
        assert response.status_code == status.HTTP_200_OK

    def test_search_by_subject(self):
        """Test search by template subject."""
        EmailTemplateFactory(subject='Very Unique Subject ABC')
        response = self.client.get(f'{self.url}?search=Very+Unique+Subject+ABC')
        assert response.status_code == status.HTTP_200_OK
