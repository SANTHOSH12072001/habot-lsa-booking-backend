import pytest
from bookings.models import Parent, LSAProfile

@pytest.fixture
def parent(db):
    return Parent.objects.create(
        full_name="Test Parent",
        email="parent@example.com",
        phone="1234567890",
    )

@pytest.fixture
def lsa(db):
    return LSAProfile.objects.create(
        full_name="Alex LSA",
        email="lsa@example.com",
        bio="Learning support specialist",
        hourly_rate="50.00",
        skills=["reading", "math", "adhd-support"],
        is_active=True,
    )

@pytest.fixture
def inactive_lsa(db):
    return LSAProfile.objects.create(
        full_name="Inactive LSA",
        email="inactive@example.com",
        hourly_rate="50.00",
        skills=["reading"],
        is_active=False,
    )
