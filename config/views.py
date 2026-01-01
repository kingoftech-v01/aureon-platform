"""
Home and authentication views for Aureon SaaS Platform.

All frontend rendering is handled by React SPA.
Django only serves the React app's index.html for all routes.
"""
import os
from django.shortcuts import redirect
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.conf import settings


def serve_react_app(request, context=None):
    """
    Serve the React SPA index.html.

    Looks for the React build in multiple locations for
    both development and production environments.
    """
    possible_paths = []

    # 1. Check STATIC_ROOT (after collectstatic)
    if settings.STATIC_ROOT:
        possible_paths.append(os.path.join(settings.STATIC_ROOT, 'dashboard', 'index.html'))

    # 2. Check STATICFILES_DIRS (development)
    if hasattr(settings, 'STATICFILES_DIRS'):
        for static_dir in settings.STATICFILES_DIRS:
            possible_paths.append(os.path.join(static_dir, 'dashboard', 'index.html'))

    # 3. Check relative to BASE_DIR
    possible_paths.append(os.path.join(settings.BASE_DIR, 'static', 'dashboard', 'index.html'))
    possible_paths.append(os.path.join(settings.BASE_DIR, 'staticfiles', 'dashboard', 'index.html'))

    # 4. Check frontend/dist for development
    possible_paths.append(os.path.join(settings.BASE_DIR, 'frontend', 'dist', 'index.html'))

    for react_index_path in possible_paths:
        if os.path.exists(react_index_path):
            with open(react_index_path, 'r', encoding='utf-8') as f:
                html = f.read()
            return HttpResponse(html, content_type='text/html')

    # Fallback: React build not found - show setup page
    # Note: Inline styles used here as fallback when React isn't built yet
    return HttpResponse('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aureon - Setup Required</title>
</head>
<body style="font-family: system-ui, -apple-system, sans-serif; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; padding: 20px;">
    <div style="background: white; border-radius: 16px; padding: 48px; max-width: 520px; text-align: center; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);">
        <div style="width: 72px; height: 72px; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 16px; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px;">
            <span style="color: white; font-size: 28px; font-weight: bold;">A</span>
        </div>
        <h1 style="color: #111827; margin: 0 0 12px; font-size: 28px; font-weight: 700;">Aureon Platform</h1>
        <p style="color: #6b7280; margin: 0 0 32px; line-height: 1.6; font-size: 16px;">The frontend application needs to be built before the site can be accessed.</p>
        <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; text-align: left; margin-bottom: 32px;">
            <p style="color: #374151; font-size: 14px; font-weight: 600; margin: 0 0 12px;">Build Commands:</p>
            <code style="display: block; background: #1f2937; color: #10b981; padding: 16px; border-radius: 8px; font-size: 13px; line-height: 1.8; overflow-x: auto;">cd frontend<br>npm install<br>npm run build<br>python manage.py collectstatic --noinput</code>
        </div>
        <p style="color: #9ca3af; font-size: 13px; margin: 0;">Powered by <strong>Rhematek Solutions</strong></p>
    </div>
</body>
</html>''', content_type='text/html')


class HomeView(View):
    """
    Home view that serves React SPA for all requests.

    - Main domain: Serves React landing page
    - Tenant subdomain: Serves React dashboard/tenant pages
    """

    MAIN_DOMAINS = [
        'aureon.rhematek-solutions.com',
        'www.aureon.rhematek-solutions.com',
        'localhost',
        '127.0.0.1',
    ]

    def get(self, request):
        # All requests are handled by React SPA
        return serve_react_app(request)


class TenantDashboardView(View):
    """
    Serve the React dashboard for all authenticated tenant routes.
    This catches /dashboard, /clients, /contracts, /invoices, etc.
    """

    def get(self, request, path=''):
        # React handles authentication state and routing
        return serve_react_app(request)


class TenantLoginView(View):
    """
    Login view for tenant subdomains.
    Redirects to React login page, handles POST for API compatibility.
    """

    def get_tenant(self, request):
        """Get the tenant from the request host."""
        from apps.tenants.models import Domain

        host = request.get_host().split(':')[0]
        try:
            domain = Domain.objects.select_related('tenant').get(domain=host)
            return domain.tenant
        except Domain.DoesNotExist:
            return None

    def get(self, request):
        # Serve React SPA which will handle routing to login page
        return serve_react_app(request)

    def post(self, request):
        """Handle login POST request for API compatibility."""
        tenant = self.get_tenant(request)

        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '/dashboard')

        if not email or not password:
            return JsonResponse({
                'success': False,
                'error': 'Please enter both email and password.'
            }, status=400)

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Check if user belongs to this tenant (or is superuser)
            if tenant is None or user.is_superuser or (user.tenant and user.tenant.id == tenant.id):
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'redirect': next_url
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'You do not have access to this workspace.'
                }, status=403)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid email or password.'
            }, status=401)


class TenantLogoutView(View):
    """
    Logout view for tenant subdomains.
    """

    def get(self, request):
        logout(request)
        return redirect('/auth/login')

    def post(self, request):
        logout(request)
        return JsonResponse({'success': True})


class ReactCatchAllView(View):
    """
    Catch-all view that serves React SPA for all frontend routes.
    This ensures React Router handles all client-side routing.
    """

    def get(self, request, path=''):
        return serve_react_app(request)
