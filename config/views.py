"""
Home and authentication views for Aureon SaaS Platform.
"""
import os
from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings


class HomeView(View):
    """
    Home view that serves different content based on the domain.

    - Main domain (aureon.rhematek-solutions.com): Shows landing/vitrine page
    - Tenant subdomain (demo.aureon.rhematek-solutions.com): Shows React dashboard
    """

    MAIN_DOMAINS = [
        'aureon.rhematek-solutions.com',
        'www.aureon.rhematek-solutions.com',
        'localhost',
        '127.0.0.1',
    ]

    def get(self, request):
        host = request.get_host().split(':')[0]  # Remove port if present

        # Check if this is the main domain
        if host in self.MAIN_DOMAINS:
            return render(request, 'website/home_plax.html')

        # Check if this is a tenant subdomain
        if host.endswith('.aureon.rhematek-solutions.com'):
            return self.handle_tenant_request(request, host)

        # Check if this is a tenant subdomain on localhost
        if host.endswith('.localhost'):
            return self.handle_tenant_request(request, host)

        # Default to landing page
        return render(request, 'website/home_plax.html')

    def handle_tenant_request(self, request, host):
        """Handle requests to tenant subdomains."""
        from apps.tenants.models import Domain, Tenant

        try:
            # Look up the domain
            domain = Domain.objects.select_related('tenant').get(domain=host)
            tenant = domain.tenant

            if not tenant.is_active:
                return render(request, 'tenant/inactive.html', {
                    'tenant': tenant,
                }, status=403)

            # Store tenant in request for use in templates
            request.tenant = tenant

            # If user is authenticated, serve React dashboard
            if request.user.is_authenticated:
                return self.serve_react_app(request, tenant)

            # Show tenant login/welcome page
            return render(request, 'tenant/welcome.html', {
                'tenant': tenant,
            })

        except Domain.DoesNotExist:
            # Domain not found - show error page
            return render(request, 'tenant/not_found.html', {
                'host': host,
            }, status=404)

    def serve_react_app(self, request, tenant):
        """Serve the React dashboard application."""
        # Try multiple locations for the React app's index.html
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

        for react_index_path in possible_paths:
            if os.path.exists(react_index_path):
                with open(react_index_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                return HttpResponse(html, content_type='text/html')

        # Fallback to Django template if React build not available
        return render(request, 'tenant/dashboard.html', {
            'tenant': tenant,
        })


class TenantDashboardView(View):
    """
    Serve the React dashboard for all authenticated tenant routes.
    This catches /dashboard, /clients, /contracts, /invoices, etc.
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

    def get(self, request, path=''):
        tenant = self.get_tenant(request)
        if not tenant:
            return redirect('home')

        if not request.user.is_authenticated:
            return redirect('tenant_login')

        # Try multiple locations for the React app's index.html
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

        for react_index_path in possible_paths:
            if os.path.exists(react_index_path):
                with open(react_index_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                return HttpResponse(html, content_type='text/html')

        # Fallback to Django template if React build not available
        return render(request, 'tenant/dashboard.html', {
            'tenant': tenant,
        })


class TenantLoginView(View):
    """
    Login view for tenant subdomains.
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
        tenant = self.get_tenant(request)
        if not tenant:
            return redirect('home')

        # Already logged in? Go to dashboard
        if request.user.is_authenticated:
            return redirect('home')

        return render(request, 'tenant/login.html', {
            'tenant': tenant,
            'next': request.GET.get('next', '/'),
        })

    def post(self, request):
        tenant = self.get_tenant(request)
        if not tenant:
            return redirect('home')

        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '/')

        if not email or not password:
            return render(request, 'tenant/login.html', {
                'tenant': tenant,
                'error': 'Please enter both email and password.',
                'email': email,
                'next': next_url,
            })

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Check if user belongs to this tenant (or is superuser)
            if user.is_superuser or (user.tenant and user.tenant.id == tenant.id):
                login(request, user)
                return redirect(next_url if next_url else '/')
            else:
                return render(request, 'tenant/login.html', {
                    'tenant': tenant,
                    'error': 'You do not have access to this workspace.',
                    'email': email,
                    'next': next_url,
                })
        else:
            return render(request, 'tenant/login.html', {
                'tenant': tenant,
                'error': 'Invalid email or password.',
                'email': email,
                'next': next_url,
            })


class TenantLogoutView(View):
    """
    Logout view for tenant subdomains.
    """

    def get(self, request):
        logout(request)
        return redirect('home')

    def post(self, request):
        logout(request)
        return redirect('home')
