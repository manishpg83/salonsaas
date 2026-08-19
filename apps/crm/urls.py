from django.urls import path

from .views import (
    customer_create_view,
    customer_delete_view,
    customer_detail_view,
    customer_edit_view,
    customer_list_view,
)

urlpatterns = [
    path("customers/", customer_list_view, name="customer-list"),
    path("customers/new/", customer_create_view, name="customer-create"),
    path("customers/<int:pk>/", customer_detail_view, name="customer-detail"),
    path("customers/<int:pk>/edit/", customer_edit_view, name="customer-edit"),
    path("customers/<int:pk>/delete/", customer_delete_view, name="customer-delete"),
]
