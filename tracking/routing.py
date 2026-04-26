from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/tracking/(?P<bus_id>\d+)/$', consumers.BusLocationConsumer.as_asgi()),
]
