"""
Tests for PortalMessage model and PortalMessageViewSet.

Tests cover:
- PortalMessage model: __str__, mark_as_read(), reply threading, defaults, ordering
- PortalMessageViewSet: list, create, retrieve, mark_read action, unread_count action
- Authorization: unauthenticated access, non-staff filtered access
"""

import pytest
import uuid
from django.utils import timezone
from rest_framework import status

from apps.clients.models import PortalMessage


# ============================================================================
# PortalMessage Model Tests
# ============================================================================


@pytest.mark.django_db
class TestPortalMessageModel:
    """Tests for PortalMessage model."""

    def test_str_representation(self, admin_user, client_company):
        """Test __str__ includes subject and client."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Hello from staff',
            content='Welcome to the portal!',
        )
        result = str(msg)
        assert 'Hello from staff' in result
        assert str(client_company) in result

    def test_mark_as_read(self, admin_user, client_company):
        """Test mark_as_read sets is_read and read_at."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Test Message',
            content='Test content',
        )
        assert msg.is_read is False
        assert msg.read_at is None
        msg.mark_as_read()
        msg.refresh_from_db()
        assert msg.is_read is True
        assert msg.read_at is not None

    def test_mark_as_read_idempotent(self, admin_user, client_company):
        """Test calling mark_as_read twice does not update read_at."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Test',
            content='Content',
        )
        msg.mark_as_read()
        first_read_at = msg.read_at
        msg.mark_as_read()
        msg.refresh_from_db()
        assert msg.read_at == first_read_at

    def test_is_from_client_default(self, admin_user, client_company):
        """Test is_from_client defaults to False."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Staff Message',
            content='Content',
        )
        assert msg.is_from_client is False

    def test_is_from_client_true(self, admin_user, client_company):
        """Test is_from_client can be set to True."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Client Message',
            content='Content',
            is_from_client=True,
        )
        assert msg.is_from_client is True

    def test_is_read_default(self, admin_user, client_company):
        """Test is_read defaults to False."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Unread Message',
            content='Content',
        )
        assert msg.is_read is False
        assert msg.read_at is None

    def test_reply_threading(self, admin_user, client_company):
        """Test parent/reply relationship for threaded messages."""
        parent = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Original',
            content='Original content',
        )
        reply = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Re: Original',
            content='Reply content',
            parent=parent,
        )
        assert reply.parent == parent
        assert parent.replies.count() == 1
        assert parent.replies.first() == reply

    def test_multiple_replies(self, admin_user, client_company):
        """Test a parent message can have multiple replies."""
        parent = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Discussion Thread',
            content='Starting a discussion.',
        )
        reply1 = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Re: Discussion Thread',
            content='First reply.',
            parent=parent,
        )
        reply2 = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Re: Discussion Thread',
            content='Second reply.',
            parent=parent,
        )
        assert parent.replies.count() == 2
        reply_ids = set(parent.replies.values_list('id', flat=True))
        assert reply1.id in reply_ids
        assert reply2.id in reply_ids

    def test_ordering(self, admin_user, client_company):
        """Test messages are ordered by -created_at (most recent first)."""
        msg1 = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='First',
            content='First message',
        )
        msg2 = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Second',
            content='Second message',
        )
        messages = list(PortalMessage.objects.filter(client=client_company))
        assert messages[0] == msg2  # Most recent first

    def test_cascade_delete_client(self, admin_user, client_company):
        """Test deleting client cascades to portal messages."""
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Test',
            content='Content',
        )
        client_id = client_company.id
        client_company.delete()
        assert PortalMessage.objects.filter(client_id=client_id).count() == 0

    def test_parent_set_null_on_delete(self, admin_user, client_company):
        """Test deleting parent message sets child parent to null."""
        parent = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Parent',
            content='Parent content',
        )
        reply = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Reply',
            content='Reply content',
            parent=parent,
        )
        parent.delete()
        reply.refresh_from_db()
        assert reply.parent is None


# ============================================================================
# PortalMessageViewSet Tests
# ============================================================================


