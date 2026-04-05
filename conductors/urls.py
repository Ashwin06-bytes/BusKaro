from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.conductor_login, name='conductor_login'),
    path('logout/', views.conductor_logout, name='conductor_logout'),
    path('dashboard/', views.dashboard, name='conductor_dashboard'),
    path('verify/', views.verify_ticket, name='conductor_verify'),
    path('expire/', views.expire_ticket, name='conductor_expire'),
    path('end-trip/', views.end_trip, name='conductor_end_trip'),
    path('count/<int:bus_id>/', views.live_count, name='conductor_count'),
]
