from django.contrib import admin

from .models import Message, MessageTemplate


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ["trigger", "salon", "is_active"]
    list_filter = ["salon", "trigger", "is_active"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["salon", "customer", "trigger", "channel", "status", "sent_at"]
    list_filter = ["salon", "trigger", "channel", "status"]
    search_fields = ["recipient", "customer__name"]
