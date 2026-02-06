"""Tests for notifications models."""

import uuid
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta
from apps.notifications.models import NotificationTemplate, Notification


@pytest.mark.django_db
class TestNotificationTemplate:
    """Tests for the NotificationTemplate model."""

    def _create_template(self, **kwargs):
        """Helper to create a NotificationTemplate."""
        defaults = {
            'name': 'Invoice Created Template',
            'template_type': NotificationTemplate.INVOICE_CREATED,
            'channel': NotificationTemplate.EMAIL,
            'subject': 'Invoice {{invoice_number}} Created',
            'body_text': 'Dear {{client_name}}, invoice {{invoice_number}} has been created.',
            'body_html': '<p>Dear {{client_name}}, invoice {{invoice_number}} has been created.</p>',
            'is_active': True,
            'send_to_client': True,
            'send_to_owner': False,
            'available_variables': ['invoice_number', 'client_name'],
        }
        defaults.update(kwargs)
        return NotificationTemplate.objects.create(**defaults)

    def test_create_template(self):
        """Test creating a notification template."""
        template = self._create_template()
        assert template.pk is not None
        assert isinstance(template.id, uuid.UUID)
        assert template.name == 'Invoice Created Template'
        assert template.template_type == NotificationTemplate.INVOICE_CREATED
        assert template.channel == NotificationTemplate.EMAIL

    def test_str_representation(self):
        """Test string representation of a template."""
        template = self._create_template()
        expected = "Invoice Created Template (Email)"
        assert str(template) == expected

    def test_str_representation_sms(self):
        """Test string representation with SMS channel."""
        template = self._create_template(
            template_type=NotificationTemplate.INVOICE_SENT,
            channel=NotificationTemplate.SMS,
        )
        expected = "Invoice Created Template (SMS)"
        assert str(template) == expected

    def test_str_representation_in_app(self):
        """Test string representation with in-app channel."""
        template = self._create_template(
            template_type=NotificationTemplate.INVOICE_PAID,
            channel=NotificationTemplate.IN_APP,
        )
        expected = "Invoice Created Template (In-App Notification)"
        assert str(template) == expected

    def test_template_type_choices(self):
        """Test that all template types are defined correctly."""
        assert NotificationTemplate.INVOICE_CREATED == 'invoice_created'
        assert NotificationTemplate.INVOICE_SENT == 'invoice_sent'
        assert NotificationTemplate.INVOICE_PAID == 'invoice_paid'
        assert NotificationTemplate.INVOICE_OVERDUE == 'invoice_overdue'
        assert NotificationTemplate.PAYMENT_RECEIVED == 'payment_received'
        assert NotificationTemplate.PAYMENT_FAILED == 'payment_failed'
        assert NotificationTemplate.PAYMENT_RECEIPT == 'payment_receipt'
        assert NotificationTemplate.CONTRACT_SIGNED == 'contract_signed'
        assert NotificationTemplate.CONTRACT_EXPIRING == 'contract_expiring'
        assert NotificationTemplate.CLIENT_WELCOME == 'client_welcome'
        assert NotificationTemplate.REMINDER_PAYMENT_DUE == 'reminder_payment_due'

    def test_channel_choices(self):
        """Test that all channel types are defined correctly."""
        assert NotificationTemplate.EMAIL == 'email'
        assert NotificationTemplate.SMS == 'sms'
        assert NotificationTemplate.IN_APP == 'in_app'

    def test_default_values(self):
        """Test default values on template creation."""
        template = self._create_template()
        assert template.is_active is True
        assert template.send_to_client is True
        assert template.send_to_owner is False
        assert template.channel == NotificationTemplate.EMAIL

    def test_render_basic(self):
        """Test rendering template with basic context."""
        template = self._create_template()
        context = {
            'invoice_number': 'INV-001',
            'client_name': 'John Doe',
        }
        result = template.render(context)
        assert result['subject'] == 'Invoice INV-001 Created'
        assert result['body_text'] == 'Dear John Doe, invoice INV-001 has been created.'
        assert result['body_html'] == '<p>Dear John Doe, invoice INV-001 has been created.</p>'

    def test_render_missing_variable(self):
        """Test rendering template when a variable is missing from context."""
        template = self._create_template()
        context = {
            'invoice_number': 'INV-001',
        }
        result = template.render(context)
        assert result['subject'] == 'Invoice INV-001 Created'
        assert '{{client_name}}' in result['body_text']

    def test_render_empty_context(self):
        """Test rendering template with empty context."""
        template = self._create_template()
        result = template.render({})
        assert '{{invoice_number}}' in result['subject']
        assert '{{client_name}}' in result['body_text']

    def test_render_no_html_body(self):
        """Test rendering template without HTML body."""
        template = self._create_template(body_html='')
        context = {
            'invoice_number': 'INV-001',
            'client_name': 'John Doe',
        }
        result = template.render(context)
        assert result['body_html'] is None

    def test_render_empty_subject(self):
        """Test rendering template with empty subject."""
        template = self._create_template(subject='')
        context = {'invoice_number': 'INV-001'}
        result = template.render(context)
        assert result['subject'] == ''

    def test_render_extra_context_variables(self):
        """Test rendering template with extra context variables not in template."""
        template = self._create_template()
        context = {
            'invoice_number': 'INV-001',
            'client_name': 'John Doe',
            'extra_var': 'should be ignored',
        }
        result = template.render(context)
        assert 'should be ignored' not in result['body_text']
        assert result['body_text'] == 'Dear John Doe, invoice INV-001 has been created.'

    def test_template_type_unique(self):
        """Test template_type field is unique."""
        self._create_template()
        with pytest.raises(Exception):
            self._create_template(name='Duplicate Template')

    def test_available_variables_default(self):
        """Test available_variables defaults to empty list."""
        template = NotificationTemplate.objects.create(
            name='Basic Template',
            template_type=NotificationTemplate.PAYMENT_RECEIPT,
            body_text='Hello',
        )
        assert template.available_variables == []

    def test_meta_ordering(self):
        """Test model ordering by template_type."""
        t2 = self._create_template(
            name='Z template',
            template_type=NotificationTemplate.PAYMENT_RECEIPT,
        )
        t1 = self._create_template(
            name='A template',
            template_type=NotificationTemplate.INVOICE_CREATED,
        )
        templates = list(NotificationTemplate.objects.all())
        assert templates[0].template_type <= templates[-1].template_type

    def test_meta_verbose_names(self):
        """Test meta verbose names."""
        assert NotificationTemplate._meta.verbose_name == 'Notification Template'
        assert NotificationTemplate._meta.verbose_name_plural == 'Notification Templates'

    def test_timestamps_set_automatically(self):
        """Test that created_at and updated_at are set automatically."""
        template = self._create_template()
        assert template.created_at is not None
        assert template.updated_at is not None

    def test_uuid_primary_key(self):
        """Test that id is a UUID."""
        template = self._create_template()
        assert isinstance(template.id, uuid.UUID)
        assert template.pk == template.id


