"""
Serializers for the calendar_app.
"""

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from .models import CalendarEvent, EventAttendee, BookingLink, Booking


class EventAttendeeSerializer(serializers.ModelSerializer):
    """
    Serializer for event attendees.
    """

    class Meta:
        model = EventAttendee
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class CalendarEventListSerializer(serializers.ModelSerializer):
    """
    Serializer for calendar event list view (minimal fields).
    """
    organizer = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    attendees_count = serializers.SerializerMethodField()

    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'title', 'event_type', 'start_time', 'end_time',
            'all_day', 'status', 'organizer', 'client', 'color',
            'attendees_count',
        ]
        read_only_fields = ['id']

    def get_organizer(self, obj):
        """Return organizer id and email."""
        return {
            'id': str(obj.organizer.id),
            'email': obj.organizer.email,
        }

    def get_client(self, obj):
        """Return client id and name."""
        if obj.client:
            return {
                'id': str(obj.client.id),
                'name': obj.client.get_display_name(),
            }
        return None

    def get_attendees_count(self, obj):
        """Return the number of attendees."""
        return obj.attendees.count()


class CalendarEventDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for calendar event detail view.
    """
    attendees = EventAttendeeSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = CalendarEvent
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_duration(self, obj):
        """Return duration as total seconds."""
        delta = obj.duration
        return delta.total_seconds() if delta else None


class CalendarEventCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating calendar events.
    """

    class Meta:
        model = CalendarEvent
        fields = [
            'title', 'description', 'event_type', 'start_time', 'end_time',
            'all_day', 'location', 'video_link', 'client', 'contract',
            'recurrence_rule', 'reminder_minutes', 'color',
        ]

    def validate(self, data):
        """Validate event data."""
        start_time = data.get('start_time') or (self.instance.start_time if self.instance else None)
        end_time = data.get('end_time') or (self.instance.end_time if self.instance else None)

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })

        return data


class BookingLinkSerializer(serializers.ModelSerializer):
    """
    Serializer for booking links (read).
    """

    class Meta:
        model = BookingLink
        fields = '__all__'
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class BookingLinkCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating booking links.
    """

    class Meta:
        model = BookingLink
        fields = [
            'title', 'description', 'slug', 'duration_minutes',
            'available_days', 'available_start_time', 'available_end_time',
            'buffer_minutes', 'max_bookings_per_day', 'is_active',
        ]

    def validate(self, data):
        """Validate booking link data."""
        start = data.get('available_start_time')
        end = data.get('available_end_time')

        if start and end and end <= start:
            raise serializers.ValidationError({
                'available_end_time': 'Available end time must be after available start time.'
            })

        return data


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for bookings (read).
    """

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = [
            'id', 'confirmation_token', 'cancelled_at', 'created_at',
        ]


class BookingCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a booking.

    Accepts a booking_link, booker details, and a start_time to
    automatically create the associated CalendarEvent.
    """
    booking_link = serializers.PrimaryKeyRelatedField(
        queryset=BookingLink.objects.all()
    )
    booker_name = serializers.CharField(max_length=255)
    booker_email = serializers.EmailField()
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    start_time = serializers.DateTimeField(write_only=True)

    def validate_booking_link(self, value):
        """Ensure booking link is active."""
        if not value.is_active:
            raise serializers.ValidationError('This booking link is not active.')
        return value

    def validate(self, data):
        """Validate booking against booking link availability."""
        booking_link = data['booking_link']
        start_time = data['start_time']

        # Check if the day is available
        day_of_week = start_time.isoweekday()  # Monday=1, Sunday=7
        if day_of_week not in booking_link.available_days:
            raise serializers.ValidationError({
                'start_time': 'The selected day is not available for bookings.'
            })

        # Check if the time is within available hours
        event_time = start_time.time()
        if event_time < booking_link.available_start_time or event_time >= booking_link.available_end_time:
            raise serializers.ValidationError({
                'start_time': 'The selected time is outside available hours.'
            })

        # Check max bookings per day
        if booking_link.max_bookings_per_day is not None:
            bookings_on_day = Booking.objects.filter(
                booking_link=booking_link,
                event__start_time__date=start_time.date(),
                status=Booking.CONFIRMED,
            ).count()
            if bookings_on_day >= booking_link.max_bookings_per_day:
                raise serializers.ValidationError({
                    'start_time': 'Maximum bookings for this day has been reached.'
                })

        return data

    def create(self, validated_data):
        """Create a booking with an associated CalendarEvent."""
        booking_link = validated_data['booking_link']
        start_time = validated_data.pop('start_time')
        end_time = start_time + timedelta(minutes=booking_link.duration_minutes)

        # Create the calendar event
        event = CalendarEvent.objects.create(
            title=f"Booking: {booking_link.title} with {validated_data['booker_name']}",
            description=validated_data.get('notes', ''),
            event_type=CalendarEvent.MEETING,
            start_time=start_time,
            end_time=end_time,
            organizer=booking_link.owner,
            status=CalendarEvent.SCHEDULED,
        )

        # Create the booking
        booking = Booking.objects.create(
            booking_link=booking_link,
            event=event,
            booker_name=validated_data['booker_name'],
            booker_email=validated_data['booker_email'],
            notes=validated_data.get('notes', ''),
        )

        return booking
