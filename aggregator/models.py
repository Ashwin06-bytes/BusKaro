from django.db import models
from django.utils import timezone

class SourceProvider(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="Internal name, e.g., 'tnstc'")
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_dummy = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.display_name

class SearchLog(models.Model):
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    travel_date = models.DateField()
    results_count = models.IntegerField(default=0)
    sources_used = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.origin} to {self.destination} on {self.travel_date}"
