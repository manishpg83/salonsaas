import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_refresh_token_returns_a_new_access_token():
    User.objects.create_user(email="owner@example.com", full_name="Owner Person", password="a-strong-password-123")
    client = APIClient()
    login = client.post(
        "/api/v1/auth/login/",
        {"email": "owner@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    refresh_token = login.json()["refresh"]

    response = client.post("/api/v1/auth/refresh/", {"refresh": refresh_token}, format="json")

    assert response.status_code == 200
    assert "access" in response.json()


def test_refresh_with_invalid_token_is_rejected():
    response = APIClient().post("/api/v1/auth/refresh/", {"refresh": "not-a-real-token"}, format="json")

    assert response.status_code == 401
