from datetime import timedelta
from unittest.mock import Mock, patch
import pytest
from django.utils import timezone

from bookings.models import BookingRequest
from bookings.services import notify_payment_gateway


@pytest.mark.django_db
def test_mock_gateway_request_uses_timeout(parent, lsa):
    # This test intentionally verifies the third-party integration boundary.
    start = timezone.now() + timedelta(days=1)
    booking = BookingRequest.objects.create(
        parent=parent,
        lsa=lsa,
        session_start=start,
        session_end=start + timedelta(hours=1),
        amount="50.00",
    )

    fake_response = Mock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {"payment_url": "https://mock.local/pay/1"}

    with patch("bookings.services.requests.post", return_value=fake_response) as mocked:
        result = notify_payment_gateway(booking)

    assert result["payment_url"]
    assert mocked.call_args.kwargs["timeout"] > 0
