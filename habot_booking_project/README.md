# HabotConnect — LSA Service Booking Backend

**Candidate:** Santhosh  
**Position:** Python Backend Developer  
**Contact:** E-Mail : santhosh93113@gmail.com | Mobile : +91 8838642312.

## 1. Project objective

This repository implements the hiring-project requirements for an LSA Service Booking module using **Python + Django REST Framework**.

The assessment asks for a normalized relational design, optimized LSA search, a booking API with double-booking protection, a payment webhook, third-party mock integration, automated tests, CI, and technical documentation.

The implementation includes the four domain entities described in the project outcome:

- `Parent`
- `LSAProfile`
- `BookingRequest`
- `Payment`

## 2. Why Django MVT?

Django uses **MVT (Model-View-Template)** rather than the classic MVC naming convention.

For this backend-only REST API:

- **Model** = database schema and ORM.
- **View** = HTTP endpoint/controller logic.
- **Serializer** = validation and API representation.
- **Template** = not required because this project returns JSON.

I chose Django REST Framework because the assessment explicitly permits Django/DRF and it gives structured validation, HTTP responses, serializers, testing tools, and a mature ORM.

## 3. Architecture

```text
HTTP Client
    |
    v
Django URL Router
    |
    +---- POST /api/v1/bookings/
    |          |
    |          v
    |     Booking Serializer
    |          |
    |          v
    |     Booking Service
    |          |
    |          +--> overlap validation
    |          +--> transaction.atomic()
    |          v
    |        Database
    |
    +---- GET /api/v1/lsas/search/
    |          |
    |          v
    |     one optimized ORM query
    |
    +---- POST /api/v1/payments/webhook/
               |
               v
        Payment Service
               |
               +--> amount validation
               +--> row lock
               +--> Payment upsert
               +--> Booking status transition
```

## 4. Data model

```text
Parent 1 -------- * BookingRequest * -------- 1 LSAProfile
                           |
                           |
                           1
                           |
                         Payment
```

### Parent
Stores the parent/customer identity.

### LSAProfile
Stores the Learning Support Assistant profile, rate, active status, and skills.

### BookingRequest
Connects a parent to an LSA for a time interval. It contains the booking lifecycle state.

### Payment
One-to-one with a booking. Stores provider, transaction ID, amount, status, and raw webhook payload.

## 5. Double-booking protection

The booking service uses half-open interval overlap logic:

```text
existing_start < new_end
AND
existing_end > new_start
```

An existing booking is considered conflicting unless its status is `CANCELLED` or `PAYMENT_FAILED`.

The check is executed inside `transaction.atomic()` and the selected LSA row is locked with `select_for_update()`. This serializes competing booking requests for the same LSA, so the overlap check is performed safely before the insert.

For a larger production deployment, PostgreSQL can additionally enforce non-overlap with an exclusion constraint over a timestamp range as a second database-level safety layer.

## 6. Query optimization / N+1 explanation

The LSA search endpoint uses a single queryset:

```python
LSAProfile.objects.filter(is_active=True)
```

and applies the skill filter at database level.

It also uses `.only(...)` to fetch only fields required by the response.

The serializer does not iterate through related bookings/parents, so it does not trigger additional relationship queries. The automated test explicitly checks that the endpoint performs one database query.

For a normalized relational skill model, a many-to-many `Skill` table could be used in a larger system. In this compact assessment prototype, `JSONField` keeps the schema lightweight while still supporting the required skill filter.

## 7. API specification

### POST `/api/v1/bookings/`

Creates a booking in `PENDING_PAYMENT`.

Example:

```json
{
  "parent_id": "PARENT_UUID",
  "lsa_id": "LSA_UUID",
  "session_start": "2026-08-20T10:00:00Z",
  "session_end": "2026-08-20T11:00:00Z",
  "amount": "50.00",
  "external_reference": "REF-001"
}
```

Success: `201 Created`

Overlap: `409 Conflict`

Invalid payload: `400 Bad Request`

Inactive LSA: `400 Bad Request`

### GET `/api/v1/lsas/search/?skill=reading`

Returns active LSAs matching a skill.

Success: `200 OK`

Example:

```json
[
  {
    "id": "LSA_UUID",
    "full_name": "Alex LSA",
    "email": "lsa@example.com",
    "bio": "Learning support specialist",
    "hourly_rate": "50.00",
    "is_active": true,
    "skills": ["reading", "math"]
  }
]
```

### POST `/api/v1/payments/webhook/`

