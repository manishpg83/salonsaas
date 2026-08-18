import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_register_creates_user_and_does_not_echo_password():
    response = APIClient().post(
        "/api/v1/auth/register/",
        {"email": "owner@example.com", "full_name": "Owner Person", "password": "a-strong-password-123"},
        format="json",
    )

    assert response.status_code == 201
    assert "password" not in response.json()
    assert User.objects.filter(email="owner@example.com").exists()

    user = User.objects.get(email="owner@example.com")
    assert user.check_password("a-strong-password-123")


def test_register_rejects_duplicate_email():
    User.objects.create_user(email="owner@example.com", full_name="Existing", password="a-strong-password-123")

    response = APIClient().post(
        "/api/v1/auth/register/",
        {"email": "owner@example.com", "full_name": "Owner Person", "password": "a-strong-password-123"},
        format="json",
    )

    assert response.status_code == 400
    assert "email" in response.json()


def test_register_rejects_weak_password():
    response = APIClient().post(
        "/api/v1/auth/register/",
        {"email": "owner@example.com", "full_name": "Owner Person", "password": "123"},
        format="json",
    )

    assert response.status_code == 400
    assert "password" in response.json()
