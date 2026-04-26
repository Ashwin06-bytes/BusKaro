from django.urls import path
from . import views

urlpatterns = [
    path('', views.passenger_entry, name='passenger_entry'),
    path('login/', views.passenger_login, name='passenger_login'),
    path('register/', views.passenger_register, name='passenger_register'),
    path('logout/', views.passenger_logout, name='passenger_logout'),
    path('<int:bus_id>/', views.passenger_home, name='passenger_home'),
    path('api/stops/<int:bus_id>/', views.get_stops_and_fares, name='api_get_stops'),
]
