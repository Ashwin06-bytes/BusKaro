from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_view, name='search'),
    path('stops/', views.stop_search_api, name='stop_search_api'),
    path('cities/', views.city_search_api, name='city_search_api'),
]
