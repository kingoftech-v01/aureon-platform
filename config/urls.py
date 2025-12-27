"""
URL configuration for Aureon Finance SaaS Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Homepage - Serve React frontend
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

    # Authentication API
    path('api/auth/', include('apps.accounts.urls')),

    # Core Business Apps API
    path('api/', include('apps.clients.urls')),
    path('api/', include('apps.contracts.urls')),
    path('api/', include('apps.invoicing.urls')),
    path('api/', include('apps.payments.urls')),

    # Analytics API
    path('api/analytics/', include('apps.analytics.urls')),

    # Webhooks (must be before API docs for proper routing)
    path('webhooks/', include('apps.webhooks.urls')),

    # API Documentation (DRF Spectacular)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Admin site customization
admin.site.site_header = 'Aureon Platform Administration'
admin.site.site_title = 'Aureon Admin'
admin.site.index_title = 'Welcome to Aureon by Rhematek Solutions'
