from django.urls import path

from .views import MyMembershipsView, SwitchActiveSalonView

urlpatterns = [
    path("me/", MyMembershipsView.as_view(), name="salons-me"),
    path("switch/", SwitchActiveSalonView.as_view(), name="salons-switch"),
]
