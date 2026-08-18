import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def make_authenticated_client(db):
    """Registers a fresh user (who auto-gets their own Salon + OWNER
    Membership via the apps.salons signal) and returns a client authenticated
    as them — handy for building two clients scoped to two different salons
    in cross-tenant tests."""

    def _make(email, password="a-strong-password-123"):
        User.objects.create_user(email=email, full_name="Test User", password=password)
        client = APIClient()
        login = client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
        return client

    return _make
