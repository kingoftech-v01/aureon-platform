"""
Views and ViewSets for the calendar_app API.
"""

from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import CalendarEvent, EventAttendee, BookingLink, Booking
from .serializers import (
    CalendarEventListSerializer,
    CalendarEventDetailSerializer,
    CalendarEventCreateUpdateSerializer,
    EventAttendeeSerializer,
    BookingLinkSerializer,
    BookingLinkCreateUpdateSerializer,
    BookingSerializer,
    BookingCreateSerializer,
)


class CalendarEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CalendarEvent CRUD operations.

    list: Get list of calendar events with filtering and search
    retrieve: Get calendar event details with attendees
    create: Create a new calendar event
    update: Update a calendar event
    partial_update: Partially update a calendar event
    destroy: Delete a calendar event
    """

    queryset = CalendarEvent.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'status', 'client', 'organizer']
    search_fields = ['title', 'description']
    ordering_fields = ['start_time', 'end_time', 'created_at']
    ordering = ['-start_time']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CalendarEventListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CalendarEventCreateUpdateSerializer
        return CalendarEventDetailSerializer

    def get_queryset(self):
        """Filter queryset with select_related for performance."""
        return super().get_queryset().select_related(
            'organizer', 'client', 'contract'
        ).prefetch_related('attendees')

    def perform_create(self, serializer):
        """Set organizer to the current user on create."""
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a calendar event.

        Sets the event status to CANCELLED.
        """
        event = self.get_object()
        event.status = CalendarEvent.CANCELLED
        event.save()
        serializer = CalendarEventDetailSerializer(event, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark a calendar event as completed.

        Sets the event status to COMPLETED.
        """
        event = self.get_object()
        event.status = CalendarEvent.COMPLETED
        event.save()
        serializer = CalendarEventDetailSerializer(event, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        """
        Get all attendees for a calendar event.
        """
        event = self.get_object()
        attendees = event.attendees.all()
        serializer = EventAttendeeSerializer(attendees, many=True, context={'request': request})
        return Response(serializer.data)


class EventAttendeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EventAttendee CRUD operations.
    """

    queryset = EventAttendee.objects.all()
    serializer_class = EventAttendeeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'response_status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset with select_related for performance."""
        return super().get_queryset().select_related('event', 'user')


class BookingLinkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BookingLink CRUD operations.
    """

    queryset = BookingLink.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return BookingLinkCreateUpdateSerializer
        return BookingLinkSerializer

    def get_queryset(self):
        """Filter queryset with select_related for performance."""
        return super().get_queryset().select_related('owner')

    def perform_create(self, serializer):
        """Set owner to the current user on create."""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Return available time slots for the next 7 days.

        Calculates open slots based on the booking link's available days,
        start/end times, duration, buffer, and existing confirmed bookings.
        """
        booking_link = self.get_object()
        now = timezone.now()
        slots = []

        for day_offset in range(7):
            current_date = (now + timedelta(days=day_offset)).date()
            day_of_week = current_date.isoweekday()  # Monday=1, Sunday=7

            if day_of_week not in booking_link.available_days:
                continue

            # Check max bookings per day
            if booking_link.max_bookings_per_day is not None:
                confirmed_count = Booking.objects.filter(
                    booking_link=booking_link,
                    event__start_time__date=current_date,
                    status=Booking.CONFIRMED,
                ).count()
                if confirmed_count >= booking_link.max_bookings_per_day:
                    continue

            # Get existing bookings for this day
            existing_bookings = CalendarEvent.objects.filter(
                booking__booking_link=booking_link,
                booking__status=Booking.CONFIRMED,
                start_time__date=current_date,
            ).values_list('start_time', 'end_time')

            booked_ranges = [
                (s, e) for s, e in existing_bookings
            ]

            # Generate time slots
            slot_start = timezone.make_aware(
                datetime.combine(current_date, booking_link.available_start_time)
            )
            slot_end_boundary = timezone.make_aware(
                datetime.combine(current_date, booking_link.available_end_time)
            )
            duration = timedelta(minutes=booking_link.duration_minutes)
            buffer = timedelta(minutes=booking_link.buffer_minutes)

            while slot_start + duration <= slot_end_boundary:
                candidate_end = slot_start + duration

                # Skip slots in the past
                if slot_start <= now:
                    slot_start = slot_start + duration + buffer
                    continue

                # Check for overlap with existing bookings
                is_available = True
                for booked_start, booked_end in booked_ranges:
                    if slot_start < booked_end and candidate_end > booked_start:
                        is_available = False
                        break

                if is_available:
                    slots.append({
                        'date': current_date.isoformat(),
                        'start_time': slot_start.isoformat(),
                        'end_time': candidate_end.isoformat(),
                    })

                slot_start = slot_start + duration + buffer

        return Response({'slots': slots})


class BookingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for Booking operations.

    Supports list, create, and retrieve. Update/delete not exposed directly.
    Use the cancel and confirm custom actions instead.
    """

    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['booking_link', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        """Filter queryset with select_related for performance."""
        return super().get_queryset().select_related('booking_link', 'event')

    def create(self, request, *args, **kwargs):
        """Create a booking and return full booking data."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        response_serializer = BookingSerializer(booking, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking.

        Sets the booking status to CANCELLED and records the cancellation time.
        """
        booking = self.get_object()
        booking.status = Booking.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.save()

        # Also cancel the associated event if it exists
        if booking.event:
            booking.event.status = CalendarEvent.CANCELLED
            booking.event.save()

        serializer = BookingSerializer(booking, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm a booking using a confirmation token.

        Expects: { "confirmation_token": "<token>" }
        """
        booking = self.get_object()
        token = request.data.get('confirmation_token')

        if not token:
            return Response(
                {'detail': 'Confirmation token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if token != booking.confirmation_token:
            return Response(
                {'detail': 'Invalid confirmation token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = Booking.CONFIRMED
        booking.save()

        serializer = BookingSerializer(booking, context={'request': request})
        return Response(serializer.data)
