"""
URL configuration for Aureon Finance SaaS Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.views import HomeView, TenantLoginView, TenantLogoutView, TenantDashboardView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Import health check views
from config.health import get_health_urls

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Homepage - Tenant-aware home view
    path('', HomeView.as_view(), name='home'),

    # Tenant Authentication
    path('login/', TenantLoginView.as_view(), name='tenant_login'),
    path('logout/', TenantLogoutView.as_view(), name='tenant_logout'),

    # React Dashboard Routes (catch-all for SPA)
    path('dashboard/', TenantDashboardView.as_view(), name='tenant_dashboard'),
    path('dashboard/<path:path>', TenantDashboardView.as_view(), name='tenant_dashboard_path'),
    path('clients/', TenantDashboardView.as_view(), name='tenant_clients'),
    path('clients/<path:path>', TenantDashboardView.as_view(), name='tenant_clients_path'),
    path('contracts/', TenantDashboardView.as_view(), name='tenant_contracts'),
    path('contracts/<path:path>', TenantDashboardView.as_view(), name='tenant_contracts_path'),
    path('invoices/', TenantDashboardView.as_view(), name='tenant_invoices'),
    path('invoices/<path:path>', TenantDashboardView.as_view(), name='tenant_invoices_path'),
    path('payments/', TenantDashboardView.as_view(), name='tenant_payments'),
    path('payments/<path:path>', TenantDashboardView.as_view(), name='tenant_payments_path'),
    path('analytics/', TenantDashboardView.as_view(), name='tenant_analytics'),
    path('documents/', TenantDashboardView.as_view(), name='tenant_documents'),
    path('documents/<path:path>', TenantDashboardView.as_view(), name='tenant_documents_path'),
    path('settings/', TenantDashboardView.as_view(), name='tenant_settings'),
    path('settings/<path:path>', TenantDashboardView.as_view(), name='tenant_settings_path'),
    path('auth/<path:path>', TenantDashboardView.as_view(), name='tenant_auth'),

    # Health Check Endpoints (Rhematek Production Shield)
    *get_health_urls(),

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

# Custom error handlers (Rhematek Production Shield)
handler400 = 'config.error_handlers.handler400'
handler403 = 'config.error_handlers.handler403'
handler404 = 'config.error_handlers.handler404'
handler500 = 'config.error_handlers.handler500'
