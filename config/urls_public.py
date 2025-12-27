"""
URL configuration for public schema routes.

This file handles URLs for the public schema (shared across all tenants):
- Marketing website
- Blog
- Product pages
- Public APIs
- Tenant registration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin (Public Schema - for superusers)
    path('admin/', admin.site.urls),

    # Public Website & Marketing
    path('', include('apps.website.urls')),  # Homepage, pricing, features, etc.

    # Tenant Management (Public)
    path('', include('apps.tenants.urls')),  # Tenant registration and management

    # Authentication for public access
    path('api/auth/', include('rest_framework.urls')),
    path('accounts/', include('allauth.urls')),

    # Stripe Webhooks (Public endpoint)
    path('webhooks/stripe/', include('djstripe.urls', namespace='djstripe')),

    # Prometheus Metrics (optional)
    path('', include('django_prometheus.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin customization
admin.site.site_header = "Aureon Public Administration"
admin.site.site_title = "Aureon Public Admin"
admin.site.index_title = "Public Schema Management"
