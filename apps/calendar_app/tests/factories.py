"""
Factories for calendar_app tests.
"""

import factory
import uuid
from datetime import timedelta, time
from django.utils import timezone
from apps.accounts.models import User
from apps.calendar_app.models import CalendarEvent, EventAttendee, BookingLink, Booking


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f'caluser{n}@test.com')
    username = factory.Sequence(lambda n: f'caluser{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    role = User.ADMIN
    is_staff = True
    is_active = True
    is_verified = True


class CalendarEventFactory(factory.django.DjangoModelFactory):
    """Factory for CalendarEvent model."""

    class Meta:
        model = CalendarEvent

    title = factory.Sequence(lambda n: f'Event {n}')
    description = factory.Faker('paragraph')
    event_type = CalendarEvent.MEETING
    start_time = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=1))
    end_time = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=2))
    all_day = False
    location = factory.Faker('address')
    organizer = factory.SubFactory(UserFactory)
    status = CalendarEvent.SCHEDULED
    reminder_minutes = 30
    color = '#3B82F6'


class EventAttendeeFactory(factory.django.DjangoModelFactory):
    """Factory for EventAttendee model."""

    class Meta:
        model = EventAttendee

    event = factory.SubFactory(CalendarEventFactory)
    email = factory.Sequence(lambda n: f'attendee{n}@test.com')
    name = factory.Faker('name')
    response_status = EventAttendee.PENDING


class BookingLinkFactory(factory.django.DjangoModelFactory):
    """Factory for BookingLink model."""

    class Meta:
        model = BookingLink

    owner = factory.SubFactory(UserFactory)
    slug = factory.Sequence(lambda n: f'booking-link-{n}')
    title = factory.Sequence(lambda n: f'Booking Link {n}')
    description = factory.Faker('paragraph')
    duration_minutes = 30
    available_days = factory.LazyFunction(lambda: [1, 2, 3, 4, 5])
    available_start_time = time(9, 0)
    available_end_time = time(17, 0)
    buffer_minutes = 15
    max_bookings_per_day = 8
    is_active = True


class BookingFactory(factory.django.DjangoModelFactory):
    """Factory for Booking model."""

    class Meta:
        model = Booking

    booking_link = factory.SubFactory(BookingLinkFactory)
    event = factory.SubFactory(
        CalendarEventFactory,
        organizer=factory.SelfAttribute('..booking_link.owner'),
    )
    booker_name = factory.Faker('name')
    booker_email = factory.Sequence(lambda n: f'booker{n}@test.com')
    notes = factory.Faker('sentence')
    status = Booking.CONFIRMED
