from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from rest_framework import viewsets

from apps.core.views import SalonScopedViewSet


def test_get_queryset_filters_by_request_salon():
    viewset = SalonScopedViewSet()
    fake_salon = object()
    viewset.request = SimpleNamespace(salon=fake_salon)
    viewset.queryset = MagicMock()

    result = viewset.get_queryset()

    viewset.queryset.filter.assert_called_once_with(salon=fake_salon)
    assert result == viewset.queryset.filter.return_value


def test_perform_create_stamps_request_salon_onto_serializer():
    viewset = SalonScopedViewSet()
    fake_salon = object()
    viewset.request = SimpleNamespace(salon=fake_salon)
    serializer = MagicMock()

    viewset.perform_create(serializer)

    serializer.save.assert_called_once_with(salon=fake_salon)


@patch("apps.core.views.get_active_membership")
def test_perform_authentication_resolves_membership_and_salon_onto_request(mock_get_active_membership):
    fake_salon = object()
    mock_get_active_membership.return_value = SimpleNamespace(salon=fake_salon)
    request = MagicMock(user="some-user")

    with patch.object(viewsets.ModelViewSet, "perform_authentication", return_value=None):
        SalonScopedViewSet().perform_authentication(request)

    mock_get_active_membership.assert_called_once_with("some-user")
    assert request.salon is fake_salon


@patch("apps.core.views.get_active_membership", return_value=None)
def test_perform_authentication_sets_salon_to_none_when_user_has_no_active_membership(_mock):
    request = MagicMock(user="some-user")

    with patch.object(viewsets.ModelViewSet, "perform_authentication", return_value=None):
        SalonScopedViewSet().perform_authentication(request)

    assert request.salon is None


def test_salon_resolution_hooks_perform_authentication_not_initial():
    """Regression test: salon resolution must live in perform_authentication(),
    not initial(). APIView.initial() calls perform_authentication() then
    check_permissions() in that order, and IsSalonMember reads request.salon
    — so if resolution were done in initial() after super().initial(),
    check_permissions() would already have run against an unresolved
    request.salon and every request would be rejected."""
    from apps.core.views import CurrentSalonMixin

    assert "perform_authentication" in CurrentSalonMixin.__dict__
    assert "initial" not in CurrentSalonMixin.__dict__
