from django.urls import path

from .views import (
    CompleteOnboardingView,
    MyMembershipsView,
    OnboardingView,
    SwitchActiveSalonView,
)

urlpatterns = [
    path("me/", MyMembershipsView.as_view(), name="salons-me"),
    path("switch/", SwitchActiveSalonView.as_view(), name="salons-switch"),
    path("onboarding/", OnboardingView.as_view(), name="salons-onboarding"),
    path("onboarding/complete/", CompleteOnboardingView.as_view(), name="salons-onboarding-complete"),
]
