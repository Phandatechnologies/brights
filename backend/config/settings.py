"""
Django settings for the Brights backend.

All secrets and environment-specific values are read from environment
variables, loaded from backend/.env in development. Nothing secret is
hardcoded here. See .env.example for the full list of variables.
"""

import os
import sys
import warnings
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load backend/.env into os.environ (does not override real environment variables).
load_dotenv(BASE_DIR / ".env")


def env(name, default=None, required=False):
    """Read an environment variable, failing loudly if a required one is missing."""
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(f"Missing required environment variable: {name}")
    return value


def env_bool(name, default=False):
    return str(env(name, default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


# --- Core security settings -------------------------------------------------

SECRET_KEY = env("DJANGO_SECRET_KEY", required=True)
DEBUG = env_bool("DJANGO_DEBUG", default=False)  # safe default: off
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")

# Websites allowed to send logged-in POST requests (CSRF origin check).
# In development this is the Vite dev server, e.g. http://localhost:5173
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# On Render, the service's own address is provided automatically (e.g. brights-ab12.onrender.com),
# so it doesn't have to be typed in by hand. A custom domain still goes in the two settings above.
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", "")
RENDER_EXTERNAL_URL = env("RENDER_EXTERNAL_URL", "")
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
if RENDER_EXTERNAL_URL and RENDER_EXTERNAL_URL not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(RENDER_EXTERNAL_URL)

# The Django admin lives at this path. Changing it from "admin/" in production
# cuts down automated login attempts (it is not a substitute for strong passwords).
ADMIN_URL = env("DJANGO_ADMIN_URL", "admin/").strip("/") + "/"

# How many reverse proxies sit in front of Django (e.g. 1 on Render). Used to read
# the real visitor IP for rate limiting. 0 = use the direct connection address.
# Setting it higher than reality would let attackers fake their IP.
TRUSTED_PROXY_COUNT = int(env("TRUSTED_PROXY_COUNT", "0"))


# --- Applications -----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Third-party
    "rest_framework",
    # Brights apps
    "core",
    "accounts",
    "tutors",
    "profiles",
    "contact",
    "moderation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.RequestSizeLimitMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves static files and the built React app
    "core.middleware.AdminLoginRateLimitMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Database (PostgreSQL) --------------------------------------------------
# Production hosts (e.g. Neon) give one DATABASE_URL; development uses DB_* values.


def database_from_url(url):
    parts = urlparse(url)
    if parts.scheme not in ("postgres", "postgresql"):
        raise ImproperlyConfigured("DATABASE_URL must be a postgres:// URL.")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parts.path.lstrip("/")),
        "USER": unquote(parts.username or ""),
        "PASSWORD": unquote(parts.password or ""),
        "HOST": parts.hostname or "",
        "PORT": str(parts.port or 5432),
        "OPTIONS": dict(parse_qsl(parts.query)),  # e.g. sslmode=require
    }


if env("DATABASE_URL"):
    DATABASES = {"default": database_from_url(env("DATABASE_URL"))}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", required=True),
            "USER": env("DB_USER", required=True),
            "PASSWORD": env("DB_PASSWORD", required=True),
            "HOST": env("DB_HOST", "localhost"),
            "PORT": env("DB_PORT", "5432"),
        }
    }
DATABASES["default"]["CONN_MAX_AGE"] = int(env("DB_CONN_MAX_AGE", "60"))
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

# Shared cache in the database, so rate limits work across several server processes.
# Created with: python manage.py createcachetable
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "brights_cache"},
}


# --- Users and authentication ---------------------------------------------

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["accounts.backends.LockoutModelBackend"]

# Sessions: the login cookie is HttpOnly (JavaScript cannot read it).
# The CSRF cookie must be readable by the frontend so it can send it back.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
# Only send cookies over HTTPS outside development.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # stay logged in for up to 2 weeks


# --- Passwords --------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Localisation (South Africa) --------------------------------------------

LANGUAGE_CODE = "en-za"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = True
USE_TZ = True


# --- Static files and the React app ------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # filled by: python manage.py collectstatic
# In production (STATIC_MANIFEST=true, set in the Dockerfile) file names get a content
# hash so browsers can cache them forever. That needs collectstatic to have run, so
# development and tests use plain storage.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if env_bool("STATIC_MANIFEST", default=False)
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

# In production Django also serves the built React app (frontend/dist), so the site
# and API share one address and the login cookie just works. In development the
# Vite dev server serves the frontend instead and this folder may not exist.
FRONTEND_DIST = Path(env("FRONTEND_DIST", str(BASE_DIR.parent / "frontend" / "dist")))
WHITENOISE_ROOT = FRONTEND_DIST if FRONTEND_DIST.is_dir() else None

