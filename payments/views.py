import json
import uuid
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from routes.models import Bus, Stop, Fare
from tickets.models import Ticket

@csrf_exempt
def create_order(request):
    if request.method == "POST":
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))
        # This is where we would call Razorpay: 
        # rzp_client.order.create({"amount": int(amount * 100), "currency": "INR"})
        order_id = f"rzp_mock_order_{uuid.uuid4().hex[:10]}"
        return JsonResponse({"order_id": order_id, "amount": amount, "currency": "INR"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        
        bus_id = data.get('bus_id')
        from_stop_id = data.get('from_stop')
        to_stop_id = data.get('to_stop')
        passenger_name = data.get('passenger_name')
        passenger_phone = data.get('passenger_phone')
        amount = data.get('amount')
        
        bus = get_object_or_404(Bus, id=bus_id)
        from_stop = get_object_or_404(Stop, id=from_stop_id)
        to_stop = get_object_or_404(Stop, id=to_stop_id)
        
        # Here we would verify Razorpay signature:
        # rzp_client.utility.verify_payment_signature(data)

        # Create Ticket
        ticket = Ticket.objects.create(
            passenger_name=passenger_name,
            passenger_phone=passenger_phone,
            bus=bus,
            from_stop=from_stop,
            to_stop=to_stop,
            fare_amount=amount,
            payment_id=data.get('razorpay_payment_id', f"mock_pay_{uuid.uuid4().hex[:8]}")
        )
        # Generate QR code task or inline (we'll do inline inside a signal or method later)
        
        return JsonResponse({"success": True, "ticket_id": str(ticket.ticket_id)})

    return JsonResponse({"error": "Invalid request"}, status=400)
