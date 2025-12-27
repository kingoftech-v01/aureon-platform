# Aureon Website App - Implementation Guide

## Overview
This guide explains the Django website app structure created for the Aureon SaaS Platform marketing website, converted from the gratech-buyer HTML template.

## What Has Been Created

### 1. Django App Structure (`apps/website/`)

#### Core Files:
- `__init__.py` - App initialization
- `apps.py` - App configuration
- `models.py` - Database models (BlogPost, Product, Contact, Newsletter, etc.)
- `views.py` - View functions and class-based views
- `urls.py` - URL routing configuration
- `forms.py` - Django forms with validation
- `admin.py` - Django admin interface
- `context_processors.py` - Site-wide template context

#### Templates (`apps/website/templates/website/`):
- `base.html` - Base template with SEO, header, footer
- `partials/header.html` - Header with navigation
- `partials/footer.html` - Footer with newsletter signup
- `partials/sidebar.html` - Mobile sidebar menu
- `partials/search.html` - Fullscreen search overlay

## Database Models

### BlogPost
- Full blog functionality with SEO optimization
- Categories and tags for organization
- Rich text editor (CKEditor) integration
- View tracking and reading time calculation
- Published/Draft/Archived status
- Featured posts capability

### BlogCategory & BlogTag
- Blog organization and filtering
- Auto-generated slugs
- Post count tracking

### Product
- Digital products, subscriptions, services
- Stripe integration ready (price_id, product_id fields)
- Image galleries
- Discount pricing support
- SEO optimization

### ContactSubmission
- Contact form submissions
- Inquiry type categorization
- Status tracking (New, In Progress, Resolved, Spam)
- IP address and user agent tracking
- Assignment to team members

### NewsletterSubscriber
- Email subscription management
- Double opt-in with confirmation tokens
- Unsubscribe functionality
- Status tracking (Active, Unsubscribed, Bounced)

### SiteSettings
- Global site configuration (singleton pattern)
- Company information
- Contact details
- Social media links
- SEO defaults
- Analytics IDs (Google Analytics, GTM, Facebook Pixel)
- Feature flags (maintenance mode, blog, store)

## Views & URLs

### Public Pages:
- **Home** (`/`) - Homepage with featured content
- **About** (`/about/`) - Company information
- **Team** (`/team/`) - Team members
- **Services** (`/services/`) - Services overview
- **Service Detail** (`/services/<slug>/`) - Individual service pages
- **Pricing** (`/pricing/`) - Pricing tiers with Stripe integration
- **Contact** (`/contact/`) - Contact form
- **FAQ** (`/faq/`) - Frequently asked questions

### Blog:
- **Blog List** (`/blog/`) - Paginated blog posts
- **Blog Detail** (`/blog/<slug>/`) - Individual post
- **Category Filter** (`/blog/category/<slug>/`) - Posts by category
- **Tag Filter** (`/blog/tag/<slug>/`) - Posts by tag
- **Search** - Full-text search across posts

### Products/Store:
- **Product List** (`/products/`) - All products
- **Product Detail** (`/products/<slug>/`) - Individual product

### Newsletter:
- **Subscribe** (`/newsletter/subscribe/`) - AJAX subscription
- **Confirm** (`/newsletter/confirm/<token>/`) - Email confirmation
- **Unsubscribe** (`/newsletter/unsubscribe/<token>/`) - Opt-out

### Payments:
- **Create Checkout** (`/create-checkout-session/`) - Stripe Checkout API
- **Payment Success** (`/payment/success/`) - Post-payment confirmation

### Legal:
- **Privacy Policy** (`/privacy-policy/`)
- **Terms of Service** (`/terms-of-service/`)

## Forms

### ContactForm
- Name, Email, Phone, Company
- Inquiry type selection
- Subject and message
- Spam detection
- Email validation
- Crispy Forms integration

### NewsletterForm
- Email subscription
- Name (optional)
- Duplicate check
- AJAX submission ready

