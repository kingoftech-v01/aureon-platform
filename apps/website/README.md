# Aureon Website App

Django app for the Aureon SaaS Platform public marketing website, converted from the gratech-buyer HTML template.

## Features

### Blog System
- Full-featured blog with categories and tags
- SEO-optimized posts with meta tags and Open Graph
- Rich text editor (CKEditor)
- View tracking and reading time calculation
- Featured posts
- Search and filtering
- RSS feed ready

### Product Catalog
- Digital products, subscriptions, and services
- Stripe integration for payments
- Product galleries
- Discount pricing display
- SEO optimization

### Contact Management
- Multiple contact forms (standard, sales inquiry, quick contact)
- Email notifications to admin and user
- Spam detection
- Inquiry tracking and assignment
- Status management

### Newsletter
- Email subscription with double opt-in
- Unsubscribe functionality
- Subscriber management
- AJAX form submission

### Pricing Page
- Tiered pricing display (Free, Starter, Pro, Business)
- Stripe Checkout integration
- Annual/monthly pricing toggle
- Feature comparison

### SEO & Analytics
- Comprehensive meta tags
- Open Graph and Twitter Cards
- Google Analytics 4
- Google Tag Manager
- Facebook Pixel
- Sitemap and robots.txt
- Schema.org ready

### Admin Interface
- Rich admin panels for all models
- Bulk actions
- Filtering and search
- Status badges
- Metrics display

## Quick Start

### 1. Install Dependencies

Already in `requirements.txt`:
- django-ckeditor
- crispy-forms
- crispy-bootstrap5
- stripe

### 2. Configure Settings

Add to `config/settings.py`:

```python
INSTALLED_APPS = [
    'ckeditor',
    'ckeditor_uploader',
    'crispy_forms',
    'crispy_bootstrap5',
    'apps.website',
]

TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            'apps.website.context_processors.site_settings',
            'apps.website.context_processors.navigation',
            'apps.website.context_processors.seo_defaults',
            'apps.website.context_processors.analytics_ids',
            'apps.website.context_processors.feature_flags',
            'apps.website.context_processors.current_year',
        ],
    },
}]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

CKEDITOR_UPLOAD_PATH = "uploads/"

# Stripe
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')

# Site
SITE_URL = env('SITE_URL', default='http://localhost:8000')
```

### 3. Add URLs

In `main/urls.py`:
```python
urlpatterns = [
    path('', include('apps.website.urls')),
]
```

### 4. Copy Static Files

```bash
cp -r gratech-buyer/assets/* apps/website/static/website/
```

### 5. Run Migrations

```bash
python manage.py makemigrations website
python manage.py migrate
python manage.py collectstatic
```

### 6. Create Site Settings

```bash
python manage.py shell
```

```python
from apps.website.models import SiteSettings

settings = SiteSettings.objects.create(
    company_name='Aureon by Rhematek Solutions',
    tagline='Automate Your Business, Amplify Your Growth',
    contact_email='info@rhematek-solutions.com',
    support_email='support@rhematek-solutions.com',
    sales_email='sales@rhematek-solutions.com',
)
```

### 7. Access Admin

Visit `http://localhost:8000/admin/` to:
- Configure site settings
- Create blog categories and posts
- Add products
- View contact submissions

## Project Structure

```
apps/website/
├── __init__.py
├── apps.py
├── models.py              # BlogPost, Product, Contact, Newsletter, SiteSettings
├── views.py               # All page views
├── urls.py                # URL routing
├── forms.py               # Contact, Newsletter, Sales forms
├── admin.py               # Admin interface
├── context_processors.py  # Template context
├── templates/
│   └── website/
│       ├── base.html      # Base template with SEO
│       ├── partials/
│       │   ├── header.html
│       │   ├── footer.html
│       │   ├── sidebar.html
│       │   └── search.html
│       └── emails/        # Email templates (to be created)
├── static/
│   └── website/           # CSS, JS, images from gratech-buyer
└── README.md
```

## URLs

| URL Pattern | View | Description |
|------------|------|-------------|
| `/` | HomeView | Homepage |
| `/about/` | AboutView | About page |
| `/team/` | TeamView | Team page |
| `/services/` | ServicesView | Services overview |
| `/services/<slug>/` | ServiceDetailView | Service details |
| `/pricing/` | PricingView | Pricing plans |
| `/contact/` | ContactView | Contact form |
| `/blog/` | BlogListView | Blog posts list |
| `/blog/<slug>/` | BlogDetailView | Blog post detail |
| `/blog/category/<slug>/` | BlogCategoryView | Category filter |
| `/blog/tag/<slug>/` | BlogTagView | Tag filter |
| `/products/` | ProductListView | Products list |
| `/products/<slug>/` | ProductDetailView | Product detail |
| `/newsletter/subscribe/` | newsletter_subscribe | Newsletter AJAX |
| `/create-checkout-session/` | create_checkout_session | Stripe checkout |
| `/faq/` | FAQView | FAQ page |
| `/privacy-policy/` | PrivacyPolicyView | Privacy policy |
| `/terms-of-service/` | TermsOfServiceView | Terms of service |

## Models

### BlogPost
Main blog post model with SEO, categories, tags, featured images.

### BlogCategory
Blog post categories.

### BlogTag
Blog post tags.

### Product
Products and services with Stripe integration.

### ContactSubmission
Contact form submissions with tracking.

### NewsletterSubscriber
Newsletter subscriptions with double opt-in.

### SiteSettings
Global site configuration (singleton).

## Context Processors

Available in all templates:
- `site_settings` - Site configuration
- `main_menu` - Navigation menu
- `seo_title`, `seo_description` - SEO defaults
- `google_analytics_id` - Analytics ID
- `current_year` - Current year for copyright

## Environment Variables

Add to `.env`:

```env
# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_ID_STARTER_MONTHLY=price_...
STRIPE_PRICE_ID_STARTER_ANNUAL=price_...
STRIPE_PRICE_ID_PRO_MONTHLY=price_...
STRIPE_PRICE_ID_PRO_ANNUAL=price_...
STRIPE_PRICE_ID_BUSINESS_MONTHLY=price_...
STRIPE_PRICE_ID_BUSINESS_ANNUAL=price_...

# Site
SITE_URL=https://yourdomain.com

# Email
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## Next Steps

1. **Create page templates** - Convert HTML sections from gratech-buyer to Django templates
2. **Set up email templates** - Create HTML emails for contact and newsletter
3. **Configure Stripe** - Create products and pricing in Stripe Dashboard
4. **Add content** - Create blog posts, products, and configure site settings
5. **Test forms** - Test contact, newsletter, and payment flows
6. **SEO optimization** - Create sitemap.xml and robots.txt templates
7. **Deploy** - Follow production deployment checklist

See `IMPLEMENTATION_GUIDE.md` for detailed instructions.

## License

Proprietary - Rhematek Solutions
