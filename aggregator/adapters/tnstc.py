from .base import BaseAdapter
from typing import List, Dict, Any
import datetime

class TNSTCAdapter(BaseAdapter):
    source_name = "tnstc"

    def fetch(self, origin: str, destination: str, date: str) -> List[Dict[str, Any]]:
        if not self.is_dummy:
            # Here we would call the TNSTC API
            return []

        # Dummy data implementation
        try:
            parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return []
            
        results = []
        for i in range(1, 11):
            dep_dt = datetime.datetime.combine(parsed_date, datetime.time(6 + (i % 12), 0))
            arr_dt = dep_dt + datetime.timedelta(hours=6, minutes=30)
            fare = 200.0 + (i * 15.0)
            seats = 15 + i
            item = {
                "source": self.source_name,
                "source_trip_id": f"TNSTC-{date}-{100+i}",
                "operator_name": f"TNSTC Govt #{i}",
                "bus_type": "ORDINARY",
                "origin": origin,
                "destination": destination,
                "departure_dt": dep_dt.isoformat(),
                "arrival_dt": arr_dt.isoformat(),
                "duration_mins": 390,
                "fare": fare,
                "tatkal_fare": None,
                "tatkal_open": False,
                "seats_available": seats,
                "is_dummy": True,
                "booking_url": f"/aggregator/book/{self.source_name}/TNSTC-{date}-{100+i}/?fare={fare}&origin={origin}&destination={destination}&date={date}",
                "amenities": []
            }
            results.append(item)

        return results
