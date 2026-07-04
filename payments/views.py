import json
import logging
import uuid
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from routes.models import Bus, Stop
from tickets.models import Ticket

logger = logging.getLogger(__name__)

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

        # ── Tatkal audit record ───────────────────────────────────────────
        # Only created when the caller explicitly flags is_tatkal=true and
        # supplies a quota_id.  All tatkal fields are optional; if any step
        # fails the ticket is still returned successfully.
        is_tatkal = bool(data.get('is_tatkal', False))
        if is_tatkal:
            try:
                from tatkal.models import TatkalQuota, TatkalBooking

                quota_id = data.get('quota_id')
                demand_score = data.get('demand_score')       # float | None
                surcharge_pct = data.get('surcharge_pct')     # float | None

                if quota_id is None:
                    raise ValueError("is_tatkal=True but no quota_id supplied.")

                quota = TatkalQuota.objects.get(id=int(quota_id))

                # Guard: do not create a duplicate TatkalBooking for this ticket
                if not TatkalBooking.objects.filter(ticket=ticket).exists():
                    surcharge_amount = float(amount) - float(data.get('base_fare', amount))

                    TatkalBooking.objects.create(
                        ticket=ticket,
                        quota=quota,
                        surcharge_amount=max(0.0, surcharge_amount),
                        predicted_demand_score=(
                            float(demand_score) if demand_score is not None else None
                        ),
                        dynamic_surcharge_pct=(
                            float(surcharge_pct) if surcharge_pct is not None else None
                        ),
                    )
                    # Increment quota counter
                    quota.seats_booked = quota.seats_booked + 1
                    quota.save(update_fields=['seats_booked'])

                    logger.info(
                        "TatkalBooking created for ticket=%s quota=%s "
                        "demand_score=%s surcharge_pct=%s",
                        ticket.ticket_id, quota.id, demand_score, surcharge_pct,
                    )
                else:
                    logger.warning(
                        "Duplicate TatkalBooking prevented for ticket=%s",
                        ticket.ticket_id,
                    )

            except Exception as _tb_exc:
                # Never let TatkalBooking failure block ticket issuance
                logger.warning(
                    "TatkalBooking creation failed for ticket=%s: %s. "
                    "Ticket issued normally.",
                    ticket.ticket_id,
                    _tb_exc,
                )
        # ── End tatkal audit ──────────────────────────────────────────────

        return JsonResponse({"success": True, "ticket_id": str(ticket.ticket_id)})

    return JsonResponse({"error": "Invalid request"}, status=400)
