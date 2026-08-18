from django.contrib import admin

from .models import Package, PackageService, Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "salon"]
    list_filter = ["salon"]
    search_fields = ["name", "salon__name"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "salon", "category", "price", "duration_minutes", "is_active"]
    list_filter = ["salon", "category", "is_active", "gender"]
    search_fields = ["name", "salon__name"]


class PackageServiceInline(admin.TabularInline):
    model = PackageService
    extra = 1
    autocomplete_fields = ["service"]


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ["name", "salon", "price", "is_active"]
    list_filter = ["salon", "is_active"]
    search_fields = ["name", "salon__name"]
    inlines = [PackageServiceInline]
