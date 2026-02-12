"""
Home and dashboard views for Aureon SaaS Platform.

Frontend rendering is handled by:
- React SPA (Vite) for dashboard routes
- Next.js static export for marketing website routes
"""
import os
from django.views import View
from django.http import HttpResponse
from django.conf import settings


def serve_marketing_site(request, path=''):
    """
    Serve the Next.js marketing site static export.

    Next.js with output: 'export' creates static HTML files for each route.
    Example: /about/ -> /about/index.html or /about.html
    """
    # Normalize path
    if path.startswith('/'):
        path = path[1:]
    if path.endswith('/'):
        path = path[:-1]

    # Build possible file paths
    possible_paths = []

    # Define base directories to check
    base_dirs = []

    # 1. Check STATIC_ROOT (after collectstatic)
    if settings.STATIC_ROOT:
        base_dirs.append(os.path.join(settings.STATIC_ROOT, 'marketing'))

    # 2. Check STATICFILES_DIRS (development)
    if hasattr(settings, 'STATICFILES_DIRS'):
        for static_dir in settings.STATICFILES_DIRS:
            base_dirs.append(os.path.join(static_dir, 'marketing'))

    # 3. Check relative to BASE_DIR
    base_dirs.append(os.path.join(settings.BASE_DIR, 'static', 'marketing'))
    base_dirs.append(os.path.join(settings.BASE_DIR, 'staticfiles', 'marketing'))

    # 4. Check frontend-marketing/out for development
    base_dirs.append(os.path.join(settings.BASE_DIR, 'frontend-marketing', 'out'))

    # For each base directory, try to find the file
    for base_dir in base_dirs:
        if not path:
            # Root path - serve index.html
            possible_paths.append(os.path.join(base_dir, 'index.html'))
        else:
            # Try path/index.html (Next.js default with trailingSlash: true)
            possible_paths.append(os.path.join(base_dir, path, 'index.html'))
            # Try path.html
            possible_paths.append(os.path.join(base_dir, f'{path}.html'))

    for html_path in possible_paths:
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()
            return HttpResponse(html, content_type='text/html')

    # Fallback: Marketing site not found - show setup page
    return HttpResponse('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aureon - Marketing Site Setup Required</title>
</head>
<body style="font-family: system-ui, -apple-system, sans-serif; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; padding: 20px;">
    <div style="background: white; border-radius: 16px; padding: 48px; max-width: 520px; text-align: center; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);">
        <div style="width: 72px; height: 72px; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 16px; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px;">
            <span style="color: white; font-size: 28px; font-weight: bold;">A</span>
        </div>
        <h1 style="color: #111827; margin: 0 0 12px; font-size: 28px; font-weight: 700;">Aureon Marketing Site</h1>
        <p style="color: #6b7280; margin: 0 0 32px; line-height: 1.6; font-size: 16px;">The marketing website needs to be built before it can be accessed.</p>
        <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; text-align: left; margin-bottom: 32px;">
            <p style="color: #374151; font-size: 14px; font-weight: 600; margin: 0 0 12px;">Build Commands:</p>
            <code style="display: block; background: #1f2937; color: #10b981; padding: 16px; border-radius: 8px; font-size: 13px; line-height: 1.8; overflow-x: auto;">cd frontend-marketing<br>npm install<br>npm run build<br>python manage.py collectstatic --noinput</code>
        </div>
        <p style="color: #9ca3af; font-size: 13px; margin: 0;">Powered by <strong>Rhematek Solutions</strong></p>
    </div>
</body>
</html>''', content_type='text/html')


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
    Home view that serves the marketing site.
    """

    def get(self, request):
        return serve_marketing_site(request, '')


class DashboardView(View):
    """
    Serve the React dashboard for all authenticated routes.
    This catches /dashboard, /clients, /contracts, /invoices, etc.
    """

    def get(self, request, path=''):
        # React handles authentication state and routing
        return serve_react_app(request)


class ReactCatchAllView(View):
    """
    Catch-all view that serves React SPA for all frontend routes.
    This ensures React Router handles all client-side routing.
    """

    def get(self, request, path=''):
        return serve_react_app(request)
