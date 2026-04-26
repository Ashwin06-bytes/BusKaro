from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from routes.models import Bus, Stop, Fare

def passenger_home(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id, is_active=True)
    return render(request, 'passengers/home.html', {'bus': bus})

def get_stops_and_fares(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id, is_active=True)
    stops = Stop.objects.filter(route=bus.route).order_by('order')
    
    stops_data = []
    for s in stops:
        stops_data.append({
            'id': s.id,
            'name': s.name,
            'name_tamil': s.name_tamil,
            'order': s.order
        })
    
    fares = Fare.objects.filter(from_stop__in=stops, to_stop__in=stops)
    fares_data = {}
    for f in fares:
        key = f"{f.from_stop.id}-{f.to_stop.id}"
        fares_data[key] = float(f.amount)

    return JsonResponse({
        'stops': stops_data,
        'fares': fares_data
    })

def passenger_entry(request):
    if request.method == 'POST':
        bus_id = request.POST.get('bus_id')
        if bus_id:
            return redirect('passenger_home', bus_id=bus_id)
    
    buses = Bus.objects.filter(is_active=True).order_by('bus_number')
    return render(request, 'passengers/entry.html', {'buses': buses})


def passenger_register(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        if phone and password:
            if User.objects.filter(username=phone).exists():
                messages.error(request, "This phone number is already registered.")
            else:
                user = User.objects.create_user(username=phone, password=password)
                login(request, user)
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
    return render(request, 'passengers/register.html')


def passenger_login(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        user = authenticate(request, username=phone, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid phone number or password.")
    return render(request, 'passengers/login.html')


def passenger_logout(request):
    logout(request)
    return redirect('landing_page')

