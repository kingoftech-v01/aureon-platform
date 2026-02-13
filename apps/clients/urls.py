"""
URL configuration for clients app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, ClientNoteViewSet, ClientDocumentViewSet, PortalMessageViewSet
from .views_frontend import (
    ClientListView,
    ClientDetailView,
    ClientCreateView,
    ClientEditView,
    ClientPortalView,
    PortalMessagesView,
)

app_name = 'clients'

# API Router
router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'notes', ClientNoteViewSet, basename='client-note')
router.register(r'documents', ClientDocumentViewSet, basename='client-document')
router.register(r'portal-messages', PortalMessageViewSet, basename='portal-message')

api_urlpatterns = [
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('', ClientListView.as_view(), name='client_list'),
    path('create/', ClientCreateView.as_view(), name='client_create'),
    path('<uuid:pk>/', ClientDetailView.as_view(), name='client_detail'),
    path('<uuid:pk>/edit/', ClientEditView.as_view(), name='client_edit'),
    path('<uuid:pk>/portal/', ClientPortalView.as_view(), name='client_portal'),
    path('<uuid:pk>/messages/', PortalMessagesView.as_view(), name='portal_messages'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
