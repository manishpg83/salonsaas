from django.contrib import admin

from .models import Appointment, AppointmentService


class AppointmentServiceInline(admin.TabularInline):
    model = AppointmentService
    extra = 1
    autocomplete_fields = ["service"]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["customer", "salon", "date", "time", "status", "price"]
    list_filter = ["salon", "status", "branch"]
    search_fields = ["customer__name", "customer__mobile", "salon__name"]
    inlines = [AppointmentServiceInline]
