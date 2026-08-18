import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.salons.models import Membership, Role

User = get_user_model()

pytestmark = pytest.mark.django_db


def _authenticated_client(email="owner@example.com", password="a-strong-password-123", role=None):
    user = User.objects.create_user(email=email, full_name="Owner Person", password=password)
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    if role is not None:
        Membership.objects.filter(user=user).update(role=role)
    return client, user


def test_get_onboarding_returns_the_current_salons_profile():
    client, user = _authenticated_client()

    response = client.get("/api/v1/salons/onboarding/")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Owner Person's Salon"
    assert body["onboarding_completed"] is False


def test_patch_onboarding_updates_step_fields():
    client, user = _authenticated_client()

    response = client.patch(
        "/api/v1/salons/onboarding/",
        {"address": "12 Main St", "contact_phone": "555-0100", "slug": "owner-salon"},
        format="json",
    )

    assert response.status_code == 200
    salon = Membership.objects.get(user=user).salon
    assert salon.address == "12 Main St"
    assert salon.contact_phone == "555-0100"
    assert salon.slug == "owner-salon"


def test_patch_onboarding_cannot_set_onboarding_completed_directly():
    client, user = _authenticated_client()

    response = client.patch(
        "/api/v1/salons/onboarding/", {"onboarding_completed": True}, format="json"
    )

    assert response.status_code == 200
    salon = Membership.objects.get(user=user).salon
    assert salon.onboarding_completed is False


def test_staff_member_cannot_edit_onboarding():
    client, _user = _authenticated_client(role=Role.STAFF)

    response = client.patch("/api/v1/salons/onboarding/", {"address": "Nope"}, format="json")

    assert response.status_code == 403


def test_onboarding_requires_authentication():
    response = APIClient().get("/api/v1/salons/onboarding/")

    assert response.status_code == 401


def test_complete_onboarding_requires_name_and_slug():
    client, user = _authenticated_client()

    response = client.post("/api/v1/salons/onboarding/complete/")

    assert response.status_code == 400
    salon = Membership.objects.get(user=user).salon
    assert salon.onboarding_completed is False


def test_complete_onboarding_succeeds_once_slug_is_set():
    client, user = _authenticated_client()
    client.patch("/api/v1/salons/onboarding/", {"slug": "owner-salon"}, format="json")

    response = client.post("/api/v1/salons/onboarding/complete/")

    assert response.status_code == 200
    assert response.json()["onboarding_completed"] is True
    salon = Membership.objects.get(user=user).salon
    assert salon.onboarding_completed is True


def test_complete_onboarding_by_staff_member_is_forbidden():
    client, _user = _authenticated_client(role=Role.STAFF)

    response = client.post("/api/v1/salons/onboarding/complete/")

    assert response.status_code == 403
