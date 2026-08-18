from rest_framework.routers import DefaultRouter

from .views import PackageViewSet, ServiceCategoryViewSet, ServiceViewSet

router = DefaultRouter()
router.register("categories", ServiceCategoryViewSet, basename="service-category")
router.register("services", ServiceViewSet, basename="service")
router.register("packages", PackageViewSet, basename="package")

urlpatterns = router.urls
