"""
Views for the calendar_app.

Re-exports from views_api for convenience.
"""

from .views_api import (  # noqa: F401
    CalendarEventViewSet,
    EventAttendeeViewSet,
    BookingLinkViewSet,
    BookingViewSet,
)
