from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from .serializers import RegisterSerializer, UserSerializer

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
