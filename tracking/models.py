from django.db import models
from routes.models import Bus


class BusLocation(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        get_latest_by = 'updated_at'

    def __str__(self):
        return f"{self.bus.bus_number} @ ({self.latitude}, {self.longitude})"
