import qrcode
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from .models import Bus

def admin_bus_qr_view(request, bus_id):
    if not request.user.is_staff:
        raise PermissionDenied

    bus = get_object_or_404(Bus, pk=bus_id)
    # The unique Bus QR simply needs to point to the booking page for this bus
    # We will build an absolute URL using request.build_absolute_uri
    scan_url = request.build_absolute_uri(reverse('passenger_home', args=[bus.id]))

    img = qrcode.make(scan_url)
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response
