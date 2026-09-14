"""
Django settings for phm_backend project.

These settings configure the core framework, installed applications and
middleware, database connections and other system behaviour. They are kept
minimal intentionally; many values should be overridden via environment
variables when deploying to production. See the README for details.
"""

from __future__ import annotations

import os
from pathlib import Path
import mimetypes


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# A placeholder key is provided for development purposes only. In production
# you should set the DJANGO_SECRET_KEY environment variable to a secure value.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-change-me-please"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in {"1", "true", "yes"}

# In development you can leave this empty; in production set allowed hosts
# explicitly via the DJANGO_ALLOWED_HOSTS environment variable (comma separated).
ALLOWED_HOSTS: list[str] = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if os.environ.get("DJANGO_ALLOWED_HOSTS") else ["localhost", "127.0.0.1", "testserver"]

# CSRF settings for development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",  # Vite dev server alternative
    "http://localhost:3000",  # Alternative dev server
    "http://127.0.0.1:3000",  # Alternative dev server
]

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party apps
    "rest_framework",
    "channels",
    "corsheaders",  # 添加 CORS 支持
    # Local apps
    "phm",
    "algorithm_integration",
    "simulation_dataset",
    "platform_health",
    "fault_diagnosis",
      "rul_service",
    "simulation_demo",
    "datasets",
    "fault_models",
]

# Optional external algorithm handoff bundle. The adapter is loaded lazily so
# Django can still start when scientific dependencies are not installed.
PHM_PLATFORM_HANDOFF_DIR = Path(os.environ.get(
    "PHM_PLATFORM_HANDOFF_DIR",
    str(BASE_DIR.parent.parent / "platform_handoff_20260911_v1"),
))
PHM_HEALTH_ASSESSMENT_ENABLED = os.environ.get(
    "PHM_HEALTH_ASSESSMENT_ENABLED", "true"
).lower() in {"1", "true", "yes"}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # 添加 CORS 中间件
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "phm_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates", BASE_DIR / "frontend" / "dist"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "phm_backend.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# SQLite is the migration-friendly default: the complete database is a single
# portable file. Set USE_SQLITE=false and provide MYSQL_* variables to use
# MySQL in an existing deployment.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("MYSQL_DATABASE", "phm_db"),
        "USER": os.environ.get("MYSQL_USER", "Kaimol"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD", "123456"),
        "HOST": os.environ.get("MYSQL_HOST", "localhost"),
        "PORT": os.environ.get("MYSQL_PORT", "3306"),
        "OPTIONS": {
            # Charset ensures proper storage of Chinese characters
            "charset": "utf8mb4",
            # 增加连接超时时间，避免出现 "Server has gone away" 错误
            "connect_timeout": 60,
            "read_timeout": 60,
            "write_timeout": 60,
            # 自动重连设置
            "autocommit": True,
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Optional: use SQLite for local development when USE_SQLITE is set
if os.environ.get("USE_SQLITE", "true").lower() in {"1", "true", "yes"}:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "UTC")

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "frontend" / "dist",
]

# Ensure correct MIME for ES modules (.mjs) when served by Django dev server (Windows)
mimetypes.add_type("text/javascript", ".mjs", True)
mimetypes.add_type("application/javascript", ".mjs", True)

# Media files (user uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model for extended fields (roles etc.)
# Custom user models from the legacy CMG modules are enabled when those apps
# are activated for a production deployment.

# Allow embedding backend pages into iframes from any origin (dev only)
X_FRAME_OPTIONS = "ALLOWALL"

# Redis Configuration for caching and WebSocket
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

# Django Channels Configuration
ASGI_APPLICATION = "phm_backend.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [f"redis://{':{}'.format(REDIS_PASSWORD) if REDIS_PASSWORD else ''}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"],
        },
    },
}

# Redis Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{':{}'.format(REDIS_PASSWORD) if REDIS_PASSWORD else ''}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "cmg_platform",
        "TIMEOUT": 300,  # 默认 5 分钟过期
    }
}

# Session storage uses the local database so login remains available when
# Redis is not running. Redis is optional for cache/realtime workloads.
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Django REST framework settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S.%fZ",
}

# Logging configuration
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
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['console', 'file'],
            'level': 'INFO',  # 鏀逛负INFO绾у埆锛岄伩鍏嶈繃澶欴EBUG鏃ュ織
            'propagate': False,
        },
        'rest_framework': {
            'handlers': ['console', 'file'],
            'level': 'INFO',  # 鏀逛负INFO绾у埆
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
import os
logs_dir = BASE_DIR / 'logs'
logs_dir.mkdir(exist_ok=True)


