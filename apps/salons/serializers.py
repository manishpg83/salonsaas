from rest_framework import serializers

from .models import Membership, Salon


class SalonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salon
        fields = ["id", "name"]
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    salon = SalonSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "salon", "role", "is_current"]
        read_only_fields = fields


class SwitchSalonSerializer(serializers.Serializer):
    salon_id = serializers.IntegerField()


class OnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salon
        fields = [
            "name",
            "logo_url",
            "address",
            "contact_phone",
            "contact_email",
            "business_hours",
            "payment_methods",
            "whatsapp_number",
            "slug",
            "services_step_done",
            "staff_step_done",
            "onboarding_completed",
        ]
        read_only_fields = ["onboarding_completed"]
