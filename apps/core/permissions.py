from rest_framework.permissions import BasePermission

from apps.salons.models import Role


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
