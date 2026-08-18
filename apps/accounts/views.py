from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from .models import OTP
from .otp import consume_valid_otp, generate_otp
from .serializers import (
    OTPRequestSerializer,
    OTPVerifySerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class TokenObtainPairView(BaseTokenObtainPairView):
    """Login. Overrides permission_classes — the project-wide default is
    IsAuthenticated, but you can't be authenticated before you've logged in."""

    permission_classes = [permissions.AllowAny]


class TokenRefreshView(BaseTokenRefreshView):
    """Same reasoning as TokenObtainPairView: must be reachable unauthenticated."""

    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """Blacklists the given refresh token so it can no longer mint new access
    tokens. The access token itself stays valid until it naturally expires
    (it's stateless) — this is the standard tradeoff for short-lived access
    tokens (SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'])."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# --- OTP login ---------------------------------------------------------------
# Both endpoints below return the same generic response whether or not the
# email belongs to an account — this avoids letting the API be used to probe
# which emails are registered (a common form of user enumeration).

class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email=serializer.validated_data["email"], is_active=True
        ).first()
        if user:
            generate_otp(user, OTP.Purpose.LOGIN)

        return Response({"detail": "If an account exists for this email, an OTP has been sent."})


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = consume_valid_otp(
            email=serializer.validated_data["email"],
            code=serializer.validated_data["code"],
            purpose=OTP.Purpose.LOGIN,
        )
        if not otp:
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(otp.user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})


# --- Forgot / reset password --------------------------------------------------

class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email=serializer.validated_data["email"], is_active=True
        ).first()
        if user:
            generate_otp(user, OTP.Purpose.PASSWORD_RESET)

        return Response({"detail": "If an account exists for this email, a reset code has been sent."})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = consume_valid_otp(
            email=serializer.validated_data["email"],
            code=serializer.validated_data["code"],
            purpose=OTP.Purpose.PASSWORD_RESET,
        )
        if not otp:
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        otp.user.set_password(serializer.validated_data["new_password"])
        otp.user.save(update_fields=["password"])
        return Response({"detail": "Password has been reset."})
