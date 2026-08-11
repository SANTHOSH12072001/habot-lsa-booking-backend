# Presentation Outline — 12 Slides

1. **Title**
   - HabotConnect LSA Service Booking Backend
   - Santhosh
   - Python Backend Developer

2. **Problem & Requirements**
   - Parent-to-LSA booking
   - Prevent double-booking
   - Skill search
   - Payment state transitions
   - Tests and CI

3. **Technology Choices**
   - Python
   - Django
   - Django REST Framework
   - SQLite for local demo / PostgreSQL for production
   - Pytest
   - GitHub Actions

4. **Architecture**
   - Client → URL router → API view → serializer/service → ORM → DB
   - Payment webhook → payment service → booking state

5. **Database Design**
   - Parent
   - LSAProfile
   - BookingRequest
   - Payment
   - Relationships and indexes

6. **Booking API**
   - POST /api/v1/bookings/
   - Validation
   - Transaction
   - HTTP 201 / 400 / 409

7. **Double-Booking Prevention**
   - `existing_start < new_end`
   - `existing_end > new_start`
   - Exclude cancelled/payment-failed bookings
   - Atomic transaction

8. **LSA Search & N+1**
   - One queryset
   - DB-side filtering
   - `.only(...)`
   - Test verifies one query

9. **Payment Integration**
   - requests library
   - timeout
   - exception logging
   - webhook amount validation
   - SUCCESS → CONFIRMED
   - FAILED → PAYMENT_FAILED

10. **Testing**
    - Success
    - Edge cases
    - Failures
    - Webhook
    - External request mocking
    - Query count

11. **CI/CD & Production Hardening**
    - GitHub Actions
    - PostgreSQL
    - webhook signatures
    - idempotency
    - authentication
    - monitoring

12. **Demo & Conclusion**
    - Search LSA
    - Create booking
    - Attempt overlap
    - Payment webhook
    - Show tests
    - GitHub link
