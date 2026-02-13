"""
Tests for calendar_app models.

Tests cover:
- Model creation and field defaults
- __str__ methods
- CalendarEvent.duration property
- Booking auto-generates confirmation_token
- EventAttendee unique_together constraint
"""

import pytest
from datetime import timedelta
from django.db import IntegrityError
from django.utils import timezone
from apps.calendar_app.models import CalendarEvent, EventAttendee, BookingLink, Booking
from .factories import (
    UserFactory,
    CalendarEventFactory,
    EventAttendeeFactory,
    BookingLinkFactory,
    BookingFactory,
)


# ============================================================================
# CalendarEvent Model Tests
# ============================================================================

@pytest.mark.django_db
class TestCalendarEventModel:
    """Tests for CalendarEvent model."""

    def test_create_event(self):
        """Test creating a calendar event with defaults."""
        event = CalendarEventFactory()
        assert event.pk is not None
        assert event.event_type == CalendarEvent.MEETING
        assert event.status == CalendarEvent.SCHEDULED
        assert event.all_day is False
        assert event.reminder_minutes == 30

    def test_str_representation(self):
        """Test __str__ returns title (start_time)."""
        event = CalendarEventFactory(title='Team Meeting')
        assert 'Team Meeting' in str(event)

    def test_duration_property(self):
        """Test duration property returns end_time - start_time."""
        now = timezone.now()
        event = CalendarEventFactory(
            start_time=now,
            end_time=now + timedelta(hours=2, minutes=30),
        )
        assert event.duration == timedelta(hours=2, minutes=30)

    def test_duration_property_short(self):
        """Test duration for short events."""
        now = timezone.now()
        event = CalendarEventFactory(
            start_time=now,
            end_time=now + timedelta(minutes=15),
        )
        assert event.duration == timedelta(minutes=15)

    def test_event_type_choices(self):
        """Test all event type choices."""
        for type_code, _ in CalendarEvent.EVENT_TYPE_CHOICES:
            event = CalendarEventFactory(event_type=type_code)
            assert event.event_type == type_code

    def test_status_choices(self):
        """Test all status choices."""
        for status_code, _ in CalendarEvent.STATUS_CHOICES:
            event = CalendarEventFactory(status=status_code)
            assert event.status == status_code

    def test_client_fk_nullable(self):
        """Test client FK is nullable."""
        event = CalendarEventFactory(client=None)
        assert event.client is None

    def test_contract_fk_nullable(self):
        """Test contract FK is nullable."""
        event = CalendarEventFactory(contract=None)
        assert event.contract is None

    def test_metadata_field(self):
        """Test metadata JSON field."""
        meta = {'meeting_type': 'standup', 'recurring': True}
        event = CalendarEventFactory(metadata=meta)
        assert event.metadata == meta

    def test_ordering(self):
        """Test default ordering is [-start_time]."""
        now = timezone.now()
        e1 = CalendarEventFactory(start_time=now - timedelta(hours=1))
        e2 = CalendarEventFactory(start_time=now + timedelta(hours=1))
        events = list(CalendarEvent.objects.filter(
            id__in=[e1.id, e2.id]
        ))
        assert events[0] == e2  # future event first (desc ordering)


# ============================================================================
# EventAttendee Model Tests
# ============================================================================

@pytest.mark.django_db
class TestEventAttendeeModel:
    """Tests for EventAttendee model."""

    def test_create_attendee(self):
        """Test creating an event attendee."""
        attendee = EventAttendeeFactory()
        assert attendee.pk is not None
        assert attendee.response_status == EventAttendee.PENDING

    def test_str_with_name(self):
        """Test __str__ returns name - response_status."""
        attendee = EventAttendeeFactory(name='John Doe', response_status=EventAttendee.ACCEPTED)
        assert str(attendee) == 'John Doe - accepted'

    def test_str_without_name(self):
        """Test __str__ returns email - response_status when name is empty."""
        attendee = EventAttendeeFactory(name='', email='john@test.com')
        assert str(attendee) == 'john@test.com - pending'

    def test_response_status_choices(self):
        """Test all response status choices."""
        for status_code, _ in EventAttendee.RESPONSE_STATUS_CHOICES:
            attendee = EventAttendeeFactory(response_status=status_code)
            assert attendee.response_status == status_code

    def test_unique_together_event_email(self):
        """Test unique_together constraint on event and email."""
        event = CalendarEventFactory()
        EventAttendeeFactory(event=event, email='same@test.com')

        with pytest.raises(IntegrityError):
            EventAttendeeFactory(event=event, email='same@test.com')

    def test_different_events_same_email_allowed(self):
        """Test same email can attend different events."""
        event1 = CalendarEventFactory()
        event2 = CalendarEventFactory()
        EventAttendeeFactory(event=event1, email='shared@test.com')
        a2 = EventAttendeeFactory(event=event2, email='shared@test.com')
        assert a2.pk is not None

    def test_user_nullable(self):
        """Test user FK is nullable."""
        attendee = EventAttendeeFactory(user=None)
        assert attendee.user is None

    def test_attendee_belongs_to_event(self):
        """Test attendee FK to event."""
        event = CalendarEventFactory()
        EventAttendeeFactory(event=event)
        EventAttendeeFactory(event=event)
        assert event.attendees.count() == 2


