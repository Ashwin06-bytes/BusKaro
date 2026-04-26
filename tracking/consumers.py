import json
from channels.generic.websocket import AsyncWebsocketConsumer


class BusLocationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time bus location tracking.
    Passengers connect to ws/tracking/<bus_id>/ and receive
    location broadcasts from the channel group `bus_<bus_id>`.
    """

    async def connect(self):
        self.bus_id = self.scope['url_route']['kwargs']['bus_id']
        self.group_name = f'bus_{self.bus_id}'

        # Join the bus tracking group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the bus tracking group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        # Passengers are read-only; ignore any incoming messages
        pass

    async def location_update(self, event):
        """
        Handler for `location_update` messages sent to the group.
        Forwards the location data to the connected WebSocket client.
        """
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'updated_at': event['updated_at'],
        }))
