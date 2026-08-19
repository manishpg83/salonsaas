from django.urls import path

from .views import (
    expense_create_view,
    expense_delete_view,
    expense_edit_view,
    expense_list_view,
    invoice_add_item_view,
    invoice_add_payment_view,
    invoice_detail_view,
    invoice_generate_view,
    invoice_list_view,
    invoice_update_discount_view,
)

urlpatterns = [
    path("invoices/", invoice_list_view, name="invoice-list"),
    path("appointments/<int:appointment_pk>/invoice/", invoice_generate_view, name="invoice-generate"),
    path("invoices/<int:pk>/", invoice_detail_view, name="invoice-detail"),
    path("invoices/<int:pk>/items/", invoice_add_item_view, name="invoice-add-item"),
    path("invoices/<int:pk>/discount/", invoice_update_discount_view, name="invoice-update-discount"),
    path("invoices/<int:pk>/payments/", invoice_add_payment_view, name="invoice-add-payment"),
    path("expenses/", expense_list_view, name="expense-list"),
    path("expenses/new/", expense_create_view, name="expense-create"),
    path("expenses/<int:pk>/edit/", expense_edit_view, name="expense-edit"),
    path("expenses/<int:pk>/delete/", expense_delete_view, name="expense-delete"),
]
