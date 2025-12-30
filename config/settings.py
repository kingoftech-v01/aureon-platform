"""
Django settings for Finance SaaS Platform.
"""

import os
from pathlib import Path
import environ

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False)
)

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'localhost',
    '127.0.0.1',
    'aureon.rhematek-solutions.com',
    '.rhematek-solutions.com',  # Allow subdomains
])

# CSRF and Security settings for reverse proxy
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'https://aureon.rhematek-solutions.com',
    'https://*.rhematek-solutions.com',
])

# Trust X-Forwarded-Proto header from reverse proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'django_filters',
    'drf_spectacular',

    # Authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'guardian',

    # Stripe
    'djstripe',

    # Celery
    'django_celery_beat',
    'django_celery_results',

    # Security
    'csp',
    'axes',
    'honeypot',

    # Monitoring
    'django_prometheus',

    # Utilities
    'storages',
    'import_export',
    'auditlog',
    'phonenumber_field',

    # Local apps
    'apps.core',  # Core security utilities
    'apps.tenants',
    'apps.accounts',
    'apps.clients',  # Fixed: was 'apps.crm'
    'apps.contracts',
    'apps.invoicing',
    'apps.payments',
    'apps.documents',
    'apps.notifications',
    'apps.analytics',
    'apps.integrations',
    'apps.webhooks',
    'apps.website',  # Marketing website
]

# Django Tenants Configuration
TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'config.middleware.security.RequestLoggingMiddleware',  # Security request logging (early)
    'django.middleware.security.SecurityMiddleware',
    'config.middleware.security.SecurityHeadersMiddleware',  # Enhanced security headers
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'config.middleware.security.CSRFEnhancementMiddleware',  # Enhanced CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'config.middleware.security.HoneypotMiddleware',  # Bot detection
    'config.middleware.security.XSSSanitizationMiddleware',  # XSS protection
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
    'axes.middleware.AxesMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ====================
# DATABASE CONFIGURATION
# Optimized for 1M users with connection pooling via PgBouncer
# ====================

# Primary database (writes go through PgBouncer to master)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='aureon_db'),
        'USER': env('DB_USER', default='aureon_user'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='pgbouncer'),  # Use PgBouncer for connection pooling
        'PORT': env.int('DB_PORT', default=6432),  # PgBouncer port
        'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=0),  # Let PgBouncer handle pooling
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 second query timeout
        },
        'ATOMIC_REQUESTS': False,  # Handle transactions explicitly
    },
    # Read replica for read-heavy operations (optional - use with database router)
    'replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='aureon_db'),
        'USER': env('DB_USER', default='aureon_user'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_REPLICA_HOST', default='db-replica-1'),
        'PORT': env.int('DB_REPLICA_PORT', default=5432),
        'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=60),
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=60000',  # 60 second for read queries
        },
    },
}

# Use environment variable to enable/disable read replica
if not env.bool('USE_READ_REPLICA', default=False):
    del DATABASES['replica']

# Database Router for read/write splitting (when replica is enabled)
if env.bool('USE_READ_REPLICA', default=False):
    DATABASE_ROUTERS = ['config.db_router.ReadWriteRouter']

# PgBouncer-specific settings
# These are passed to the database engine and work with PgBouncer
PGBOUNCER_SETTINGS = {
    'pool_mode': 'transaction',  # Transaction pooling mode
    'max_client_conn': 10000,  # Maximum client connections
    'default_pool_size': 100,  # Default pool size per user/database pair
    'min_pool_size': 20,  # Minimum pool size
    'reserve_pool_size': 50,  # Reserve connections for burst traffic
    'reserve_pool_timeout': 5,  # Timeout for reserve pool
    'max_db_connections': 200,  # Maximum connections to database
    'max_user_connections': 200,  # Maximum connections per user
    'server_idle_timeout': 600,  # Idle server connection timeout
    'server_lifetime': 3600,  # Maximum server connection lifetime
    'client_idle_timeout': 300,  # Idle client connection timeout
    'query_timeout': 60,  # Query timeout in seconds
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Site ID
SITE_ID = 1

# ====================
# SECURITY SETTINGS
# ====================

# ------------------------------------------------
# PROTECTION 1: HTTPS/TLS Settings
# ------------------------------------------------
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=not DEBUG)
SECURE_REDIRECT_EXEMPT = []  # No exemptions from HTTPS

