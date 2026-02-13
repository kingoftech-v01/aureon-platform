"""
Admin configuration for calendar_app.
"""

from django.contrib import admin
from .models import CalendarEvent, EventAttendee, BookingLink, Booking


class EventAttendeeInline(admin.TabularInline):
    """Inline admin for event attendees."""
    model = EventAttendee
    extra = 1
    fields = ['email', 'name', 'user', 'response_status']


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    """Admin for CalendarEvent model."""

    list_display = [
        'title', 'event_type', 'start_time', 'end_time', 'all_day',
        'organizer', 'client', 'status', 'created_at',
    ]
    list_filter = ['event_type', 'status', 'all_day', 'created_at']
    search_fields = [
        'title', 'description', 'organizer__email',
        'organizer__first_name', 'organizer__last_name',
        'client__first_name', 'client__last_name', 'client__company_name',
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [EventAttendeeInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'event_type', 'status', 'color')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time', 'all_day', 'recurrence_rule', 'reminder_minutes')
        }),
        ('Location', {
            'fields': ('location', 'video_link')
        }),
        ('Relationships', {
            'fields': ('organizer', 'client', 'contract')
        }),
        ('External', {
            'fields': ('external_id', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    """Admin for EventAttendee model."""

    list_display = ['email', 'name', 'event', 'user', 'response_status', 'created_at']
    list_filter = ['response_status', 'created_at']
    search_fields = ['email', 'name', 'event__title']
    readonly_fields = ['id', 'created_at']

    fieldsets = (
        ('Attendee Information', {
            'fields': ('id', 'event', 'user', 'email', 'name', 'response_status')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingLink)
class BookingLinkAdmin(admin.ModelAdmin):
    """Admin for BookingLink model."""

    list_display = [
        'title', 'slug', 'owner', 'duration_minutes',
        'is_active', 'created_at',
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'slug', 'owner__email', 'owner__first_name', 'owner__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'owner', 'title', 'slug', 'description', 'is_active')
        }),
        ('Availability', {
            'fields': (
                'duration_minutes', 'available_days',
                'available_start_time', 'available_end_time',
                'buffer_minutes', 'max_bookings_per_day',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin for Booking model."""

    list_display = [
        'booker_name', 'booker_email', 'booking_link', 'event',
        'status', 'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'booker_name', 'booker_email', 'booking_link__title',
        'confirmation_token',
    ]
    readonly_fields = ['id', 'confirmation_token', 'created_at', 'cancelled_at']

    fieldsets = (
        ('Booking Information', {
            'fields': ('id', 'booking_link', 'event', 'booker_name', 'booker_email', 'notes')
        }),
        ('Status', {
            'fields': ('status', 'confirmation_token', 'cancelled_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
