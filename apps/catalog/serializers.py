from rest_framework import serializers

from .models import Package, PackageService, Service, ServiceCategory


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, name):
        # The DB constraint is on (salon, name), but `salon` isn't a
        # serializer field (it's stamped by SalonScopedViewSet.perform_create,
        # not client-supplied) — DRF can't build its usual
        # UniqueTogetherValidator without every constraint field present, so
        # a duplicate would otherwise fall through to a raw IntegrityError.
        salon = self.context["request"].salon
        queryset = ServiceCategory.objects.filter(salon=salon, name=name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return name


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "category",
            "branch",
            "name",
            "description",
            "price",
            "duration_minutes",
            "tax_percent",
            "gender",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def _current_salon(self):
        return self.context["request"].salon

    def validate_category(self, category):
        # Without this, a client could pass another salon's category id: the
        # Service itself still gets salon=request.salon stamped by
        # SalonScopedViewSet.perform_create(), but its category FK would
        # point cross-tenant. PrimaryKeyRelatedField's default queryset is
        # unscoped (ServiceCategory.objects.all()), so this has to be
        # enforced here explicitly.
        if category.salon_id != self._current_salon().id:
            raise serializers.ValidationError("Invalid category.")
        return category

    def validate_branch(self, branch):
        if branch is not None and branch.salon_id != self._current_salon().id:
            raise serializers.ValidationError("Invalid branch.")
        return branch


class PackageServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageService
        fields = ["service", "quantity"]


class PackageSerializer(serializers.ModelSerializer):
    items = PackageServiceSerializer(many=True)

    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "description",
            "price",
            "is_active",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("A package must include at least one service.")

        request = self.context["request"]
        seen_service_ids = set()
        for item in items:
            service = item["service"]
            if service.salon_id != request.salon.id:
                raise serializers.ValidationError("Invalid service in package.")
            if service.id in seen_service_ids:
                raise serializers.ValidationError("Duplicate service in package.")
            seen_service_ids.add(service.id)
        return items

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        salon = validated_data["salon"]
        package = Package.objects.create(**validated_data)
        PackageService.objects.bulk_create(
            PackageService(package=package, salon=salon, **item) for item in items_data
        )
        return package
