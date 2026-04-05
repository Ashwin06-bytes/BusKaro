from django.db import models
from routes.models import Bus, Route

class Seat(models.Model):
    SEAT_TYPE_CHOICES = [
        ('WINDOW', 'Window'),
        ('AISLE', 'Aisle'),
        ('MIDDLE', 'Middle'),
        ('LOWER_BERTH', 'Lower Berth'),
        ('UPPER_BERTH', 'Upper Berth'),
    ]
    
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=5)
    row = models.PositiveIntegerField()
    column = models.PositiveIntegerField()
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPE_CHOICES)
    is_ladies_reserved = models.BooleanField(default=False)
    is_tatkal = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.bus.bus_number} - {self.seat_number}"

class Schedule(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('DEPARTED', 'Departed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='schedules')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules')
    journey_date = models.DateField()
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    base_fare = models.DecimalField(max_digits=8, decimal_places=2)
    tatkal_fare = models.DecimalField(max_digits=8, decimal_places=2)
    tatkal_quota_pct = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    def __str__(self):
        return f"{self.bus.bus_number} on {self.journey_date}"

class SeatInventory(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('ON_HOLD', 'On Hold'),
        ('BOOKED', 'Booked'),
        ('EXPIRED', 'Expired'),
    ]
    
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='inventory')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='inventory')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    held_by_session = models.CharField(max_length=100, null=True, blank=True)
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    booking = models.ForeignKey('bookings.Booking', null=True, blank=True, on_delete=models.SET_NULL, related_name='seat_inventory')

    class Meta:
        unique_together = ('schedule', 'seat')

    def __str__(self):
        return f"{self.schedule} - {self.seat.seat_number} ({self.status})"
