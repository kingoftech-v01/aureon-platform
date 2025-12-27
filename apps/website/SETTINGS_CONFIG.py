# ============================================================================
# WEBSITE APP CONFIGURATION
# Copy these settings into your config/settings.py file
# ============================================================================

# ADD TO INSTALLED_APPS
# ============================================================================
INSTALLED_APPS = [
    # ... existing apps ...

    # Website App Dependencies
    'ckeditor',
    'ckeditor_uploader',
    'crispy_forms',
    'crispy_bootstrap5',

    # Website App
    'apps.website',

    # ... other apps ...
]


# ADD TO TEMPLATES CONTEXT PROCESSORS
# ============================================================================
TEMPLATES = [
    {
        # ... existing config ...
        'OPTIONS': {
            'context_processors': [
                # ... existing context processors ...

                # Website App Context Processors
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


# CRISPY FORMS CONFIGURATION
# ============================================================================
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# CKEDITOR CONFIGURATION
# ============================================================================
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"
CKEDITOR_JQUERY_URL = 'https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js'

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 400,
        'width': '100%',
        'extraPlugins': ','.join([
            'codesnippet',
            'widget',
            'dialog',
        ]),
    },
    'basic': {
        'toolbar': 'Basic',
        'height': 300,
    },
}


# STRIPE CONFIGURATION
# ============================================================================
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')

# Pricing Plan Price IDs (from Stripe Dashboard)
STRIPE_PRICE_ID_STARTER_MONTHLY = env('STRIPE_PRICE_ID_STARTER_MONTHLY', default='')
STRIPE_PRICE_ID_STARTER_ANNUAL = env('STRIPE_PRICE_ID_STARTER_ANNUAL', default='')
STRIPE_PRICE_ID_PRO_MONTHLY = env('STRIPE_PRICE_ID_PRO_MONTHLY', default='')
STRIPE_PRICE_ID_PRO_ANNUAL = env('STRIPE_PRICE_ID_PRO_ANNUAL', default='')
STRIPE_PRICE_ID_BUSINESS_MONTHLY = env('STRIPE_PRICE_ID_BUSINESS_MONTHLY', default='')
STRIPE_PRICE_ID_BUSINESS_ANNUAL = env('STRIPE_PRICE_ID_BUSINESS_ANNUAL', default='')


# SITE CONFIGURATION
# ============================================================================
SITE_URL = env('SITE_URL', default='http://localhost:8000')


# EMAIL CONFIGURATION
# ============================================================================
# For Development (prints to console)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# For Production (use SES, SendGrid, etc.)
# EMAIL_BACKEND = 'django_ses.SESBackend'
# AWS_SES_REGION_NAME = env('AWS_SES_REGION_NAME', default='us-east-1')
# AWS_SES_REGION_ENDPOINT = env('AWS_SES_REGION_ENDPOINT', default='email.us-east-1.amazonaws.com')

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@rhematek-solutions.com')
SERVER_EMAIL = env('SERVER_EMAIL', default='server@rhematek-solutions.com')


# MEDIA FILES CONFIGURATION (for uploaded images)
# ============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# For Production (use S3, etc.)
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')


# STATIC FILES CONFIGURATION
# ============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# For Production with WhiteNoise
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# SECURITY SETTINGS (for production)
# ============================================================================
# Uncomment these for production deployment

# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY'
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
