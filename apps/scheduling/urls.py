from django.urls import path

from .views import (
    appointment_create_view,
    appointment_delete_view,
    appointment_detail_view,
    appointment_edit_view,
    appointment_list_view,
    appointment_services_view,
    appointment_status_view,
)

urlpatterns = [
    path("appointments/", appointment_list_view, name="appointment-list"),
    path("appointments/new/", appointment_create_view, name="appointment-create"),
    path("appointments/<int:pk>/", appointment_detail_view, name="appointment-detail"),
    path("appointments/<int:pk>/edit/", appointment_edit_view, name="appointment-edit"),
    path("appointments/<int:pk>/delete/", appointment_delete_view, name="appointment-delete"),
    path("appointments/<int:pk>/services/", appointment_services_view, name="appointment-services"),
    path("appointments/<int:pk>/status/", appointment_status_view, name="appointment-status"),
]
