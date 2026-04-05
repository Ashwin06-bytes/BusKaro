import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from routes.models import Bus
from tickets.models import Ticket

def conductor_login(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        b = request.POST.get('bus_id')
        user = authenticate(request, username=u, password=p)
        if user is not None and hasattr(user, 'conductor_profile'):
            bus = get_object_or_404(Bus, id=b, is_active=True)
            # Update conductor's active bus layout
            conductor = user.conductor_profile
            conductor.bus = bus
            conductor.save()
            login(request, user)
            return redirect('conductor_dashboard')
        return render(request, 'conductors/login.html', {'error': 'Invalid credentials or not a conductor', 'buses': Bus.objects.filter(is_active=True)})
    
    buses = Bus.objects.filter(is_active=True)
    return render(request, 'conductors/login.html', {'buses': buses})

def conductor_logout(request):
    logout(request)
    return redirect('conductor_login')

@login_required
def dashboard(request):
    conductor = request.user.conductor_profile
    if not conductor.bus:
        return redirect('conductor_login')
    
    # Active passengers logic: tickets marked ACTIVE for this bus
    active_count = Ticket.objects.filter(bus=conductor.bus, status='ACTIVE').count()
    return render(request, 'conductors/dashboard.html', {
        'conductor': conductor,
        'bus': conductor.bus,
        'active_count': active_count
    })

@login_required
@csrf_exempt
def verify_ticket(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ticket_uuid = data.get('ticket_uuid')
        conductor = request.user.conductor_profile
        
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_uuid)
            
            # Check if ticket belongs to the same bus
            if ticket.bus != conductor.bus:
                return JsonResponse({
                    'valid': False,
                    'message': 'Ticket is for a different bus',
                })
                
            if ticket.status == 'EXPIRED':
                return JsonResponse({
                    'valid': False,
                    'message': 'Ticket Already Used',
                    'passenger_name': ticket.passenger_name,
                    'from_stop': ticket.from_stop.name,
                    'to_stop': ticket.to_stop.name
                })
                
            return JsonResponse({
                'valid': True,
                'message': 'Valid Ticket',
                'passenger_name': ticket.passenger_name,
                'from_stop': ticket.from_stop.name,
                'to_stop': ticket.to_stop.name,
            })
            
        except Ticket.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'message': 'Invalid QR Code'
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def expire_ticket(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ticket_uuid = data.get('ticket_uuid')
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_uuid)
            if ticket.status == 'ACTIVE':
                ticket.status = 'EXPIRED'
                ticket.save()
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'message': 'Already expired'})
        except Ticket.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Ticket not found'})
            
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def end_trip(request):
    """
    Called by conductor to mark all active tickets for their bus as EXPIRED at the end of a trip.
    """
    if request.method == 'POST':
        conductor = request.user.conductor_profile
        if conductor.bus:
            updated_count = Ticket.objects.filter(bus=conductor.bus, status='ACTIVE').update(status='EXPIRED')
            return JsonResponse({'success': True, 'expired_count': updated_count})
        return JsonResponse({'success': False, 'message': 'No bus assigned'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def live_count(request, bus_id):
    active_count = Ticket.objects.filter(bus_id=bus_id, status='ACTIVE').count()
    return JsonResponse({'active_count': active_count})
