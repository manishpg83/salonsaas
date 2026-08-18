"""Local development settings. Run with DJANGO_SETTINGS_MODULE=config.settings.dev."""

from .base import *  # noqa: F401,F403

DEBUG = True

# Local dev never needs a real allowlist — the runserver host is always trusted.
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
