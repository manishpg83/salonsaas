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
