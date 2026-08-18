from django.contrib import admin

from .models import Branch, Membership, Salon


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "salon", "phone"]
    list_filter = ["salon"]
    search_fields = ["name", "salon__name"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "salon", "role", "is_current"]
    list_filter = ["role", "is_current"]
    search_fields = ["user__email", "salon__name"]
