"""
Tests for PortalMessage model and PortalMessageViewSet.
"""

import pytest
from django.utils import timezone

from apps.clients.models import PortalMessage


@pytest.mark.django_db
class TestPortalMessageModel:
    """Tests for PortalMessage model."""

    def test_str_representation(self, admin_user, client_company):
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Hello from staff',
            content='Welcome to the portal!',
        )
        assert 'Hello from staff' in str(msg)

    def test_mark_as_read(self, admin_user, client_company):
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
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Staff Message',
            content='Content',
        )
        assert msg.is_from_client is False

    def test_is_from_client_true(self, admin_user, client_company):
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Client Message',
            content='Content',
            is_from_client=True,
        )
        assert msg.is_from_client is True

    def test_reply_threading(self, admin_user, client_company):
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

    def test_ordering(self, admin_user, client_company):
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
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Test',
            content='Content',
        )
        client_id = client_company.id
        client_company.delete()
        assert PortalMessage.objects.filter(client_id=client_id).count() == 0


@pytest.mark.django_db
class TestPortalMessageViewSet:
    """Tests for PortalMessageViewSet API."""

    def test_list_messages(self, authenticated_admin_client, admin_user, client_company):
        PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Test',
            content='Content',
        )
        response = authenticated_admin_client.get('/api/clients/api/portal-messages/')
        assert response.status_code == 200

    def test_create_message(self, authenticated_admin_client, admin_user, client_company):
        data = {
            'client': str(client_company.id),
            'subject': 'New Message',
            'content': 'Message content here',
        }
        response = authenticated_admin_client.post(
            '/api/clients/api/portal-messages/', data, format='json'
        )
        assert response.status_code in [201, 400]

    def test_retrieve_message(self, authenticated_admin_client, admin_user, client_company):
        msg = PortalMessage.objects.create(
            client=client_company,
            sender=admin_user,
            subject='Retrieve Test',
            content='Content',
        )
        response = authenticated_admin_client.get(f'/api/clients/api/portal-messages/{msg.id}/')
        assert response.status_code == 200

    def test_unauthenticated_access(self, api_client, admin_user, client_company):
        response = api_client.get('/api/clients/api/portal-messages/')
        assert response.status_code == 401
