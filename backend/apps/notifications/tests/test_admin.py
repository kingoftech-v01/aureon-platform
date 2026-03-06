"""Tests for notifications admin configuration."""

import uuid
import pytest
from unittest.mock import MagicMock, patch
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from apps.notifications.models import NotificationTemplate, Notification
from apps.notifications.admin import NotificationTemplateAdmin, NotificationAdmin


def _make_request(method='post'):
    """Create a request with messages middleware support."""
    factory = RequestFactory()
    request = factory.post('/') if method == 'post' else factory.get('/')
    request.user = MagicMock()
    request.session = SessionStore()
    request._messages = FallbackStorage(request)
    return request


@pytest.mark.django_db
class TestNotificationTemplateAdmin:
    """Tests for NotificationTemplateAdmin."""

    @pytest.fixture
    def template_admin(self):
        """Create a NotificationTemplateAdmin instance."""
        site = AdminSite()
        return NotificationTemplateAdmin(NotificationTemplate, site)

    @pytest.fixture
    def template(self):
        """Create a notification template."""
        return NotificationTemplate.objects.create(
            name='Test Template',
            template_type=NotificationTemplate.INVOICE_CREATED,
            channel=NotificationTemplate.EMAIL,
            subject='Test Subject',
            body_text='Test body',
            body_html='<p>Test</p>',
            is_active=True,
            send_to_client=True,
            send_to_owner=False,
        )

    def test_registered_with_admin(self):
        """Test that NotificationTemplate is registered with admin site."""
        assert NotificationTemplate in admin.site._registry

    def test_list_display(self, template_admin):
        """Test list_display configuration."""
        expected = [
            'name', 'template_type', 'channel_badge', 'is_active',
            'send_to_client', 'send_to_owner', 'updated_at',
        ]
        assert template_admin.list_display == expected

    def test_list_filter(self, template_admin):
        """Test list_filter configuration."""
        assert 'channel' in template_admin.list_filter
        assert 'is_active' in template_admin.list_filter
        assert 'template_type' in template_admin.list_filter

    def test_search_fields(self, template_admin):
        """Test search_fields configuration."""
        assert 'name' in template_admin.search_fields
        assert 'template_type' in template_admin.search_fields
        assert 'subject' in template_admin.search_fields
        assert 'body_text' in template_admin.search_fields

    def test_readonly_fields(self, template_admin):
        """Test readonly_fields configuration."""
        assert 'id' in template_admin.readonly_fields
        assert 'created_at' in template_admin.readonly_fields
        assert 'updated_at' in template_admin.readonly_fields
        assert 'preview_html' in template_admin.readonly_fields

    def test_channel_badge_email(self, template_admin, template):
        """Test channel_badge for email channel."""
        result = template_admin.channel_badge(template)
        assert 'Email' in result
        assert '#3B82F6' in result

    def test_channel_badge_sms(self, template_admin):
        """Test channel_badge for SMS channel."""
        template = NotificationTemplate.objects.create(
            name='SMS Template',
            template_type=NotificationTemplate.INVOICE_SENT,
            channel=NotificationTemplate.SMS,
            body_text='Test',
        )
        result = template_admin.channel_badge(template)
        assert 'SMS' in result
        assert '#10B981' in result

    def test_channel_badge_in_app(self, template_admin):
        """Test channel_badge for in-app channel."""
        template = NotificationTemplate.objects.create(
            name='In-App Template',
            template_type=NotificationTemplate.PAYMENT_RECEIPT,
            channel=NotificationTemplate.IN_APP,
            body_text='Test',
        )
        result = template_admin.channel_badge(template)
        assert 'In-App Notification' in result
        assert '#F59E0B' in result

    def test_channel_badge_unknown(self, template_admin):
        """Test channel_badge for unknown channel falls back to gray."""
        template = MagicMock()
        template.channel = 'unknown'
        template.get_channel_display.return_value = 'Unknown'
        result = template_admin.channel_badge(template)
        assert '#6B7280' in result

    def test_preview_html_with_content(self, template_admin, template):
        """Test preview_html with HTML content."""
        result = template_admin.preview_html(template)
        assert '<p>Test</p>' in result

    def test_preview_html_without_content(self, template_admin):
        """Test preview_html without HTML content."""
        template = NotificationTemplate.objects.create(
            name='No HTML Template',
            template_type=NotificationTemplate.PAYMENT_RECEIVED,
            body_text='Test',
            body_html='',
        )
        result = template_admin.preview_html(template)
        assert result == '-'

    def test_duplicate_template_action(self, template_admin, template):
        """Test duplicate_template admin action."""
        request = _make_request()
        queryset = NotificationTemplate.objects.filter(pk=template.pk)

        template_admin.duplicate_template(request, queryset)

        assert NotificationTemplate.objects.count() == 2
        copy = NotificationTemplate.objects.exclude(pk=template.pk).first()
        assert '(Copy)' in copy.name

    def test_activate_templates_action(self, template_admin):
        """Test activate_templates admin action."""
        template = NotificationTemplate.objects.create(
            name='Inactive Template',
            template_type=NotificationTemplate.CLIENT_WELCOME,
            body_text='Test',
            is_active=False,
        )
        request = _make_request()
        queryset = NotificationTemplate.objects.filter(pk=template.pk)

        template_admin.activate_templates(request, queryset)

        template.refresh_from_db()
        assert template.is_active is True

    def test_deactivate_templates_action(self, template_admin, template):
        """Test deactivate_templates admin action."""
        request = _make_request()
        queryset = NotificationTemplate.objects.filter(pk=template.pk)

        template_admin.deactivate_templates(request, queryset)

        template.refresh_from_db()
        assert template.is_active is False

    def test_fieldsets_defined(self, template_admin):
        """Test that fieldsets are properly defined."""
        assert template_admin.fieldsets is not None
        fieldset_names = [fs[0] for fs in template_admin.fieldsets]
        assert 'Template Information' in fieldset_names
        assert 'Content' in fieldset_names
        assert 'Configuration' in fieldset_names
        assert 'Template Variables' in fieldset_names
        assert 'Timestamps' in fieldset_names

    def test_actions_defined(self, template_admin):
        """Test that admin actions are defined."""
        assert 'duplicate_template' in template_admin.actions
        assert 'activate_templates' in template_admin.actions
        assert 'deactivate_templates' in template_admin.actions


