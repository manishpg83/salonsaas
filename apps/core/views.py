from rest_framework import viewsets

from .permissions import IsSalonMember
from .salon_context import get_active_membership


class CurrentSalonMixin:
    """
    Resolves request.membership/request.salon from the authenticated user's
    current Membership, for any DRF view that needs salon context — not just
    full CRUD ModelViewSets (see SalonScopedViewSet below), but also
    one-off views like the onboarding endpoint.

    Overrides perform_authentication() rather than initial(): APIView.initial()
    calls perform_authentication() then check_permissions() in that order, and
    permission classes like IsSalonMember read request.salon — so resolution
    must happen strictly between those two steps, after request.user exists
    but before permissions are evaluated. (Overriding initial() itself and
    calling super().initial() first — as this used to do — runs
    check_permissions() before request.salon is set, so IsSalonMember would
    reject every request.)
    """

    def perform_authentication(self, request):
        super().perform_authentication(request)
        request.membership = get_active_membership(request.user)
        request.salon = request.membership.salon if request.membership else None


class SalonScopedViewSet(CurrentSalonMixin, viewsets.ModelViewSet):
    """
    Base viewset for every salon-scoped business model (Customer,
    Appointment, Service, ...). Scopes the queryset to the current salon and
    stamps it onto new objects. This is the multi-tenancy boundary
    (CLAUDE.md §4.2) — subclasses must not query a scoped model any other way.
    """

    permission_classes = [IsSalonMember]

    def get_queryset(self):
        return super().get_queryset().filter(salon=self.request.salon)

    def perform_create(self, serializer):
        serializer.save(salon=self.request.salon)
