from django.urls import path

from .views import (
    message_log_view,
    template_edit_view,
    template_list_view,
    template_send_test_view,
)

urlpatterns = [
    path("messaging/templates/", template_list_view, name="message-template-list"),
    path("messaging/templates/<str:trigger>/edit/", template_edit_view, name="message-template-edit"),
    path("messaging/templates/<str:trigger>/test/", template_send_test_view, name="message-template-test"),
    path("messaging/log/", message_log_view, name="message-log"),
]
