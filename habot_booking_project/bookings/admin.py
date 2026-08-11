from django.contrib import admin
from .models import Parent, LSAProfile, BookingRequest, Payment

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "created_at")
    search_fields = ("full_name", "email")

@admin.register(LSAProfile)
class LSAProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "hourly_rate", "is_active")
    list_filter = ("is_active",)
    search_fields = ("full_name", "email")

@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "parent", "lsa", "session_start", "session_end", "status", "amount")
    list_filter = ("status",)
    search_fields = ("external_reference",)
    date_hierarchy = "session_start"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "booking", "provider", "status", "amount")
    list_filter = ("status", "provider")
    search_fields = ("transaction_id",)
