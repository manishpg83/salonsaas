from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsOwnerOrManager
from apps.core.views import CurrentSalonMixin

from .models import Membership
from .serializers import MembershipSerializer, OnboardingSerializer, SwitchSalonSerializer


class MyMembershipsView(generics.ListAPIView):
    """Every salon the authenticated user belongs to, with their role and
    which one is currently active. Deliberately not a SalonScopedViewSet —
    this is how the client discovers salons *before* a current one is set."""

    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Membership.objects.filter(user=self.request.user)
            .select_related("salon")
            .order_by("salon__name")
        )


class SwitchActiveSalonView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SwitchSalonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target = Membership.objects.filter(
            user=request.user, salon_id=serializer.validated_data["salon_id"]
        ).first()
        if not target:
            return Response(
                {"detail": "You are not a member of this salon."},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            Membership.objects.filter(user=request.user, is_current=True).update(is_current=False)
            target.is_current = True
            target.save(update_fields=["is_current"])

        return Response(MembershipSerializer(target).data)


class OnboardingView(CurrentSalonMixin, generics.RetrieveUpdateAPIView):
    """Read/update the current salon's onboarding profile. A single flexible
    endpoint rather than ten step-specific ones — each PATCH call from the
    wizard just sends the fields for whichever step the user is on."""

    serializer_class = OnboardingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    http_method_names = ["get", "patch"]

    def get_object(self):
        if self.request.salon is None:
            raise NotFound("No active salon.")
        return self.request.salon


class CompleteOnboardingView(CurrentSalonMixin, APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request):
        salon = request.salon
        if salon is None:
            raise NotFound("No active salon.")

        if not salon.name or not salon.slug:
            return Response(
                {"detail": "Salon name and booking slug are required before onboarding can be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        salon.onboarding_completed = True
        salon.save(update_fields=["onboarding_completed"])
        return Response(OnboardingSerializer(salon).data)
