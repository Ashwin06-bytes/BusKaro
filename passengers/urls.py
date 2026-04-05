from django.urls import path
from . import views

urlpatterns = [
    path('', views.passenger_entry, name='passenger_entry'),
    path('<int:bus_id>/', views.passenger_home, name='passenger_home'),
    path('api/stops/<int:bus_id>/', views.get_stops_and_fares, name='api_get_stops'),
]
