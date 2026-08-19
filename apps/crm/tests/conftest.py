import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.salons.models import Membership

User = get_user_model()


@pytest.fixture
def make_web_client(db):
    """Registers a fresh user (auto-gets Salon + OWNER Membership via the
    apps.salons signal) and returns a session-authenticated Django test
    Client alongside their Membership — same fixture as apps/staff/tests
    (kept per-app per this project's existing convention rather than a
    shared root conftest)."""

    def _make(email, password="a-strong-password-123"):
        User.objects.create_user(email=email, full_name="Test User", password=password)
        client = Client()
        assert client.login(username=email, password=password)
        membership = Membership.objects.get(user__email=email, is_current=True)
        return client, membership

    return _make
