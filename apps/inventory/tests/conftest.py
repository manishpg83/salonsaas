import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.salons.models import Membership

User = get_user_model()


@pytest.fixture
def make_web_client(db):
    """Same fixture as apps/staff, apps/crm, apps/scheduling, apps/billing
    tests (kept per-app per this project's existing convention rather than a
    shared root conftest)."""

    def _make(email, password="a-strong-password-123"):
        User.objects.create_user(email=email, full_name="Test User", password=password)
        client = Client()
        assert client.login(username=email, password=password)
        membership = Membership.objects.get(user__email=email, is_current=True)
        return client, membership

    return _make
