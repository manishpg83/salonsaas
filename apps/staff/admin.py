from django.contrib import admin

from .models import Staff, StaffService


class StaffServiceInline(admin.TabularInline):
    model = StaffService
    extra = 1
    autocomplete_fields = ["service"]


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ["name", "salon", "role", "branch", "mobile", "is_active"]
    list_filter = ["salon", "branch", "is_active"]
    search_fields = ["name", "mobile", "salon__name"]
    inlines = [StaffServiceInline]