# ------------------------------------------------
# PROTECTION 2: Secure Cookie Settings
# ------------------------------------------------
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_NAME = '__Host-sessionid' if not DEBUG else 'sessionid'  # Cookie prefix for HTTPS
CSRF_COOKIE_NAME = '__Host-csrftoken' if not DEBUG else 'csrftoken'  # Cookie prefix for HTTPS
CSRF_USE_SESSIONS = False

# ------------------------------------------------
# PROTECTION 3: HSTS (HTTP Strict Transport Security)
# ------------------------------------------------
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000 if not DEBUG else 0)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True  # Enable HSTS preload

# ------------------------------------------------
# PROTECTION 4: X-Frame-Options & Clickjacking Protection
# ------------------------------------------------
X_FRAME_OPTIONS = 'DENY'  # Prevent all framing

# ------------------------------------------------
# PROTECTION 5: Content Type Sniffing Protection
# ------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True

# ------------------------------------------------
# PROTECTION 6: XSS Protection Headers
# ------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True  # Legacy browser support

# ------------------------------------------------
# PROTECTION 7: Content Security Policy (Strict Mode)
# ------------------------------------------------
# Note: 'unsafe-inline' needed for some third-party integrations
# Consider using nonces for inline scripts in production
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for Stripe and some UI frameworks
    "'unsafe-eval'",    # Required for some JS frameworks
    "https://js.stripe.com",
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for inline styles
    "https://fonts.googleapis.com",
    "https://cdn.jsdelivr.net",
)
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "data:", "https://cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:", "https:", "blob:")
CSP_CONNECT_SRC = ("'self'", "https://api.stripe.com", "wss:", "https:")
CSP_FRAME_SRC = ("'self'", "https://js.stripe.com", "https://hooks.stripe.com")
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)  # Equivalent to X-Frame-Options DENY
CSP_UPGRADE_INSECURE_REQUESTS = not DEBUG
CSP_BLOCK_ALL_MIXED_CONTENT = True
CSP_REPORT_URI = env('CSP_REPORT_URI', default=None)  # Optional CSP violation reporting
CSP_REPORT_ONLY = env.bool('CSP_REPORT_ONLY', default=False)

# ------------------------------------------------
# PROTECTION 8: Session Security
# ------------------------------------------------
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'  # Use dedicated session cache
SESSION_COOKIE_AGE = 1209600  # 14 days
SESSION_SAVE_EVERY_REQUEST = True  # Extend session on activity
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ------------------------------------------------
# PROTECTION 9: Permissions Policy (Feature Policy)
# ------------------------------------------------
PERMISSIONS_POLICY = {
    'accelerometer': [],
    'ambient-light-sensor': [],
    'autoplay': [],
    'camera': [],
    'display-capture': [],
    'document-domain': [],
    'encrypted-media': [],
    'fullscreen': ['self'],
    'geolocation': [],
    'gyroscope': [],
    'interest-cohort': [],  # Disable FLoC
    'magnetometer': [],
    'microphone': [],
    'midi': [],
    'payment': ['self'],
    'picture-in-picture': [],
    'publickey-credentials-get': [],
    'speaker-selection': [],
    'sync-xhr': [],
    'usb': [],
    'xr-spatial-tracking': [],
}

# ------------------------------------------------
# PROTECTION 10: Cross-Origin Policies
# ------------------------------------------------
CROSS_ORIGIN_POLICIES = {
    'Cross-Origin-Embedder-Policy': 'require-corp',
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'same-origin',
}

# ------------------------------------------------
# PROTECTION 11: Honeypot Configuration
# ------------------------------------------------
HONEYPOT_FIELDS = [
    'website_url',
    'phone_number_2',
    'email_confirm',
    'hp_field',
    'contact_me_by_fax',
    'leave_blank',
    'company_fax',
    'url',
    'address2',
    'name_confirm',
]
HONEYPOT_MIN_FORM_SUBMISSION_TIME = 2  # seconds

