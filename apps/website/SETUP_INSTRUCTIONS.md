# Aureon Website App - Setup Instructions

Follow these steps to complete the website app integration.

## Step 1: Update Django Settings

**File: `config/settings.py` or `main/settings.py`**

### 1.1 Add to INSTALLED_APPS

Find the `INSTALLED_APPS` list and add these entries:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps for website
    'ckeditor',              # Rich text editor for blog
    'ckeditor_uploader',     # Image uploads for CKEditor
    'crispy_forms',          # Form styling
    'crispy_bootstrap5',     # Bootstrap 5 for crispy forms

    # ... your existing apps ...

    # Website app (add this)
    'apps.website',
]
```

### 1.2 Add Context Processors

Find the `TEMPLATES` configuration and add context processors:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Add these website context processors
                'apps.website.context_processors.site_settings',
                'apps.website.context_processors.navigation',
                'apps.website.context_processors.seo_defaults',
                'apps.website.context_processors.analytics_ids',
                'apps.website.context_processors.feature_flags',
                'apps.website.context_processors.current_year',
            ],
        },
    },
]
```

### 1.3 Add Website Configuration

Add at the end of your settings file:

```python
# ============================================================================
# WEBSITE APP CONFIGURATION
# ============================================================================

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# CKEditor
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 400,
        'width': '100%',
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

# Media files (for uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

## Step 2: Update Main URLs

**File: `main/urls.py` or `config/urls.py`**

Add the website URLs:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Your existing URLs
    # path('api/', include('apps.api.urls')),
    # path('accounts/', include('allauth.urls')),

    # Website URLs (add this at the end, so it catches root URL)
    path('', include('apps.website.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

## Step 3: Update Environment Variables

**File: `.env`**

Add these variables:

```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_SECRET_KEY=sk_test_your_key_here

# Stripe Price IDs (get these from Stripe Dashboard after creating products)
STRIPE_PRICE_ID_STARTER_MONTHLY=price_xxx
STRIPE_PRICE_ID_STARTER_ANNUAL=price_xxx
STRIPE_PRICE_ID_PRO_MONTHLY=price_xxx
STRIPE_PRICE_ID_PRO_ANNUAL=price_xxx
STRIPE_PRICE_ID_BUSINESS_MONTHLY=price_xxx
STRIPE_PRICE_ID_BUSINESS_ANNUAL=price_xxx

# Site Configuration
SITE_URL=http://localhost:8000

# Email Configuration
DEFAULT_FROM_EMAIL=noreply@rhematek-solutions.com
```

## Step 4: Copy Static Assets

Copy the gratech-buyer assets to the website static folder:

### Windows (PowerShell):
```powershell
# Create directory
New-Item -ItemType Directory -Force -Path "apps\website\static\website"

# Copy assets
Copy-Item -Path "gratech-buyer\assets\*" -Destination "apps\website\static\website\" -Recurse -Force
```

### Linux/Mac:
```bash
# Create directory
mkdir -p apps/website/static/website

