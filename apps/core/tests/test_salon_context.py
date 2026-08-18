import pytest
from django.contrib.auth import get_user_model

from apps.core.salon_context import get_active_membership

User = get_user_model()


def test_returns_none_for_unauthenticated_user():
    from types import SimpleNamespace

    anonymous = SimpleNamespace(is_authenticated=False)
    assert get_active_membership(anonymous) is None


def test_returns_none_when_user_is_none():
    assert get_active_membership(None) is None


@pytest.mark.django_db
def test_returns_the_users_current_membership():
    # Registering a user auto-creates an OWNER Membership (apps.salons
    # signal) with is_current=True — see apps/salons/signals.py.
    user = User.objects.create_user(
        email="owner@example.com", full_name="Owner Person", password="a-strong-password-123"
    )

    membership = get_active_membership(user)

    assert membership is not None
    assert membership.user_id == user.id
    assert membership.is_current is True
