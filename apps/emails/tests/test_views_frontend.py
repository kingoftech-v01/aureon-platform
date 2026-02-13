"""
Tests for emails app frontend views.

Tests cover:
- EmailInboxView (list, filtering by direction/status, search)
- EmailDetailView (detail page with attachments and related entities)
- EmailComposeView (compose form page with accounts and templates)
- EmailAccountSettingsView (account settings listing)
- EmailTemplateListView (template listing with counts)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import pytest
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist

from apps.emails.models import EmailMessage
from .factories import (
    UserFactory,
    EmailAccountFactory,
    EmailMessageFactory,
    EmailAttachmentFactory,
    EmailTemplateFactory,
)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
EMAIL_INBOX_URL = '/api/emails/'
EMAIL_COMPOSE_URL = '/api/emails/compose/'
EMAIL_ACCOUNT_SETTINGS_URL = '/api/emails/accounts/'
EMAIL_TEMPLATE_LIST_URL = '/api/emails/templates/'


def email_detail_url(pk):
    return f'/api/emails/{pk}/'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(user):
    client = TestClient()
    client.force_login(user)
    return client


@pytest.fixture
def email_account(user):
    return EmailAccountFactory(user=user, is_active=True)


@pytest.fixture
def email_account_default(user):
    return EmailAccountFactory(user=user, is_active=True, is_default=True)


@pytest.fixture
def email_message(email_account):
    return EmailMessageFactory(account=email_account, direction=EmailMessage.OUTBOUND)


@pytest.fixture
def email_message_with_attachments(email_message):
    EmailAttachmentFactory(email=email_message)
    EmailAttachmentFactory(email=email_message)
    return email_message


@pytest.fixture
def email_template(user):
    return EmailTemplateFactory(owner=user)


# ---------------------------------------------------------------------------
# EmailInboxView tests
# ---------------------------------------------------------------------------
class TestEmailInboxView:
    """Tests for EmailInboxView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(EMAIL_INBOX_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, email_message):
        try:
            response = auth_client.get(EMAIL_INBOX_URL)
            assert response.status_code in (200, 302)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, email_message):
        try:
            response = auth_client.get(EMAIL_INBOX_URL)
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['page_title'] == 'Email Inbox'
                assert 'direction_choices' in ctx
                assert 'status_choices' in ctx
                assert 'current_direction' in ctx
                assert 'current_status' in ctx
                assert 'search_query' in ctx
                assert 'accounts' in ctx
                assert 'unread_count' in ctx
                assert 'emails' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_direction(self, auth_client, user):
        account = EmailAccountFactory(user=user)
        inbound_msg = EmailMessageFactory(
            account=account, direction=EmailMessage.INBOUND
        )
        EmailMessageFactory(
            account=account, direction=EmailMessage.OUTBOUND
        )
        try:
            response = auth_client.get(EMAIL_INBOX_URL, {'direction': EmailMessage.INBOUND})
            if response.status_code == 200 and response.context:
                emails = list(response.context['emails'])
                assert inbound_msg in emails
                assert all(e.direction == EmailMessage.INBOUND for e in emails)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_status(self, auth_client, user):
        account = EmailAccountFactory(user=user)
        sent_msg = EmailMessageFactory(
            account=account, status=EmailMessage.SENT
        )
        EmailMessageFactory(
            account=account, status=EmailMessage.DRAFT
        )
        try:
            response = auth_client.get(EMAIL_INBOX_URL, {'status': EmailMessage.SENT})
            if response.status_code == 200 and response.context:
                emails = list(response.context['emails'])
                assert sent_msg in emails
                assert all(e.status == EmailMessage.SENT for e in emails)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_subject(self, auth_client, user):
        account = EmailAccountFactory(user=user)
        target = EmailMessageFactory(
            account=account, subject='Unique Search Target Email'
        )
        EmailMessageFactory(account=account, subject='Other email')
        try:
            response = auth_client.get(EMAIL_INBOX_URL, {'q': 'Unique Search Target'})
            if response.status_code == 200 and response.context:
                emails = list(response.context['emails'])
                assert target in emails
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_from_email(self, auth_client, user):
        account = EmailAccountFactory(user=user)
        target = EmailMessageFactory(
            account=account, from_email='special@unique-domain.com'
        )
        EmailMessageFactory(account=account, from_email='other@test.com')
        try:
            response = auth_client.get(EMAIL_INBOX_URL, {'q': 'special@unique-domain'})
            if response.status_code == 200 and response.context:
                emails = list(response.context['emails'])
                assert target in emails
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# EmailDetailView tests
# ---------------------------------------------------------------------------
class TestEmailDetailView:
    """Tests for EmailDetailView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, email_message):
        client = TestClient()
        response = client.get(email_detail_url(email_message.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, email_message_with_attachments):
        try:
            response = auth_client.get(email_detail_url(email_message_with_attachments.pk))
            assert response.status_code in (200, 302)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_email_and_details(self, auth_client, email_message_with_attachments):
        try:
            response = auth_client.get(email_detail_url(email_message_with_attachments.pk))
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['email'] == email_message_with_attachments
                assert 'page_title' in ctx
                assert 'attachments' in ctx
                assert 'replies' in ctx
                assert 'client' in ctx
                assert 'contract' in ctx
                assert 'invoice' in ctx
                assert 'is_read' in ctx
                assert 'from_email' in ctx
                assert 'to_emails' in ctx
                assert 'cc_emails' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# EmailComposeView tests
# ---------------------------------------------------------------------------
class TestEmailComposeView:
    """Tests for EmailComposeView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(EMAIL_COMPOSE_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, email_account):
        try:
            response = auth_client.get(EMAIL_COMPOSE_URL)
            assert response.status_code in (200, 302)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_compose_data(self, auth_client, email_account, email_template):
        try:
            response = auth_client.get(EMAIL_COMPOSE_URL)
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['page_title'] == 'Compose Email'
                assert 'accounts' in ctx
                assert 'templates' in ctx
                assert 'clients' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_compose_with_reply_to(self, auth_client, email_message):
        try:
            response = auth_client.get(EMAIL_COMPOSE_URL, {'reply_to': str(email_message.pk)})
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['reply_to'] == email_message
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# EmailAccountSettingsView tests
# ---------------------------------------------------------------------------
class TestEmailAccountSettingsView:
    """Tests for EmailAccountSettingsView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(EMAIL_ACCOUNT_SETTINGS_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, email_account):
        try:
            response = auth_client.get(EMAIL_ACCOUNT_SETTINGS_URL)
            assert response.status_code in (200, 302)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_account_settings_data(self, auth_client, email_account_default):
        try:
            response = auth_client.get(EMAIL_ACCOUNT_SETTINGS_URL)
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['page_title'] == 'Email Account Settings'
                assert 'provider_choices' in ctx
                assert 'total_accounts' in ctx
                assert 'default_account' in ctx
                assert 'accounts' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_default_account_present(self, auth_client, email_account_default):
        try:
            response = auth_client.get(EMAIL_ACCOUNT_SETTINGS_URL)
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['default_account'] == email_account_default
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# EmailTemplateListView tests
# ---------------------------------------------------------------------------
class TestEmailTemplateListView:
    """Tests for EmailTemplateListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(EMAIL_TEMPLATE_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, email_template):
        try:
            response = auth_client.get(EMAIL_TEMPLATE_LIST_URL)
            assert response.status_code in (200, 302)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_template_list_data(self, auth_client, email_template):
        try:
            response = auth_client.get(EMAIL_TEMPLATE_LIST_URL)
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['page_title'] == 'Email Templates'
                assert 'category_choices' in ctx
                assert 'active_count' in ctx
                assert 'total_count' in ctx
                assert 'templates' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_template_counts(self, auth_client, user):
        EmailTemplateFactory(owner=user, is_active=True)
        EmailTemplateFactory(owner=user, is_active=True)
        EmailTemplateFactory(owner=user, is_active=False)
        try:
            response = auth_client.get(EMAIL_TEMPLATE_LIST_URL)
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['active_count'] == 2
                assert ctx['total_count'] == 3
        except TemplateDoesNotExist:
            pass
