import uuid
from django.db import models
from routes.models import Bus, Stop

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]

    booking = models.ForeignKey('bookings.Booking', null=True, blank=True, on_delete=models.SET_NULL, related_name='tickets')
    seat = models.ForeignKey('inventory.Seat', null=True, blank=True, on_delete=models.SET_NULL, related_name='tickets')
    
    ticket_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passenger_name = models.CharField(max_length=255)
    passenger_phone = models.CharField(max_length=15)
    
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, related_name='tickets')
    from_stop = models.ForeignKey(Stop, on_delete=models.SET_NULL, null=True, related_name='tickets_from')
    to_stop = models.ForeignKey(Stop, on_delete=models.SET_NULL, null=True, related_name='tickets_to')
    
    fare_amount = models.DecimalField(max_digits=6, decimal_places=2)
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    
    qr_image = models.ImageField(upload_to='tickets/qr/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='tickets/pdf/', blank=True, null=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ticket {self.ticket_id} - {self.passenger_name} ({self.status})"
