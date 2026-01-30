"""
TravelTime API Client

TravelTime is specifically designed for travel time searches:
- Time Filter: Check up to 2000 locations in ONE request
- Time Map: Draw isochrones showing everywhere reachable within X mins

This is MUCH faster than checking stations one-by-one!

Get API keys at: https://traveltime.com/
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
import time


@dataclass
class LocationResult:
    """Result for a single location from time filter"""
    id: str
    travel_time_seconds: int
    distance_meters: Optional[int] = None

    @property
    def travel_time_mins(self) -> int:
        return self.travel_time_seconds // 60


class TravelTimeClient:
    """
    Client for TravelTime API.

    Key features:
    - Time Filter: Check travel times to many locations at once
    - Time Map: Get isochrone shapes

    Much more efficient than Google Maps for bulk queries!
    """

    BASE_URL = "https://api.traveltimeapp.com/v4"

    def __init__(self, app_id: str, api_key: str):
        """
        Initialize with TravelTime credentials.

        Get these at: https://traveltime.com/
        """
        self.app_id = app_id
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Application-Id': app_id,
            'X-Api-Key': api_key
        })
        self._last_request_time = 0
        self._min_request_interval = 0.2  # Rate limit

    def _rate_limit(self):
        """Simple rate limiting"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, endpoint: str, payload: Dict) -> Optional[Dict]:
        """Make a rate-limited POST request"""
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.post(url, json=payload, timeout=60)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print("\n" + "=" * 60)
                print("TRAVELTIME API AUTHENTICATION ERROR")
                print("=" * 60)
                print("Check your Application ID and API Key")
                print("Get credentials at: https://traveltime.com/")
                print("=" * 60 + "\n")
                return None
            elif response.status_code == 429:
                print("TravelTime API rate limit hit - waiting...")
                time.sleep(5)
                return self._make_request(endpoint, payload)
            else:
                print(f"TravelTime API Error {response.status_code}: {response.text[:200]}")
                return None

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def _get_arrival_time(self, hour: int = 9, minute: int = 0) -> str:
        """Get next weekday arrival time in ISO format"""
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if target <= now:
            target += timedelta(days=1)

        # Skip weekends
        while target.weekday() >= 5:
            target += timedelta(days=1)

        return target.strftime("%Y-%m-%dT%H:%M:%SZ")

    def time_filter_many(
        self,
        origin_coords: Tuple[float, float],  # (lat, lon)
        locations: List[Tuple[str, float, float]],  # [(id, lat, lon), ...]
        max_travel_time_mins: int = 90,
        arrival_hour: int = 9,
        arrival_minute: int = 0,
        transport_type: str = "public_transport"
    ) -> Dict[str, Optional[int]]:
        """
        Check travel times from origin to MANY locations in one request.

        Args:
            origin_coords: Starting point (lat, lon)
            locations: List of (id, lat, lon) tuples to check
            max_travel_time_mins: Maximum travel time to include
            arrival_hour/minute: When to arrive
            transport_type: 'public_transport', 'driving', 'cycling', 'walking'

        Returns:
            Dict mapping location_id -> travel_time_mins (None if unreachable)

        Note: API supports up to 2000 locations per request!
        """

        if not locations:
            return {}

        # Build location objects
        location_objs = [
            {"id": loc_id, "coords": {"lat": lat, "lng": lon}}
            for loc_id, lat, lon in locations
        ]

        # Add origin
        location_objs.append({
            "id": "origin",
            "coords": {"lat": origin_coords[0], "lng": origin_coords[1]}
        })

        payload = {
            "locations": location_objs,
            "arrival_searches": [{
                "id": "commute_search",
                "arrival_location_id": "origin",
                "departure_location_ids": [loc[0] for loc in locations],
                "arrival_time": self._get_arrival_time(arrival_hour, arrival_minute),
                "travel_time": max_travel_time_mins * 60,  # API wants seconds
                "transportation": {"type": transport_type},
                "properties": ["travel_time"]
            }]
        }

        data = self._make_request("time-filter", payload)

        if not data or "results" not in data:
            return {}

        # Parse results
        results = {}
        for search_result in data.get("results", []):
            for loc in search_result.get("locations", []):
                loc_id = loc.get("id")
                props = loc.get("properties", [{}])
                if props:
                    travel_time = props[0].get("travel_time")
                    if travel_time is not None:
                        results[loc_id] = travel_time // 60  # Convert to mins

        # Mark unreachable as None
        for loc_id, _, _ in locations:
            if loc_id not in results:
                results[loc_id] = None

        return results

    def time_filter_batch(
        self,
        origin_coords: Tuple[float, float],
        locations: List[Tuple[str, float, float]],
        max_travel_time_mins: int = 90,
        arrival_hour: int = 9,
        batch_size: int = 2000,
        **kwargs
    ) -> Dict[str, Optional[int]]:
        """
        Check travel times for a large number of locations, batching as needed.

        TravelTime supports up to 2000 locations per request.
        """
        results = {}

        for i in range(0, len(locations), batch_size):
            batch = locations[i:i + batch_size]
            batch_results = self.time_filter_many(
                origin_coords, batch, max_travel_time_mins, arrival_hour, **kwargs
            )
            results.update(batch_results)

        return results

    def get_reachable_stations(
        self,
        work_coords: Tuple[float, float],
        stations: List[Tuple[str, str, float, float]],  # (name, postcode, lat, lon)
        max_travel_time_mins: int = 90,
        arrival_hour: int = 9
    ) -> List[Tuple[str, str, float, float, int]]:
        """
        Find all stations reachable within the given time.

        Returns list of (name, postcode, lat, lon, travel_time_mins) tuples.
        """

        # Convert to format for time_filter
        locations = [
            (f"{name}|{postcode}", lat, lon)
            for name, postcode, lat, lon in stations
        ]

        # Get all travel times in bulk
        results = self.time_filter_batch(
            work_coords, locations, max_travel_time_mins, arrival_hour
        )

        # Build output
        reachable = []
        for name, postcode, lat, lon in stations:
            loc_id = f"{name}|{postcode}"
            travel_time = results.get(loc_id)
            if travel_time is not None:
                reachable.append((name, postcode, lat, lon, travel_time))

        # Sort by travel time
        reachable.sort(key=lambda x: x[4])

        return reachable

    def check_two_destinations(
        self,
        station_coords: Tuple[float, float],
        dest1_coords: Tuple[float, float],
        dest2_coords: Tuple[float, float],
        max_time1: int = 90,
        max_time2: int = 90,
        arrival_hour: int = 9
    ) -> Optional[Tuple[int, int]]:
        """
        Check travel time from a station to TWO destinations.

        Returns (time_to_dest1, time_to_dest2) or None if either is unreachable.
        """

        # We need to do departure searches (from station to destinations)
        payload = {
            "locations": [
                {"id": "station", "coords": {"lat": station_coords[0], "lng": station_coords[1]}},
                {"id": "dest1", "coords": {"lat": dest1_coords[0], "lng": dest1_coords[1]}},
                {"id": "dest2", "coords": {"lat": dest2_coords[0], "lng": dest2_coords[1]}}
            ],
            "departure_searches": [{
                "id": "from_station",
                "departure_location_id": "station",
                "arrival_location_ids": ["dest1", "dest2"],
                "departure_time": self._get_arrival_time(arrival_hour - 2, 0),  # Leave 2 hours before
                "travel_time": max(max_time1, max_time2) * 60,
                "transportation": {"type": "public_transport"},
                "properties": ["travel_time"]
            }]
        }

        data = self._make_request("time-filter", payload)

        if not data or "results" not in data:
            return None

        # Parse
        time1 = None
        time2 = None

        for search_result in data.get("results", []):
            for loc in search_result.get("locations", []):
                loc_id = loc.get("id")
                props = loc.get("properties", [{}])
                if props:
                    travel_time = props[0].get("travel_time")
                    if travel_time is not None:
                        mins = travel_time // 60
                        if loc_id == "dest1":
                            time1 = mins
                        elif loc_id == "dest2":
                            time2 = mins

        if time1 is None or time2 is None:
            return None

        if time1 > max_time1 or time2 > max_time2:
            return None

        return (time1, time2)


    def get_isochrone(
        self,
        origin_coords: Tuple[float, float],
        travel_time_mins: int = 60,
        arrival_hour: int = 9,
        transport_type: str = "public_transport"
    ) -> Optional[List[List[Tuple[float, float]]]]:
        """
        Get isochrone (time map) - the shape of everywhere reachable within the time limit.

        Returns list of polygon shells, each as list of (lat, lon) tuples.
        The first polygon is the outer boundary, others are holes.
        """

        payload = {
            "arrival_searches": [{
                "id": "isochrone",
                "coords": {"lat": origin_coords[0], "lng": origin_coords[1]},
                "arrival_time": self._get_arrival_time(arrival_hour, 0),
                "travel_time": travel_time_mins * 60,
                "transportation": {"type": transport_type}
            }]
        }

        data = self._make_request("time-map", payload)

        if not data or "results" not in data:
            return None

        polygons = []
        for result in data.get("results", []):
            for shape in result.get("shapes", []):
                shell = shape.get("shell", [])
                if shell:
                    # Convert to (lat, lon) tuples
                    polygon = [(p["lat"], p["lng"]) for p in shell]
                    polygons.append(polygon)

        return polygons if polygons else None

    def get_intersection_stations(
        self,
        work1_coords: Tuple[float, float],
        work1_max_mins: int,
        work2_coords: Tuple[float, float],
        work2_max_mins: int,
        stations: List[Tuple[str, str, float, float]],  # (name, postcode, lat, lon)
        arrival_hour: int = 9
    ) -> List[Tuple[str, str, float, float, int, int]]:
        """
        Find stations reachable from BOTH workplaces using the intersection method.

        1. Get all stations reachable from work1
        2. Of those, check which are also reachable from work2
        3. Return stations with times to both

        Returns: [(name, postcode, lat, lon, time_to_work1, time_to_work2), ...]
        """

        # Step 1: Bulk check all stations -> work1
        station_list = [(f"{name}|{postcode}", lat, lon) for name, postcode, lat, lon in stations]

        times_to_work1 = self.time_filter_batch(
            work1_coords,
            station_list,
            max_travel_time_mins=work1_max_mins,
            arrival_hour=arrival_hour
        )

        # Filter to reachable from work1
        reachable = {k: v for k, v in times_to_work1.items() if v is not None}

        if not reachable:
            return []

        # Step 2: Check those stations -> work2
        filtered = [(sid, lat, lon) for sid, lat, lon in station_list if sid in reachable]

        times_to_work2 = self.time_filter_batch(
            work2_coords,
            filtered,
            max_travel_time_mins=work2_max_mins,
            arrival_hour=arrival_hour
        )

        # Build results
        results = []
        station_dict = {f"{name}|{postcode}": (name, postcode, lat, lon) for name, postcode, lat, lon in stations}

        for station_id, time1 in reachable.items():
            time2 = times_to_work2.get(station_id)
            if time2 is not None:
                name, postcode, lat, lon = station_dict[station_id]
                results.append((name, postcode, lat, lon, time1, time2))

        # Sort by combined time
        results.sort(key=lambda x: x[4] + x[5])

        return results


