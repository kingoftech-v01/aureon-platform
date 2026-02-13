"""
URL configuration for calendar_app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CalendarEventViewSet,
    EventAttendeeViewSet,
    BookingLinkViewSet,
    BookingViewSet,
)
from .views_frontend import (
    CalendarView,
    EventDetailView,
    EventCreateView,
    BookingLinkListView,
    BookingLinkPublicView,
    BookingConfirmView,
)

app_name = 'calendar_app'

router = DefaultRouter()
router.register(r'calendar-events', CalendarEventViewSet, basename='calendar-event')
router.register(r'event-attendees', EventAttendeeViewSet, basename='event-attendee')
router.register(r'booking-links', BookingLinkViewSet, basename='booking-link')
router.register(r'bookings', BookingViewSet, basename='booking')

api_urlpatterns = [
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('', CalendarView.as_view(), name='calendar'),
    path('events/create/', EventCreateView.as_view(), name='event_create'),
    path('events/<uuid:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('booking-links/', BookingLinkListView.as_view(), name='booking_link_list'),
    path('book/<slug:slug>/', BookingLinkPublicView.as_view(), name='booking_public'),
    path('book/<slug:slug>/confirm/', BookingConfirmView.as_view(), name='booking_confirm'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
