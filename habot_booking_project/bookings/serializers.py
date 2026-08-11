from django.utils import timezone
from rest_framework import serializers
from .models import Parent, LSAProfile, BookingRequest, Payment


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ["id", "full_name", "email", "phone", "created_at"]
        read_only_fields = ["id", "created_at"]


class LSASerializer(serializers.ModelSerializer):
    class Meta:
        model = LSAProfile
        fields = ["id", "full_name", "email", "bio", "hourly_rate", "is_active", "skills"]
        read_only_fields = ["id"]


class BookingCreateSerializer(serializers.ModelSerializer):
    parent_id = serializers.UUIDField(write_only=True)
    lsa_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = BookingRequest
        fields = [
            "id", "parent_id", "lsa_id", "session_start", "session_end",
            "amount", "status", "external_reference", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs["session_start"]
        end = attrs["session_end"]
        if start <= timezone.now():
            raise serializers.ValidationError({"session_start": "Session start must be in the future."})
        if end <= start:
            raise serializers.ValidationError({"session_end": "Session end must be after session start."})
        return attrs

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class BookingResponseSerializer(serializers.ModelSerializer):
    parent = ParentSerializer(read_only=True)
    lsa = LSASerializer(read_only=True)
    payment = serializers.SerializerMethodField()

    class Meta:
        model = BookingRequest
        fields = [
            "id", "parent", "lsa", "session_start", "session_end",
            "amount", "status", "external_reference", "payment",
            "created_at", "updated_at"
        ]

    def get_payment(self, obj):
        try:
            p = obj.payment
        except Payment.DoesNotExist:
            return None
        return {
            "transaction_id": p.transaction_id,
            "provider": p.provider,
            "status": p.status,
            "amount": str(p.amount),
        }
