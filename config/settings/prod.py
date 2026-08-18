"""
Production settings placeholder — not used until we actually deploy.

Everything below is a sane starting point for when that day comes: no debug
output, HTTPS-only cookies, HSTS. ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS must
be set via .env (no wildcard defaults, unlike dev.py).
"""

from .base import *  # noqa: F401,F403

DEBUG = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
