from django.contrib import admin
from .models import Ticket

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'passenger_name', 'bus', 'fare_amount', 'status', 'created_at')
    list_filter = ('status', 'bus', 'created_at')
    search_fields = ('passenger_name', 'passenger_phone', 'ticket_id', 'payment_id')
    readonly_fields = ('ticket_id', 'created_at', 'qr_image', 'pdf_file')
