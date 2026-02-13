"""
Tests for calendar_app serializers.

Tests cover:
- CalendarEventListSerializer (including nested organizer, client, attendees_count)
- CalendarEventDetailSerializer (including nested attendees, duration)
- CalendarEventCreateUpdateSerializer (validation)
- EventAttendeeSerializer
- BookingLinkSerializer / BookingLinkCreateUpdateSerializer
- BookingSerializer / BookingCreateSerializer
"""

import pytest
from datetime import timedelta, time
from django.utils import timezone
from apps.calendar_app.serializers import (
    CalendarEventListSerializer,
    CalendarEventDetailSerializer,
    CalendarEventCreateUpdateSerializer,
    EventAttendeeSerializer,
    BookingLinkSerializer,
    BookingLinkCreateUpdateSerializer,
    BookingSerializer,
    BookingCreateSerializer,
)
from apps.calendar_app.models import CalendarEvent
from .factories import (
    UserFactory,
    CalendarEventFactory,
    EventAttendeeFactory,
    BookingLinkFactory,
    BookingFactory,
)


# ============================================================================
# CalendarEventListSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestCalendarEventListSerializer:
    """Tests for CalendarEventListSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        event = CalendarEventFactory()
        serializer = CalendarEventListSerializer(event)
        data = serializer.data

        assert 'id' in data
        assert 'title' in data
        assert 'event_type' in data
        assert 'start_time' in data
        assert 'end_time' in data
        assert 'all_day' in data
        assert 'status' in data
        assert 'organizer' in data
        assert 'client' in data
        assert 'color' in data
        assert 'attendees_count' in data

    def test_organizer_method_field(self):
        """Test organizer SerializerMethodField returns id and email."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user)
        serializer = CalendarEventListSerializer(event)
        org_data = serializer.data['organizer']

        assert 'id' in org_data
        assert 'email' in org_data
        assert org_data['id'] == str(user.id)
        assert org_data['email'] == user.email

    def test_client_method_field_with_client(self):
        """Test client SerializerMethodField returns id and name."""
        from apps.clients.models import Client

        user = UserFactory()
        client = Client.objects.create(
            client_type=Client.COMPANY,
            company_name='Test Corp',
            first_name='John',
            last_name='Doe',
            email='john@testcorp.com',
            owner=user,
        )
        event = CalendarEventFactory(organizer=user, client=client)
        serializer = CalendarEventListSerializer(event)
        client_data = serializer.data['client']

        assert client_data is not None
        assert 'id' in client_data
        assert 'name' in client_data

    def test_client_method_field_without_client(self):
        """Test client returns None when no client."""
        event = CalendarEventFactory(client=None)
        serializer = CalendarEventListSerializer(event)
        assert serializer.data['client'] is None

    def test_attendees_count(self):
        """Test attendees_count SerializerMethodField."""
        event = CalendarEventFactory()
        EventAttendeeFactory(event=event)
        EventAttendeeFactory(event=event)

        serializer = CalendarEventListSerializer(event)
        assert serializer.data['attendees_count'] == 2

    def test_attendees_count_zero(self):
        """Test attendees_count is 0 with no attendees."""
        event = CalendarEventFactory()
        serializer = CalendarEventListSerializer(event)
        assert serializer.data['attendees_count'] == 0


# ============================================================================
# CalendarEventDetailSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestCalendarEventDetailSerializer:
    """Tests for CalendarEventDetailSerializer."""

    def test_includes_nested_attendees(self):
        """Test detail serializer includes nested attendees."""
        event = CalendarEventFactory()
        EventAttendeeFactory(event=event, name='Alice')
        serializer = CalendarEventDetailSerializer(event)

        assert 'attendees' in serializer.data
        assert len(serializer.data['attendees']) == 1
        assert serializer.data['attendees'][0]['name'] == 'Alice'

    def test_duration_method_field(self):
        """Test duration SerializerMethodField returns total seconds."""
        now = timezone.now()
        event = CalendarEventFactory(
            start_time=now,
            end_time=now + timedelta(hours=1, minutes=30),
        )
        serializer = CalendarEventDetailSerializer(event)
        assert serializer.data['duration'] == 5400.0  # 1h30m = 5400s

    def test_includes_all_fields(self):
        """Test detail serializer includes all model fields."""
        event = CalendarEventFactory()
        serializer = CalendarEventDetailSerializer(event)
        data = serializer.data

        assert 'description' in data
        assert 'location' in data
        assert 'video_link' in data
        assert 'metadata' in data


