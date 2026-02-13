"""
Tests for calendar_app URL configuration.

Tests cover:
- API router URL resolution for all four ViewSets
  (CalendarEventViewSet, EventAttendeeViewSet, BookingLinkViewSet, BookingViewSet)
- Custom action URLs (cancel, complete, attendees, availability, confirm)
- Frontend URL resolution (calendar, event_detail, event_create,
  booking_link_list, booking_public, booking_confirm)
- URL reversibility (reverse -> resolve round-trip)
"""

import uuid
import pytest
from django.urls import resolve, reverse


# ============================================================================
# API Router URL Resolution Tests
# ============================================================================

@pytest.mark.django_db
class TestCalendarEventAPIUrls:
    """Tests for CalendarEvent API URL patterns."""

    def test_calendar_event_list_url_resolves(self):
        """calendar-event-list resolves to CalendarEventViewSet."""
        url = reverse('calendar_app:calendar-event-list')
        assert '/api/calendar-events/' in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'CalendarEventViewSet'
        assert match.func.actions.get('get') == 'list'

    def test_calendar_event_detail_url_resolves(self):
        """calendar-event-detail resolves to CalendarEventViewSet retrieve."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:calendar-event-detail', kwargs={'pk': pk})
        assert str(pk) in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'CalendarEventViewSet'
        assert match.func.actions.get('get') == 'retrieve'

    def test_calendar_event_cancel_url_resolves(self):
        """calendar-event-cancel resolves to CalendarEventViewSet cancel action."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:calendar-event-cancel', kwargs={'pk': pk})
        assert '/cancel/' in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'CalendarEventViewSet'
        assert match.func.actions.get('post') == 'cancel'

    def test_calendar_event_complete_url_resolves(self):
        """calendar-event-complete resolves to CalendarEventViewSet complete action."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:calendar-event-complete', kwargs={'pk': pk})
        assert '/complete/' in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'CalendarEventViewSet'
        assert match.func.actions.get('post') == 'complete'

    def test_calendar_event_attendees_url_resolves(self):
        """calendar-event-attendees resolves to CalendarEventViewSet attendees action."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:calendar-event-attendees', kwargs={'pk': pk})
        assert '/attendees/' in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'CalendarEventViewSet'
        assert match.func.actions.get('get') == 'attendees'


@pytest.mark.django_db
class TestEventAttendeeAPIUrls:
    """Tests for EventAttendee API URL patterns."""

    def test_event_attendee_list_url_resolves(self):
        """event-attendee-list resolves to EventAttendeeViewSet."""
        url = reverse('calendar_app:event-attendee-list')
        assert '/event-attendees/' in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'EventAttendeeViewSet'
        assert match.func.actions.get('get') == 'list'

    def test_event_attendee_detail_url_resolves(self):
        """event-attendee-detail resolves to EventAttendeeViewSet retrieve."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:event-attendee-detail', kwargs={'pk': pk})
        assert str(pk) in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'EventAttendeeViewSet'
        assert match.func.actions.get('get') == 'retrieve'


@pytest.mark.django_db
class TestBookingLinkAPIUrls:
    """Tests for BookingLink API URL patterns."""

    def test_booking_link_list_url_resolves(self):
        """booking-link-list resolves to BookingLinkViewSet."""
        url = reverse('calendar_app:booking-link-list')
        assert '/booking-links/' in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'BookingLinkViewSet'
        assert match.func.actions.get('get') == 'list'

    def test_booking_link_detail_url_resolves(self):
        """booking-link-detail resolves to BookingLinkViewSet retrieve."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:booking-link-detail', kwargs={'pk': pk})
        assert str(pk) in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'BookingLinkViewSet'
        assert match.func.actions.get('get') == 'retrieve'

    def test_booking_link_availability_url_resolves(self):
        """booking-link-availability resolves to BookingLinkViewSet availability action."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:booking-link-availability', kwargs={'pk': pk})
        assert '/availability/' in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'BookingLinkViewSet'
        assert match.func.actions.get('get') == 'availability'


@pytest.mark.django_db
class TestBookingAPIUrls:
    """Tests for Booking API URL patterns."""

    def test_booking_list_url_resolves(self):
        """booking-list resolves to BookingViewSet."""
        url = reverse('calendar_app:booking-list')
        assert '/bookings/' in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'BookingViewSet'
        assert match.func.actions.get('get') == 'list'

    def test_booking_detail_url_resolves(self):
        """booking-detail resolves to BookingViewSet retrieve."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:booking-detail', kwargs={'pk': pk})
        assert str(pk) in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'BookingViewSet'
        assert match.func.actions.get('get') == 'retrieve'

    def test_booking_cancel_url_resolves(self):
        """booking-cancel resolves to BookingViewSet cancel action."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:booking-cancel', kwargs={'pk': pk})
        assert '/cancel/' in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'BookingViewSet'
        assert match.func.actions.get('post') == 'cancel'

    def test_booking_confirm_url_resolves(self):
        """booking-confirm resolves to BookingViewSet confirm action."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:booking-confirm', kwargs={'pk': pk})
        assert '/confirm/' in url
        match = resolve(url)
        assert match.func.cls.__name__ == 'BookingViewSet'
        assert match.func.actions.get('post') == 'confirm'


# ============================================================================
# Frontend URL Resolution Tests
# ============================================================================

@pytest.mark.django_db
class TestCalendarFrontendUrls:
    """Tests for calendar_app frontend URL patterns."""

    def test_calendar_view_url_resolves(self):
        """calendar_app:calendar resolves to CalendarView."""
        url = reverse('calendar_app:calendar')
        match = resolve(url)
        assert match.func.view_class.__name__ == 'CalendarView'

    def test_event_create_url_resolves(self):
        """calendar_app:event_create resolves to EventCreateView."""
        url = reverse('calendar_app:event_create')
        assert '/events/create/' in url
        match = resolve(url)
        assert match.func.view_class.__name__ == 'EventCreateView'

    def test_event_detail_url_resolves(self):
        """calendar_app:event_detail resolves to EventDetailView."""
        pk = uuid.uuid4()
        url = reverse('calendar_app:event_detail', kwargs={'pk': pk})
        assert str(pk) in url
        match = resolve(url)
        assert match.func.view_class.__name__ == 'EventDetailView'

    def test_booking_link_list_frontend_url_resolves(self):
        """calendar_app:booking_link_list resolves to BookingLinkListView."""
        url = reverse('calendar_app:booking_link_list')
        assert '/booking-links/' in url
        match = resolve(url)
        assert match.func.view_class.__name__ == 'BookingLinkListView'

    def test_booking_public_url_resolves(self):
        """calendar_app:booking_public resolves to BookingLinkPublicView."""
        url = reverse('calendar_app:booking_public', kwargs={'slug': 'my-meeting'})
        assert '/book/my-meeting/' in url
        match = resolve(url)
        assert match.func.view_class.__name__ == 'BookingLinkPublicView'

    def test_booking_confirm_url_resolves(self):
        """calendar_app:booking_confirm resolves to BookingConfirmView."""
        url = reverse('calendar_app:booking_confirm', kwargs={'slug': 'my-meeting'})
        assert '/book/my-meeting/confirm/' in url
        match = resolve(url)
        assert match.func.view_class.__name__ == 'BookingConfirmView'