# ------------------------------------------------
# PROTECTION 12: IP Whitelist/Blacklist
# ------------------------------------------------
IP_WHITELIST = env.list('IP_WHITELIST', default=[
    '127.0.0.1',
])

# ------------------------------------------------
# PROTECTION 13: Login Security Settings
# ------------------------------------------------
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_TIMES = [60, 300, 900, 3600, 86400]  # Progressive lockout

# ------------------------------------------------
# PROTECTION 14: Security Monitoring Thresholds
# ------------------------------------------------
SECURITY_THRESHOLDS = {
    'failed_logins_per_hour': 100,
    'blocked_ips_per_hour': 50,
    'rate_limits_per_hour': 200,
    'suspicious_requests_per_hour': 100,
}

# ------------------------------------------------
# PROTECTION 15: File Upload Security
# ------------------------------------------------
BLOCK_ON_SCAN_ERROR = True  # Block file if virus scan fails
MAX_IMAGE_DIMENSION = 4096  # Maximum image dimension in pixels
XSS_SKIP_FIELDS = set()  # Fields to skip XSS sanitization (e.g., WYSIWYG editors)

# ====================
# CACHING (Redis Cluster Configuration)
# Multi-layer caching optimized for 1M users
# ====================

# Redis connection settings
REDIS_PASSWORD = env('REDIS_PASSWORD', default='')
REDIS_CACHE_HOST = env('REDIS_CACHE_HOST', default='redis-cache')
REDIS_CACHE_PORT = env.int('REDIS_CACHE_PORT', default=6379)
REDIS_QUEUE_HOST = env('REDIS_QUEUE_HOST', default='redis-queue')
REDIS_RESULT_HOST = env('REDIS_RESULT_HOST', default='redis-result')

# Base Redis connection options
_REDIS_BASE_OPTIONS = {
    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    'PASSWORD': REDIS_PASSWORD,
    'SOCKET_CONNECT_TIMEOUT': 5,
    'SOCKET_TIMEOUT': 5,
    'RETRY_ON_TIMEOUT': True,
    'CONNECTION_POOL_KWARGS': {
        'max_connections': 100,
        'retry_on_timeout': True,
        'socket_keepalive': True,
    },
    'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
    'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
}

CACHES = {
    # Default cache - General purpose caching (Redis node 1)
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}/0',
        'OPTIONS': {
            **_REDIS_BASE_OPTIONS,
            'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
            'CONNECTION_POOL_KWARGS': {
                **_REDIS_BASE_OPTIONS['CONNECTION_POOL_KWARGS'],
                'max_connections': 200,
                'timeout': 20,
            },
        },
        'KEY_PREFIX': 'aureon',
        'TIMEOUT': 900,  # 15 minutes default
    },

    # Session cache - User sessions (Redis node 1, database 1)
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}/1',
        'OPTIONS': {
            **_REDIS_BASE_OPTIONS,
            'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
            'CONNECTION_POOL_KWARGS': {
                **_REDIS_BASE_OPTIONS['CONNECTION_POOL_KWARGS'],
                'max_connections': 150,
                'timeout': 20,
            },
        },
        'KEY_PREFIX': 'aureon_session',
        'TIMEOUT': 1209600,  # 14 days for sessions
    },

    # Lock cache - Distributed locking (Redis node 1, database 2)
    'locks': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}/2',
        'OPTIONS': {
            **_REDIS_BASE_OPTIONS,
            'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
            'CONNECTION_POOL_KWARGS': {
                **_REDIS_BASE_OPTIONS['CONNECTION_POOL_KWARGS'],
                'max_connections': 50,
            },
        },
        'KEY_PREFIX': 'aureon_lock',
        'TIMEOUT': 300,  # 5 minutes max lock time
    },

    # Throttle cache - Rate limiting (Redis node 1, database 3)
    'throttle': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}/3',
        'OPTIONS': {
            **_REDIS_BASE_OPTIONS,
            'CONNECTION_POOL_KWARGS': {
                **_REDIS_BASE_OPTIONS['CONNECTION_POOL_KWARGS'],
                'max_connections': 100,
            },
        },
        'KEY_PREFIX': 'aureon_throttle',
        'TIMEOUT': 3600,  # 1 hour
    },

    # Local memory cache - L1 cache layer (no Redis, in-process)
    'local': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'aureon-local-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
            'CULL_FREQUENCY': 4,
        },
        'TIMEOUT': 300,  # 5 minutes
    },
}

