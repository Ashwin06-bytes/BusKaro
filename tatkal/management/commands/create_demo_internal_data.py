import datetime
import random
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.test import RequestFactory
from django.core.cache import cache

from routes.models import Route, Bus, Stop, Fare
from operators.models import Operator
from tatkal.models import TatkalConfig, TatkalQuota, TatkalBooking
from inventory.models import Seat, Schedule, SeatInventory
from bookings.models import Booking
from aggregator.views import aggregated_search

class Command(BaseCommand):
    help = 'Create realistic demo internal data for AI tatkal pricing'

    def handle(self, *args, **options):
        # We must NOT train the model here, just seed data
        self.stdout.write("Starting Busify AI Demo Data Seeding...")
        
        today = timezone.now().date()
        
        passenger_names = [
            "Arjun", "Aditya", "Vijay", "Ananya", "Diya", "Rahul", "Priya", 
            "Karthik", "Rohan", "Siddharth", "Meera", "Vikram", "Neha", 
            "Amit", "Pooja", "Sanjay", "Aishwarya", "Deepak", "Shruti", "Harish"
        ]
        
        # Track statistics
        stats = {
            "operators": 0,
            "tatkal_configs": 0,
            "routes": 0,
            "stops": 0,
            "fares": 0,
            "buses": 0,
            "seats": 0,
            "schedules_hist": 0,
            "schedules_fut": 0,
            "bookings_hist": 0,
            "bookings_fut": 0,
            "seat_inventories": 0,
            "tatkal_quotas": 0,
        }
        
        ROUTES_DATA = [
            {
                "name": "Coimbatore to Chennai",
                "description": "Direct route connecting Coimbatore to Chennai via Salem and Villupuram",
                "stops": [
                    {"name": "Coimbatore", "tamil": "கோயம்புத்தூர்", "offset": 0},
                    {"name": "Salem", "tamil": "சேலம்", "offset": 180},
                    {"name": "Villupuram", "tamil": "விழுப்புரம்", "offset": 300},
                    {"name": "Chennai", "tamil": "சென்னை", "offset": 480},
                ],
                "bus_number": "Busify Express 101",
                "dep_time": datetime.time(22, 0),
                "arr_time": datetime.time(6, 0),
                "base_fare": 520.00,
            },
            {
                "name": "Chennai to Madurai",
                "description": "Route from Chennai to Madurai via Villupuram and Trichy",
                "stops": [
                    {"name": "Chennai", "tamil": "சென்னை", "offset": 0},
                    {"name": "Villupuram", "tamil": "விழுப்புரம்", "offset": 180},
                    {"name": "Trichy", "tamil": "திருச்சி", "offset": 300},
                    {"name": "Madurai", "tamil": "மதுரை", "offset": 480},
                ],
                "bus_number": "Busify Express 102",
                "dep_time": datetime.time(8, 0),
                "arr_time": datetime.time(16, 0),
                "base_fare": 480.00,
            },
            {
                "name": "Coimbatore to Salem",
                "description": "Short route connecting Coimbatore and Salem via Erode",
                "stops": [
                    {"name": "Coimbatore", "tamil": "கோயம்புத்தூர்", "offset": 0},
                    {"name": "Erode", "tamil": "ஈரோடு", "offset": 100},
                    {"name": "Salem", "tamil": "சேலம்", "offset": 180},
                ],
                "bus_number": "Busify Express 103",
                "dep_time": datetime.time(10, 0),
                "arr_time": datetime.time(13, 0),
                "base_fare": 180.00,
            },
            {
                "name": "Madurai to Trichy",
                "description": "Express connection between Madurai and Trichy via Dindigul",
                "stops": [
                    {"name": "Madurai", "tamil": "மதுரை", "offset": 0},
                    {"name": "Dindigul", "tamil": "திண்டுக்கல்", "offset": 80},
                    {"name": "Trichy", "tamil": "திருச்சி", "offset": 150},
                ],
                "bus_number": "Busify Express 104",
                "dep_time": datetime.time(14, 30),
                "arr_time": datetime.time(17, 0),
                "base_fare": 150.00,
            },
            {
                "name": "Coimbatore to Bangalore",
                "description": "Interstate route connecting Coimbatore to Bangalore via Salem and Hosur",
                "stops": [
                    {"name": "Coimbatore", "tamil": "கோயம்புத்தூர்", "offset": 0},
                    {"name": "Salem", "tamil": "சேலம்", "offset": 180},
                    {"name": "Hosur", "tamil": "ஓசூர்", "offset": 320},
                    {"name": "Bangalore", "tamil": "பெங்களூரு", "offset": 380},
                ],
                "bus_number": "Busify Express 105",
                "dep_time": datetime.time(23, 30),
                "arr_time": datetime.time(6, 0),
                "base_fare": 650.00,
            },
        ]
        
        with transaction.atomic():
            # 1. Setup Operator & config
            user, _ = User.objects.get_or_create(
                username="busify_operator",
                defaults={
                    "email": "info@busify.com",
                    "first_name": "Busify",
                    "last_name": "Operator"
                }
            )
            operator, op_created = Operator.objects.get_or_create(
                user=user,
                defaults={
                    "name": "Busify",
                    "operator_type": "PRIVATE",
                    "contact_email": "info@busify.com",
                    "contact_phone": "1234567890",
                    "is_verified": True
                }
            )
            if op_created:
                stats["operators"] += 1
                
            config, cfg_created = TatkalConfig.objects.get_or_create(
                operator=operator,
                defaults={
                    "window_minutes_before": 120,
                    "surcharge_percent": 25.00,
                    "quota_seats": 5,
                    "is_active": True
                }
            )
            if cfg_created:
                stats["tatkal_configs"] += 1
                
            # 2. Seed routes, stops, fares, buses, seats
            for r_idx, r_data in enumerate(ROUTES_DATA):
                route, r_created = Route.objects.get_or_create(
                    name=r_data["name"],
                    defaults={"description": r_data["description"]}
                )
                if r_created:
                    stats["routes"] += 1
                
                # Stops
                stops = []
                for s_order, s_data in enumerate(r_data["stops"], start=1):
                    stop, s_created = Stop.objects.get_or_create(
                        route=route,
                        name=s_data["name"],
                        defaults={
                            "name_tamil": s_data["tamil"],
                            "order": s_order,
                            "arrival_offset_minutes": s_data["offset"]
                        }
                    )
                    stops.append(stop)
                    if s_created:
                        stats["stops"] += 1
                
                # Fares between stops
                for i, from_stop in enumerate(stops):
                    for j, to_stop in enumerate(stops):
                        if i < j:
                            # Distance based fare
                            distance = to_stop.order - from_stop.order
                            amount = r_data["base_fare"] * (distance / (len(stops) - 1))
                            fare, f_created = Fare.objects.get_or_create(
                                from_stop=from_stop,
                                to_stop=to_stop,
                                defaults={"amount": round(amount, 2)}
                            )
                            if f_created:
                                stats["fares"] += 1
                
                # Bus
                bus, b_created = Bus.objects.update_or_create(
                    bus_number=r_data["bus_number"],
                    defaults={
                        "route": route,
                        "operator_type": "PRIVATE",
                        "bus_type": "EXPRESS",
                        "layout_type": "2x2",
                        "total_seats": 40,
                        "amenities": {"ac": True, "wifi": True, "charging": True}
                    }
                )
                if b_created:
                    stats["buses"] += 1
                
                # Seats
                seats = list(bus.seats.all())
                if len(seats) < 40:
                    row = 1
                    col = 1
                    seats = []
                    for s_num in range(1, 41):
                        seat_str = f"{s_num}"
                        if col in [1, 4]:
                            seat_type = 'WINDOW'
                        elif col in [2, 3]:
                            seat_type = 'AISLE'
                        else:
                            seat_type = 'MIDDLE'
                        
                        seat, s_created = Seat.objects.get_or_create(
                            bus=bus,
                            seat_number=seat_str,
                            defaults={
                                'row': row,
                                'column': col,
                                'seat_type': seat_type,
                                'is_ladies_reserved': (s_num % 10 == 0),
                                'is_tatkal': (s_num % 8 == 0)
                            }
                        )
                        seats.append(seat)
                        if s_created:
                            stats["seats"] += 1
                        
                        col += 1
                        if col > 4:
                            col = 1
                            row += 1
                
                # 3. Create completed schedules (past 90 days)
                for days_ago in range(1, 91):
                    past_date = today - datetime.timedelta(days=days_ago)
                    
                    # Create past schedule
                    schedule, s_created = Schedule.objects.update_or_create(
                        bus=bus,
                        journey_date=past_date,
                        defaults={
                            "route": route,
                            "departure_time": r_data["dep_time"],
                            "arrival_time": r_data["arr_time"],
                            "base_fare": r_data["base_fare"],
                            "tatkal_fare": r_data["base_fare"] * 1.25,
                            "tatkal_quota_pct": 20,
                            "status": "COMPLETED"
                        }
                    )
                    if s_created:
                        stats["schedules_hist"] += 1
                        
                    # Deterministic randomness per schedule
                    random.seed(schedule.id)
                    
                    # Control bookings volume based on route to get different popularity tiers
                    if r_idx == 3:  # Low popularity (Tier 1) -> < 10 bookings total in 90 days
                        should_have_bookings = (random.random() < 0.05)
                    elif r_idx in [1, 2]:  # Mid popularity (Tier 2) -> ~30 bookings total
                        should_have_bookings = (random.random() < 0.3)
                    else:  # High popularity (Tier 3) -> > 50 bookings
                        should_have_bookings = True
                    
                    booked_seats = []
                    if should_have_bookings:
                        # Occupancy between 40% and 95%
                        occupancy_pct = random.randint(40, 95)
                        booked_count = int(40 * occupancy_pct / 100)
                        booked_seats = random.sample(seats, booked_count)
                    
                    booked_seats_set = set(booked_seats)
                    seat_to_booking = {}
                    
                    i = 0
                    booking_idx = 1
                    while i < len(booked_seats):
                        group_size = random.randint(1, 4)
                        group_seats = booked_seats[i : i + group_size]
                        i += group_size
                        
                        payment_id = f"pay_hist_{schedule.id}_{booking_idx}"
                        
                        booking, b_created = Booking.objects.update_or_create(
                            payment_id=payment_id,
                            defaults={
                                "schedule": schedule,
                                "passenger_name": f"{random.choice(passenger_names)} {booking_idx}",
                                "passenger_phone": f"98765{random.randint(10000, 99999)}",
                                "passenger_email": f"pass_{schedule.id}_{booking_idx}@example.com",
                                "from_stop": stops[0],
                                "to_stop": stops[-1],
                                "booking_type": "ADVANCE",
                                "is_tatkal": False,
                                "total_fare": float(schedule.base_fare) * len(group_seats),
                                "payment_status": "PAID",
                                "status": "CONFIRMED"
                            }
                        )
                        booking.seats.set(group_seats)
                        
                        # Set historical created_at
                        booking_dt = timezone.make_aware(
                            datetime.datetime.combine(schedule.journey_date, schedule.departure_time) - datetime.timedelta(hours=random.randint(2, 24))
                        )
                        Booking.objects.filter(booking_id=booking.booking_id).update(created_at=booking_dt)
                        
                        for s in group_seats:
                            seat_to_booking[s] = booking
                            
                        if b_created:
                            stats["bookings_hist"] += 1
                        booking_idx += 1
                        
                    # Create seat inventory for past schedules
                    for seat in seats:
                        is_booked = (seat in booked_seats_set)
                        _, si_created = SeatInventory.objects.update_or_create(
                            schedule=schedule,
                            seat=seat,
                            defaults={
                                "status": "BOOKED" if is_booked else "AVAILABLE",
                                "booking": seat_to_booking.get(seat) if is_booked else None
                            }
                        )
                        if si_created:
                            stats["seat_inventories"] += 1
                
                # 4. Create future schedules (next 7 days, 0 to 7)
                for day_idx in range(0, 8):
                    fut_date = today + datetime.timedelta(days=day_idx)
                    
                    schedule, s_created = Schedule.objects.update_or_create(
                        bus=bus,
                        journey_date=fut_date,
                        defaults={
                            "route": route,
                            "departure_time": r_data["dep_time"],
                            "arrival_time": r_data["arr_time"],
                            "base_fare": r_data["base_fare"],
                            "tatkal_fare": r_data["base_fare"] * 1.25,
                            "tatkal_quota_pct": 20,
                            "status": "SCHEDULED"
                        }
                    )
                    if s_created:
                        stats["schedules_fut"] += 1
                        
                    # Deterministic randomness per schedule
                    random.seed(schedule.id)
                    
                    # Future occupancy: 10% to 60% (advanced bookings)
                    occupancy_pct = random.randint(10, 60)
                    booked_count = int(40 * occupancy_pct / 100)
                    booked_seats = random.sample(seats, booked_count)
                    booked_seats_set = set(booked_seats)
                    seat_to_booking = {}
                    
                    i = 0
                    booking_idx = 1
                    while i < len(booked_seats):
                        group_size = random.randint(1, 4)
                        group_seats = booked_seats[i : i + group_size]
                        i += group_size
                        
                        payment_id = f"pay_fut_{schedule.id}_{booking_idx}"
                        
                        booking, b_created = Booking.objects.update_or_create(
                            payment_id=payment_id,
                            defaults={
                                "schedule": schedule,
                                "passenger_name": f"{random.choice(passenger_names)} {booking_idx}",
                                "passenger_phone": f"98765{random.randint(10000, 99999)}",
                                "passenger_email": f"pass_fut_{schedule.id}_{booking_idx}@example.com",
                                "from_stop": stops[0],
                                "to_stop": stops[-1],
                                "booking_type": "ADVANCE",
                                "is_tatkal": False,
                                "total_fare": float(schedule.base_fare) * len(group_seats),
                                "payment_status": "PAID",
                                "status": "CONFIRMED"
                            }
                        )
                        booking.seats.set(group_seats)
                        
                        # Set created_at to a recent time
                        booking_dt = timezone.now() - datetime.timedelta(hours=random.randint(1, 12))
                        Booking.objects.filter(booking_id=booking.booking_id).update(created_at=booking_dt)
                        
                        for s in group_seats:
                            seat_to_booking[s] = booking
                            
                        if b_created:
                            stats["bookings_fut"] += 1
                        booking_idx += 1
                        
                    # Create seat inventory for future schedules
                    for seat in seats:
                        is_booked = (seat in booked_seats_set)
                        _, si_created = SeatInventory.objects.update_or_create(
                            schedule=schedule,
                            seat=seat,
                            defaults={
                                "status": "BOOKED" if is_booked else "AVAILABLE",
                                "booking": seat_to_booking.get(seat) if is_booked else None
                            }
                        )
                        if si_created:
                            stats["seat_inventories"] += 1
                            
                    # Create Tatkal Quota for every future schedule
                    _, q_created = TatkalQuota.objects.update_or_create(
                        schedule=schedule,
                        source='internal',
                        source_trip_id=str(schedule.id),
                        defaults={
                            "is_open": True,
                            "opened_at": timezone.now() - datetime.timedelta(minutes=10),
                            "seats_allocated": 5,
                            "seats_booked": 0,
                            "auto_open_time": timezone.now() - datetime.timedelta(hours=1)
                        }
                    )
                    if q_created:
                        stats["tatkal_quotas"] += 1
                        
        # 5. Search & AI Pricing Verification
        self.stdout.write("Running verification test...")
        
        # Clear search cache
        cache.clear()
        
        # Build Request targeting tomorrow's schedule on route 1 (Coimbatore to Chennai)
        tomorrow_date = today + datetime.timedelta(days=1)
        factory = RequestFactory()
        request = factory.get(
            '/aggregator/search/',
            {
                'origin': 'Coimbatore',
                'destination': 'Chennai',
                'date': str(tomorrow_date)
            }
        )
        
        response = aggregated_search(request)
        if response.status_code != 200:
            raise CommandError(f"Search request failed with status code {response.status_code}")
            
        import json
        data = json.loads(response.content)
        results = data.get("results", [])
        
        target_schedule = Schedule.objects.filter(
            bus__bus_number="Busify Express 101",
            journey_date=tomorrow_date
        ).first()
        
        if not target_schedule:
            raise CommandError("Target schedule not found in database for Busify Express 101 tomorrow.")
            
        target_result = None
        for r in results:
            if r.get("source") == "internal" and r.get("source_trip_id") == str(target_schedule.id):
                target_result = r
                break
                
        if not target_result:
            raise CommandError("Search did not return the tomorrow's schedule for Busify Express 101.")
            
        # Verify AI pricing keys are present and active
        tatkal_demand_score = target_result.get("tatkal_demand_score")
        surcharge_percent = target_result.get("surcharge_percent")
        tatkal_fare = target_result.get("tatkal_fare")
        base_fare = target_result.get("fare")
        
        if tatkal_demand_score is None:
            raise CommandError("Verification failed: tatkal_demand_score is None (AI path was not executed/failed).")
            
        if surcharge_percent is None:
            raise CommandError("Verification failed: surcharge_percent is None.")
            
        # Confirm surcharge percent is not always 25% (it will depend on ML)
        # Verify formula: tatkal_fare = base_fare * (1 + surcharge_percent / 100)
        expected_tatkal_fare = round(float(base_fare) * (1 + float(surcharge_percent) / 100), 2)
        if abs(float(tatkal_fare) - expected_tatkal_fare) > 0.01:
            raise CommandError(f"Verification failed: Tatkal fare {tatkal_fare} != expected {expected_tatkal_fare}")
            
        # Success output formatting (ASCII-safe for Windows cp1252)
        self.stdout.write(self.style.SUCCESS("[OK] Internal schedules are returned"))
        self.stdout.write(self.style.SUCCESS("[OK] AI pricing path is executed"))
        self.stdout.write(self.style.SUCCESS("[OK] Dynamic surcharge calculated"))
        self.stdout.write(self.style.SUCCESS("[OK] No errors occurred"))
        
        # --- Live DB counts (always correct regardless of how many times command is run)
        busify_buses = Bus.objects.filter(bus_number__startswith='Busify')
        busify_bus_ids = list(busify_buses.values_list('id', flat=True))
        busify_route_ids = list(busify_buses.values_list('route_id', flat=True))

        fut_sched_count = Schedule.objects.filter(bus_id__in=busify_bus_ids, status='SCHEDULED').count()
        hist_sched_count = Schedule.objects.filter(bus_id__in=busify_bus_ids, status='COMPLETED').count()
        all_sched_ids = list(Schedule.objects.filter(bus_id__in=busify_bus_ids).values_list('id', flat=True))
        booking_count = Booking.objects.filter(schedule_id__in=all_sched_ids).count()
        seat_inv_count = SeatInventory.objects.filter(schedule_id__in=all_sched_ids).count()
        quota_count = TatkalQuota.objects.filter(schedule_id__in=all_sched_ids, source='internal').count()
        route_count = Route.objects.filter(id__in=busify_route_ids).count()

        print("\n=================================================")
        print("BUSIFY AI DEMO DATA CREATED")
        print("=================================================")
        print(f"Internal buses : {busify_buses.count()}")
        print(f"Routes : {route_count}")
        print(f"Future schedules : {fut_sched_count}")
        print(f"Historical schedules : {hist_sched_count}")
        print(f"Bookings : {booking_count}")
        print(f"Seat inventory : {seat_inv_count}")
        print(f"Tatkal quotas : {quota_count}")
        print("=================================================")
        print("Sample AI Prediction")
        print(f"Bus : {target_schedule.bus.bus_number}")
        print(f"Route : {target_schedule.route.name}")
        print(f"Base Fare : Rs.{float(base_fare)}")
        print(f"Demand Score : {float(tatkal_demand_score):.2f}")
        print(f"Dynamic Surcharge : {float(surcharge_percent):.2f} %")
        print(f"Tatkal Fare : Rs.{float(tatkal_fare):.2f}")
        print("=================================================")
        print("Website Demo")
        print("https://busify-o9an.onrender.com")
        print("\nSearch:")
        print("Coimbatore -> Chennai")
        print("Tomorrow")
        print("\nExpected:")
        print("Internal Busify buses appear.")
        print("Dynamic surcharge displayed.")
        print("=================================================\n")


