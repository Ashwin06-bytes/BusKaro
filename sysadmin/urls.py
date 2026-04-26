from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_overview, name='sysadmin_dashboard'),
    path('buses/', views.manage_buses, name='sysadmin_buses'),
    path('buses/<int:bus_id>/qr/', views.bus_qr, name='sysadmin_bus_qr'),
    path('buses/remove/', views.remove_bus, name='sysadmin_remove_bus'),
    path('conductors/', views.manage_conductors, name='sysadmin_conductors'),
    path('conductors/remove/', views.remove_conductor, name='sysadmin_remove_conductor'),
    path('tatkal/', views.manage_tatkal, name='sysadmin_tatkal'),
    path('tatkal/add/', views.add_tatkal, name='sysadmin_add_tatkal'),
    path('tatkal/toggle/', views.toggle_tatkal, name='sysadmin_toggle_tatkal'),
    path('export/csv/', views.export_revenue_csv, name='sysadmin_export_csv'),
    path('export/pdf/', views.export_revenue_pdf, name='sysadmin_export_pdf'),
]