### SalesInquiryForm
- Extended contact form
- Company size and industry
- Budget range and timeline
- Plan interest selection
- Privacy policy acceptance

### QuickContactForm
- Simplified sidebar/footer contact
- Name, email, message only

## Admin Interface

All models have comprehensive admin interfaces with:
- List displays with custom columns
- Filters and search
- Bulk actions (publish, feature, mark as resolved, etc.)
- Status badges with color coding
- Readonly fields for metadata
- Collapsible fieldsets
- Date hierarchies

## Context Processors

Available in all templates:
- `site_settings` - Global site configuration
- `main_menu` - Navigation menu with active state
- `blog_categories` - Blog categories for navigation
- `seo_title`, `seo_description`, `seo_keywords` - SEO defaults
- `og_*` - Open Graph tags
- `twitter_*` - Twitter Card tags
- `google_analytics_id`, `google_tag_manager_id`, `facebook_pixel_id`
- `maintenance_mode`, `show_blog`, `show_store`, `allow_newsletter_signup`
- `current_year` - For copyright notices

## Features Implemented

### SEO Optimization:
- Meta tags (title, description, keywords)
- Open Graph tags for social sharing
- Twitter Card tags
- Canonical URLs
- Schema.org structured data ready
- Lazy loading images
- Sitemap.xml and robots.txt endpoints

### Stripe Integration:
- Checkout session creation
- Subscription pricing support
- Product integration
- Payment success handling
- Webhook ready (views.py has placeholder)

### Email Functionality:
- Contact form notifications (admin)
- Contact form confirmations (user)
- Newsletter confirmation emails
- Double opt-in for newsletter
- Templated emails with HTML

### Analytics:
- Google Analytics 4 integration
- Google Tag Manager support
- Facebook Pixel integration
- View tracking for blog posts

### Security:
- CSRF protection
- Email validation
- Spam detection (basic)
- IP address logging
- User agent tracking
- Sanitized form inputs

## Next Steps Required

### 1. Update Django Settings (`config/settings.py`)

Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'ckeditor',
    'ckeditor_uploader',
    'crispy_forms',
    'crispy_bootstrap5',
    'apps.website',
]
```

Add to `TEMPLATES` context_processors:
```python
'context_processors': [
    # ... existing processors ...
    'apps.website.context_processors.site_settings',
    'apps.website.context_processors.navigation',
    'apps.website.context_processors.seo_defaults',
    'apps.website.context_processors.analytics_ids',
    'apps.website.context_processors.feature_flags',
    'apps.website.context_processors.current_year',
],
```

Add settings:
```python
# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# CKEditor
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
    },
}

# Stripe
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_PRICE_ID_STARTER_MONTHLY = env('STRIPE_PRICE_ID_STARTER_MONTHLY', default='')
STRIPE_PRICE_ID_STARTER_ANNUAL = env('STRIPE_PRICE_ID_STARTER_ANNUAL', default='')
STRIPE_PRICE_ID_PRO_MONTHLY = env('STRIPE_PRICE_ID_PRO_MONTHLY', default='')
STRIPE_PRICE_ID_PRO_ANNUAL = env('STRIPE_PRICE_ID_PRO_ANNUAL', default='')
STRIPE_PRICE_ID_BUSINESS_MONTHLY = env('STRIPE_PRICE_ID_BUSINESS_MONTHLY', default='')
STRIPE_PRICE_ID_BUSINESS_ANNUAL = env('STRIPE_PRICE_ID_BUSINESS_ANNUAL', default='')

# Site URL (for email links)
SITE_URL = env('SITE_URL', default='http://localhost:8000')

# Email settings (configure for production)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@aureon.com')
```

### 2. Update Main URLs (`config/urls.py` or `main/urls.py`)

```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('', include('apps.website.urls')),  # Website at root
    # OR
    # path('', include('apps.website.urls', namespace='website')),
]
```

### 3. Copy Static Assets

Copy all files from `gratech-buyer/assets/` to a new directory:
```
apps/website/static/website/
├── css/
├── images/
├── js/
├── sass/
└── webfonts/
```

Command:
```bash
# Windows
xcopy /E /I "gratech-buyer\assets" "apps\website\static\website"

