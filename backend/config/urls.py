"""
URL configuration for Aureon Finance SaaS Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.views import HomeView, DashboardView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Import health check views
from config.health import get_health_urls

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Homepage
    path('', HomeView.as_view(), name='home'),

    # Public Website (for namespace resolution in templates)
    path('', include('apps.website.urls')),

    # Django Allauth (for account_login, account_logout, etc.)
    path('accounts/', include('allauth.urls')),

    # React Dashboard Routes (catch-all for SPA)
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/<path:path>', DashboardView.as_view(), name='dashboard_path'),
    path('clients/', DashboardView.as_view(), name='clients'),
    path('clients/<path:path>', DashboardView.as_view(), name='clients_path'),
    path('contracts/', DashboardView.as_view(), name='contracts'),
    path('contracts/<path:path>', DashboardView.as_view(), name='contracts_path'),
    path('invoices/', DashboardView.as_view(), name='invoices'),
    path('invoices/<path:path>', DashboardView.as_view(), name='invoices_path'),
    path('payments/', DashboardView.as_view(), name='payments'),
    path('payments/<path:path>', DashboardView.as_view(), name='payments_path'),
    path('analytics/', DashboardView.as_view(), name='analytics'),
    path('documents/', DashboardView.as_view(), name='documents'),
    path('documents/<path:path>', DashboardView.as_view(), name='documents_path'),
    path('settings/', DashboardView.as_view(), name='settings'),
    path('settings/<path:path>', DashboardView.as_view(), name='settings_path'),
    path('auth/<path:path>', DashboardView.as_view(), name='auth'),

    # Health Check Endpoints (Rhematek Production Shield)
    *get_health_urls(),

    # API Documentation (DRF Spectacular) - must be before app API includes
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # JWT Token Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Authentication API
    path('api/auth/', include('apps.accounts.urls')),
    path('api/auth/', include('rest_framework.urls')),

    # Website Marketing API (for React frontend)
    path('api/v1/website/', include('apps.website.api_urls')),

    # Core Business Apps API
    path('api/', include('apps.clients.urls')),
    path('api/', include('apps.contracts.urls')),
    path('api/', include('apps.invoicing.urls')),
    path('api/', include('apps.payments.urls')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.documents.urls')),
    path('api/', include('apps.integrations.urls')),

    # Tenants API
    path('api/', include('apps.tenants.urls')),

    # Analytics API
    path('api/analytics/', include('apps.analytics.urls')),

    # Subscriptions API
    path('api/subscriptions/', include('apps.subscriptions.urls')),

    # Webhooks (must be before API docs for proper routing)
    path('webhooks/', include('apps.webhooks.urls')),

    # Stripe Webhooks
    path('webhooks/stripe/', include('djstripe.urls', namespace='djstripe')),

    # Prometheus Metrics
    path('', include('django_prometheus.urls')),
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

# Custom error handlers (Rhematek Production Shield)
handler400 = 'config.error_handlers.handler400'
handler403 = 'config.error_handlers.handler403'
handler404 = 'config.error_handlers.handler404'
handler500 = 'config.error_handlers.handler500'
