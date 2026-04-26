from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:uuid>/', views.view_ticket, name='view_ticket'),
    path('<uuid:uuid>/pdf/', views.download_pdf, name='download_pdf'),
    path('<uuid:uuid>/qr.png', views.download_qr, name='download_qr'),
    path('<uuid:uuid>/cancel/', views.cancel_ticket, name='cancel_ticket'),
]