# Linux/Mac
cp -r gratech-buyer/assets/* apps/website/static/website/
```

### 4. Run Migrations

```bash
python manage.py makemigrations website
python manage.py migrate
```

### 5. Create Superuser and Configure Site Settings

```bash
python manage.py createsuperuser
python manage.py runserver
```

Then visit `http://localhost:8000/admin/` and configure:
1. Site Settings (company info, contact details, social links, SEO)
2. Create blog categories
3. Create blog posts
4. Create products (optional)

### 6. Create Page Templates

You need to create actual content templates for each page. Use `base.html` and extend it:

Example `home.html`:
```django
{% extends 'website/base.html' %}
{% load static %}

{% block title %}Aureon - Business Automation Platform{% endblock %}

{% block content %}
<!-- Hero Section -->
<section class="banner-area">
    <!-- Hero content here -->
</section>

<!-- Features Section -->
<section class="features-area">
    <!-- Features content here -->
</section>
{% endblock %}
```

You can copy the HTML content sections from `gratech-buyer/index.html`, `gratech-buyer/pricing.html`, etc., and adapt them to Django template syntax.

### 7. Configure Stripe

1. Create a Stripe account at https://stripe.com
2. Create products and pricing in Stripe Dashboard
3. Copy the Price IDs to your `.env` file
4. Test checkout flow

### 8. Configure Email

For development:
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

For production (using SES or other):
```python
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'
```

### 9. Create Email Templates

Create HTML email templates in `apps/website/templates/website/emails/`:
- `contact_notification.html` - Admin notification
- `contact_confirmation.html` - User confirmation
- `newsletter_confirmation.html` - Newsletter double opt-in

### 10. SEO Files

Create `apps/website/templates/website/sitemap.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{{ request.scheme }}://{{ request.get_host }}{% url 'website:home' %}</loc>
        <priority>1.0</priority>
    </url>
    <!-- Add more URLs -->
</urlset>
```

Create `apps/website/templates/website/robots.txt`:
```
User-agent: *
Allow: /
Disallow: /admin/

Sitemap: {{ request.scheme }}://{{ request.get_host }}/sitemap.xml
```

## Testing Checklist

- [ ] All URLs resolve correctly
- [ ] Contact form sends emails
- [ ] Newsletter signup works
- [ ] Blog pagination works
- [ ] Blog search works
- [ ] Product pages load
- [ ] Stripe checkout initiates
- [ ] Admin interface accessible
- [ ] SEO meta tags render correctly
- [ ] Social sharing previews work
- [ ] Mobile menu functions
- [ ] Search overlay works
- [ ] Static files load correctly

## Production Deployment Checklist

- [ ] Set `DEBUG = False`
- [ ] Configure allowed hosts
- [ ] Set up proper email backend (SES, SendGrid, etc.)
- [ ] Configure media file storage (S3, etc.)
- [ ] Set up CDN for static files
- [ ] Enable SSL/HTTPS
- [ ] Configure Stripe webhooks
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Configure backup strategy
- [ ] Set up staging environment
- [ ] Load test contact forms
- [ ] Test newsletter confirmation flow
- [ ] Configure spam protection (reCAPTCHA, etc.)

## Support & Documentation

For questions about:
- Django: https://docs.djangoproject.com/
- Stripe: https://stripe.com/docs
- CKEditor: https://django-ckeditor.readthedocs.io/
- Crispy Forms: https://django-crispy-forms.readthedocs.io/

## Branding Replacements Done

All instances of "Gratech" have been replaced with "Aureon" in the codebase. The following branding elements are used:
- Company Name: Aureon by Rhematek Solutions
- Tagline: Automate Your Business, Amplify Your Growth
- Email Domain: @rhematek-solutions.com

You'll need to replace logos and images in the static files with your actual branding assets.