# ====================
# CELERY CONFIGURATION
# Optimized for 1M users with Redis cluster
# ====================

# Broker settings - Use dedicated Redis queue node
CELERY_BROKER_URL = env(
    'CELERY_BROKER_URL',
    default=f'redis://:{REDIS_PASSWORD}@{REDIS_QUEUE_HOST}:6379/1'
)

# Result backend - Use dedicated Redis result node for high throughput
CELERY_RESULT_BACKEND = env(
    'CELERY_RESULT_BACKEND',
    default=f'redis://:{REDIS_PASSWORD}@{REDIS_RESULT_HOST}:6379/0'
)

# Broker connection settings for high availability
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
CELERY_BROKER_CONNECTION_TIMEOUT = 10
CELERY_BROKER_POOL_LIMIT = 100
CELERY_BROKER_HEARTBEAT = 10

# Broker transport options for Redis cluster
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,  # 1 hour
    'fanout_prefix': True,
    'fanout_patterns': True,
    'socket_connect_timeout': 5,
    'socket_keepalive': True,
    'socket_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30,
}

# Result backend settings
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour
CELERY_RESULT_EXTENDED = True
CELERY_RESULT_COMPRESSION = 'gzip'

# Serialization
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_EVENT_SERIALIZER = 'json'

# Timezone
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Task execution settings
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
CELERY_TASK_ALWAYS_EAGER = False  # Never run synchronously in production

# Task acknowledgment settings
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Worker settings (configured in celery.py, but defaults here)
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 400000  # 400MB

# Task publishing settings
CELERY_TASK_PUBLISH_RETRY = True
CELERY_TASK_PUBLISH_RETRY_POLICY = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.5,
}

# Cache backend for rate limiting
CELERY_CACHE_BACKEND = 'default'

# ====================
# DJANGO ALLAUTH
# ====================

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'guardian.backends.ObjectPermissionBackend',
    'axes.backends.AxesBackend',
]

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SESSION_REMEMBER = True
LOGIN_REDIRECT_URL = '/dashboard/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# ====================
# EMAIL CONFIGURATION
# ====================

EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@example.com')

# ====================
# STRIPE CONFIGURATION
# ====================

STRIPE_LIVE_PUBLIC_KEY = env('STRIPE_PUBLIC_KEY', default='')
STRIPE_LIVE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_TEST_PUBLIC_KEY = env('STRIPE_PUBLIC_KEY', default='')
STRIPE_TEST_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_LIVE_MODE = not DEBUG
DJSTRIPE_WEBHOOK_SECRET = env('DJSTRIPE_WEBHOOK_SECRET', default='')
DJSTRIPE_FOREIGN_KEY_TO_FIELD = 'id'
DJSTRIPE_USE_NATIVE_JSONFIELD = True

# ====================
# REST FRAMEWORK
# ====================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# ====================
# API DOCUMENTATION
# ====================

SPECTACULAR_SETTINGS = {
    'TITLE': 'Finance SaaS Platform API',
    'DESCRIPTION': 'End-to-end financial workflow automation platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api',
}

# ====================
# CORS SETTINGS
# ====================

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
])

CORS_ALLOW_CREDENTIALS = True

# ====================
# AXES (Brute Force Protection)
# ====================

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
AXES_RESET_ON_SUCCESS = True

# ====================
# LOGGING
# ====================

# Check if running in Docker/container environment
import os
_RUNNING_IN_DOCKER = os.path.exists('/.dockerenv') or env.bool('DOCKER_CONTAINER', default=False)

# Check if logs directory is writable
_LOGS_DIR = BASE_DIR / 'logs'
_LOGS_WRITABLE = False
try:
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    _test_file = _LOGS_DIR / '.test_write'
    _test_file.touch()
    _test_file.unlink()
    _LOGS_WRITABLE = True
except (PermissionError, OSError):
    _LOGS_WRITABLE = False

