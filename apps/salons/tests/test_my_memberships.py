import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


def _authenticated_client(email="owner@example.com", password="a-strong-password-123"):
    User.objects.create_user(email=email, full_name="Owner Person", password=password)
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    return client


def test_me_lists_the_users_memberships():
    client = _authenticated_client()

    response = client.get("/api/v1/salons/me/")

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["role"] == "OWNER"
    assert results[0]["is_current"] is True
    assert results[0]["salon"]["name"] == "Owner Person's Salon"


def test_me_requires_authentication():
    response = APIClient().get("/api/v1/salons/me/")

    assert response.status_code == 401