# The React build uses only its own scripts, styles, fonts and images, so browsers are
# told to refuse anything else. This blocks most injected-script attacks.
CONTENT_SECURITY_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    # Tutor how-to videos: YouTube thumbnails, and the privacy-enhanced YouTube player.
    "img-src 'self' data: https://i.ytimg.com",
    "frame-src https://www.youtube-nocookie.com",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])


def _whitenoise_html_headers(headers, path, url):
    """Any HTML file served directly (e.g. /index.html) gets the same protection as React pages."""
    if path.endswith(".html"):
        headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        headers["X-Frame-Options"] = "DENY"
        headers["Cache-Control"] = "no-cache"


WHITENOISE_ADD_HEADERS_FUNCTION = _whitenoise_html_headers

# Private files (tutor verification documents). This folder is never served by a URL;
# staff download files through a permission-checked API view instead.
PRIVATE_MEDIA_ROOT = Path(env("PRIVATE_MEDIA_ROOT", str(BASE_DIR / "private_media")))

# "local" keeps private files on this server's disk. "s3" uses a private S3-compatible
# bucket (e.g. Cloudflare R2) — needed on hosts whose disk is wiped on every deploy.
PRIVATE_STORAGE_BACKEND = env("PRIVATE_STORAGE_BACKEND", "local")
S3_BUCKET = env("S3_BUCKET", "")
S3_ENDPOINT_URL = env("S3_ENDPOINT_URL", "")
S3_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID", "")
S3_SECRET_ACCESS_KEY = env("S3_SECRET_ACCESS_KEY", "")
S3_REGION = env("S3_REGION", "auto")
if PRIVATE_STORAGE_BACKEND == "s3" and not all([S3_BUCKET, S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY]):
    raise ImproperlyConfigured("PRIVATE_STORAGE_BACKEND=s3 needs S3_BUCKET, S3_ENDPOINT_URL, S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY.")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Django REST Framework --------------------------------------------------
# Secure by default: every endpoint requires a logged-in user unless the view
# explicitly opts out (like the public health check).

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    # Slow down password guessing and sign-up spam on the auth endpoints.
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/minute",       # login, password reset, email links (per IP)
        "register": "30/hour",     # new accounts per IP (schools share one IP, so not too low)
        "contact": "60/day",       # WhatsApp number reveals per IP, on top of 10 new tutors/account/day
        "upload": "30/hour",       # document and photo uploads per account
    },
    # Read the visitor's IP correctly behind a proxy (see TRUSTED_PROXY_COUNT).
    "NUM_PROXIES": TRUSTED_PROXY_COUNT,
}


# --- Email -----------------------------------------------------------------------
# Development default prints emails in the runserver terminal. At deployment set
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend plus the EMAIL_* values.
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=True)
# Give up on a mail server after this many seconds, so a slow or blocked one can't freeze a request.
EMAIL_TIMEOUT = int(env("EMAIL_TIMEOUT", "10"))
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Brights <no-reply@brights.local>")

# Used to build links in emails.
# Used to build links in emails. On Render they default to the service's own address.
FRONTEND_URL = env("FRONTEND_URL") or RENDER_EXTERNAL_URL or "http://localhost:5173"
BACKEND_URL = env("BACKEND_URL") or RENDER_EXTERNAL_URL or "http://localhost:8000"

# Who is emailed immediately about urgent (child-safety) reports. Comma-separated.
# If empty, all active superusers are emailed.
REPORT_ALERT_EMAILS = [e.strip() for e in env("REPORT_ALERT_EMAILS", "").split(",") if e.strip()]

# Brights' YouTube channel, linked from the tutor how-to videos (optional, e.g. https://www.youtube.com/@brights).
YOUTUBE_CHANNEL_URL = env("YOUTUBE_CHANNEL_URL", "")


# --- Production security ------------------------------------------------------------
# Applied whenever DEBUG is off. Check with: python manage.py check --deploy

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
    # The hosting proxy terminates HTTPS and tells Django via this header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", str(60 * 60 * 24 * 30)))  # 30 days
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
    SECURE_HSTS_PRELOAD = False

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# --- Logging --------------------------------------------------------------------------
# Everything goes to the console, where the host collects it. Personal data is never logged.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", "INFO"), "propagate": False},
    },
}

# During `manage.py test`, many tests send bad or forbidden requests on purpose and Django
# logs each refusal. Silence that expected noise so a clean run is just dots and "OK".
# Test results are unaffected: failures still come from assertions, not logs.
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"
if TESTING:
    LOGGING["loggers"]["django"]["level"] = "CRITICAL"
    # WhiteNoise warns that staticfiles/ is missing; it only exists after a production build.
    warnings.filterwarnings("ignore", message=r"No directory at", category=UserWarning)
