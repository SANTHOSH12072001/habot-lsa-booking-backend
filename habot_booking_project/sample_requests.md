# API Demo Commands

Start the server:

```bash
python manage.py runserver
```

## 1. Search LSAs

```bash
curl "http://127.0.0.1:8000/api/v1/lsas/search/?skill=reading"
```

## 2. Create booking

Replace UUIDs with values from your database:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/bookings/" ^
  -H "Content-Type: application/json" ^
  -d "{"parent_id":"PARENT_UUID","lsa_id":"LSA_UUID","session_start":"2026-08-20T10:00:00Z","session_end":"2026-08-20T11:00:00Z","amount":"50.00","external_reference":"REF-001"}"
```

## 3. Trigger successful payment

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/payments/webhook/" ^
  -H "Content-Type: application/json" ^
  -d "{"transaction_id":"TXN-1001","booking_id":"BOOKING_UUID","status":"SUCCESS","amount":"50.00","provider":"mock_gateway"}"
```

Expected booking status:

```text
CONFIRMED
```

## 4. Trigger failed payment

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/payments/webhook/" ^
  -H "Content-Type: application/json" ^
  -d "{"transaction_id":"TXN-1002","booking_id":"BOOKING_UUID","status":"FAILED","amount":"50.00","provider":"mock_gateway"}"
```

Expected booking status:

```text
PAYMENT_FAILED
```
