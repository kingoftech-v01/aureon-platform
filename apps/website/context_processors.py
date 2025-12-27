from django.conf import settings
from .models import SiteSettings, BlogCategory
from django.db.models import Q


def site_settings(request):
    """Add site settings to all templates"""
    return {
        'site_settings': SiteSettings.get_settings(),
    }


def navigation(request):
    """Add navigation data to all templates"""
    # Main navigation menu
    main_menu = [
        {
            'title': 'Home',
            'url': '/',
            'active': request.path == '/',
        },
        {
            'title': 'About',
            'url': '/about/',
            'active': request.path == '/about/',
        },
        {
            'title': 'Services',
            'url': '/services/',
            'active': request.path.startswith('/services/'),
            'submenu': [
                {'title': 'Contract Management', 'url': '/services/contract-management/'},
                {'title': 'Invoicing & Billing', 'url': '/services/invoicing-billing/'},
                {'title': 'Payment Processing', 'url': '/services/payment-processing/'},
                {'title': 'Document Management', 'url': '/services/document-management/'},
                {'title': 'E-Signatures', 'url': '/services/e-signatures/'},
                {'title': 'Analytics & Reporting', 'url': '/services/analytics-reporting/'},
            ]
        },
        {
            'title': 'Pricing',
            'url': '/pricing/',
            'active': request.path == '/pricing/',
        },
        {
            'title': 'Blog',
            'url': '/blog/',
            'active': request.path.startswith('/blog/'),
        },
        {
            'title': 'Contact',
            'url': '/contact/',
            'active': request.path == '/contact/',
        },
    ]

    # Blog categories for navigation
    blog_categories = BlogCategory.objects.annotate(
        post_count=Q(posts__status='published')
    )[:5]

    return {
        'main_menu': main_menu,
        'blog_categories': blog_categories,
    }


def seo_defaults(request):
    """Add SEO defaults to all templates"""
    site = SiteSettings.get_settings()

    # Build absolute URL for canonical and social sharing
    current_url = request.build_absolute_uri()

    # Default SEO meta tags
    seo_data = {
        'seo_title': site.default_meta_title or 'Aureon - Business Automation Platform',
        'seo_description': site.default_meta_description or 'Automate your business workflows with Aureon by Rhematek Solutions.',
        'seo_keywords': site.default_meta_keywords or 'business automation, SaaS, contract management, invoicing',
        'canonical_url': current_url,
        'og_url': current_url,
        'og_type': 'website',
        'og_site_name': site.company_name,
        'og_image': request.build_absolute_uri(settings.STATIC_URL + 'website/images/og-image.jpg'),
        'twitter_card': 'summary_large_image',
        'twitter_site': '@aureonapp',  # Update with actual Twitter handle
    }

    return seo_data


def analytics_ids(request):
    """Add analytics IDs to templates"""
    site = SiteSettings.get_settings()

    return {
        'google_analytics_id': site.google_analytics_id,
        'google_tag_manager_id': site.google_tag_manager_id,
        'facebook_pixel_id': site.facebook_pixel_id,
    }


def feature_flags(request):
    """Add feature flags to templates"""
    site = SiteSettings.get_settings()

    return {
        'maintenance_mode': site.maintenance_mode,
        'show_blog': site.show_blog,
        'show_store': site.show_store,
        'allow_newsletter_signup': site.allow_newsletter_signup,
    }


def current_year(request):
    """Add current year for copyright notices"""
    from datetime import datetime
    return {
        'current_year': datetime.now().year,
    }
