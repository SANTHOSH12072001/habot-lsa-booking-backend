import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Parent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class LSAProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True, db_index=True)
    bio = models.TextField(blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True, db_index=True)
    skills = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["is_active", "id"], name="lsa_active_id_idx"),
        ]

    def __str__(self):
        return self.full_name


class BookingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "PENDING_PAYMENT", "Pending Payment"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PAYMENT_FAILED = "PAYMENT_FAILED", "Payment Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Parent, on_delete=models.PROTECT, related_name="bookings")
    lsa = models.ForeignKey(LSAProfile, on_delete=models.PROTECT, related_name="bookings")
    session_start = models.DateTimeField(db_index=True)
    session_end = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING_PAYMENT, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    external_reference = models.CharField(max_length=120, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-session_start"]
        indexes = [
            models.Index(fields=["lsa", "session_start", "session_end"], name="booking_lsa_time_idx"),
            models.Index(fields=["parent", "session_start"], name="booking_parent_time_idx"),
            models.Index(fields=["status", "session_start"], name="booking_status_time_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(session_end__gt=models.F("session_start")),
                name="booking_end_after_start",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="booking_amount_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.id} - {self.lsa.full_name} - {self.status}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(BookingRequest, on_delete=models.CASCADE, related_name="payment")
    provider = models.CharField(max_length=50, default="mock_gateway")
    transaction_id = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"], name="payment_status_created_idx"),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"
