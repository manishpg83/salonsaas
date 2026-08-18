from rest_framework import viewsets

from .permissions import IsSalonMember
from .salon_context import get_active_membership


class SalonScopedViewSet(viewsets.ModelViewSet):
    """
    Base viewset for every salon-scoped business model (Customer,
    Appointment, Service, ...). Resolves the acting user's active salon from
    their Membership, scopes the queryset to it, and stamps it onto new
    objects. This is the multi-tenancy boundary (CLAUDE.md §4.2) — subclasses
    must not query a scoped model any other way.
    """

    permission_classes = [IsSalonMember]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        request.membership = get_active_membership(request.user)
        request.salon = request.membership.salon if request.membership else None

    def get_queryset(self):
        return super().get_queryset().filter(salon=self.request.salon)

    def perform_create(self, serializer):
        serializer.save(salon=self.request.salon)
