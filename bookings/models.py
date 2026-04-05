import uuid
from django.db import models
from inventory.models import Schedule, Seat
from routes.models import Stop

class Booking(models.Model):
    TYPE_CHOICES = [('ADVANCE', 'Advance'), ('ON_BUS', 'On Bus')]
    PAYMENT_STATUS_CHOICES = [('PENDING', 'Pending'), ('PAID', 'Paid'), ('FAILED', 'Failed')]
    STATUS_CHOICES = [('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('CANCELLED', 'Cancelled')]
    
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='bookings')
    passenger_name = models.CharField(max_length=200)
    passenger_phone = models.CharField(max_length=15)
    passenger_email = models.EmailField(blank=True)
    seats = models.ManyToManyField(Seat, related_name='bookings')
    from_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='bookings_from')
    to_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='bookings_to')
    booking_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='ADVANCE')
    is_tatkal = models.BooleanField(default=False)
    total_fare = models.DecimalField(max_digits=8, decimal_places=2)
    payment_id = models.CharField(max_length=200, blank=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Booking {self.booking_id} - {self.passenger_name}"
