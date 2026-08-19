from django.contrib import admin

from .models import (
    Product,
    ProductCategory,
    Purchase,
    PurchaseItem,
    ServiceProduct,
    StockTransaction,
    Supplier,
)


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    autocomplete_fields = ["product"]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "salon", "contact_phone", "contact_email"]
    list_filter = ["salon"]
    search_fields = ["name", "salon__name"]


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "salon"]
    list_filter = ["salon"]
    search_fields = ["name", "salon__name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "salon", "category", "current_stock", "min_stock", "is_active"]
    list_filter = ["salon", "category", "is_active"]
    search_fields = ["name", "sku", "salon__name"]


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ["product", "type", "quantity", "salon", "created_at"]
    list_filter = ["salon", "type"]
    search_fields = ["product__name", "reference"]


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ["id", "salon", "supplier", "date", "total"]
    list_filter = ["salon"]
    search_fields = ["salon__name", "supplier__name"]
    inlines = [PurchaseItemInline]


@admin.register(ServiceProduct)
class ServiceProductAdmin(admin.ModelAdmin):
    list_display = ["service", "product", "quantity", "salon"]
    list_filter = ["salon"]
    search_fields = ["service__name", "product__name"]
