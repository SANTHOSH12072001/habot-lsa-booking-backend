import logging
import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Q

from .models import BookingRequest, LSAProfile, Payment

logger = logging.getLogger(__name__)


def has_overlapping_booking(*, lsa_id, start, end):
    # Half-open interval logic:
    # existing_start < new_end AND existing_end > new_start
    return BookingRequest.objects.filter(
        lsa_id=lsa_id,
        session_start__lt=end,
        session_end__gt=start,
    ).exclude(
        status__in=[BookingRequest.Status.CANCELLED, BookingRequest.Status.PAYMENT_FAILED]
    ).exists()


@transaction.atomic
def create_booking(*, parent, lsa, start, end, amount, external_reference=""):
    # Lock the LSA row so concurrent booking requests for the same LSA
    # serialize the overlap check + insert.
    lsa_locked = LSAProfile.objects.select_for_update().get(pk=lsa.id)

    if has_overlapping_booking(lsa_id=lsa_locked.id, start=start, end=end):
        raise ValueError("The selected LSA already has an overlapping session.")

    booking = BookingRequest.objects.create(
        parent=parent,
        lsa=lsa_locked,
        session_start=start,
        session_end=end,
        amount=amount,
        external_reference=external_reference,
        status=BookingRequest.Status.PENDING_PAYMENT,
    )
    return booking


def notify_payment_gateway(booking):
    payload = {
        "booking_id": str(booking.id),
        "amount": str(booking.amount),
        "currency": "USD",
        "customer_email": booking.parent.email,
    }
    headers = {"Content-Type": "application/json"}
    if settings.PAYMENT_GATEWAY_API_KEY:
        headers["Authorization"] = f"Bearer {settings.PAYMENT_GATEWAY_API_KEY}"

    try:
        response = requests.post(
            settings.PAYMENT_GATEWAY_URL,
            json=payload,
            headers=headers,
            timeout=settings.PAYMENT_GATEWAY_TIMEOUT,
        )
        response.raise_for_status()
        logger.info("Payment gateway request succeeded for booking=%s status=%s",
                    booking.id, response.status_code)
        return response.json()
    except requests.RequestException:
        logger.exception("Payment gateway request failed for booking=%s", booking.id)
        raise


@transaction.atomic
def apply_payment_webhook(*, transaction_id, booking_id, status, amount, payload, provider="mock_gateway"):
    try:
        booking = BookingRequest.objects.select_for_update().get(id=booking_id)
    except BookingRequest.DoesNotExist as exc:
        raise ValueError("Booking not found.") from exc

    if str(booking.amount) != str(amount):
        raise ValueError("Payment amount does not match booking amount.")

    normalized = status.upper()
    if normalized not in {"SUCCESS", "FAILED"}:
        raise ValueError("Unsupported payment status.")

    payment, _ = Payment.objects.update_or_create(
        booking=booking,
        defaults={
            "provider": provider,
            "transaction_id": transaction_id,
            "status": Payment.Status.SUCCESS if normalized == "SUCCESS" else Payment.Status.FAILED,
            "amount": amount,
            "raw_payload": payload,
        },
    )

    if normalized == "SUCCESS":
        booking.status = BookingRequest.Status.CONFIRMED
    else:
        booking.status = BookingRequest.Status.PAYMENT_FAILED
    booking.save(update_fields=["status", "updated_at"])

    logger.info("Booking=%s transitioned to status=%s from payment webhook.",
                booking.id, booking.status)
    return booking, payment
