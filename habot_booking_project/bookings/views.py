import logging
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Parent, LSAProfile
from .serializers import BookingCreateSerializer, BookingResponseSerializer, LSASerializer
from .services import create_booking, has_overlapping_booking, apply_payment_webhook

logger = logging.getLogger(__name__)


class BookingCreateAPIView(APIView):
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        parent = get_object_or_404(Parent, id=data["parent_id"])
        lsa = get_object_or_404(LSAProfile, id=data["lsa_id"])

        if not lsa.is_active:
            return Response({"detail": "Selected LSA is inactive."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            booking = create_booking(
                parent=parent,
                lsa=lsa,
                start=data["session_start"],
                end=data["session_end"],
                amount=data["amount"],
                external_reference=data.get("external_reference", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        except IntegrityError:
            logger.exception("Database integrity error while creating booking.")
            return Response({"detail": "Booking could not be created."},
                            status=status.HTTP_409_CONFLICT)

        return Response(
            BookingResponseSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )


class LSASearchAPIView(APIView):
    def get(self, request):
        skill = request.query_params.get("skill", "").strip().lower()
        qs = LSAProfile.objects.filter(is_active=True)

        # JSONField skill filtering. This is a single ORM query and the response
        # does not access reverse relations, so it does not introduce N+1 queries.
        if skill:
            qs = qs.filter(skills__icontains=skill)

        qs = qs.only(
            "id", "full_name", "email", "bio", "hourly_rate", "is_active", "skills"
        )
        return Response(LSASerializer(qs, many=True).data)


class PaymentWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        required = ["transaction_id", "booking_id", "status", "amount"]
        missing = [field for field in required if field not in request.data]
        if missing:
            return Response(
                {"detail": "Missing required fields.", "fields": missing},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking, payment = apply_payment_webhook(
                transaction_id=request.data["transaction_id"],
                booking_id=request.data["booking_id"],
                status=request.data["status"],
                amount=request.data["amount"],
                payload=request.data,
                provider=request.data.get("provider", "mock_gateway"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "booking_id": str(booking.id),
            "booking_status": booking.status,
            "payment": {
                "transaction_id": payment.transaction_id,
                "status": payment.status,
            },
        }, status=status.HTTP_200_OK)
