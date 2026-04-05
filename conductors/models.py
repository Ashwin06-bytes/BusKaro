from django.db import models
from django.contrib.auth.models import User
from routes.models import Bus

class Conductor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='conductor_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, blank=True, related_name='conductors')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.employee_id}"
