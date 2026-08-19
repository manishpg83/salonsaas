"""
Base settings — shared by every environment.

Why split settings? `dev.py` and `prod.py` each import everything from here
and override only what differs (DEBUG, ALLOWED_HOSTS, security headers, ...).
This keeps environment-specific config in one small file instead of a tangle
of `if DEBUG:` branches in a single settings.py.

Nothing here should read directly from a hardcoded value for anything secret
or environment-dependent — that all comes from `.env` via django-environ.
"""

from pathlib import Path

import environ

# BASE_DIR = salonos/ (the folder containing manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# django-environ reads KEY=VALUE pairs from a .env file and exposes them with
# type casting (env.bool, env.int, env.list, ...) and defaults. This is how
# secrets (DB password, SECRET_KEY) stay out of source control — only
# .env.example (placeholders) is committed; .env (real values) is gitignored.
env = environ.Env()
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-changeme-in-env")

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])


# --- Application definition -------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
    # local apps
    "apps.core",
    "apps.accounts",
    "apps.salons",
    "apps.catalog",
    "apps.staff",
    "apps.crm",
    "apps.scheduling",
    "apps.billing",
]

# Custom user model — email login, no username (set before the first
# migration; changing this later requires recreating the accounts migrations).
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CorsMiddleware must sit above CommonMiddleware so CORS headers are
    # added before Django's own response processing runs.
    "corsheaders.middleware.CorsMiddleware",
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
        # Project-wide templates (base.html, the shared sidebar+topbar shell)
        # live in salonos/templates/. Each app's own templates still resolve
        # via APP_DIRS (salonos/apps/<app>/templates/<app_label>/*.html).
        "DIRS": [BASE_DIR / "templates"],
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


# --- Database ----------------------------------------------------------------
# PostgreSQL only — no sqlite fallback, so dev and prod behave the same way
# (Postgres-only features like JSONField behavior, constraints, etc.)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME", default="salonos_dev"),
        "USER": env("DATABASE_USER", default="postgres"),
        "PASSWORD": env("DATABASE_PASSWORD", default=""),
        "HOST": env("DATABASE_HOST", default="localhost"),
        "PORT": env("DATABASE_PORT", default="5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Password validation ------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Internationalization ------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True  # store everything in UTC; convert to local time at the edges


# --- Static files --------------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]


# --- Media (user uploads, e.g. Staff.photo) -------------------------------------
# Local FileSystemStorage for dev/MVP; swapping to django-storages/S3 for
# production is a later, separate change (see requirements.txt).

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# --- Session auth (Django Templates era, Phase 3+) ---------------------------
# Where to send a user who hits @salon_member_required / @login_required
# while logged out, and where "log in" / "log out" send them afterward.

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"


# --- CORS ------------------------------------------------------------------
# Empty by default; each environment (dev/prod) sets its own allowed origins
# since a frontend dev server (e.g. localhost:3000) is not a prod origin.

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])


# --- Django REST Framework ---------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# --- JWT (SimpleJWT) ---------------------------------------------------------
# Access tokens are short-lived (used on every request); refresh tokens are
# longer-lived and only used to mint a new access token. Rotating refresh
# tokens on use + blacklisting the old one limits the damage if one leaks.

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
