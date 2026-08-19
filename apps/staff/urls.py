from django.urls import path

from .views import (
    staff_create_view,
    staff_delete_view,
    staff_edit_view,
    staff_list_view,
    staff_services_view,
)

urlpatterns = [
    path("staff/", staff_list_view, name="staff-list"),
    path("staff/new/", staff_create_view, name="staff-create"),
    path("staff/<int:pk>/edit/", staff_edit_view, name="staff-edit"),
    path("staff/<int:pk>/delete/", staff_delete_view, name="staff-delete"),
    path("staff/<int:pk>/services/", staff_services_view, name="staff-services"),
]