Expected payload:

```json
{
  "transaction_id": "TXN-1001",
  "booking_id": "BOOKING_UUID",
  "status": "SUCCESS",
  "amount": "50.00",
  "provider": "mock_gateway"
}
```

Payment `SUCCESS` changes booking status to `CONFIRMED`.

Payment `FAILED` changes booking status to `PAYMENT_FAILED`.

A mismatched payment amount is rejected.

## 8. Third-party mock integration

`bookings/services.py` contains `notify_payment_gateway()`.

It uses Python's `requests` library and includes:

- timeout
- `raise_for_status()`
- exception handling
- structured logging
- optional bearer API key
- JSON request/response

The external URL is configurable through `.env`.

In the test suite, `requests.post` is mocked so tests never call a real external service.

## 9. Setup

### Windows

```powershell
py -m venv .venv
.venv\Scriptsctivate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API base URL:

```text
http://127.0.0.1:8000/api/v1/
```

Admin:

```text
http://127.0.0.1:8000/admin/
```

## 10. Seed sample data

Open Django shell:

```bash
python manage.py shell
```

Then:

```python
from bookings.models import Parent, LSAProfile

parent = Parent.objects.create(
    full_name="Jane Parent",
    email="jane@example.com",
    phone="1234567890",
)

lsa = LSAProfile.objects.create(
    full_name="Alex LSA",
    email="alex@example.com",
    bio="Learning support specialist",
    hourly_rate="50.00",
    skills=["reading", "math", "adhd-support"],
)
```

## 11. Run tests

```bash
pytest
```

The suite covers more than the required five cases, including:

1. Successful booking.
2. Overlapping booking rejection.
3. Past session rejection.
4. LSA skill search and query count.
5. Inactive LSA rejection.
6. Successful payment webhook.
7. Payment amount mismatch.
8. Mock third-party request and timeout boundary.

## 12. CI/CD

GitHub Actions is defined in:

```text
.github/workflows/tests.yml
```

Every push and pull request runs the test suite against Python 3.11, 3.12, and 3.13.

## 13. Production hardening

Before real production use:

- PostgreSQL should be the default database.
- Add authentication and authorization.
- Sign and verify webhook requests.
- Add rate limiting.
- Add idempotency keys for booking/payment operations.
- Add database-level exclusion constraints for time-range conflicts.
- Use a secret manager instead of `.env` secrets.
- Add API versioning and OpenAPI/Swagger documentation.
- Add structured JSON logs and centralized monitoring.
- Add Celery/background jobs for payment retries and notifications.

## 14. Git workflow

Recommended branches:

```text
main
develop
feature/booking-api
feature/lsa-search
feature/payment-webhook
```

Example:

```bash
git checkout -b feature/booking-api
git add .
git commit -m "feat: add booking API with overlap validation"
git push origin feature/booking-api
```

Open a pull request into `develop` and merge into `main` only after CI passes.

## 15. Submission checklist

- [ ] Replace candidate contact placeholders.
- [ ] Create a public GitHub/GitLab repository.
- [ ] Push this codebase.
- [ ] Add repository URL to the presentation.
- [ ] Run `pytest` locally and keep the passing output ready.
- [ ] Run the API and demonstrate booking creation.
- [ ] Demonstrate an overlapping request returning `409`.
- [ ] Demonstrate LSA skill search.
- [ ] Demonstrate payment webhook changing booking status.
- [ ] Present the included PowerPoint (maximum 15 slides).
- [ ] Keep code, presentation, and documents labelled with full name and contact information.

## 16. Important assessment talking points

During the interview, be prepared to explain:

1. Why Django REST Framework was selected.
2. Why MVT terminology is used in Django.
3. How the overlap condition works.
4. Why a transaction is used during booking creation.
5. How the LSA search avoids N+1 queries.
6. Why the webhook validates payment amount.
7. Why external requests have a timeout.
8. How tests isolate the third-party dependency.
9. Why PostgreSQL is recommended for stronger concurrency guarantees.
10. What would be changed before production.

## 17. Assignment source alignment

The provided hiring form asks for a production-ready prototype with Parent, LSA, Booking and Payment entities, optimized available-LSA querying, a booking API, payment webhook state transitions, automated tests, and README documentation. It also specifies POST `/api/v1/bookings/` and GET `/api/v1/lsas/search/`, third-party integration with `requests`, and GitHub Actions CI.

Submission deadline stated in the provided form: **13 August 2026**.
