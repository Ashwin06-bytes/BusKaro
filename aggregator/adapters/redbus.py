from .base import BaseAdapter
from typing import List, Dict, Any
import datetime

class RedbusAdapter(BaseAdapter):
    source_name = "redbus"

    def fetch(self, origin: str, destination: str, date: str) -> List[Dict[str, Any]]:
        if not self.is_dummy:
            return []

        # Dummy data implementation
        try:
            parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return []
            
        results = []
        for i in range(1, 11):
            dep_dt = datetime.datetime.combine(parsed_date, datetime.time(7 + (i % 12), 30))
            arr_dt = dep_dt + datetime.timedelta(hours=7, minutes=0)
            fare = 800.0 + (i * 30.0)
            seats = 4 + i
            item = {
                "source": self.source_name,
                "source_trip_id": f"RB-{date}-{999+i}",
                "operator_name": f"KPN Travels (via redBus) #{i}",
                "bus_type": "AC SLEEPER",
                "origin": origin,
                "destination": destination,
                "departure_dt": dep_dt.isoformat(),
                "arrival_dt": arr_dt.isoformat(),
                "duration_mins": 420,
                "fare": fare,
                "tatkal_fare": None,
                "tatkal_open": False,
                "seats_available": seats,
                "is_dummy": True,
                "booking_url": f"/aggregator/book/{self.source_name}/RB-{date}-{999+i}/?fare={fare}&origin={origin}&destination={destination}&date={date}",
                "amenities": ["ac", "blanket", "water"]
            }
            results.append(item)

        return results
