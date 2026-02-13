"""
Tests for notifications views_api.py -- NotificationViewSet.

Targets the uncovered lines (29-58) in views_api.py:
- get_queryset (non-staff filtering)
- mark_read action
- mark_all_read action
- unread_count action

Uses pytest + DRF APIClient, relying on fixtures from the root conftest.
"""

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.notifications.models import Notification, NotificationTemplate


# ---------------------------------------------------------------------------
# URL helpers -- router registers at  api/ -> notifications/
# Full path: /api/api/notifications/  (the include is at 'api/')
# ---------------------------------------------------------------------------

NOTIFICATIONS_LIST_URL = '/api/api/notifications/'


def _detail_url(pk):
    return f'{NOTIFICATIONS_LIST_URL}{pk}/'


def _mark_read_url(pk):
    return f'{NOTIFICATIONS_LIST_URL}{pk}/mark_read/'


MARK_ALL_READ_URL = f'{NOTIFICATIONS_LIST_URL}mark_all_read/'
UNREAD_COUNT_URL = f'{NOTIFICATIONS_LIST_URL}unread_count/'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_notification(user=None, email='', notification_status=Notification.PENDING, **kwargs):
    """Create a Notification for testing."""
    defaults = {
        'subject': 'Test notification',
        'message_text': 'Test message body.',
        'channel': NotificationTemplate.EMAIL,
        'priority': Notification.NORMAL,
        'status': notification_status,
    }
    if user:
        defaults['user'] = user
    if email:
        defaults['email'] = email
    defaults.update(kwargs)
    return Notification.objects.create(**defaults)


