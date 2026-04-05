from django.db import models
from django.contrib.auth.models import User

class Operator(models.Model):
    OPERATOR_TYPE_CHOICES = [('GOVT','Government'),('PRIVATE','Private'),('LOCAL','Local')]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='operator_profile')
    name = models.CharField(max_length=200)
    operator_type = models.CharField(max_length=10, choices=OPERATOR_TYPE_CHOICES)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
