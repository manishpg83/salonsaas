from rest_framework.permissions import BasePermission


class Role:
    """
    Mirrors the choices that will be formalized as `Membership.role`
    (TextChoices) in Phase 1.3 (apps.salons). Defined here as plain strings
    so permission classes have something to compare against before that
    model exists — replace these references with the real enum once it
    lands, per CLAUDE.md §4.3.
    """

    OWNER = "OWNER"
    MANAGER = "MANAGER"
    RECEPTIONIST = "RECEPTIONIST"
    STAFF = "STAFF"


class IsSalonMember(BasePermission):
    """User is authenticated and has an active membership in some salon."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request, "salon", None)
        )


class IsOwnerOrManager(BasePermission):
    """User's active membership in the current salon is OWNER or MANAGER."""

    def has_permission(self, request, view):
        membership = getattr(request, "membership", None)
        return bool(membership and membership.role in (Role.OWNER, Role.MANAGER))


class IsOwner(BasePermission):
    """User's active membership in the current salon is OWNER."""

    def has_permission(self, request, view):
        membership = getattr(request, "membership", None)
        return bool(membership and membership.role == Role.OWNER)
