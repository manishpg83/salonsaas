"""
URL configuration for the config project.

Template pages (the primary interface as of the Phase 3 architecture pivot —
see CLAUDE.md §3) are mounted at the root. The legacy Phase 0-2 DRF API is
still live under /api/v1/ — untouched, not the pattern for new endpoints.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from config.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),

    # Template pages (Phase 3+ primary interface)
    path('', RedirectView.as_view(pattern_name='login'), name='home'),
    path('', include('apps.accounts.web_urls')),
    path('', include('apps.salons.web_urls')),
    path('', include('apps.staff.urls')),
    path('', include('apps.crm.urls')),
    path('', include('apps.scheduling.urls')),
    path('', include('apps.billing.urls')),

    # Legacy DRF API (Phase 0-2, kept but not extended — see CLAUDE.md §3)
    path('api/v1/health/', health_check, name='health-check'),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/salons/', include('apps.salons.urls')),
    path('api/v1/catalog/', include('apps.catalog.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
