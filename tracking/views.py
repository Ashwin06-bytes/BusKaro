import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from routes.models import Bus
from .models import BusLocation


@require_GET
def live_tracking(request, bus_id):
    """
    Passenger-facing page that connects to the WebSocket
    and shows the bus location updating in real time.
    """
    bus = get_object_or_404(Bus, id=bus_id, is_active=True)

    # Get the latest known location (if any)
    latest = BusLocation.objects.filter(bus=bus).first()

    return render(request, 'tracking/live.html', {
        'bus': bus,
        'latest': latest,
    })


@login_required
@require_POST
@csrf_exempt
def update_location(request, bus_id):
    """
    Conductor-only endpoint.
    Saves the bus location and broadcasts it to all connected passengers
    via the channel group `bus_<bus_id>`.
    """
    bus = get_object_or_404(Bus, id=bus_id, is_active=True)

    # Verify the user is a conductor
    if not hasattr(request.user, 'conductor_profile'):
        return JsonResponse({'error': 'Only conductors can update location.'}, status=403)

    try:
        data = json.loads(request.body)
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid payload. Required: latitude, longitude'}, status=400)

    # Save the location to the database
    location = BusLocation.objects.create(
        bus=bus,
        latitude=latitude,
        longitude=longitude,
    )

    # Broadcast to the channel group
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'bus_{bus_id}',
        {
            'type': 'location_update',
            'latitude': latitude,
            'longitude': longitude,
            'updated_at': location.updated_at.isoformat(),
        }
    )

    return JsonResponse({
        'success': True,
        'latitude': latitude,
        'longitude': longitude,
        'updated_at': location.updated_at.isoformat(),
    })