@pytest.mark.django_db
class TestNotificationAdmin:
    """Tests for NotificationAdmin."""

    @pytest.fixture
    def notification_admin(self):
        """Create a NotificationAdmin instance."""
        site = AdminSite()
        return NotificationAdmin(Notification, site)

    @pytest.fixture
    def notification(self):
        """Create a notification."""
        return Notification.objects.create(
            email='test@example.com',
            subject='Test Subject That Is Quite Long And Might Need Truncation In Some Views',
            message_text='Test body text',
            message_html='<p>Test html</p>',
            channel=NotificationTemplate.EMAIL,
            status=Notification.PENDING,
            priority=Notification.NORMAL,
        )

    def test_registered_with_admin(self):
        """Test that Notification is registered with admin site."""
        assert Notification in admin.site._registry

    def test_list_display(self, notification_admin):
        """Test list_display configuration."""
        expected = [
            'id_short', 'recipient', 'subject_short', 'channel_badge',
            'status_badge', 'priority', 'created_at', 'sent_at',
        ]
        assert notification_admin.list_display == expected

    def test_list_filter(self, notification_admin):
        """Test list_filter configuration."""
        assert 'channel' in notification_admin.list_filter
        assert 'status' in notification_admin.list_filter
        assert 'priority' in notification_admin.list_filter

    def test_search_fields(self, notification_admin):
        """Test search_fields configuration."""
        assert 'subject' in notification_admin.search_fields
        assert 'email' in notification_admin.search_fields
        assert 'user__email' in notification_admin.search_fields

    def test_id_short(self, notification_admin, notification):
        """Test id_short method."""
        result = notification_admin.id_short(notification)
        assert len(result) == 8
        assert result == str(notification.id)[:8]

    def test_subject_short_truncation(self, notification_admin, notification):
        """Test subject_short truncates long subjects."""
        result = notification_admin.subject_short(notification)
        assert len(result) <= 53  # 50 + '...'
        assert result.endswith('...')

    def test_subject_short_no_truncation(self, notification_admin):
        """Test subject_short does not truncate short subjects."""
        notification = Notification.objects.create(
            email='test@example.com',
            subject='Short',
            message_text='Test',
        )
        result = notification_admin.subject_short(notification)
        assert result == 'Short'

    def test_channel_badge_email(self, notification_admin, notification):
        """Test channel_badge for email."""
        result = notification_admin.channel_badge(notification)
        assert 'Email' in result
        assert '#3B82F6' in result

    def test_channel_badge_sms(self, notification_admin):
        """Test channel_badge for SMS."""
        notification = Notification.objects.create(
            email='test@example.com',
            subject='SMS Test',
            message_text='Test',
            channel=NotificationTemplate.SMS,
        )
        result = notification_admin.channel_badge(notification)
        assert 'SMS' in result
        assert '#10B981' in result

    def test_channel_badge_in_app(self, notification_admin):
        """Test channel_badge for in-app."""
        notification = Notification.objects.create(
            email='test@example.com',
            subject='In-App Test',
            message_text='Test',
            channel=NotificationTemplate.IN_APP,
        )
        result = notification_admin.channel_badge(notification)
        assert 'In-App Notification' in result
        assert '#F59E0B' in result

    def test_channel_badge_unknown(self, notification_admin):
        """Test channel_badge for unknown channel."""
        notification = MagicMock()
        notification.channel = 'unknown'
        notification.get_channel_display.return_value = 'Unknown'
        result = notification_admin.channel_badge(notification)
        assert '#6B7280' in result

    def test_status_badge_pending(self, notification_admin, notification):
        """Test status_badge for pending status."""
        result = notification_admin.status_badge(notification)
        assert 'Pending' in result
        assert '#6B7280' in result

    def test_status_badge_sent(self, notification_admin):
        """Test status_badge for sent status."""
        notification = Notification.objects.create(
            email='test@example.com',
            subject='Sent',
            message_text='Test',
            status=Notification.SENT,
        )
        result = notification_admin.status_badge(notification)
        assert 'Sent' in result
        assert '#3B82F6' in result

    def test_status_badge_delivered(self, notification_admin):
        """Test status_badge for delivered status."""
        notification = Notification.objects.create(
            email='test@example.com',
            subject='Delivered',
            message_text='Test',
            status=Notification.DELIVERED,
        )
        result = notification_admin.status_badge(notification)
        assert 'Delivered' in result
        assert '#10B981' in result

    def test_status_badge_failed(self, notification_admin):
        """Test status_badge for failed status."""
        notification = Notification.objects.create(
            email='test@example.com',
            subject='Failed',
            message_text='Test',
            status=Notification.FAILED,
        )
        result = notification_admin.status_badge(notification)
        assert 'Failed' in result
        assert '#EF4444' in result

    def test_status_badge_read(self, notification_admin):
        """Test status_badge for read status."""
        notification = Notification.objects.create(
            email='test@example.com',
            subject='Read',
            message_text='Test',
            status=Notification.READ,
        )
        result = notification_admin.status_badge(notification)
        assert 'Read' in result
        assert '#8B5CF6' in result

    def test_status_badge_unknown(self, notification_admin):
        """Test status_badge for unknown status."""
        notification = MagicMock()
        notification.status = 'unknown'
        notification.get_status_display.return_value = 'Unknown'
        result = notification_admin.status_badge(notification)
        assert '#6B7280' in result

    def test_message_text_display(self, notification_admin, notification):
        """Test message_text_display method."""
        result = notification_admin.message_text_display(notification)
        assert 'Test body text' in result
        assert '<pre' in result

    def test_message_html_display_with_content(self, notification_admin, notification):
        """Test message_html_display with HTML content."""
        result = notification_admin.message_html_display(notification)
        assert '<p>Test html</p>' in result

    def test_message_html_display_without_content(self, notification_admin):
        """Test message_html_display without HTML content."""
        notification = Notification.objects.create(
            email='test@example.com',
            subject='No HTML',
            message_text='Test',
            message_html='',
        )
        result = notification_admin.message_html_display(notification)
        assert result == '-'

    @patch('apps.notifications.tasks.send_notification_async')
    def test_resend_notifications_action(self, mock_task, notification_admin):
        """Test resend_notifications admin action."""
        failed = Notification.objects.create(
            email='test@example.com',
            subject='Failed',
            message_text='Test',
            status=Notification.FAILED,
        )
        pending = Notification.objects.create(
            email='test@example.com',
            subject='Pending',
            message_text='Test',
            status=Notification.PENDING,
        )
        sent = Notification.objects.create(
            email='test@example.com',
            subject='Sent',
            message_text='Test',
            status=Notification.SENT,
        )
        request = _make_request()
        queryset = Notification.objects.all()

        notification_admin.resend_notifications(request, queryset)

        # Only failed and pending should be queued
        assert mock_task.delay.call_count == 2

    def test_mark_as_read_action(self, notification_admin, notification):
        """Test mark_as_read admin action."""
        request = _make_request()
        queryset = Notification.objects.filter(pk=notification.pk)

        notification_admin.mark_as_read(request, queryset)

        notification.refresh_from_db()
        assert notification.status == Notification.READ
        assert notification.read_at is not None

    def test_fieldsets_defined(self, notification_admin):
        """Test that fieldsets are properly defined."""
        assert notification_admin.fieldsets is not None
        fieldset_names = [fs[0] for fs in notification_admin.fieldsets]
        assert 'Notification Info' in fieldset_names
        assert 'Recipient' in fieldset_names
        assert 'Content' in fieldset_names
        assert 'Delivery Status' in fieldset_names
        assert 'Related Objects' in fieldset_names
        assert 'Metadata' in fieldset_names
        assert 'Timestamps' in fieldset_names

    def test_actions_defined(self, notification_admin):
        """Test that admin actions are defined."""
        assert 'resend_notifications' in notification_admin.actions
        assert 'mark_as_read' in notification_admin.actions

    def test_readonly_fields(self, notification_admin):
        """Test readonly_fields configuration."""
        assert 'id' in notification_admin.readonly_fields
        assert 'status' in notification_admin.readonly_fields
        assert 'sent_at' in notification_admin.readonly_fields
        assert 'created_at' in notification_admin.readonly_fields
