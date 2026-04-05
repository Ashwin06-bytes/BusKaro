from .base import BaseAdapter
from typing import List, Dict, Any
import datetime

class AbhibusAdapter(BaseAdapter):
    source_name = "abhibus"

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
            dep_dt = datetime.datetime.combine(parsed_date, datetime.time(8 + (i % 12), 15))
            arr_dt = dep_dt + datetime.timedelta(hours=6, minutes=45)
            fare = 600.0 + (i * 25.0)
            seats = 10 + i
            item = {
                "source": self.source_name,
                "source_trip_id": f"ABHI-{date}-{555+i}",
                "operator_name": f"YBM Travels (via AbhiBus) #{i}",
                "bus_type": "AC SEATER",
                "origin": origin,
                "destination": destination,
                "departure_dt": dep_dt.isoformat(),
                "arrival_dt": arr_dt.isoformat(),
                "duration_mins": 405,
                "fare": fare,
                "tatkal_fare": None,
                "tatkal_open": False,
                "seats_available": seats,
                "is_dummy": True,
                "booking_url": f"/aggregator/book/{self.source_name}/ABHI-{date}-{555+i}/?fare={fare}&origin={origin}&destination={destination}&date={date}",
                "amenities": ["ac", "wifi"]
            }
            results.append(item)

        return results
