from apps.core.views import SalonScopedViewSet

from .models import Service, ServiceCategory
from .serializers import ServiceCategorySerializer, ServiceSerializer


class ServiceCategoryViewSet(SalonScopedViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer


class ServiceViewSet(SalonScopedViewSet):
    queryset = Service.objects.select_related("category", "branch").all()
    serializer_class = ServiceSerializer
