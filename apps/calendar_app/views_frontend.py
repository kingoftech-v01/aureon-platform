"""
Frontend views for the calendar_app.

Provides class-based views for calendar display, event detail, event creation,
booking link management, public booking view, and booking confirmation.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView

from .models import CalendarEvent, EventAttendee, BookingLink, Booking


class CalendarView(LoginRequiredMixin, TemplateView):
    """Calendar view showing events for the current user."""
    template_name = 'calendar_app/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Calendar'
        # Get events organized by the current user or where they are an attendee
        context['events'] = CalendarEvent.objects.filter(
            organizer=self.request.user
        ).select_related('client', 'contract').order_by('start_time')
        context['event_type_choices'] = CalendarEvent.EVENT_TYPE_CHOICES
        context['status_choices'] = CalendarEvent.STATUS_CHOICES
        # Upcoming events (next 7 days)
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        context['upcoming_events'] = CalendarEvent.objects.filter(
            organizer=self.request.user,
            start_time__gte=now,
            start_time__lte=now + timedelta(days=7),
            status=CalendarEvent.SCHEDULED
        ).order_by('start_time')
        return context


class EventDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a calendar event with attendees."""
    template_name = 'calendar_app/event_detail.html'
    model = CalendarEvent
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Event: {self.object.title}'
        context['attendees'] = self.object.attendees.all()
        context['client'] = self.object.client
        context['contract'] = self.object.contract
        context['organizer'] = self.object.organizer
        context['duration'] = self.object.duration
        # Check if this event has a booking
        context['booking'] = getattr(self.object, 'booking', None)
        return context


class EventCreateView(LoginRequiredMixin, CreateView):
    """Create a new calendar event."""
    template_name = 'calendar_app/event_create.html'
    model = CalendarEvent
    fields = [
        'title', 'description', 'event_type', 'start_time', 'end_time',
        'all_day', 'location', 'video_link', 'client', 'contract',
        'recurrence_rule', 'reminder_minutes', 'color',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Event'
        context['event_type_choices'] = CalendarEvent.EVENT_TYPE_CHOICES
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        from apps.contracts.models import Contract
        context['contracts'] = Contract.objects.filter(status=Contract.ACTIVE)
        return context


class BookingLinkListView(LoginRequiredMixin, ListView):
    """List all booking links for the current user."""
    template_name = 'calendar_app/booking_link_list.html'
    context_object_name = 'booking_links'

    def get_queryset(self):
        return BookingLink.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Booking Links'
        context['active_count'] = BookingLink.objects.filter(
            owner=self.request.user, is_active=True
        ).count()
        context['total_bookings'] = Booking.objects.filter(
            booking_link__owner=self.request.user
        ).count()
        return context


class BookingLinkPublicView(TemplateView):
    """Public booking link page -- no login required."""
    template_name = 'calendar_app/booking_link_public.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_link = BookingLink.objects.get(slug=self.kwargs['slug'])
        context['booking_link'] = booking_link
        context['page_title'] = f'Book: {booking_link.title}'
        context['owner'] = booking_link.owner
        context['duration_minutes'] = booking_link.duration_minutes
        context['available_days'] = booking_link.available_days
        context['available_start_time'] = booking_link.available_start_time
        context['available_end_time'] = booking_link.available_end_time
        context['is_active'] = booking_link.is_active
        return context


class BookingConfirmView(TemplateView):
    """Booking confirmation page showing booking details after scheduling."""
    template_name = 'calendar_app/booking_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = Booking.objects.select_related(
            'booking_link', 'event'
        ).get(confirmation_token=self.kwargs['token'])
        context['booking'] = booking
        context['page_title'] = 'Booking Confirmed'
        context['booking_link'] = booking.booking_link
        context['event'] = booking.event
        context['booker_name'] = booking.booker_name
        context['booker_email'] = booking.booker_email
        context['status'] = booking.status
        return context
