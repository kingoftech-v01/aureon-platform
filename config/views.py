"""
Home view with tenant detection for Aureon SaaS Platform.
"""
from django.shortcuts import render, redirect
from django.views import View
from django.http import Http404


class HomeView(View):
    """
    Home view that serves different content based on the domain.

    - Main domain (aureon.rhematek-solutions.com): Shows landing/vitrine page
    - Tenant subdomain (demo.aureon.rhematek-solutions.com): Shows tenant dashboard
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
            return render(request, 'index.html')

        # Check if this is a tenant subdomain
        if host.endswith('.aureon.rhematek-solutions.com'):
            return self.handle_tenant_request(request, host)

        # Check if this is a tenant subdomain on localhost
        if host.endswith('.localhost'):
            return self.handle_tenant_request(request, host)

        # Default to landing page
        return render(request, 'index.html')

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

            # If user is authenticated, show dashboard
            if request.user.is_authenticated:
                return render(request, 'tenant/dashboard.html', {
                    'tenant': tenant,
                })

            # Show tenant login/welcome page
            return render(request, 'tenant/welcome.html', {
                'tenant': tenant,
            })

        except Domain.DoesNotExist:
            # Domain not found - show error page
            return render(request, 'tenant/not_found.html', {
                'host': host,
            }, status=404)
