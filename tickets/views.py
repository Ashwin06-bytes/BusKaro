import qrcode
import os
import razorpay
from io import BytesIO
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from decouple import config
from .models import Ticket

# Long-route bus types eligible for cancellation (excludes LOCAL operator buses)
CANCELLABLE_OPERATOR_TYPES = ('GOVT', 'PRIVATE')

def _is_cancellable(ticket):
    """Check if a ticket is eligible for cancellation (long-route only)."""
    if ticket.status != 'ACTIVE':
        return False
    if not ticket.bus:
        return False
    return ticket.bus.operator_type in CANCELLABLE_OPERATOR_TYPES

def generate_ticket_qr(ticket, request):
    if not ticket.qr_image:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(str(ticket.ticket_id))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        file_name = f"qr_{ticket.ticket_id}.png"
        ticket.qr_image.save(file_name, ContentFile(buffer.getvalue()), save=True)

def view_ticket(request, uuid):
    ticket = get_object_or_404(Ticket, ticket_id=uuid)
    # Ensure QR exists
    if not ticket.qr_image:
        generate_ticket_qr(ticket, request)
    context = {
        'ticket': ticket,
        'is_cancellable': _is_cancellable(ticket),
    }
    return render(request, 'tickets/view.html', context)

def download_pdf(request, uuid):
    ticket = get_object_or_404(Ticket, ticket_id=uuid)
    if not ticket.qr_image:
        generate_ticket_qr(ticket, request)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{ticket.ticket_id}.pdf"'

    c = canvas.Canvas(response, pagesize=A5)
    width, height = A5

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2.0, height - 2*cm, f"TNSTC QR Bus Ticket")
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2.0, height - 3*cm, f"Bus Number: {ticket.bus.bus_number}")
    
    c.drawString(2*cm, height - 5*cm, f"Ticket ID: {str(ticket.ticket_id)[:8]}")
    c.drawString(2*cm, height - 6*cm, f"Date: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}")
    c.drawString(2*cm, height - 7*cm, f"From: {ticket.from_stop.name}")
    c.drawString(2*cm, height - 8*cm, f"To: {ticket.to_stop.name}")
    c.drawString(2*cm, height - 9*cm, f"Fare: Rs. {ticket.fare_amount}")
    
    # Draw Status Watermark
    c.setFont("Helvetica-Bold", 40)
    c.setFillColorRGB(0.8, 0.8, 0.8)
    if ticket.status == 'ACTIVE':
        c.drawCentredString(width/2.0, height/2.0, "ACTIVE")
    elif ticket.status == 'CANCELLED':
        c.drawCentredString(width/2.0, height/2.0, "CANCELLED")
    else:
        c.drawCentredString(width/2.0, height/2.0, "EXPIRED")
        
    # Draw QR code
    c.setFillColorRGB(0, 0, 0)
    img_path = ticket.qr_image.path
    if os.path.exists(img_path):
        c.drawImage(img_path, (width - 5*cm)/2.0, 3*cm, width=5*cm, height=5*cm)
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2.0, 1*cm, "Valid for single trip only. Non-transferable.")
    
    c.showPage()
    c.save()
    
    return response

def download_qr(request, uuid):
    ticket = get_object_or_404(Ticket, ticket_id=uuid)
    if not ticket.qr_image:
        generate_ticket_qr(ticket, request)
    response = HttpResponse(ticket.qr_image, content_type="image/png")
    response['Content-Disposition'] = f'attachment; filename="qr_{ticket.ticket_id}.png"'
    return response

@require_POST
def cancel_ticket(request, uuid):
    """
    Cancel an ACTIVE ticket and initiate a Razorpay refund.
    Only allowed for long-route tickets (GOVT/PRIVATE operators, not LOCAL).
    """
    ticket = get_object_or_404(Ticket, ticket_id=uuid)

    # Guard: only active tickets can be cancelled
    if ticket.status != 'ACTIVE':
        return JsonResponse({'error': 'Only active tickets can be cancelled.'}, status=400)

    # Guard: cancellation only allowed for long-route (non-LOCAL) buses
    if not _is_cancellable(ticket):
        return JsonResponse({'error': 'Cancellation is only available for long-route tickets.'}, status=403)

    # Mark ticket as cancelled
    ticket.status = 'CANCELLED'
    ticket.cancelled_at = timezone.now()
    ticket.save()

    # Initiate Razorpay refund if a payment_id exists
    refund_id = None
    refund_error = None
    if ticket.payment_id and not ticket.payment_id.startswith('mock_pay_'):
        try:
            rzp_client = razorpay.Client(
                auth=(config('RAZORPAY_KEY_ID'), config('RAZORPAY_KEY_SECRET'))
            )
            refund = rzp_client.payment.refund(ticket.payment_id, {
                'amount': int(ticket.fare_amount * 100),  # amount in paise
                'speed': 'normal',
            })
            refund_id = refund.get('id')
        except Exception as e:
            refund_error = str(e)

    # For browser form submissions, redirect back to the ticket view
    if request.content_type != 'application/json':
        return redirect('view_ticket', uuid=ticket.ticket_id)

    return JsonResponse({
        'success': True,
        'ticket_id': str(ticket.ticket_id),
        'status': 'CANCELLED',
        'refund_id': refund_id,
        'refund_error': refund_error,
    })
