from django.urls import path

from .views import (
    LogoutView,
    MeView,
    RegisterView,
    RequestOTPView,
    RequestPasswordResetView,
    ResetPasswordView,
    TokenObtainPairView,
    TokenRefreshView,
    VerifyOTPView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("otp/request/", RequestOTPView.as_view(), name="auth-otp-request"),
    path("otp/verify/", VerifyOTPView.as_view(), name="auth-otp-verify"),
    path("password/forgot/", RequestPasswordResetView.as_view(), name="auth-password-forgot"),
    path("password/reset/", ResetPasswordView.as_view(), name="auth-password-reset"),
]
