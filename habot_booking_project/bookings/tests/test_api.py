from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from bookings.models import BookingRequest, Payment


@pytest.fixture
def client():
    return APIClient()


def booking_payload(parent, lsa, start):
    return {
        "parent_id": str(parent.id),
        "lsa_id": str(lsa.id),
        "session_start": start.isoformat(),
        "session_end": (start + timedelta(hours=1)).isoformat(),
        "amount": "50.00",
        "external_reference": "REF-001",
    }


@pytest.mark.django_db
def test_create_booking_success(client, parent, lsa):
    start = timezone.now() + timedelta(days=1)
    response = client.post("/api/v1/bookings/", booking_payload(parent, lsa, start), format="json")

    assert response.status_code == 201
    assert response.data["status"] == BookingRequest.Status.PENDING_PAYMENT
    assert BookingRequest.objects.count() == 1


@pytest.mark.django_db
def test_reject_overlapping_booking(client, parent, lsa):
    start = timezone.now() + timedelta(days=1)
    first = client.post("/api/v1/bookings/", booking_payload(parent, lsa, start), format="json")
    second = client.post(
        "/api/v1/bookings/",
        booking_payload(parent, lsa, start + timedelta(minutes=30)),
        format="json",
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert "overlapping" in second.data["detail"].lower()


@pytest.mark.django_db
def test_reject_past_session(client, parent, lsa):
    payload = booking_payload(parent, lsa, timezone.now() - timedelta(hours=1))
    response = client.post("/api/v1/bookings/", payload, format="json")

    assert response.status_code == 400
    assert "session_start" in response.data


@pytest.mark.django_db
def test_search_lsas_by_skill_is_single_query(client, lsa, inactive_lsa, django_assert_num_queries):
    with django_assert_num_queries(1):
        response = client.get("/api/v1/lsas/search/?skill=reading")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["full_name"] == "Alex LSA"


@pytest.mark.django_db
def test_inactive_lsa_cannot_be_booked(client, parent, inactive_lsa):
    start = timezone.now() + timedelta(days=1)
    response = client.post(
        "/api/v1/bookings/",
        booking_payload(parent, inactive_lsa, start),
        format="json",
    )

    assert response.status_code == 400
    assert "inactive" in response.data["detail"].lower()


@pytest.mark.django_db
def test_payment_webhook_success_confirms_booking(client, parent, lsa):
    start = timezone.now() + timedelta(days=1)
    create_response = client.post("/api/v1/bookings/", booking_payload(parent, lsa, start), format="json")
    booking_id = create_response.data["id"]

    webhook = client.post("/api/v1/payments/webhook/", {
        "transaction_id": "TXN-1001",
        "booking_id": booking_id,
        "status": "SUCCESS",
        "amount": "50.00",
    }, format="json")

    assert webhook.status_code == 200
    assert webhook.data["booking_status"] == BookingRequest.Status.CONFIRMED
    assert Payment.objects.get(transaction_id="TXN-1001").status == Payment.Status.SUCCESS


@pytest.mark.django_db
def test_payment_webhook_amount_mismatch_does_not_confirm(client, parent, lsa):
    start = timezone.now() + timedelta(days=1)
    create_response = client.post("/api/v1/bookings/", booking_payload(parent, lsa, start), format="json")
    booking_id = create_response.data["id"]

    webhook = client.post("/api/v1/payments/webhook/", {
        "transaction_id": "TXN-1002",
        "booking_id": booking_id,
        "status": "SUCCESS",
        "amount": "999.00",
    }, format="json")

    assert webhook.status_code == 400
    booking = BookingRequest.objects.get(id=booking_id)
    assert booking.status == BookingRequest.Status.PENDING_PAYMENT
