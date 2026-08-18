from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Membership
from .serializers import MembershipSerializer, SwitchSalonSerializer


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
