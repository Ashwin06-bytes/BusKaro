from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Route, Bus, Stop, Fare

class StopInline(admin.TabularInline):
    model = Stop
    extra = 1

class BusInline(admin.TabularInline):
    model = Bus
    extra = 1
    readonly_fields = ('qr_code_link',)
    
    def qr_code_link(self, obj):
        if obj.pk:
            url = reverse('admin:bus_qr_code', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">View QR Code</a>', url)
        return "Not saved yet"
    qr_code_link.short_description = 'Passenger QR Code'

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    inlines = [StopInline, BusInline]

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('bus_number', 'route', 'is_active', 'qr_code_link')
    list_filter = ('route', 'is_active')
    search_fields = ('bus_number',)

    def qr_code_link(self, obj):
        # We'll create a simple admin view that returns the QR code image for this bus
        url = reverse('admin:bus_qr_code', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">View QR Code</a>', url)
    qr_code_link.short_description = 'Passenger QR Code'

    def get_urls(self):
        from django.urls import path
        from . import views
        urls = super().get_urls()
        custom_urls = [
            path('<int:bus_id>/qr/', self.admin_site.admin_view(views.admin_bus_qr_view), name='bus_qr_code'),
        ]
        return custom_urls + urls

@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_tamil', 'route', 'order')
    list_filter = ('route',)

@admin.register(Fare)
class FareAdmin(admin.ModelAdmin):
    list_display = ('from_stop', 'to_stop', 'amount')
    list_editable = ('amount',)
    list_filter = ('from_stop__route',)
    list_per_page = 100
    search_fields = ('from_stop__name', 'to_stop__name')
