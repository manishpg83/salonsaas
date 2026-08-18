import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.salons.models import Membership, Role, Salon

User = get_user_model()

pytestmark = pytest.mark.django_db


def _authenticated_client(email="owner@example.com", password="a-strong-password-123"):
    user = User.objects.create_user(email=email, full_name="Owner Person", password=password)
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    return client, user


def test_switch_to_a_salon_the_user_belongs_to_makes_it_current():
    client, user = _authenticated_client()
    original_membership = Membership.objects.get(user=user)

    other_salon = Salon.objects.create(name="Second Salon")
    other_membership = Membership.objects.create(user=user, salon=other_salon, role=Role.STAFF)

    response = client.post("/api/v1/salons/switch/", {"salon_id": other_salon.id}, format="json")

    assert response.status_code == 200
    assert response.json()["salon"]["id"] == other_salon.id

    original_membership.refresh_from_db()
    other_membership.refresh_from_db()
    assert original_membership.is_current is False
    assert other_membership.is_current is True


def test_switch_to_a_salon_the_user_does_not_belong_to_is_rejected():
    client, _ = _authenticated_client()
    someone_elses_salon = Salon.objects.create(name="Not Mine")

    response = client.post("/api/v1/salons/switch/", {"salon_id": someone_elses_salon.id}, format="json")

    assert response.status_code == 404


def test_switch_requires_authentication():
    response = APIClient().post("/api/v1/salons/switch/", {"salon_id": 1}, format="json")

    assert response.status_code == 401
