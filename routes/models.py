from django.db import models

class Route(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Stop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    name = models.CharField(max_length=255)
    name_tamil = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    arrival_offset_minutes = models.IntegerField(default=0)

    class Meta:
        ordering = ['route', 'order']

    def __str__(self):
        return self.name

class Bus(models.Model):
    OPERATOR_CHOICES = [('GOVT','Government'),('PRIVATE','Private'),('LOCAL','Local')]
    BUS_TYPE_CHOICES = [('ORDINARY','Ordinary'),('EXPRESS','Express'),
                        ('SUPER_DELUXE','Super Deluxe'),('AC','AC'),('SLEEPER','Sleeper')]
    LAYOUT_CHOICES = [('2x2','2x2'),('2x3','2x3'),('SLEEPER','Sleeper')]

    bus_number = models.CharField(max_length=50, unique=True)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='buses')
    is_active = models.BooleanField(default=True)
    
    operator_type = models.CharField(max_length=10, choices=OPERATOR_CHOICES, default='GOVT')
    bus_type = models.CharField(max_length=20, choices=BUS_TYPE_CHOICES, default='ORDINARY')
    layout_type = models.CharField(max_length=10, choices=LAYOUT_CHOICES, default='2x2')
    total_seats = models.PositiveIntegerField(default=40)
    amenities = models.JSONField(
        default=dict, 
        blank=True,
        help_text='e.g. {"ac": false, "wifi": false, "charging": false, "water": false, "blanket": false}'
    )

    def __str__(self):
        return f"{self.bus_number} - {self.route.name}"

class Fare(models.Model):
    from_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='fares_from')
    to_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='fares_to')
    amount = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.from_stop.name} to {self.to_stop.name}: ₹{self.amount}"
