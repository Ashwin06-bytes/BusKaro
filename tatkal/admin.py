from django.contrib import admin
from .models import TatkalConfig, TatkalQuota, TatkalBooking
from operators.models import Operator

class TatkalConfigInline(admin.StackedInline):
    model = TatkalConfig
    can_delete = False

# We'll need to re-register Operator in an actual integration,
# but for now we just define the inline so it's ready.

@admin.register(TatkalConfig)
class TatkalConfigAdmin(admin.ModelAdmin):
    list_display = ('operator', 'window_minutes_before', 'surcharge_percent', 'quota_seats', 'is_active')
    list_filter = ('is_active',)

@admin.register(TatkalQuota)
class TatkalQuotaAdmin(admin.ModelAdmin):
    list_display = ('source', 'source_trip_id', 'is_open', 'opened_at', 'seats_allocated', 'seats_booked')
    list_filter = ('is_open', 'source')
    readonly_fields = ('opened_at',)

@admin.register(TatkalBooking)
class TatkalBookingAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'quota', 'surcharge_amount', 'predicted_demand_score', 'dynamic_surcharge_pct', 'booked_at')
    readonly_fields = ('ticket', 'quota', 'surcharge_amount', 'predicted_demand_score', 'dynamic_surcharge_pct', 'booked_at')

    def has_add_permission(self, request):
        return False