# ============================================================================
# BookingLink Model Tests
# ============================================================================

@pytest.mark.django_db
class TestBookingLinkModel:
    """Tests for BookingLink model."""

    def test_create_booking_link(self):
        """Test creating a booking link."""
        link = BookingLinkFactory()
        assert link.pk is not None
        assert link.is_active is True
        assert link.duration_minutes == 30
        assert link.buffer_minutes == 15

    def test_str_representation(self):
        """Test __str__ returns title."""
        link = BookingLinkFactory(title='Discovery Call')
        assert str(link) == 'Discovery Call'

    def test_slug_unique(self):
        """Test slug is unique."""
        BookingLinkFactory(slug='unique-slug')
        with pytest.raises(IntegrityError):
            BookingLinkFactory(slug='unique-slug')

    def test_available_days_json(self):
        """Test available_days JSON field."""
        days = [1, 3, 5]
        link = BookingLinkFactory(available_days=days)
        assert link.available_days == days

    def test_ordering(self):
        """Test default ordering is [-created_at]."""
        l1 = BookingLinkFactory()
        l2 = BookingLinkFactory()
        links = list(BookingLink.objects.filter(id__in=[l1.id, l2.id]))
        assert links[0] == l2  # most recent first


# ============================================================================
# Booking Model Tests
# ============================================================================

@pytest.mark.django_db
class TestBookingModel:
    """Tests for Booking model."""

    def test_create_booking(self):
        """Test creating a booking."""
        booking = BookingFactory()
        assert booking.pk is not None
        assert booking.status == Booking.CONFIRMED

    def test_str_representation(self):
        """Test __str__ returns 'Booking by name - status'."""
        booking = BookingFactory(booker_name='Alice', status=Booking.CONFIRMED)
        assert str(booking) == 'Booking by Alice - confirmed'

    def test_auto_generates_confirmation_token(self):
        """Test save() auto-generates confirmation_token when not set."""
        link = BookingLinkFactory()
        event = CalendarEventFactory()
        booking = Booking(
            booking_link=link,
            event=event,
            booker_name='Test Booker',
            booker_email='booker@test.com',
        )
        # confirmation_token is empty string by default
        booking.confirmation_token = ''
        booking.save()
        assert booking.confirmation_token != ''
        assert len(booking.confirmation_token) > 20

    def test_confirmation_token_not_overwritten_if_set(self):
        """Test save() does not overwrite existing confirmation_token."""
        booking = BookingFactory(confirmation_token='my-custom-token')
        booking.save()
        assert booking.confirmation_token == 'my-custom-token'

    def test_confirmation_token_unique(self):
        """Test confirmation_token is unique."""
        b1 = BookingFactory()
        b2 = BookingFactory()
        assert b1.confirmation_token != b2.confirmation_token

    def test_status_choices(self):
        """Test all status choices."""
        for status_code, _ in Booking.STATUS_CHOICES:
            booking = BookingFactory(status=status_code)
            assert booking.status == status_code

    def test_event_nullable(self):
        """Test event FK is nullable."""
        link = BookingLinkFactory()
        booking = Booking(
            booking_link=link,
            booker_name='No Event Booker',
            booker_email='noev@test.com',
            event=None,
        )
        booking.save()
        assert booking.event is None

    def test_ordering(self):
        """Test default ordering is [-created_at]."""
        b1 = BookingFactory()
        b2 = BookingFactory()
        bookings = list(Booking.objects.filter(id__in=[b1.id, b2.id]))
        assert bookings[0] == b2
