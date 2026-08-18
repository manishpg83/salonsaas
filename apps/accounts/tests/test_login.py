import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


def _create_user(email="owner@example.com", password="a-strong-password-123"):
    return User.objects.create_user(email=email, full_name="Owner Person", password=password)


def test_login_with_correct_credentials_returns_access_and_refresh_tokens():
    _create_user()

    response = APIClient().post(
        "/api/v1/auth/login/",
        {"email": "owner@example.com", "password": "a-strong-password-123"},
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert "access" in body
    assert "refresh" in body


def test_login_with_wrong_password_is_rejected():
    _create_user()

    response = APIClient().post(
        "/api/v1/auth/login/",
        {"email": "owner@example.com", "password": "wrong-password"},
        format="json",
    )

    assert response.status_code == 401
