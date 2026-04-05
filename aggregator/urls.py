from django.urls import path
from . import views

app_name = 'aggregator'

urlpatterns = [
    path('search/', views.aggregated_search, name='search'),
    path('book/<str:source_name>/<str:trip_id>/', views.dummy_booking, name='dummy_booking'),
]