# ============================================================================
# CalendarEventCreateUpdateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestCalendarEventCreateUpdateSerializer:
    """Tests for CalendarEventCreateUpdateSerializer."""

    def test_valid_data(self):
        """Test serializer validates correct data."""
        now = timezone.now()
        data = {
            'title': 'New Event',
            'event_type': 'meeting',
            'start_time': (now + timedelta(hours=1)).isoformat(),
            'end_time': (now + timedelta(hours=2)).isoformat(),
        }
        serializer = CalendarEventCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_end_time_before_start_time_invalid(self):
        """Test end_time before start_time raises validation error."""
        now = timezone.now()
        data = {
            'title': 'Bad Event',
            'event_type': 'meeting',
            'start_time': (now + timedelta(hours=2)).isoformat(),
            'end_time': (now + timedelta(hours=1)).isoformat(),
        }
        serializer = CalendarEventCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'end_time' in serializer.errors

    def test_end_time_equal_start_time_invalid(self):
        """Test end_time equal to start_time raises validation error."""
        now = timezone.now()
        data = {
            'title': 'Same Time Event',
            'event_type': 'meeting',
            'start_time': now.isoformat(),
            'end_time': now.isoformat(),
        }
        serializer = CalendarEventCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()


# ============================================================================
# EventAttendeeSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestEventAttendeeSerializer:
    """Tests for EventAttendeeSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        attendee = EventAttendeeFactory()
        serializer = EventAttendeeSerializer(attendee)
        data = serializer.data

        assert 'id' in data
        assert 'event' in data
        assert 'email' in data
        assert 'name' in data
        assert 'response_status' in data

    def test_read_only_fields(self):
        """Test read-only fields."""
        assert 'id' in EventAttendeeSerializer.Meta.read_only_fields
        assert 'created_at' in EventAttendeeSerializer.Meta.read_only_fields


# ============================================================================
# BookingLinkSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestBookingLinkSerializer:
    """Tests for BookingLinkSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        link = BookingLinkFactory()
        serializer = BookingLinkSerializer(link)
        data = serializer.data

        assert 'id' in data
        assert 'owner' in data
        assert 'slug' in data
        assert 'title' in data
        assert 'duration_minutes' in data
        assert 'available_days' in data
        assert 'is_active' in data

    def test_read_only_fields(self):
        """Test owner is read-only."""
        assert 'owner' in BookingLinkSerializer.Meta.read_only_fields


# ============================================================================
# BookingLinkCreateUpdateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestBookingLinkCreateUpdateSerializer:
    """Tests for BookingLinkCreateUpdateSerializer."""

    def test_valid_data(self):
        """Test serializer validates correct data."""
        data = {
            'title': 'New Booking',
            'slug': 'new-booking',
            'duration_minutes': 60,
            'available_days': [1, 2, 3, 4, 5],
            'available_start_time': '09:00:00',
            'available_end_time': '17:00:00',
        }
        serializer = BookingLinkCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_end_time_before_start_time_invalid(self):
        """Test available_end_time before available_start_time raises error."""
        data = {
            'title': 'Bad Link',
            'slug': 'bad-link',
            'duration_minutes': 30,
            'available_days': [1, 2, 3],
            'available_start_time': '17:00:00',
            'available_end_time': '09:00:00',
        }
        serializer = BookingLinkCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'available_end_time' in serializer.errors


# ============================================================================
# BookingSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestBookingSerializer:
    """Tests for BookingSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        booking = BookingFactory()
        serializer = BookingSerializer(booking)
        data = serializer.data

        assert 'id' in data
        assert 'booking_link' in data
        assert 'event' in data
        assert 'booker_name' in data
        assert 'booker_email' in data
        assert 'status' in data
        assert 'confirmation_token' in data

    def test_read_only_fields(self):
        """Test read-only fields."""
        assert 'confirmation_token' in BookingSerializer.Meta.read_only_fields


# ============================================================================
# BookingCreateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestBookingCreateSerializer:
    """Tests for BookingCreateSerializer."""

    def test_valid_data(self):
        """Test serializer validates correct data."""
        link = BookingLinkFactory(available_days=[1, 2, 3, 4, 5])
        # Find a future weekday
        now = timezone.now()
        start_time = now + timedelta(days=1)
        # Ensure it's a weekday
        while start_time.isoweekday() > 5:
            start_time += timedelta(days=1)
        start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)

        data = {
            'booking_link': str(link.id),
            'booker_name': 'Test Booker',
            'booker_email': 'booker@test.com',
            'start_time': start_time.isoformat(),
        }
        serializer = BookingCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_inactive_booking_link_invalid(self):
        """Test inactive booking link fails validation."""
        link = BookingLinkFactory(is_active=False)
        now = timezone.now()
        start_time = now + timedelta(days=1)
        while start_time.isoweekday() > 5:
            start_time += timedelta(days=1)
        start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)

        data = {
            'booking_link': str(link.id),
            'booker_name': 'Test',
            'booker_email': 'test@test.com',
            'start_time': start_time.isoformat(),
        }
        serializer = BookingCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'booking_link' in serializer.errors
