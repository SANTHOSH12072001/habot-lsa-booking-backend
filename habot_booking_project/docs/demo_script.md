# 5-Minute Interview Demo Script

## 1. Introduce

"This is a Django REST Framework backend for an LSA service booking module. I focused on data integrity, query efficiency, and safe state transitions."

## 2. Show schema

Open `bookings/models.py`.

Explain:
- four domain entities
- foreign keys
- indexes
- check constraints
- one-to-one payment

## 3. Show booking

Create a valid booking using the API.

Explain:
- serializer validation
- active LSA validation
- transaction
- PENDING_PAYMENT state

## 4. Show Poka-Yoke

Submit another booking with an overlapping interval.

Expected result:

```text
409 Conflict
The selected LSA already has an overlapping session.
```

Explain that the API prevents the mistake instead of relying on an operator to remember.

## 5. Show N+1 solution

Open `LSASearchAPIView`.

Explain that the endpoint uses one queryset and the serializer does not traverse related collections.

Show the query-count test.

## 6. Show payment

Post a successful webhook.

Expected:

```text
PENDING_PAYMENT -> CONFIRMED
```

Explain amount validation and row locking.

## 7. Show tests

Run:

```bash
pytest -q
```

Explain the success, edge, failure, webhook, and mocked external service cases.

## 8. Finish

Mention that production would add webhook signatures, authentication, idempotency, PostgreSQL range constraints, monitoring, and rate limiting.
