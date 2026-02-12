"""
Test settings for running pytest without external services.
Uses SQLite in-memory database and disables external dependencies.
"""
from config.settings import *  # noqa: F401, F403

# Use local PostgreSQL for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'aureon_test',
        'USER': 'aureon_user',
        'PASSWORD': 'testpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable Celery during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable caching during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sessions',
    },
    'locks': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'locks',
    },
    'throttle': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'throttle',
    },
    'local': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'local',
    },
}

# Use console email backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Session engine compatible with test caches
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'

# Disable SSL for tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_NAME = 'sessionid'
CSRF_COOKIE_NAME = 'csrftoken'

# Disable HSTS for tests
SECURE_HSTS_SECONDS = 0

# Disable Axes during tests (can cause issues with test isolation)
AXES_ENABLED = False

# Simplified logging for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'WARNING',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
