from types import SimpleNamespace

from apps.core.permissions import IsOwner, IsOwnerOrManager, IsSalonMember, Role


def _request(*, authenticated=True, salon=None, membership=None):
    user = SimpleNamespace(is_authenticated=authenticated)
    return SimpleNamespace(user=user, salon=salon, membership=membership)


def test_is_salon_member_requires_authenticated_user_with_a_salon():
    assert IsSalonMember().has_permission(_request(salon="some-salon"), None) is True
    assert IsSalonMember().has_permission(_request(salon=None), None) is False
    assert (
        IsSalonMember().has_permission(_request(authenticated=False, salon="x"), None)
        is False
    )


def test_is_owner_or_manager_checks_membership_role():
    owner_membership = SimpleNamespace(role=Role.OWNER)
    manager_membership = SimpleNamespace(role=Role.MANAGER)
    staff_membership = SimpleNamespace(role=Role.STAFF)

    assert IsOwnerOrManager().has_permission(_request(membership=owner_membership), None)
    assert IsOwnerOrManager().has_permission(_request(membership=manager_membership), None)
    assert not IsOwnerOrManager().has_permission(_request(membership=staff_membership), None)
    assert not IsOwnerOrManager().has_permission(_request(membership=None), None)


def test_is_owner_checks_membership_role():
    owner_membership = SimpleNamespace(role=Role.OWNER)
    manager_membership = SimpleNamespace(role=Role.MANAGER)

    assert IsOwner().has_permission(_request(membership=owner_membership), None) is True
    assert IsOwner().has_permission(_request(membership=manager_membership), None) is False
    assert IsOwner().has_permission(_request(membership=None), None) is False
