import pytest
from django.contrib.auth import get_user_model

from apps.salons.models import Membership, Role, Salon

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_creating_a_user_creates_a_salon_and_an_owner_membership():
    user = User.objects.create_user(
        email="owner@example.com", full_name="Owner Person", password="a-strong-password-123"
    )

    assert Salon.objects.filter(name="Owner Person's Salon").exists()

    membership = Membership.objects.get(user=user)
    assert membership.role == Role.OWNER
    assert membership.is_current is True
    assert membership.salon.name == "Owner Person's Salon"


def test_creating_a_superuser_does_not_create_a_salon():
    User.objects.create_superuser(
        email="admin@example.com", full_name="Super Admin", password="a-strong-password-123"
    )

    assert not Salon.objects.exists()
    assert not Membership.objects.exists()
