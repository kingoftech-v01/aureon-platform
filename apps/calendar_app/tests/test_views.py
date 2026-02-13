"""
Tests for calendar_app API views.

Tests cover:
- CalendarEventViewSet: CRUD, cancel, complete, attendees actions
- EventAttendeeViewSet: CRUD, filtering by event and response_status
- BookingLinkViewSet: CRUD, availability action, filtering
- BookingViewSet: list, create, retrieve, confirm, cancel actions
- Authentication enforcement on all endpoints
"""

import pytest
from datetime import timedelta, time
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.calendar_app.models import CalendarEvent, EventAttendee, BookingLink, Booking
from .factories import (
    UserFactory,
    CalendarEventFactory,
    EventAttendeeFactory,
    BookingLinkFactory,
    BookingFactory,
)


# ============================================================================
# Helpers
# ============================================================================

def _api_client_for(user):
    """Return an APIClient authenticated as *user*."""
    client = APIClient()
    client.defaults['HTTP_ORIGIN'] = 'http://testserver'
    client.defaults['SERVER_NAME'] = 'testserver'
    client.force_authenticate(user=user)
    return client


def _unauthed_client():
    """Return an unauthenticated APIClient."""
    client = APIClient()
    client.defaults['HTTP_ORIGIN'] = 'http://testserver'
    client.defaults['SERVER_NAME'] = 'testserver'
    return client