@pytest.mark.django_db
class TestPortalMessageViewSet:
    """Tests for PortalMessageViewSet API."""

    def test_list_messages(self, authenticated_admin_client, admin_user, client_company):
        """Test listing portal messages returns 200."""
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Test',
            content='Content',
        )
        response = authenticated_admin_client.get('/api/api/portal-messages/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_unauthenticated(self, api_client):
        """Test unauthenticated access is denied."""
        response = api_client.get('/api/api/portal-messages/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_message(self, authenticated_admin_client, admin_user, client_company):
        """Test creating a portal message."""
        data = {
            'client': str(client_company.id),
            'subject': 'New Message',
            'content': 'Message content here',
        }
        response = authenticated_admin_client.post(
            '/api/api/portal-messages/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['subject'] == 'New Message'
        assert response.data['content'] == 'Message content here'
        # Sender should be set automatically via perform_create
        assert response.data['sender'] is not None

    def test_create_message_sets_sender(self, authenticated_admin_client, admin_user, client_company):
        """Test that perform_create sets the sender to the current user."""
        data = {
            'client': str(client_company.id),
            'subject': 'Sender Test',
            'content': 'Testing sender assignment.',
        }
        response = authenticated_admin_client.post(
            '/api/api/portal-messages/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        msg = PortalMessage.objects.get(id=response.data['id'])
        assert msg.sender == admin_user

    def test_create_reply_to_parent(self, authenticated_admin_client, admin_user, client_company):
        """Test creating a reply linked to a parent message."""
        parent = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Original Thread',
            content='Starting a thread.',
        )
        data = {
            'client': str(client_company.id),
            'subject': 'Re: Original Thread',
            'content': 'This is a reply.',
            'parent': str(parent.id),
        }
        response = authenticated_admin_client.post(
            '/api/api/portal-messages/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['parent'] == str(parent.id)

    def test_retrieve_message(self, authenticated_admin_client, admin_user, client_company):
        """Test retrieving a single portal message."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Retrieve Test',
            content='Content',
        )
        response = authenticated_admin_client.get(f'/api/api/portal-messages/{msg.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'Retrieve Test'
        assert 'sender_name' in response.data
        assert 'replies_count' in response.data

    def test_retrieve_nonexistent_message(self, authenticated_admin_client):
        """Test retrieving a nonexistent message returns 404."""
        fake_id = uuid.uuid4()
        response = authenticated_admin_client.get(f'/api/api/portal-messages/{fake_id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_read_action(self, authenticated_admin_client, admin_user, client_company):
        """Test mark_read action marks a message as read."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Unread',
            content='Mark me as read.',
        )
        assert msg.is_read is False

        response = authenticated_admin_client.post(
            f'/api/api/portal-messages/{msg.id}/mark_read/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_read'] is True
        assert response.data['read_at'] is not None

    def test_mark_read_already_read(self, authenticated_admin_client, admin_user, client_company):
        """Test mark_read on already-read message is idempotent."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Already Read',
            content='Already read message.',
            is_read=True,
            read_at=timezone.now(),
        )
        response = authenticated_admin_client.post(
            f'/api/api/portal-messages/{msg.id}/mark_read/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_read'] is True

    def test_unread_count_action(self, authenticated_admin_client, admin_user, client_company):
        """Test unread_count returns count of unread messages not sent by current user."""
        # Create a message from another user (simulate by directly setting sender)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@test.com',
            password='SecurePass123!',
            first_name='Other',
            last_name='User',
            is_active=True,
        )

        # Unread message from another user
        PortalMessage.objects.create(
            client=client_company,
            sender=other_user,
            subject='From Other',
            content='Unread from other.',
            is_read=False,
        )
        # Read message from another user (should not count)
        PortalMessage.objects.create(
            client=client_company,
            sender=other_user,
            subject='Read From Other',
            content='Already read.',
            is_read=True,
            read_at=timezone.now(),
        )
        # Unread message from self (should not count)
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='From Self',
            content='Unread from self.',
            is_read=False,
        )

        response = authenticated_admin_client.get('/api/api/portal-messages/unread_count/')
        assert response.status_code == status.HTTP_200_OK
        assert 'unread_count' in response.data
        assert response.data['unread_count'] >= 1

    def test_unread_count_empty(self, authenticated_admin_client, admin_user, client_company):
        """Test unread_count returns 0 when all messages are read or from self."""
        # Only a message from self
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Self Message',
            content='Message from self.',
            is_read=False,
        )
        response = authenticated_admin_client.get('/api/api/portal-messages/unread_count/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['unread_count'] == 0

    def test_filter_by_client(self, authenticated_admin_client, admin_user, client_company):
        """Test filtering messages by client."""
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Filtered',
            content='Content',
        )
        response = authenticated_admin_client.get(
            f'/api/api/portal-messages/?client={client_company.id}'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_is_read(self, authenticated_admin_client, admin_user, client_company):
        """Test filtering messages by is_read."""
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Unread Msg',
            content='Unread content',
            is_read=False,
        )
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Read Msg',
            content='Read content',
            is_read=True,
            read_at=timezone.now(),
        )
        response = authenticated_admin_client.get(
            '/api/api/portal-messages/?is_read=false'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_is_from_client(self, authenticated_admin_client, admin_user, client_company):
        """Test filtering messages by is_from_client."""
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Staff Msg',
            content='From staff',
            is_from_client=False,
        )
        response = authenticated_admin_client.get(
            '/api/api/portal-messages/?is_from_client=false'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_search_by_subject(self, authenticated_admin_client, admin_user, client_company):
        """Test searching messages by subject."""
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='UniqueSubjectXYZ',
            content='Content',
        )
        response = authenticated_admin_client.get(
            '/api/api/portal-messages/?search=UniqueSubjectXYZ'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_search_by_content(self, authenticated_admin_client, admin_user, client_company):
        """Test searching messages by content."""
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Content Search',
            content='UniqueContentABC123',
        )
        response = authenticated_admin_client.get(
            '/api/api/portal-messages/?search=UniqueContentABC123'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_message(self, authenticated_admin_client, admin_user, client_company):
        """Test updating a portal message."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Original Subject',
            content='Original content.',
        )
        response = authenticated_admin_client.patch(
            f'/api/api/portal-messages/{msg.id}/',
            {'subject': 'Updated Subject'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'Updated Subject'

    def test_delete_message(self, authenticated_admin_client, admin_user, client_company):
        """Test deleting a portal message."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Delete Me',
            content='Content to delete.',
        )
        response = authenticated_admin_client.delete(
            f'/api/api/portal-messages/{msg.id}/'
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PortalMessage.objects.filter(id=msg.id).exists()

    def test_non_staff_filtered_access(
        self, authenticated_contributor_client, admin_user, client_company
    ):
        """Test non-staff users have filtered access to portal messages."""
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Filtered Msg',
            content='Should be filtered.',
        )
        response = authenticated_contributor_client.get('/api/api/portal-messages/')
        assert response.status_code == status.HTTP_200_OK

    def test_serializer_includes_sender_name(
        self, authenticated_admin_client, admin_user, client_company
    ):
        """Test response includes sender_name computed field."""
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Sender Name Test',
            content='Testing sender name.',
        )
        response = authenticated_admin_client.get(f'/api/api/portal-messages/{msg.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'sender_name' in response.data
        expected_name = admin_user.get_full_name()
        assert response.data['sender_name'] == expected_name

    def test_serializer_includes_replies_count(
        self, authenticated_admin_client, admin_user, client_company
    ):
        """Test response includes replies_count computed field."""
        parent = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Parent Msg',
            content='Has replies.',
        )
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Reply 1',
            content='First reply.',
            parent=parent,
        )
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Reply 2',
            content='Second reply.',
            parent=parent,
        )
        response = authenticated_admin_client.get(f'/api/api/portal-messages/{parent.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['replies_count'] == 2