# Build handlers dict conditionally - file handlers only if logs directory is writable
_BASE_HANDLERS = {
    'console': {
        'level': 'INFO',
        'class': 'logging.StreamHandler',
        'formatter': 'simple'
    },
    'security_console': {
        'level': 'WARNING',
        'class': 'logging.StreamHandler',
        'formatter': 'security',
    },
}

# Add file handlers only if logs directory is writable
if _LOGS_WRITABLE:
    _BASE_HANDLERS['file'] = {
        'level': 'INFO',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': BASE_DIR / 'logs' / 'django.log',
        'maxBytes': 1024 * 1024 * 15,  # 15MB
        'backupCount': 10,
        'formatter': 'verbose',
    }
    _BASE_HANDLERS['security_file'] = {
        'level': 'INFO',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': BASE_DIR / 'logs' / 'security.log',
        'maxBytes': 1024 * 1024 * 50,  # 50MB - security logs need more space
        'backupCount': 20,
        'formatter': 'security',
    }
    _BASE_HANDLERS['security_requests_file'] = {
        'level': 'INFO',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': BASE_DIR / 'logs' / 'security_requests.log',
        'maxBytes': 1024 * 1024 * 100,  # 100MB for request logs
        'backupCount': 30,
        'formatter': 'json',
    }

# Use console-only logging if logs directory is not writable
_LOG_HANDLERS = ['console', 'file'] if _LOGS_WRITABLE else ['console']
_SECURITY_HANDLERS = ['security_console', 'security_file'] if _LOGS_WRITABLE else ['security_console']
_SECURITY_REQUESTS_HANDLERS = ['security_requests_file'] if _LOGS_WRITABLE else ['security_console']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'security': {
            'format': '[SECURITY] {levelname} {asctime} {name} {message}',
            'style': '{',
        },
        'json': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': _BASE_HANDLERS,
    'root': {
        'handlers': _LOG_HANDLERS,
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': _LOG_HANDLERS,
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.security': {
            'handlers': _SECURITY_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
        # Security loggers
        'security': {
            'handlers': _SECURITY_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
        'security.requests': {
            'handlers': _SECURITY_REQUESTS_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
        'security.validation': {
            'handlers': _SECURITY_HANDLERS,
            'level': 'WARNING',
            'propagate': False,
        },
        # Django Axes logging
        'axes': {
            'handlers': _SECURITY_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ====================
# FILE UPLOAD SETTINGS
# ====================

MAX_UPLOAD_SIZE = env.int('MAX_UPLOAD_SIZE', default=10485760)  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE

# ====================
# CRISPY FORMS
# ====================

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ====================
# AUDIT LOG
# ====================

AUDITLOG_INCLUDE_ALL_MODELS = True

# ====================
# SENTRY (Error Tracking)
# ====================

if env('SENTRY_DSN', default=''):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=env('ENVIRONMENT', default='development'),
    )

# ====================
# CUSTOM SETTINGS
# ====================

# Application settings
SITE_NAME = env('SITE_NAME', default='Finance SaaS Platform')
SITE_URL = env('SITE_URL', default='http://localhost')
ADMIN_EMAIL = env('ADMIN_EMAIL', default='admin@example.com')

# Feature flags
ENABLE_ANALYTICS = env.bool('ENABLE_ANALYTICS', default=True)
ENABLE_INTEGRATIONS = env.bool('ENABLE_INTEGRATIONS', default=True)
ENABLE_WEBHOOKS = env.bool('ENABLE_WEBHOOKS', default=True)
ENABLE_NOTIFICATIONS = env.bool('ENABLE_NOTIFICATIONS', default=True)

# Compliance
DATA_RETENTION_DAYS = env.int('DATA_RETENTION_DAYS', default=2555)  # 7 years
GDPR_ENABLED = env.bool('GDPR_ENABLED', default=True)
AUDIT_LOG_ENABLED = env.bool('AUDIT_LOG_ENABLED', default=True)

# Phone number field
PHONENUMBER_DEFAULT_REGION = 'US'
PHONENUMBER_DEFAULT_FORMAT = 'INTERNATIONAL'

# AWS S3 Configuration (Optional)
if env.bool('USE_S3', default=False):
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'private'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
