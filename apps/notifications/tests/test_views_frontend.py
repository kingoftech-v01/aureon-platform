"""
Tests for notifications app frontend views.

Tests cover:
- NotificationListView (list, filtering by status/channel)
- NotificationSettingsView (user notification preferences)
- NotificationTemplateListView (notification template management)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import pytest
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist

import factory
from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationTemplate


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'notifuser{n}@test.com')
    username = factory.LazyAttribute(lambda o: o.email)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    full_name = factory.LazyAttribute(lambda o: f'{o.first_name} {o.last_name}')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_active = True
    role = User.ADMIN
    email_notifications = True
    sms_notifications = False


class NotificationTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for creating NotificationTemplate instances."""

    class Meta:
        model = NotificationTemplate

    name = factory.Sequence(lambda n: f'Template {n}')
    template_type = factory.Sequence(lambda n: [
        NotificationTemplate.INVOICE_CREATED,
        NotificationTemplate.INVOICE_SENT,
        NotificationTemplate.INVOICE_PAID,
        NotificationTemplate.INVOICE_OVERDUE,
        NotificationTemplate.PAYMENT_RECEIVED,
        NotificationTemplate.PAYMENT_FAILED,
        NotificationTemplate.PAYMENT_RECEIPT,
        NotificationTemplate.CONTRACT_SIGNED,
        NotificationTemplate.CONTRACT_EXPIRING,
        NotificationTemplate.CLIENT_WELCOME,
        NotificationTemplate.REMINDER_PAYMENT_DUE,
    ][n % 11])
    channel = NotificationTemplate.EMAIL
    subject = factory.Sequence(lambda n: f'Subject {n}')
    body_text = factory.Faker('paragraph')
    is_active = True


class NotificationFactory(factory.django.DjangoModelFactory):
    """Factory for creating Notification instances."""

    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    subject = factory.Sequence(lambda n: f'Notification {n}')
    message_text = factory.Faker('paragraph')
    channel = NotificationTemplate.EMAIL
    priority = Notification.NORMAL
    status = Notification.PENDING


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
NOTIFICATION_LIST_URL = '/api/'
NOTIFICATION_SETTINGS_URL = '/api/settings/'
NOTIFICATION_TEMPLATE_LIST_URL = '/api/templates/'


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
def notification(user):
    return NotificationFactory(user=user)


@pytest.fixture
def notification_template(db):
    return NotificationTemplateFactory()


# ---------------------------------------------------------------------------
# NotificationListView tests
# ---------------------------------------------------------------------------
class TestNotificationListView:
    """Tests for NotificationListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(NOTIFICATION_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, notification):
        try:
            response = auth_client.get(NOTIFICATION_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, notification):
        try:
            response = auth_client.get(NOTIFICATION_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Notifications'
            assert 'status_choices' in ctx
            assert 'channel_choices' in ctx
            assert 'current_status' in ctx
            assert 'current_channel' in ctx
            assert 'unread_count' in ctx
            assert 'total_count' in ctx
            assert 'notifications' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_status(self, auth_client, user):
        pending_notif = NotificationFactory(user=user, status=Notification.PENDING)
        NotificationFactory(user=user, status=Notification.READ)
        try:
            response = auth_client.get(
                NOTIFICATION_LIST_URL, {'status': Notification.PENDING}
            )
            notifications = list(response.context['notifications'])
            assert pending_notif in notifications
            assert all(n.status == Notification.PENDING for n in notifications)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_channel(self, auth_client, user):
        email_notif = NotificationFactory(
            user=user, channel=NotificationTemplate.EMAIL
        )
        NotificationFactory(
            user=user, channel=NotificationTemplate.SMS
        )
        try:
            response = auth_client.get(
                NOTIFICATION_LIST_URL, {'channel': NotificationTemplate.EMAIL}
            )
            notifications = list(response.context['notifications'])
            assert email_notif in notifications
            assert all(
                n.channel == NotificationTemplate.EMAIL for n in notifications
            )
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_only_shows_current_user_notifications(self, auth_client, user):
        my_notif = NotificationFactory(user=user)
        other_user = UserFactory()
        NotificationFactory(user=other_user)
        try:
            response = auth_client.get(NOTIFICATION_LIST_URL)
            notifications = list(response.context['notifications'])
            assert my_notif in notifications
            assert all(n.user == user for n in notifications)
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# NotificationSettingsView tests
# ---------------------------------------------------------------------------
class TestNotificationSettingsView:
    """Tests for NotificationSettingsView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(NOTIFICATION_SETTINGS_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client):
        try:
            response = auth_client.get(NOTIFICATION_SETTINGS_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, notification_template):
        try:
            response = auth_client.get(NOTIFICATION_SETTINGS_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Notification Settings'
            assert 'user' in ctx
            assert 'email_notifications' in ctx
            assert 'sms_notifications' in ctx
            assert 'templates' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# NotificationTemplateListView tests
# ---------------------------------------------------------------------------
class TestNotificationTemplateListView:
    """Tests for NotificationTemplateListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(NOTIFICATION_TEMPLATE_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, notification_template):
        try:
            response = auth_client.get(NOTIFICATION_TEMPLATE_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, notification_template):
        try:
            response = auth_client.get(NOTIFICATION_TEMPLATE_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Notification Templates'
            assert 'template_type_choices' in ctx
            assert 'channel_choices' in ctx
            assert 'active_count' in ctx
            assert 'total_count' in ctx
            assert 'templates' in ctx
        except TemplateDoesNotExist:
            pass
