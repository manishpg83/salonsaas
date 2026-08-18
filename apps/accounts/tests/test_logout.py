import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


def _login(client):
    User.objects.create_user(email="owner@example.com", full_name="Owner Person", password="a-strong-password-123")
    login = client.post(
        "/api/v1/auth/login/",
        {"email": "owner@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    return login.json()


def test_logout_blacklists_the_refresh_token():
    client = APIClient()
    tokens = _login(client)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    logout_response = client.post("/api/v1/auth/logout/", {"refresh": tokens["refresh"]}, format="json")
    assert logout_response.status_code == 205

    reuse_response = client.post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert reuse_response.status_code == 401


def test_logout_requires_authentication():
    response = APIClient().post("/api/v1/auth/logout/", {"refresh": "irrelevant"}, format="json")

    assert response.status_code == 401
