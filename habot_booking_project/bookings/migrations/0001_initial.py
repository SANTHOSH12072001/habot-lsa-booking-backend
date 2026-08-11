from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.core.validators import MinValueValidator


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LSAProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("full_name", models.CharField(max_length=120)),
                ("email", models.EmailField(db_index=True, max_length=254, unique=True)),
                ("bio", models.TextField(blank=True)),
                ("hourly_rate", models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("skills", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["full_name"], "indexes": [
                models.Index(fields=["is_active", "id"], name="lsa_active_id_idx")
            ]},
        ),
        migrations.CreateModel(
            name="Parent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("full_name", models.CharField(max_length=120)),
                ("email", models.EmailField(db_index=True, max_length=254, unique=True)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["full_name"]},
        ),
        migrations.CreateModel(
            name="BookingRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("session_start", models.DateTimeField(db_index=True)),
                ("session_end", models.DateTimeField(db_index=True)),
                ("status", models.CharField(choices=[
                    ("PENDING_PAYMENT", "Pending Payment"), ("CONFIRMED", "Confirmed"),
                    ("PAYMENT_FAILED", "Payment Failed"), ("CANCELLED", "Cancelled")
                ], db_index=True, default="PENDING_PAYMENT", max_length=30)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])),
                ("external_reference", models.CharField(blank=True, db_index=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("lsa", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="bookings.lsaprofile")),
                ("parent", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="bookings.parent")),
            ],
            options={"ordering": ["-session_start"], "indexes": [
                models.Index(fields=["lsa", "session_start", "session_end"], name="booking_lsa_time_idx"),
                models.Index(fields=["parent", "session_start"], name="booking_parent_time_idx"),
                models.Index(fields=["status", "session_start"], name="booking_status_time_idx"),
            ]},
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("provider", models.CharField(default="mock_gateway", max_length=50)),
                ("transaction_id", models.CharField(max_length=120, unique=True)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("SUCCESS", "Success"), ("FAILED", "Failed")], db_index=True, default="PENDING", max_length=20)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("booking", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment", to="bookings.bookingrequest")),
            ],
            options={"indexes": [
                models.Index(fields=["status", "created_at"], name="payment_status_created_idx")
            ]},
        ),
        migrations.AddConstraint(
            model_name="bookingrequest",
            constraint=models.CheckConstraint(
                condition=models.Q(("session_end__gt", models.F("session_start"))),
                name="booking_end_after_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="bookingrequest",
            constraint=models.CheckConstraint(
                condition=models.Q(("amount__gte", 0)),
                name="booking_amount_nonnegative",
            ),
        ),
    ]