# ============================================================================
# CalendarEventViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestCalendarEventViewSet:
    """Tests for CalendarEventViewSet (CRUD + custom actions)."""

    # -- Authentication -------------------------------------------------------

    def test_list_requires_authentication(self):
        """Unauthenticated requests to list events should return 401."""
        client = _unauthed_client()
        response = client.get('/api/calendar/api/calendar-events/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # -- List -----------------------------------------------------------------

    def test_list_events(self):
        """Authenticated user can list calendar events."""
        user = UserFactory()
        CalendarEventFactory(organizer=user)
        CalendarEventFactory(organizer=user)
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/calendar-events/')
        assert response.status_code == status.HTTP_200_OK
        # The response may be paginated; accept both list and paginated dict
        data = response.data
        results = data.get('results', data) if isinstance(data, dict) else data
        assert len(results) >= 2

    def test_list_events_filter_by_status(self):
        """Events can be filtered by status query parameter."""
        user = UserFactory()
        CalendarEventFactory(organizer=user, status=CalendarEvent.SCHEDULED)
        CalendarEventFactory(organizer=user, status=CalendarEvent.CANCELLED)
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/calendar-events/', {'status': 'scheduled'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for event in results:
            assert event['status'] == 'scheduled'

    def test_list_events_search_by_title(self):
        """Events can be searched by title."""
        user = UserFactory()
        CalendarEventFactory(organizer=user, title='Strategy Workshop')
        CalendarEventFactory(organizer=user, title='Team Standup')
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/calendar-events/', {'search': 'Strategy'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert any('Strategy' in e['title'] for e in results)

    # -- Retrieve -------------------------------------------------------------

    def test_retrieve_event(self):
        """Authenticated user can retrieve a single event with detail serializer."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user)
        EventAttendeeFactory(event=event, name='Alice')
        client = _api_client_for(user)

        response = client.get(f'/api/calendar/api/calendar-events/{event.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(event.pk)
        # Detail serializer includes attendees and duration
        assert 'attendees' in response.data
        assert 'duration' in response.data
        assert len(response.data['attendees']) == 1

    # -- Create ---------------------------------------------------------------

    def test_create_event(self):
        """Authenticated user can create a calendar event; organizer is auto-set."""
        user = UserFactory()
        client = _api_client_for(user)
        now = timezone.now()
        payload = {
            'title': 'Sprint Planning',
            'event_type': 'meeting',
            'start_time': (now + timedelta(hours=1)).isoformat(),
            'end_time': (now + timedelta(hours=2)).isoformat(),
        }

        response = client.post('/api/calendar/api/calendar-events/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        # organizer should be set to the requesting user
        created_event = CalendarEvent.objects.get(pk=response.data['id'])
        assert created_event.organizer == user

    def test_create_event_invalid_times(self):
        """Creating an event with end_time before start_time fails validation."""
        user = UserFactory()
        client = _api_client_for(user)
        now = timezone.now()
        payload = {
            'title': 'Bad Event',
            'event_type': 'meeting',
            'start_time': (now + timedelta(hours=2)).isoformat(),
            'end_time': (now + timedelta(hours=1)).isoformat(),
        }

        response = client.post('/api/calendar/api/calendar-events/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # -- Update ---------------------------------------------------------------

    def test_update_event(self):
        """Authenticated user can update an event with PATCH."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user, title='Old Title')
        client = _api_client_for(user)

        response = client.patch(
            f'/api/calendar/api/calendar-events/{event.pk}/',
            {'title': 'New Title'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        event.refresh_from_db()
        assert event.title == 'New Title'

    # -- Delete ---------------------------------------------------------------

    def test_delete_event(self):
        """Authenticated user can delete an event."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user)
        client = _api_client_for(user)

        response = client.delete(f'/api/calendar/api/calendar-events/{event.pk}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CalendarEvent.objects.filter(pk=event.pk).exists()

    # -- Cancel action --------------------------------------------------------

    def test_cancel_event(self):
        """POST to cancel action sets status to CANCELLED."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user, status=CalendarEvent.SCHEDULED)
        client = _api_client_for(user)

        response = client.post(f'/api/calendar/api/calendar-events/{event.pk}/cancel/')
        assert response.status_code == status.HTTP_200_OK
        event.refresh_from_db()
        assert event.status == CalendarEvent.CANCELLED

    # -- Complete action ------------------------------------------------------

    def test_complete_event(self):
        """POST to complete action sets status to COMPLETED."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user, status=CalendarEvent.SCHEDULED)
        client = _api_client_for(user)

        response = client.post(f'/api/calendar/api/calendar-events/{event.pk}/complete/')
        assert response.status_code == status.HTTP_200_OK
        event.refresh_from_db()
        assert event.status == CalendarEvent.COMPLETED

    # -- Attendees action -----------------------------------------------------

    def test_get_attendees_for_event(self):
        """GET attendees action returns all attendees for the given event."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user)
        EventAttendeeFactory(event=event, name='Alice')
        EventAttendeeFactory(event=event, name='Bob')
        client = _api_client_for(user)

        response = client.get(f'/api/calendar/api/calendar-events/{event.pk}/attendees/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        names = {a['name'] for a in response.data}
        assert 'Alice' in names
        assert 'Bob' in names

    def test_get_attendees_empty(self):
        """GET attendees action returns an empty list when event has no attendees."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user)
        client = _api_client_for(user)

        response = client.get(f'/api/calendar/api/calendar-events/{event.pk}/attendees/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []


# ============================================================================
# EventAttendeeViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestEventAttendeeViewSet:
    """Tests for EventAttendeeViewSet."""

    def test_list_requires_authentication(self):
        """Unauthenticated requests should return 401."""
        client = _unauthed_client()
        response = client.get('/api/calendar/api/event-attendees/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_attendees(self):
        """Authenticated user can list all attendees."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user)
        EventAttendeeFactory(event=event)
        EventAttendeeFactory(event=event)
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/event-attendees/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_attendee(self):
        """Authenticated user can add an attendee to an event."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user)
        client = _api_client_for(user)
        payload = {
            'event': str(event.pk),
            'email': 'newattendee@example.com',
            'name': 'New Attendee',
            'response_status': 'pending',
        }

        response = client.post('/api/calendar/api/event-attendees/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert EventAttendee.objects.filter(event=event, email='newattendee@example.com').exists()

    def test_retrieve_attendee(self):
        """Authenticated user can retrieve a single attendee."""
        user = UserFactory()
        attendee = EventAttendeeFactory(event__organizer=user)
        client = _api_client_for(user)

        response = client.get(f'/api/calendar/api/event-attendees/{attendee.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(attendee.pk)

    def test_update_attendee_response_status(self):
        """Attendee response_status can be updated via PATCH (accept/decline)."""
        user = UserFactory()
        attendee = EventAttendeeFactory(
            event__organizer=user,
            response_status=EventAttendee.PENDING,
        )
        client = _api_client_for(user)

        # Accept
        response = client.patch(
            f'/api/calendar/api/event-attendees/{attendee.pk}/',
            {'response_status': 'accepted'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        attendee.refresh_from_db()
        assert attendee.response_status == EventAttendee.ACCEPTED

        # Decline
        response = client.patch(
            f'/api/calendar/api/event-attendees/{attendee.pk}/',
            {'response_status': 'declined'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        attendee.refresh_from_db()
        assert attendee.response_status == EventAttendee.DECLINED

    def test_delete_attendee(self):
        """Attendee can be deleted."""
        user = UserFactory()
        attendee = EventAttendeeFactory(event__organizer=user)
        client = _api_client_for(user)

        response = client.delete(f'/api/calendar/api/event-attendees/{attendee.pk}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not EventAttendee.objects.filter(pk=attendee.pk).exists()

    def test_filter_by_event(self):
        """Attendees can be filtered by event UUID."""
        user = UserFactory()
        event1 = CalendarEventFactory(organizer=user)
        event2 = CalendarEventFactory(organizer=user)
        EventAttendeeFactory(event=event1)
        EventAttendeeFactory(event=event2)
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/event-attendees/', {'event': str(event1.pk)})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for att in results:
            assert att['event'] == str(event1.pk)

    def test_filter_by_response_status(self):
        """Attendees can be filtered by response_status."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user)
        EventAttendeeFactory(event=event, response_status=EventAttendee.ACCEPTED)
        EventAttendeeFactory(event=event, response_status=EventAttendee.DECLINED)
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/event-attendees/', {'response_status': 'accepted'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for att in results:
            assert att['response_status'] == 'accepted'


# ============================================================================
# BookingLinkViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestBookingLinkViewSet:
    """Tests for BookingLinkViewSet."""

    def test_list_requires_authentication(self):
        """Unauthenticated requests should return 401."""
        client = _unauthed_client()
        response = client.get('/api/calendar/api/booking-links/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_booking_links(self):
        """Authenticated user can list booking links."""
        user = UserFactory()
        BookingLinkFactory(owner=user)
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/booking-links/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_booking_link(self):
        """Authenticated user can create a booking link; owner is auto-set."""
        user = UserFactory()
        client = _api_client_for(user)
        payload = {
            'title': 'Discovery Call',
            'slug': 'discovery-call',
            'duration_minutes': 45,
            'available_days': [1, 2, 3, 4, 5],
            'available_start_time': '09:00:00',
            'available_end_time': '17:00:00',
            'buffer_minutes': 10,
        }

        response = client.post('/api/calendar/api/booking-links/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        link = BookingLink.objects.get(slug='discovery-call')
        assert link.owner == user
        assert link.duration_minutes == 45

    def test_create_booking_link_invalid_times(self):
        """Creating a booking link with end_time before start_time fails."""
        user = UserFactory()
        client = _api_client_for(user)
        payload = {
            'title': 'Bad Link',
            'slug': 'bad-link',
            'duration_minutes': 30,
            'available_days': [1, 2, 3],
            'available_start_time': '17:00:00',
            'available_end_time': '09:00:00',
        }

        response = client.post('/api/calendar/api/booking-links/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_booking_link(self):
        """Authenticated user can retrieve a single booking link."""
        user = UserFactory()
        link = BookingLinkFactory(owner=user)
        client = _api_client_for(user)

        response = client.get(f'/api/calendar/api/booking-links/{link.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(link.pk)
        assert response.data['title'] == link.title

    def test_update_booking_link(self):
        """Booking link can be updated via PATCH."""
        user = UserFactory()
        link = BookingLinkFactory(owner=user, is_active=True)
        client = _api_client_for(user)

        response = client.patch(
            f'/api/calendar/api/booking-links/{link.pk}/',
            {'is_active': False},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        link.refresh_from_db()
        assert link.is_active is False

    def test_delete_booking_link(self):
        """Booking link can be deleted."""
        user = UserFactory()
        link = BookingLinkFactory(owner=user)
        client = _api_client_for(user)

        response = client.delete(f'/api/calendar/api/booking-links/{link.pk}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not BookingLink.objects.filter(pk=link.pk).exists()

    def test_filter_by_is_active(self):
        """Booking links can be filtered by is_active."""
        user = UserFactory()
        BookingLinkFactory(owner=user, is_active=True)
        BookingLinkFactory(owner=user, is_active=False)
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/booking-links/', {'is_active': 'true'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for link in results:
            assert link['is_active'] is True

    def test_search_by_title(self):
        """Booking links can be searched by title."""
        user = UserFactory()
        BookingLinkFactory(owner=user, title='Discovery Call')
        BookingLinkFactory(owner=user, title='Onboarding Meeting')
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/booking-links/', {'search': 'Discovery'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert any('Discovery' in l['title'] for l in results)

    def test_availability_action(self):
        """GET availability returns slots list for the booking link."""
        user = UserFactory()
        link = BookingLinkFactory(
            owner=user,
            available_days=[1, 2, 3, 4, 5],
            available_start_time=time(9, 0),
            available_end_time=time(17, 0),
            duration_minutes=30,
            buffer_minutes=0,
        )
        client = _api_client_for(user)

        response = client.get(f'/api/calendar/api/booking-links/{link.pk}/availability/')
        assert response.status_code == status.HTTP_200_OK
        assert 'slots' in response.data
        assert isinstance(response.data['slots'], list)


# ============================================================================
# BookingViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestBookingViewSet:
    """Tests for BookingViewSet (list, create, retrieve, confirm, cancel)."""

    def test_list_requires_authentication(self):
        """Unauthenticated requests should return 401."""
        client = _unauthed_client()
        response = client.get('/api/calendar/api/bookings/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_bookings(self):
        """Authenticated user can list bookings."""
        user = UserFactory()
        link = BookingLinkFactory(owner=user)
        BookingFactory(booking_link=link, event__organizer=user)
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/bookings/')
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_booking(self):
        """Authenticated user can retrieve a single booking."""
        user = UserFactory()
        booking = BookingFactory(booking_link__owner=user, event__organizer=user)
        client = _api_client_for(user)

        response = client.get(f'/api/calendar/api/bookings/{booking.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(booking.pk)

    def test_create_booking(self):
        """Authenticated user can create a booking through the API."""
        user = UserFactory()
        link = BookingLinkFactory(
            owner=user,
            available_days=[1, 2, 3, 4, 5],
            available_start_time=time(9, 0),
            available_end_time=time(17, 0),
            duration_minutes=30,
            is_active=True,
        )
        client = _api_client_for(user)

        # Find a valid future weekday at 10:00
        now = timezone.now()
        start_time = now + timedelta(days=1)
        while start_time.isoweekday() > 5:
            start_time += timedelta(days=1)
        start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)

        payload = {
            'booking_link': str(link.pk),
            'booker_name': 'Jane Client',
            'booker_email': 'jane@client.com',
            'notes': 'Looking forward to our call.',
            'start_time': start_time.isoformat(),
        }

        response = client.post('/api/calendar/api/bookings/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        # A CalendarEvent should also have been created
        booking = Booking.objects.get(pk=response.data['id'])
        assert booking.event is not None
        assert booking.booker_name == 'Jane Client'

    def test_create_booking_inactive_link_fails(self):
        """Creating a booking with an inactive link fails validation."""
        user = UserFactory()
        link = BookingLinkFactory(owner=user, is_active=False)
        client = _api_client_for(user)

        now = timezone.now()
        start_time = now + timedelta(days=1)
        while start_time.isoweekday() > 5:
            start_time += timedelta(days=1)
        start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)

        payload = {
            'booking_link': str(link.pk),
            'booker_name': 'Test',
            'booker_email': 'test@test.com',
            'start_time': start_time.isoformat(),
        }

        response = client.post('/api/calendar/api/bookings/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_not_allowed(self):
        """PUT/PATCH should not be allowed on BookingViewSet (no UpdateMixin)."""
        user = UserFactory()
        booking = BookingFactory(booking_link__owner=user, event__organizer=user)
        client = _api_client_for(user)

        response = client.patch(
            f'/api/calendar/api/bookings/{booking.pk}/',
            {'booker_name': 'Changed'},
            format='json',
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self):
        """DELETE should not be allowed on BookingViewSet (no DestroyMixin)."""
        user = UserFactory()
        booking = BookingFactory(booking_link__owner=user, event__organizer=user)
        client = _api_client_for(user)

        response = client.delete(f'/api/calendar/api/bookings/{booking.pk}/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # -- Cancel action --------------------------------------------------------

    def test_cancel_booking(self):
        """POST to cancel action sets status to CANCELLED and records cancelled_at."""
        user = UserFactory()
        booking = BookingFactory(
            booking_link__owner=user,
            event__organizer=user,
            status=Booking.CONFIRMED,
        )
        client = _api_client_for(user)

        response = client.post(f'/api/calendar/api/bookings/{booking.pk}/cancel/')
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == Booking.CANCELLED
        assert booking.cancelled_at is not None

    def test_cancel_booking_also_cancels_event(self):
        """Cancelling a booking also sets the associated event to CANCELLED."""
        user = UserFactory()
        event = CalendarEventFactory(organizer=user, status=CalendarEvent.SCHEDULED)
        booking = BookingFactory(
            booking_link__owner=user,
            event=event,
            status=Booking.CONFIRMED,
        )
        client = _api_client_for(user)

        client.post(f'/api/calendar/api/bookings/{booking.pk}/cancel/')
        event.refresh_from_db()
        assert event.status == CalendarEvent.CANCELLED

    # -- Confirm action -------------------------------------------------------

    def test_confirm_booking_with_valid_token(self):
        """POST to confirm action with correct token sets status to CONFIRMED."""
        user = UserFactory()
        booking = BookingFactory(
            booking_link__owner=user,
            event__organizer=user,
            status=Booking.CANCELLED,  # start from non-confirmed to see the change
        )
        token = booking.confirmation_token
        client = _api_client_for(user)

        response = client.post(
            f'/api/calendar/api/bookings/{booking.pk}/confirm/',
            {'confirmation_token': token},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == Booking.CONFIRMED

    def test_confirm_booking_without_token_fails(self):
        """POST to confirm action without a token returns 400."""
        user = UserFactory()
        booking = BookingFactory(booking_link__owner=user, event__organizer=user)
        client = _api_client_for(user)

        response = client.post(
            f'/api/calendar/api/bookings/{booking.pk}/confirm/',
            {},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'confirmation_token' in response.data.get('detail', '').lower() or 'token' in response.data.get('detail', '').lower()

    def test_confirm_booking_with_invalid_token_fails(self):
        """POST to confirm action with a wrong token returns 400."""
        user = UserFactory()
        booking = BookingFactory(booking_link__owner=user, event__organizer=user)
        client = _api_client_for(user)

        response = client.post(
            f'/api/calendar/api/bookings/{booking.pk}/confirm/',
            {'confirmation_token': 'wrong-token-value'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'invalid' in response.data.get('detail', '').lower() or 'token' in response.data.get('detail', '').lower()

    def test_filter_bookings_by_status(self):
        """Bookings can be filtered by status."""
        user = UserFactory()
        link = BookingLinkFactory(owner=user)
        BookingFactory(booking_link=link, event__organizer=user, status=Booking.CONFIRMED)
        BookingFactory(booking_link=link, event__organizer=user, status=Booking.CANCELLED)
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/bookings/', {'status': 'confirmed'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for b in results:
            assert b['status'] == 'confirmed'

    def test_filter_bookings_by_booking_link(self):
        """Bookings can be filtered by booking_link."""
        user = UserFactory()
        link1 = BookingLinkFactory(owner=user)
        link2 = BookingLinkFactory(owner=user)
        BookingFactory(booking_link=link1, event__organizer=user)
        BookingFactory(booking_link=link2, event__organizer=user)
        client = _api_client_for(user)

        response = client.get('/api/calendar/api/bookings/', {'booking_link': str(link1.pk)})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for b in results:
            assert b['booking_link'] == str(link1.pk)