# ---------------------------------------------------------------------------
# get_queryset -- non-staff users only see their own notifications
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNotificationGetQueryset:
    """get_queryset filters to the requesting user when non-staff."""

    def test_non_staff_sees_only_own_notifications(self, api_client, contributor_user):
        """A non-staff user should see only notifications assigned to them or matching their email."""
        api_client.force_authenticate(user=contributor_user)

        # Notification assigned to this user
        own = _create_notification(user=contributor_user)
        # Notification matching email but no user FK
        by_email = _create_notification(email=contributor_user.email)
        # Notification belonging to someone else
        _create_notification(email='other@example.com')

        response = api_client.get(NOTIFICATIONS_LIST_URL)

        assert response.status_code == status.HTTP_200_OK
        returned_ids = {str(n['id']) for n in response.data['results']}
        assert str(own.pk) in returned_ids
        assert str(by_email.pk) in returned_ids
        assert len(returned_ids) == 2

    def test_staff_sees_all_notifications(self, authenticated_admin_client):
        """A staff user should see all notifications."""
        n1 = _create_notification(email='a@example.com')
        n2 = _create_notification(email='b@example.com')

        response = authenticated_admin_client.get(NOTIFICATIONS_LIST_URL)

        assert response.status_code == status.HTTP_200_OK
        returned_ids = {str(n['id']) for n in response.data['results']}
        assert str(n1.pk) in returned_ids
        assert str(n2.pk) in returned_ids

    def test_unauthenticated_rejected(self, api_client):
        """Unauthenticated requests are denied."""
        response = api_client.get(NOTIFICATIONS_LIST_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ---------------------------------------------------------------------------
# mark_read action (POST /notifications/<pk>/mark_read/)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNotificationMarkRead:
    """Tests for the mark_read detail action."""

    def test_mark_read_success(self, api_client, contributor_user):
        """POST mark_read transitions the notification to READ status."""
        api_client.force_authenticate(user=contributor_user)
        notification = _create_notification(
            user=contributor_user,
            notification_status=Notification.SENT,
        )

        response = api_client.post(_mark_read_url(notification.pk))

        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.status == Notification.READ
        assert notification.read_at is not None

    def test_mark_read_already_read(self, api_client, contributor_user):
        """Marking an already-read notification is idempotent."""
        api_client.force_authenticate(user=contributor_user)
        notification = _create_notification(
            user=contributor_user,
            notification_status=Notification.READ,
        )
        notification.read_at = timezone.now()
        notification.save()

        response = api_client.post(_mark_read_url(notification.pk))

        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.status == Notification.READ

    def test_mark_read_other_users_notification_404(self, api_client, contributor_user):
        """Non-staff users cannot mark another user's notification as read."""
        api_client.force_authenticate(user=contributor_user)
        other_notification = _create_notification(email='someone@else.com')

        response = api_client.post(_mark_read_url(other_notification.pk))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_read_unauthenticated(self, api_client):
        """Unauthenticated requests are denied."""
        notification = _create_notification(email='test@example.com')
        response = api_client.post(_mark_read_url(notification.pk))
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ---------------------------------------------------------------------------
# mark_all_read action (POST /notifications/mark_all_read/)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNotificationMarkAllRead:
    """Tests for the mark_all_read list action."""

    def test_mark_all_read_success(self, api_client, contributor_user):
        """POST mark_all_read updates all non-read notifications."""
        api_client.force_authenticate(user=contributor_user)
        _create_notification(user=contributor_user, notification_status=Notification.PENDING)
        _create_notification(user=contributor_user, notification_status=Notification.SENT)
        _create_notification(user=contributor_user, notification_status=Notification.READ)

        response = api_client.post(MARK_ALL_READ_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['marked_read'] == 2

        # Verify in the database
        unread = Notification.objects.filter(
            user=contributor_user,
        ).exclude(status=Notification.READ).count()
        assert unread == 0

    def test_mark_all_read_none_unread(self, api_client, contributor_user):
        """When there are no unread notifications, marked_read is 0."""
        api_client.force_authenticate(user=contributor_user)
        _create_notification(user=contributor_user, notification_status=Notification.READ)

        response = api_client.post(MARK_ALL_READ_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['marked_read'] == 0

    def test_mark_all_read_scoped_to_user(self, api_client, contributor_user):
        """mark_all_read only affects the requesting user's notifications."""
        api_client.force_authenticate(user=contributor_user)
        _create_notification(user=contributor_user, notification_status=Notification.PENDING)
        other = _create_notification(email='other@example.com', notification_status=Notification.PENDING)

        api_client.post(MARK_ALL_READ_URL)

        other.refresh_from_db()
        assert other.status == Notification.PENDING  # unaffected

    def test_mark_all_read_unauthenticated(self, api_client):
        """Unauthenticated requests are denied."""
        response = api_client.post(MARK_ALL_READ_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ---------------------------------------------------------------------------
# unread_count action (GET /notifications/unread_count/)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNotificationUnreadCount:
    """Tests for the unread_count list action."""

    def test_unread_count_returns_correct_number(self, api_client, contributor_user):
        """GET unread_count returns the count of non-read notifications."""
        api_client.force_authenticate(user=contributor_user)
        _create_notification(user=contributor_user, notification_status=Notification.PENDING)
        _create_notification(user=contributor_user, notification_status=Notification.SENT)
        _create_notification(user=contributor_user, notification_status=Notification.READ)

        response = api_client.get(UNREAD_COUNT_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['unread_count'] == 2

    def test_unread_count_zero_when_all_read(self, api_client, contributor_user):
        """Returns 0 when every notification is already read."""
        api_client.force_authenticate(user=contributor_user)
        _create_notification(user=contributor_user, notification_status=Notification.READ)

        response = api_client.get(UNREAD_COUNT_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['unread_count'] == 0

    def test_unread_count_zero_when_empty(self, api_client, contributor_user):
        """Returns 0 when the user has no notifications at all."""
        api_client.force_authenticate(user=contributor_user)

        response = api_client.get(UNREAD_COUNT_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['unread_count'] == 0

    def test_unread_count_scoped_to_user(self, api_client, contributor_user):
        """Count excludes notifications belonging to other users."""
        api_client.force_authenticate(user=contributor_user)
        _create_notification(user=contributor_user, notification_status=Notification.PENDING)
        _create_notification(email='other@example.com', notification_status=Notification.PENDING)

        response = api_client.get(UNREAD_COUNT_URL)

        assert response.status_code == status.HTTP_200_OK
        # Only the user's own notification counts
        assert response.data['unread_count'] == 1

    def test_unread_count_unauthenticated(self, api_client):
        """Unauthenticated requests are denied."""
        response = api_client.get(UNREAD_COUNT_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
