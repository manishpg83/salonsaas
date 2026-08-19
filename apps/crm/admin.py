from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "salon", "mobile", "email", "gender", "source"]
    list_filter = ["salon", "gender", "source"]
    search_fields = ["name", "mobile", "email", "salon__name"]
