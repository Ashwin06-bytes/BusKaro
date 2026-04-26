from django.contrib import admin
from .models import BusLocation


@admin.register(BusLocation)
class BusLocationAdmin(admin.ModelAdmin):
    list_display = ('bus', 'latitude', 'longitude', 'updated_at')
    list_filter = ('bus',)
    readonly_fields = ('updated_at',)
