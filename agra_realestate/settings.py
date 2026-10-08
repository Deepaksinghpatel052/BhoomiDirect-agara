"""
Django settings for agra_realestate (BhoomiDirect Agra demo).

Secrets and debug flags are read from environment variables so the same
file works for local demo and a real deployment.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# Writable runtime data (database, uploads). In Docker this is the /app/data volume.
DATA_DIR = Path(os.environ.get("DJANGO_DATA_DIR", BASE_DIR))


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-demo-only-change-me-bhoomidirect-agra-2026",
)
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,*")
# e.g. "https://bhoomidirect.in,https://www.bhoomidirect.in" (needed for forms behind HTTPS / a domain)
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# --------------------------------------------------------------------------
# Brand / business settings (change the brand name here only)
# --------------------------------------------------------------------------
SITE_NAME = "BhoomiDirect Agra"
SITE_TAGLINE = "Sell your land directly. Fair price. Fast payment. No brokers."
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "http://127.0.0.1:8000")
SITE_PHONE = "+91 98970 00000"
SITE_PHONE_RAW = "919897000000"
SITE_WHATSAPP = "919897000000"
SITE_EMAIL = "hello@bhoomidirect-agra.demo"
SITE_ADDRESS = "Demo Office, Fatehabad Road, Agra, Uttar Pradesh 282001"
SITE_LAT = 27.1592
SITE_LNG = 78.0436

# Land unit constants (sq. metre per unit).
# NOTE: Bigha and Biswa differ from region to region in India. For Agra / western
# UP the commonly used "pucca bigha" is 27,225 sq ft (= 5/8 acre ≈ 2529.29 sq m)
# and 1 bigha = 20 biswa. Change these values if the client uses a local variant.
AREA_BIGHA_SQ_METER = 2529.2853
AREA_BISWA_PER_BIGHA = 20

# Multiplier applied over sample circle rate to estimate market value range.
ESTIMATOR_MARKET_MULTIPLIER_LOW = 1.15
ESTIMATOR_MARKET_MULTIPLIER_HIGH = 1.60

# --------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    # Project apps
    "core",
    "accounts",
    "locations",
    "submissions",
    "acquisitions",
    "listings",
    "partners",
    "blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "agra_realestate.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "agra_realestate.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(os.environ.get("DJANGO_DB_PATH", DATA_DIR / "db.sqlite3")),
    }
}

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "accounts.backends.PhoneEmailUsernameBackend",
]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:after_login"
LOGOUT_REDIRECT_URL = "core:home"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
]

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(os.environ.get("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles"))
# WhiteNoise serves CSS/JS/images from STATIC_ROOT in production (compressed, cached).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
# Serve *.min.css / *.min.js built by `python manage.py minify_assets`
USE_MINIFIED_ASSETS = env_bool("USE_MINIFIED_ASSETS", not DEBUG)

MEDIA_URL = "/media/"
MEDIA_ROOT = DATA_DIR / "media"
# Serve uploaded/demo photos through Django when no Nginx is in front (DEBUG off).
SERVE_MEDIA = env_bool("DJANGO_SERVE_MEDIA", True)
# Owner title documents are kept outside MEDIA_ROOT (never publicly served).
PRIVATE_MEDIA_ROOT = DATA_DIR / "private_media"

# Upload limits
MAX_IMAGE_UPLOAD_MB = 5
MAX_DOC_UPLOAD_MB = 10
DATA_UPLOAD_MAX_MEMORY_SIZE = 30 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {message_constants.ERROR: "danger"}

# --------------------------------------------------------------------------
# Production security (enabled automatically when DEBUG is off)
# --------------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
    SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", False)
    CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0"))
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
    "loggers": {"django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False}},
}
