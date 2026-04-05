from .base import BaseAdapter
from typing import List, Dict, Any
import datetime
from django.utils import timezone
from inventory.models import Schedule, SeatInventory

class InternalAdapter(BaseAdapter):
    source_name = "internal"

    def fetch(self, origin: str, destination: str, date: str) -> List[Dict[str, Any]]:
        try:
            parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return []

        # Find schedules that match the criteria
        # Assuming route name or stop names match origin/destination for simplicity
        # More robust approach would check stops in between
        schedules = Schedule.objects.filter(
            journey_date=parsed_date,
            route__stops__name__icontains=origin,
            status='SCHEDULED'
        ).distinct()
        
        # In a real scenario, we check if destination stop comes after origin stop.
        # For this MVP, we return schedules matching the date and vaguely matching origin/dest.

        results = []
        for schedule in schedules:
            # Count available seats
            seats_available = SeatInventory.objects.filter(schedule=schedule, status='AVAILABLE').count()
            
            # Construct datetime
            dep_dt = timezone.make_aware(datetime.datetime.combine(schedule.journey_date, schedule.departure_time))
            arr_dt = timezone.make_aware(datetime.datetime.combine(schedule.journey_date, schedule.arrival_time))
            if arr_dt < dep_dt:
                arr_dt += datetime.timedelta(days=1)
            
            duration_mins = int((arr_dt - dep_dt).total_seconds() / 60)
            operator_name = schedule.bus.route.name  # fallback
            if hasattr(schedule.bus, 'operator_type'):
                # Operator logic
                operator_name = "Internal Operator"

            results.append({
                "source": self.source_name,
                "source_trip_id": str(schedule.id),
                "operator_name": operator_name,
                "bus_type": schedule.bus.bus_type,
                "origin": origin,
                "destination": destination,
                "departure_dt": dep_dt.isoformat(),
                "arrival_dt": arr_dt.isoformat(),
                "duration_mins": duration_mins,
                "fare": float(schedule.base_fare),
                "tatkal_fare": None,
                "tatkal_open": False,
                "seats_available": seats_available,
                "is_dummy": False,
                "booking_url": None,
                "amenities": list(schedule.bus.amenities.keys()) if isinstance(schedule.bus.amenities, dict) else []
            })
            
        return results