@pytest.mark.django_db
class TestNotification:
    """Tests for the Notification model."""

    @pytest.fixture
    def template(self):
        """Create a notification template for testing."""
        return NotificationTemplate.objects.create(
            name='Test Template',
            template_type=NotificationTemplate.INVOICE_CREATED,
            channel=NotificationTemplate.EMAIL,
            subject='Test Subject',
            body_text='Test body',
        )

    def _create_notification(self, user=None, template=None, **kwargs):
        """Helper to create a Notification."""
        defaults = {
            'email': 'test@example.com',
            'template': template,
            'subject': 'Test Notification',
            'message_text': 'This is a test notification.',
            'message_html': '<p>This is a test notification.</p>',
            'channel': NotificationTemplate.EMAIL,
            'priority': Notification.NORMAL,
            'status': Notification.PENDING,
        }
        if user:
            defaults['user'] = user
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)

    def test_create_notification(self, template):
        """Test creating a notification."""
        notification = self._create_notification(template=template)
        assert notification.pk is not None
        assert isinstance(notification.id, uuid.UUID)
        assert notification.subject == 'Test Notification'

    def test_str_representation_with_user(self, admin_user, template):
        """Test string representation with a user."""
        notification = self._create_notification(user=admin_user, template=template)
        expected = f"Email to {admin_user.email}: Test Notification"
        assert str(notification) == expected

    def test_str_representation_with_email(self, template):
        """Test string representation with email only."""
        notification = self._create_notification(template=template)
        expected = "Email to test@example.com: Test Notification"
        assert str(notification) == expected

    def test_status_choices(self):
        """Test status choice constants."""
        assert Notification.PENDING == 'pending'
        assert Notification.SENT == 'sent'
        assert Notification.DELIVERED == 'delivered'
        assert Notification.FAILED == 'failed'
        assert Notification.READ == 'read'

    def test_priority_choices(self):
        """Test priority choice constants."""
        assert Notification.LOW == 'low'
        assert Notification.NORMAL == 'normal'
        assert Notification.HIGH == 'high'
        assert Notification.URGENT == 'urgent'

    def test_default_values(self, template):
        """Test default values on notification."""
        notification = Notification.objects.create(
            email='test@example.com',
            message_text='Test',
        )
        assert notification.status == Notification.PENDING
        assert notification.priority == Notification.NORMAL
        assert notification.channel == NotificationTemplate.EMAIL
        assert notification.retry_count == 0
        assert notification.metadata == {}

    def test_mark_as_sent(self, template):
        """Test marking notification as sent."""
        notification = self._create_notification(template=template)
        assert notification.status == Notification.PENDING

        notification.mark_as_sent()
        notification.refresh_from_db()

        assert notification.status == Notification.SENT
        assert notification.sent_at is not None

    def test_mark_as_sent_with_external_id(self, template):
        """Test marking notification as sent with external ID."""
        notification = self._create_notification(template=template)
        notification.mark_as_sent(external_id='ext-12345')
        notification.refresh_from_db()

        assert notification.status == Notification.SENT
        assert notification.external_id == 'ext-12345'
        assert notification.sent_at is not None

    def test_mark_as_sent_without_external_id(self, template):
        """Test mark_as_sent preserves empty external_id when not provided."""
        notification = self._create_notification(template=template)
        notification.mark_as_sent()
        notification.refresh_from_db()

        assert notification.status == Notification.SENT
        assert notification.external_id == ''

    def test_mark_as_delivered(self, template):
        """Test marking notification as delivered."""
        notification = self._create_notification(template=template)
        notification.mark_as_delivered()
        notification.refresh_from_db()

        assert notification.status == Notification.DELIVERED
        assert notification.delivered_at is not None

    def test_mark_as_read(self, template):
        """Test marking notification as read."""
        notification = self._create_notification(template=template)
        notification.mark_as_read()
        notification.refresh_from_db()

        assert notification.status == Notification.READ
        assert notification.read_at is not None

    def test_mark_as_failed(self, template):
        """Test marking notification as failed."""
        notification = self._create_notification(template=template)
        notification.mark_as_failed('Connection timeout')
        notification.refresh_from_db()

        assert notification.status == Notification.FAILED
        assert notification.failed_at is not None
        assert notification.error_message == 'Connection timeout'
        assert notification.retry_count == 1

    def test_mark_as_failed_increments_retry_count(self, template):
        """Test that repeated failures increment retry_count."""
        notification = self._create_notification(template=template)
        notification.mark_as_failed('Error 1')
        notification.mark_as_failed('Error 2')
        notification.refresh_from_db()

        assert notification.retry_count == 2
        assert notification.error_message == 'Error 2'

    def test_mark_as_failed_converts_error_to_string(self, template):
        """Test that error message is converted to string."""
        notification = self._create_notification(template=template)
        notification.mark_as_failed(ValueError('Test error'))
        notification.refresh_from_db()

        assert notification.error_message == 'Test error'

    def test_is_read_property_true(self, template):
        """Test is_read property when notification is read."""
        notification = self._create_notification(template=template, status=Notification.READ)
        assert notification.is_read is True

    def test_is_read_property_false(self, template):
        """Test is_read property when notification is not read."""
        notification = self._create_notification(template=template, status=Notification.PENDING)
        assert notification.is_read is False

    def test_is_read_property_sent(self, template):
        """Test is_read property when notification is sent."""
        notification = self._create_notification(template=template, status=Notification.SENT)
        assert notification.is_read is False

    def test_recipient_property_with_user(self, admin_user, template):
        """Test recipient property returns user email."""
        notification = self._create_notification(user=admin_user, template=template)
        assert notification.recipient == admin_user.email

    def test_recipient_property_with_email(self, template):
        """Test recipient property returns email when no user."""
        notification = self._create_notification(template=template, email='client@example.com')
        assert notification.recipient == 'client@example.com'

    def test_recipient_property_with_phone(self, template):
        """Test recipient property returns phone when no user or email."""
        notification = self._create_notification(
            template=template,
            email='',
            phone='+1234567890',
        )
        assert notification.recipient == '+1234567890'

    def test_recipient_property_with_no_contact(self, template):
        """Test recipient property when no contact info."""
        notification = self._create_notification(
            template=template,
            email='',
            phone='',
        )
        assert notification.recipient == ''

    def test_related_invoice(self, template, invoice_paid):
        """Test notification with related invoice."""
        notification = self._create_notification(
            template=template,
            related_invoice=invoice_paid,
        )
        assert notification.related_invoice == invoice_paid

    def test_related_payment(self, template, payment_successful):
        """Test notification with related payment."""
        notification = self._create_notification(
            template=template,
            related_payment=payment_successful,
        )
        assert notification.related_payment == payment_successful

    def test_related_contract(self, template, contract_fixed):
        """Test notification with related contract."""
        notification = self._create_notification(
            template=template,
            related_contract=contract_fixed,
        )
        assert notification.related_contract == contract_fixed

    def test_metadata_field(self, template):
        """Test metadata JSON field."""
        metadata = {'source': 'test', 'version': '1.0'}
        notification = self._create_notification(
            template=template,
            metadata=metadata,
        )
        notification.refresh_from_db()
        assert notification.metadata == metadata

    def test_meta_ordering(self, template):
        """Test model ordering by -created_at."""
        n1 = self._create_notification(template=template, subject='First')
        n2 = self._create_notification(template=template, subject='Second')
        notifications = list(Notification.objects.all())
        assert notifications[0].created_at >= notifications[1].created_at

    def test_meta_verbose_names(self):
        """Test meta verbose names."""
        assert Notification._meta.verbose_name == 'Notification'
        assert Notification._meta.verbose_name_plural == 'Notifications'

    def test_uuid_primary_key(self, template):
        """Test that id is a UUID."""
        notification = self._create_notification(template=template)
        assert isinstance(notification.id, uuid.UUID)

    def test_timestamps_set_automatically(self, template):
        """Test that timestamps are set automatically."""
        notification = self._create_notification(template=template)
        assert notification.created_at is not None
        assert notification.updated_at is not None

    def test_channel_sms(self, template):
        """Test notification with SMS channel."""
        notification = self._create_notification(
            template=template,
            channel=NotificationTemplate.SMS,
            phone='+1234567890',
        )
        assert notification.channel == 'sms'

    def test_channel_in_app(self, template):
        """Test notification with in-app channel."""
        notification = self._create_notification(
            template=template,
            channel=NotificationTemplate.IN_APP,
        )
        assert notification.channel == 'in_app'

    def test_all_priority_levels(self, template):
        """Test creating notifications with all priority levels."""
        for priority, _ in Notification.PRIORITY_CHOICES:
            notification = self._create_notification(
                template=template,
                priority=priority,
                subject=f'Priority {priority}',
            )
            assert notification.priority == priority

    def test_all_status_values(self, template):
        """Test creating notifications with all status values."""
        for status_val, _ in Notification.STATUS_CHOICES:
            notification = self._create_notification(
                template=template,
                status=status_val,
                subject=f'Status {status_val}',
            )
            assert notification.status == status_val

    def test_notification_without_template(self):
        """Test notification can be created without template."""
        notification = Notification.objects.create(
            email='test@example.com',
            subject='No Template',
            message_text='Direct notification',
        )
        assert notification.template is None
        assert notification.subject == 'No Template'

    def test_template_deletion_sets_null(self, template):
        """Test that deleting template sets notification.template to NULL."""
        notification = self._create_notification(template=template)
        template_id = template.id
        template.delete()
        notification.refresh_from_db()
        assert notification.template is None

    def test_indexes_exist(self):
        """Test that indexes are defined."""
        index_fields = [
            idx.fields for idx in Notification._meta.indexes
        ]
        assert ['user', '-created_at'] in index_fields
        assert ['email', '-created_at'] in index_fields
        assert ['status'] in index_fields
        assert ['-created_at'] in index_fields
