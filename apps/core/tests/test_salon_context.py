from types import SimpleNamespace
from unittest.mock import patch

from apps.core.salon_context import get_active_membership


def test_returns_none_for_unauthenticated_user():
    anonymous = SimpleNamespace(is_authenticated=False)
    assert get_active_membership(anonymous) is None


def test_returns_none_when_user_is_none():
    assert get_active_membership(None) is None


@patch("apps.core.salon_context.apps")
def test_queries_active_membership_for_authenticated_user(mock_apps):
    user = SimpleNamespace(is_authenticated=True)
    membership_model = mock_apps.get_model.return_value
    filtered = membership_model.objects.filter.return_value.select_related.return_value
    filtered.first.return_value = "membership-instance"

    result = get_active_membership(user)

    mock_apps.get_model.assert_called_once_with("salons", "Membership")
    membership_model.objects.filter.assert_called_once_with(user=user, is_active=True)
    assert result == "membership-instance"
