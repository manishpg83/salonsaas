import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_me_returns_the_authenticated_users_profile():
    User.objects.create_user(email="owner@example.com", full_name="Owner Person", password="a-strong-password-123")
    client = APIClient()
    login = client.post(
        "/api/v1/auth/login/",
        {"email": "owner@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")

    response = client.get("/api/v1/auth/me/")

    assert response.status_code == 200
    assert response.json()["email"] == "owner@example.com"


def test_me_requires_authentication():
    response = APIClient().get("/api/v1/auth/me/")

    assert response.status_code == 401
