from django.contrib import admin

from .models import Expense, Invoice, InvoiceItem, Payment


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    autocomplete_fields = ["service"]


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "salon", "appointment", "total", "paid_total"]
    list_filter = ["salon"]
    search_fields = ["appointment__customer__name", "salon__name"]
    inlines = [InvoiceItemInline, PaymentInline]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["category", "salon", "amount", "date"]
    list_filter = ["salon", "category"]
    search_fields = ["salon__name", "note"]
