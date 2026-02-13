"""
Calendar event, attendee, booking link, and booking models.
"""

import secrets
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class CalendarEvent(models.Model):
    """
    Calendar event model for scheduling meetings, deadlines, milestones, etc.
    """

    # Event Types
    MEETING = 'meeting'
    DEADLINE = 'deadline'
    MILESTONE = 'milestone'
    FOLLOW_UP = 'follow_up'
    OTHER = 'other'

    EVENT_TYPE_CHOICES = [
        (MEETING, _('Meeting')),
        (DEADLINE, _('Deadline')),
        (MILESTONE, _('Milestone')),
        (FOLLOW_UP, _('Follow-up')),
        (OTHER, _('Other')),
    ]

    # Event Status
    SCHEDULED = 'scheduled'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'

    STATUS_CHOICES = [
        (SCHEDULED, _('Scheduled')),
        (CANCELLED, _('Cancelled')),
        (COMPLETED, _('Completed')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    title = models.CharField(
        _('Title'),
        max_length=255,
        help_text=_('Event title')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Event description')
    )

    event_type = models.CharField(
        _('Event Type'),
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default=MEETING
    )

    start_time = models.DateTimeField(
        _('Start Time'),
        help_text=_('Event start date and time')
    )

    end_time = models.DateTimeField(
        _('End Time'),
        help_text=_('Event end date and time')
    )

    all_day = models.BooleanField(
        _('All Day'),
        default=False,
        help_text=_('Whether this is an all-day event')
    )

    location = models.CharField(
        _('Location'),
        max_length=255,
        blank=True,
        help_text=_('Physical location of the event')
    )

    video_link = models.URLField(
        _('Video Link'),
        blank=True,
        help_text=_('Video conferencing link')
    )

    organizer = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='organized_events',
        help_text=_('User who organized this event')
    )

    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendar_events',
        help_text=_('Client associated with this event')
    )

    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendar_events',
        help_text=_('Contract associated with this event')
    )

    recurrence_rule = models.CharField(
        _('Recurrence Rule'),
        max_length=255,
        blank=True,
        help_text=_('RRULE string for recurring events')
    )

    reminder_minutes = models.IntegerField(
        _('Reminder Minutes'),
        default=30,
        help_text=_('Minutes before event to send reminder')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=SCHEDULED
    )

    external_id = models.CharField(
        _('External ID'),
        max_length=255,
        blank=True,
        help_text=_('ID from external calendar system')
    )

    color = models.CharField(
        _('Color'),
        max_length=7,
        blank=True,
        help_text=_('Hex color code for the event (e.g., #FF5733)')
    )

    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional metadata in JSON format')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Calendar Event')
        verbose_name_plural = _('Calendar Events')
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['organizer']),
            models.Index(fields=['client']),
            models.Index(fields=['start_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.start_time})"

    @property
    def duration(self):
        """Return the duration of the event."""
        return self.end_time - self.start_time


class EventAttendee(models.Model):
    """
    Attendee for a calendar event.
    """

    # Response Status
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'
    TENTATIVE = 'tentative'

    RESPONSE_STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (ACCEPTED, _('Accepted')),
        (DECLINED, _('Declined')),
        (TENTATIVE, _('Tentative')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    event = models.ForeignKey(
        CalendarEvent,
        on_delete=models.CASCADE,
        related_name='attendees',
        help_text=_('Event this attendee is associated with')
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='event_attendances',
        help_text=_('User account of the attendee (if registered)')
    )

    email = models.EmailField(
        _('Email'),
        help_text=_('Email address of the attendee')
    )

    name = models.CharField(
        _('Name'),
        max_length=255,
        blank=True,
        help_text=_('Name of the attendee')
    )

    response_status = models.CharField(
        _('Response Status'),
        max_length=20,
        choices=RESPONSE_STATUS_CHOICES,
        default=PENDING
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Event Attendee')
        verbose_name_plural = _('Event Attendees')
        unique_together = ['event', 'email']

    def __str__(self):
        return f"{self.name or self.email} - {self.response_status}"


class BookingLink(models.Model):
    """
    Booking link for scheduling appointments.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='booking_links',
        help_text=_('User who owns this booking link')
    )

    slug = models.SlugField(
        _('Slug'),
        unique=True,
        help_text=_('URL-friendly identifier for the booking link')
    )

    title = models.CharField(
        _('Title'),
        max_length=255,
        help_text=_('Title of the booking link')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description of the booking link')
    )

    duration_minutes = models.IntegerField(
        _('Duration (minutes)'),
        help_text=_('Duration of each booking in minutes')
    )

    available_days = models.JSONField(
        _('Available Days'),
        default=list,
        help_text=_('List of available days (1=Monday, 7=Sunday), e.g. [1,2,3,4,5]')
    )

    available_start_time = models.TimeField(
        _('Available Start Time'),
        help_text=_('Earliest time for bookings')
    )

    available_end_time = models.TimeField(
        _('Available End Time'),
        help_text=_('Latest time for bookings')
    )

    buffer_minutes = models.IntegerField(
        _('Buffer Minutes'),
        default=0,
        help_text=_('Buffer time between bookings in minutes')
    )

    max_bookings_per_day = models.IntegerField(
        _('Max Bookings Per Day'),
        null=True,
        blank=True,
        help_text=_('Maximum number of bookings allowed per day')
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this booking link is currently active')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Booking Link')
        verbose_name_plural = _('Booking Links')
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Booking(models.Model):
    """
    A booking made through a booking link.
    """

    # Booking Status
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    NO_SHOW = 'no_show'

    STATUS_CHOICES = [
        (CONFIRMED, _('Confirmed')),
        (CANCELLED, _('Cancelled')),
        (COMPLETED, _('Completed')),
        (NO_SHOW, _('No Show')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    booking_link = models.ForeignKey(
        BookingLink,
        on_delete=models.CASCADE,
        related_name='bookings',
        help_text=_('Booking link this booking was made through')
    )

    event = models.OneToOneField(
        CalendarEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booking',
        help_text=_('Calendar event created for this booking')
    )

    booker_name = models.CharField(
        _('Booker Name'),
        max_length=255,
        help_text=_('Name of the person who made the booking')
    )

    booker_email = models.EmailField(
        _('Booker Email'),
        help_text=_('Email of the person who made the booking')
    )

    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Additional notes from the booker')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=CONFIRMED
    )

    confirmation_token = models.CharField(
        _('Confirmation Token'),
        max_length=64,
        unique=True,
        help_text=_('Unique token for booking confirmation')
    )

    cancelled_at = models.DateTimeField(
        _('Cancelled At'),
        null=True,
        blank=True,
        help_text=_('When the booking was cancelled')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Booking')
        verbose_name_plural = _('Bookings')
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking by {self.booker_name} - {self.status}"

    def save(self, *args, **kwargs):
        """Auto-generate confirmation_token if not set."""
        if not self.confirmation_token:
            self.confirmation_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