def point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
    """Check if a point is inside a polygon using ray casting algorithm."""
    x, y = point
    n = len(polygon)
    inside = False

    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i

    return inside


def geocode_postcode(postcode: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a UK postcode to lat/lon using postcodes.io (free, no API key needed).
    """
    postcode = postcode.replace(" ", "").upper()

    try:
        response = requests.get(
            f"https://api.postcodes.io/postcodes/{postcode}",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 200:
                result = data.get("result", {})
                return (result.get("latitude"), result.get("longitude"))
    except:
        pass

    return None


def test_client(app_id: str, api_key: str):
    """Test the TravelTime client"""
    client = TravelTimeClient(app_id, api_key)

    print("Testing TravelTime API...")
    print("-" * 50)

    # Test with some known stations
    from uk_stations import UK_STATIONS

    # Get work coordinates
    work_coords = geocode_postcode("W1T3JF")
    if not work_coords:
        print("Could not geocode W1T 3JF")
        return

    print(f"Work location: {work_coords}")

    # Test first 20 stations
    test_stations = UK_STATIONS[:20]

    print(f"\nChecking {len(test_stations)} stations...")
    reachable = client.get_reachable_stations(
        work_coords, test_stations, max_travel_time_mins=90
    )

    print(f"\nReachable within 90 mins: {len(reachable)}")
    for name, postcode, lat, lon, travel_time in reachable[:10]:
        print(f"  {name} ({postcode}): {travel_time} mins")

    print("-" * 50)
    print("API test complete!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        test_client(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python traveltime_client.py APP_ID API_KEY")
