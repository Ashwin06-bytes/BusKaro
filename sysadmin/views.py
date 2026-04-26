from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
import qrcode
from django.utils import timezone
from routes.models import Bus, Route
from conductors.models import Conductor
from tickets.models import Ticket
from tatkal.models import TatkalQuota
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from django.utils.dateparse import parse_date

def is_sysadmin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def dashboard_overview(request):
    
    total_tickets = Ticket.objects.count()
    revenue_res = Ticket.objects.aggregate(total_revenue=Sum('fare_amount'))
    total_revenue = revenue_res['total_revenue'] or 0.0
    
    active_passengers = Ticket.objects.filter(status='ACTIVE').count()
    
    total_buses = Bus.objects.count()
    total_conductors = Conductor.objects.count()
    
    # recent 5 tickets
    recent_tickets = Ticket.objects.order_by('-created_at')[:5]

    # Date-wise revenue
    date_revenue = Ticket.objects.annotate(date=TruncDate('created_at')).values('date').annotate(
        total=Sum('fare_amount'), 
        ticket_count=Count('ticket_id')
    ).order_by('-date')[:7]  # Last 7 active days

    # Bus-wise revenue
    bus_revenue = Ticket.objects.values('bus__bus_number').annotate(
        total=Sum('fare_amount'),
        ticket_count=Count('ticket_id')
    ).order_by('-total')

    context = {
        'total_tickets': total_tickets,
        'total_revenue': total_revenue,
        'active_passengers': active_passengers,
        'total_buses': total_buses,
        'total_conductors': total_conductors,
        'recent_tickets': recent_tickets,
        'date_revenue': date_revenue,
        'bus_revenue': bus_revenue,
    }
    return render(request, 'sysadmin/dashboard.html', context)

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def manage_buses(request):
    if request.method == 'POST':
        bus_number = request.POST.get('bus_number')
        route_id = request.POST.get('route_id')
        if bus_number and route_id:
            route = get_object_or_404(Route, id=route_id)
            Bus.objects.create(bus_number=bus_number, route=route, is_active=True)
            messages.success(request, f"Bus {bus_number} successfully added!")
        return redirect('sysadmin_buses')
        
    buses = Bus.objects.all().order_by('route__name', 'bus_number')
    routes = Route.objects.all()
    return render(request, 'sysadmin/buses.html', {'buses': buses, 'routes': routes})

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def remove_bus(request):
    if request.method == 'POST':
        bus_id = request.POST.get('bus_id')
        bus = get_object_or_404(Bus, id=bus_id)
        bus.delete()
        messages.success(request, f"Bus removed.")
    return redirect('sysadmin_buses')

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def manage_conductors(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        password = request.POST.get('password')
        employee_id = request.POST.get('employee_id')
        bus_id = request.POST.get('bus_id')
        
        if username and password and employee_id:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
            else:
                user = User.objects.create_user(username=username, password=password, first_name=first_name)
                bus = None
                if bus_id:
                    bus = get_object_or_404(Bus, id=bus_id)
                Conductor.objects.create(user=user, employee_id=employee_id, bus=bus)
                messages.success(request, f"Conductor {employee_id} created.")
        return redirect('sysadmin_conductors')
        
    conductors = Conductor.objects.select_related('user', 'bus').all()
    buses = Bus.objects.filter(is_active=True)
    return render(request, 'sysadmin/conductors.html', {'conductors': conductors, 'buses': buses})

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def remove_conductor(request):
    if request.method == 'POST':
        conductor_id = request.POST.get('conductor_id')
        conductor = get_object_or_404(Conductor, id=conductor_id)
        user = conductor.user
        conductor.delete()
        user.delete() # removing the base user as well
        messages.success(request, f"Conductor removed.")
    return redirect('sysadmin_conductors')

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def bus_qr(request, bus_id):
    bus = get_object_or_404(Bus, pk=bus_id)
    scan_url = request.build_absolute_uri(reverse('passenger_home', args=[bus.id]))
    
    img = qrcode.make(scan_url)
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    response['Content-Disposition'] = f'inline; filename="bus_{bus.bus_number}_qr.png"'
    return response

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def manage_tatkal(request):
    quotas = TatkalQuota.objects.all().order_by('-id')
    return render(request, 'sysadmin/tatkal.html', {'quotas': quotas})

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def add_tatkal(request):
    if request.method == 'POST':
        source = request.POST.get('source')
        source_trip_id = request.POST.get('source_trip_id')
        seats = request.POST.get('seats_allocated')
        auto_open_str = request.POST.get('auto_open_time')
        
        auto_open_time = None
        if auto_open_str:
            from django.utils.dateparse import parse_datetime
            auto_open_time = parse_datetime(auto_open_str)
            if auto_open_time and timezone.is_naive(auto_open_time):
                auto_open_time = timezone.make_aware(auto_open_time)

        TatkalQuota.objects.create(
            source=source,
            source_trip_id=source_trip_id,
            seats_allocated=seats,
            auto_open_time=auto_open_time,
            is_open=False if auto_open_time else True # open immediately if no timer
        )
        messages.success(request, f"Tatkal quota added for {source} trip {source_trip_id}.")
    return redirect('sysadmin_tatkal')

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def toggle_tatkal(request):
    if request.method == 'POST':
        quota_id = request.POST.get('quota_id')
        quota = get_object_or_404(TatkalQuota, id=quota_id)
        quota.is_open = not quota.is_open
        if quota.is_open and not quota.opened_at:
            quota.opened_at = timezone.now()
        quota.save()
        messages.success(request, f"Tatkal status toggled for {quota.source} trip {quota.source_trip_id}.")
    return redirect('sysadmin_tatkal')

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def export_revenue_csv(request):
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    
    tickets = Ticket.objects.filter(status__in=['ACTIVE', 'EXPIRED']).select_related('bus', 'bus__route')
    
    if from_date_str:
        from_date = parse_date(from_date_str)
        if from_date:
            tickets = tickets.filter(created_at__date__gte=from_date)
    if to_date_str:
        to_date = parse_date(to_date_str)
        if to_date:
            tickets = tickets.filter(created_at__date__lte=to_date)
            
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="revenue_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ticket_uuid', 'bus_number', 'route', 'passenger_fare', 'payment_id', 'created_at'])
    
    for t in tickets:
        writer.writerow([
            t.ticket_id,
            t.bus.bus_number if t.bus else '',
            t.bus.route.name if t.bus and t.bus.route else '',
            t.fare_amount,
            t.payment_id or '',
            t.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
        
    return response

@user_passes_test(is_sysadmin, login_url='/admin/login/')
def export_revenue_pdf(request):
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    
    tickets = Ticket.objects.filter(status__in=['ACTIVE', 'EXPIRED']).select_related('bus', 'bus__route')
    
    if from_date_str:
        from_date = parse_date(from_date_str)
        if from_date:
            tickets = tickets.filter(created_at__date__gte=from_date)
    if to_date_str:
        to_date = parse_date(to_date_str)
        if to_date:
            tickets = tickets.filter(created_at__date__lte=to_date)
            
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="revenue_export.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    
    data = [['ticket_uuid', 'bus_number', 'route', 'passenger_fare', 'payment_id', 'created_at']]
    total_fare = 0.0
    
    for t in tickets:
        data.append([
            str(t.ticket_id)[:8] + '...',
            t.bus.bus_number if t.bus else '',
            (t.bus.route.name[:15] + '...') if (t.bus and t.bus.route and len(t.bus.route.name) > 15) else (t.bus.route.name if t.bus and t.bus.route else ''),
            f"{t.fare_amount}",
            (t.payment_id[:10] + '...') if (t.payment_id and len(t.payment_id) > 10) else (t.payment_id or ''),
            t.created_at.strftime('%Y-%m-%d %H:%M')
        ])
        total_fare += float(t.fare_amount)
        
    data.append(['', '', 'TOTAL', f"{total_fare:.2f}", '', ''])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return response
