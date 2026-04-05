from django.contrib import admin
from .models import Conductor

@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'bus')
    list_filter = ('bus',)
    search_fields = ('user__username', 'user__first_name', 'employee_id')
