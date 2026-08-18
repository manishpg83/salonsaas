from apps.core.views import SalonScopedViewSet

from .models import Package, Service, ServiceCategory
from .serializers import PackageSerializer, ServiceCategorySerializer, ServiceSerializer


class ServiceCategoryViewSet(SalonScopedViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer


class ServiceViewSet(SalonScopedViewSet):
    queryset = Service.objects.select_related("category", "branch").all()
    serializer_class = ServiceSerializer


class PackageViewSet(SalonScopedViewSet):
    """Read/create only per CLAUDE.md §2.2 — no PATCH/PUT/DELETE. Editing or
    removing a package once it may have been sold is a usage-tracking
    concern, deferred to V2."""

    queryset = Package.objects.prefetch_related("items__service").all()
    serializer_class = PackageSerializer
    http_method_names = ["get", "post", "head", "options"]
