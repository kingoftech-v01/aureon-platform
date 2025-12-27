"""
URL configuration for tenant-specific routes.

This file handles all URLs for tenant schemas (individual organizations).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # API Schema & Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication APIs
    path('api/auth/', include('rest_framework.urls')),
    path('api/auth/', include('dj_rest_auth.urls')),  # Login, Logout, Password Reset
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),  # Registration

    # JWT Tokens
    path('api/token/', include([
        path('', include('rest_framework_simplejwt.urls')),
    ])),

    # App APIs (Tenant-specific)
    path('', include('apps.accounts.urls')),  # User management
    path('', include('apps.clients.urls')),  # CRM
    path('', include('apps.contracts.urls')),  # Contracts
    path('', include('apps.invoicing.urls')),  # Invoices
    path('', include('apps.payments.urls')),  # Payments
    path('', include('apps.notifications.urls')),  # Notifications
    path('', include('apps.analytics.urls')),  # Analytics
    path('', include('apps.documents.urls')),  # Documents
    path('', include('apps.webhooks.urls')),  # Webhooks
    path('', include('apps.integrations.urls')),  # Integrations

    # Django Allauth
    path('accounts/', include('allauth.urls')),

    # Prometheus Metrics (optional, can be restricted)
    path('', include('django_prometheus.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin customization
admin.site.site_header = "Aureon Administration"
admin.site.site_title = "Aureon Admin"
admin.site.index_title = "Welcome to Aureon by Rhematek Solutions"
