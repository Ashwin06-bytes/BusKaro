from django.db import models
from operators.models import Operator
from inventory.models import Schedule
from tickets.models import Ticket

class TatkalConfig(models.Model):
    operator = models.OneToOneField(Operator, on_delete=models.CASCADE, related_name='tatkal_config')
    window_minutes_before = models.PositiveIntegerField(default=120)
    surcharge_percent = models.DecimalField(max_digits=5, decimal_places=2, default=25.00)
    quota_seats = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.operator.name} Tatkal Config"


class TatkalQuota(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, null=True, blank=True, related_name='tatkal_quotas')
    source = models.CharField(max_length=50, help_text="Matches aggregator source name")
    source_trip_id = models.CharField(max_length=100)
    is_open = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    seats_allocated = models.PositiveIntegerField()
    seats_booked = models.PositiveIntegerField(default=0)
    auto_open_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Tatkal Quota for {self.source} - {self.source_trip_id} (Open: {self.is_open})"


class TatkalBooking(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, null=True, blank=True, related_name='tatkal_bookings')
    quota = models.ForeignKey(TatkalQuota, on_delete=models.CASCADE, related_name='bookings')
    surcharge_amount = models.DecimalField(max_digits=8, decimal_places=2)
    booked_at = models.DateTimeField(auto_now_add=True)

    # AI demand prediction audit fields ──────────────────────────────────────
    # Populated at booking time from predict_dynamic_surcharge().
    # NULL when the ticket is not tatkal or when AI values are unavailable.
    predicted_demand_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Raw ML demand score [0–10] at the time of booking."
    )
    dynamic_surcharge_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="AI-predicted surcharge percentage applied at booking time."
    )

    def __str__(self):
        return f"Booking in quota {self.quota.id}"
