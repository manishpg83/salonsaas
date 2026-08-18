"""
URL configuration for the config project.

All API routes live under /api/v1/ (see CLAUDE.md §4.4). Each app will get
its own urls.py included here as it's built (e.g. path('api/v1/', include('apps.accounts.urls'))).
"""
from django.contrib import admin
from django.urls import include, path

from config.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/health/', health_check, name='health-check'),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/salons/', include('apps.salons.urls')),
]
