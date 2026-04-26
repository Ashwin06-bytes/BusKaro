from django.urls import path
from . import views

urlpatterns = [
    path('<int:bus_id>/', views.live_tracking, name='live_tracking'),
    path('<int:bus_id>/update/', views.update_location, name='update_location'),
]