# Copy assets
cp -r gratech-buyer/assets/* apps/website/static/website/
```

## Step 5: Run Migrations

```bash
# Create migrations for website app
python manage.py makemigrations website

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput
```

## Step 6: Create Superuser

```bash
python manage.py createsuperuser
```

Follow prompts to create admin user.

## Step 7: Initialize Site Settings

Start Django shell:
```bash
python manage.py shell
```

Run this Python code:
```python
from apps.website.models import SiteSettings

# Create site settings
settings = SiteSettings.objects.create(
    company_name='Aureon by Rhematek Solutions',
    tagline='Automate Your Business, Amplify Your Growth',
    description='Comprehensive SaaS platform for contract management, invoicing, and business automation.',

    # Contact Information
    contact_email='info@rhematek-solutions.com',
    support_email='support@rhematek-solutions.com',
    sales_email='sales@rhematek-solutions.com',
    phone='+1-555-0100',
    address='123 Business Ave, Suite 100, City, State 12345',

    # Social Media (update with real URLs)
    facebook_url='https://facebook.com/aureonapp',
    twitter_url='https://twitter.com/aureonapp',
    linkedin_url='https://linkedin.com/company/aureon',
    youtube_url='https://youtube.com/@aureonapp',
    github_url='https://github.com/rhematek',

    # SEO Defaults
    default_meta_title='Aureon - Business Automation Platform',
    default_meta_description='Automate your business workflows with Aureon by Rhematek Solutions. Contract management, invoicing, payments, and more.',
    default_meta_keywords='business automation, contract management, invoicing, SaaS, payments, e-signatures',

    # Features
    maintenance_mode=False,
    allow_newsletter_signup=True,
    show_blog=True,
    show_store=True,
)

print("Site settings created successfully!")
```

Exit shell: `exit()`

## Step 8: Create Sample Blog Content

In Django shell (`python manage.py shell`):

```python
from apps.website.models import BlogCategory, BlogTag, BlogPost
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.first()  # Get first user (your superuser)

# Create categories
tech = BlogCategory.objects.create(
    name='Technology',
    description='Technology and software development'
)
business = BlogCategory.objects.create(
    name='Business',
    description='Business tips and strategies'
)
automation = BlogCategory.objects.create(
    name='Automation',
    description='Business automation and productivity'
)

# Create tags
saas_tag = BlogTag.objects.create(name='SaaS')
productivity_tag = BlogTag.objects.create(name='Productivity')
contracts_tag = BlogTag.objects.create(name='Contracts')

# Create sample blog post
post = BlogPost.objects.create(
    title='Getting Started with Business Automation',
    author=admin_user,
    category=automation,
    excerpt='Learn how to automate your business processes and save time.',
    content='<h2>Introduction</h2><p>Business automation is the key to scaling your operations...</p>',
    status='published',
    featured=True,
)
post.tags.add(saas_tag, productivity_tag)

print("Sample blog content created!")
```

## Step 9: Test the Website

```bash
python manage.py runserver
```

Visit these URLs to test:
- Homepage: http://localhost:8000/
- Admin: http://localhost:8000/admin/
- Blog: http://localhost:8000/blog/
- Pricing: http://localhost:8000/pricing/
- Contact: http://localhost:8000/contact/
- About: http://localhost:8000/about/

## Step 10: Configure Stripe (Optional)

1. Create a Stripe account at https://stripe.com
2. Go to Dashboard → Products → Add Product
3. Create products for each pricing tier:
   - Starter ($19/month, $190/year)
   - Pro ($49/month, $490/year)
   - Business ($99/month, $990/year)
4. Copy the Price IDs to your `.env` file
5. Test checkout at http://localhost:8000/pricing/

## Step 11: Create Email Templates

Create these files for email functionality:

### `apps/website/templates/website/emails/contact_notification.html`
```django
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>New Contact Form Submission</title>
</head>
<body>
    <h2>New Contact Form Submission</h2>
    <p><strong>Name:</strong> {{ contact.name }}</p>
    <p><strong>Email:</strong> {{ contact.email }}</p>
    <p><strong>Phone:</strong> {{ contact.phone }}</p>
    <p><strong>Company:</strong> {{ contact.company }}</p>
    <p><strong>Subject:</strong> {{ contact.subject }}</p>
    <p><strong>Message:</strong></p>
    <p>{{ contact.message|linebreaks }}</p>
</body>
</html>
```

### `apps/website/templates/website/emails/contact_confirmation.html`
```django
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Thank you for contacting Aureon</title>
</head>
<body>
    <h2>Thank you for contacting us!</h2>
    <p>Dear {{ contact.name }},</p>
    <p>We have received your message and will get back to you within 24 hours.</p>
    <p><strong>Your message:</strong></p>
    <p>{{ contact.message|linebreaks }}</p>
    <p>Best regards,<br>The Aureon Team</p>
</body>
</html>
```

### `apps/website/templates/website/emails/newsletter_confirmation.html`
```django
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Confirm Your Newsletter Subscription</title>
</head>
<body>
    <h2>Confirm Your Newsletter Subscription</h2>
    <p>Hi{% if subscriber.name %} {{ subscriber.name }}{% endif %},</p>
    <p>Please click the link below to confirm your subscription to the Aureon newsletter:</p>
    <p><a href="{{ confirmation_url }}">Confirm Subscription</a></p>
    <p>If you didn't subscribe, you can ignore this email.</p>
    <p>Best regards,<br>The Aureon Team</p>
</body>
</html>
```

## Step 12: Admin Configuration

1. Visit http://localhost:8000/admin/
2. Log in with superuser credentials
3. Configure:
   - **Site Settings**: Update company info, social links, analytics IDs
   - **Blog Categories**: Add categories relevant to your business
   - **Blog Tags**: Add common tags
   - **Blog Posts**: Create and publish posts
   - **Products**: Add products/services (if using store)

## Troubleshooting

### Static files not loading:
```bash
python manage.py collectstatic --clear --noinput
```

### Database errors:
```bash
python manage.py migrate --run-syncdb
```

### CKEditor not working:
```bash
pip install django-ckeditor pillow
python manage.py migrate
```

### Stripe checkout not working:
- Check `.env` has correct Stripe keys
- Verify Price IDs are correct
- Check browser console for JavaScript errors

## Next Steps

1. **Create Page Content**: Design actual page templates by converting HTML sections
2. **Add Real Content**: Blog posts, products, team members
3. **Configure Email**: Set up production email backend (SES, SendGrid)
4. **SEO Optimization**: Add more meta tags, schema.org markup
5. **Analytics**: Add Google Analytics ID to Site Settings
6. **Security**: Review security settings for production
7. **Deploy**: Follow production deployment checklist

See `IMPLEMENTATION_GUIDE.md` for detailed implementation instructions.
