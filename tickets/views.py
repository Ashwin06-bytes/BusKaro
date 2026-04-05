import qrcode
import os
from io import BytesIO
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.urls import reverse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from .models import Ticket

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
    return render(request, 'tickets/view.html', {'ticket': ticket})

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
