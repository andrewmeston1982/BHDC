"""
Google Maps Directions API Client

More accurate than TfL for:
- Areas outside London
- Multi-modal journeys
- Real-time traffic consideration
- Comprehensive National Rail coverage

API Pricing (as of 2024):
- $5 per 1000 requests for Directions API
- $200 free credit per month (~40,000 requests)
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
import time


@dataclass
class TransitStep:
    """A single step in a transit journey"""
    mode: str  # WALKING, TRANSIT, etc.
    instruction: str
    duration_mins: int
    distance_km: float
    # Transit-specific
    line_name: Optional[str] = None
    line_short_name: Optional[str] = None
    vehicle_type: Optional[str] = None  # RAIL, BUS, SUBWAY, etc.
    departure_stop: Optional[str] = None
    arrival_stop: Optional[str] = None
    num_stops: Optional[int] = None


@dataclass
class TransitJourney:
    """A complete transit journey"""
    total_duration_mins: int
    departure_time: str
    arrival_time: str
    steps: List[TransitStep]
    num_changes: int
    fare_estimate: Optional[float] = None
    walking_mins: int = 0

    def summary(self) -> str:
        """Human readable summary"""
        transit_steps = [s for s in self.steps if s.mode == "TRANSIT"]
        lines = [s.line_short_name or s.line_name or s.vehicle_type for s in transit_steps]
        return f"{self.total_duration_mins}min ({self.num_changes} changes): {' → '.join(lines)}"


class GoogleMapsClient:
    """
    Client for Google Maps Directions API with transit support.

    Much more accurate than TfL for:
    - Areas outside Greater London
    - Complex multi-modal journeys
    - National Rail connections
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/directions/json"

    def __init__(self, api_key: str):
        """
        Initialize with Google Maps API key.

        Get a key at: https://console.cloud.google.com/apis/credentials
        Enable: Directions API
        """
        self.api_key = api_key
        self.session = requests.Session()
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 10 requests per second max

    def _rate_limit(self):
        """Simple rate limiting"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make a rate-limited request to the API"""
        self._rate_limit()

        params['key'] = self.api_key

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            data = response.json()

            if data.get('status') == 'OK':
                return data
            elif data.get('status') == 'ZERO_RESULTS':
                return None
            elif data.get('status') == 'REQUEST_DENIED':
                error_msg = data.get('error_message', '')
                if 'not enabled' in error_msg.lower() or 'legacy' in error_msg.lower():
                    print("\n" + "=" * 60)
                    print("GOOGLE MAPS API NOT ENABLED")
                    print("=" * 60)
                    print("To enable the Directions API:")
                    print("1. Go to: https://console.cloud.google.com/apis/library")
                    print("2. Search for 'Directions API'")
                    print("3. Click 'Enable'")
                    print("4. Make sure billing is set up (free tier includes $200/month)")
                    print("=" * 60 + "\n")
                    print("Falling back to TfL API...\n")
                else:
                    print(f"Google Maps API Error: {data.get('status')} - {error_msg}")
                return None
            else:
                print(f"Google Maps API Error: {data.get('status')} - {data.get('error_message', '')}")
                return None

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def plan_journey(
        self,
        from_location: str,
        to_location: str,
        arrival_time: Optional[datetime] = None,
        departure_time: Optional[datetime] = None,
        transit_modes: Optional[List[str]] = None,
        alternatives: bool = True,
    ) -> Optional[List[TransitJourney]]:
        """
        Plan a transit journey between two locations.

        Args:
            from_location: Starting point (address, postcode, or "lat,lng")
            to_location: Destination (address, postcode, or "lat,lng")
            arrival_time: When to arrive by
            departure_time: When to depart (ignored if arrival_time set)
            transit_modes: List of modes - 'bus', 'rail', 'subway', 'tram'
                          Default: all modes
            alternatives: Return multiple route options

        Returns:
            List of TransitJourney options, sorted by duration
        """

        params = {
            'origin': from_location,
            'destination': to_location,
            'mode': 'transit',
            'alternatives': 'true' if alternatives else 'false',
            'region': 'uk',
        }

        # Handle timing
        if arrival_time:
            params['arrival_time'] = int(arrival_time.timestamp())
        elif departure_time:
            params['departure_time'] = int(departure_time.timestamp())
        else:
            # Default: arrive at 9am next weekday
            now = datetime.now()
            target = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            while target.weekday() >= 5:  # Skip weekends
                target += timedelta(days=1)
            params['arrival_time'] = int(target.timestamp())

        # Handle transit mode preferences
        if transit_modes:
            params['transit_mode'] = '|'.join(transit_modes)

        data = self._make_request(params)

        if not data or 'routes' not in data:
            return None

        journeys = []

        for route in data['routes']:
            # Google returns one leg for transit journeys
            leg = route['legs'][0]

            steps = []
            walking_mins = 0
            transit_count = 0

            for step in leg['steps']:
                mode = step['travel_mode']
                duration_mins = step['duration']['value'] // 60
                distance_km = step['distance']['value'] / 1000

                transit_step = TransitStep(
                    mode=mode,
                    instruction=step.get('html_instructions', ''),
                    duration_mins=duration_mins,
                    distance_km=distance_km,
                )

                if mode == 'WALKING':
                    walking_mins += duration_mins

                elif mode == 'TRANSIT':
                    transit_count += 1
                    details = step.get('transit_details', {})
                    line = details.get('line', {})

                    transit_step.line_name = line.get('name')
                    transit_step.line_short_name = line.get('short_name')
                    transit_step.vehicle_type = line.get('vehicle', {}).get('type')
                    transit_step.departure_stop = details.get('departure_stop', {}).get('name')
                    transit_step.arrival_stop = details.get('arrival_stop', {}).get('name')
                    transit_step.num_stops = details.get('num_stops')

                steps.append(transit_step)

            # Get fare if available
            fare = None
            if 'fare' in route:
                fare = route['fare'].get('value')

            journey = TransitJourney(
                total_duration_mins=leg['duration']['value'] // 60,
                departure_time=leg['departure_time']['text'],
                arrival_time=leg['arrival_time']['text'],
                steps=steps,
                num_changes=max(0, transit_count - 1),
                fare_estimate=fare,
                walking_mins=walking_mins,
            )

            journeys.append(journey)

        # Sort by duration
        journeys.sort(key=lambda j: j.total_duration_mins)

        return journeys

    def get_commute_time(
        self,
        from_location: str,
        to_location: str,
        arrival_hour: int = 9,
        arrival_minute: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        Get typical commute time arriving by a specific time.

        Returns dict with:
            - fastest_mins: Fastest journey time
            - num_changes: Number of changes
            - walking_mins: Total walking time
            - journey: Full journey details
        """

        # Set arrival time to next weekday
        now = datetime.now()
        target = now.replace(hour=arrival_hour, minute=arrival_minute, second=0)

        if target <= now:
            target += timedelta(days=1)

        while target.weekday() >= 5:
            target += timedelta(days=1)

        journeys = self.plan_journey(
            from_location,
            to_location,
            arrival_time=target,
        )

        if not journeys:
            return None

        best = journeys[0]

        return {
            'fastest_mins': best.total_duration_mins,
            'num_changes': best.num_changes,
            'walking_mins': best.walking_mins,
            'departure_time': best.departure_time,
            'arrival_time': best.arrival_time,
            'journey': best,
        }

    def get_fastest_time(
        self,
        from_location: str,
        to_location: str,
        **kwargs
    ) -> Optional[int]:
        """Get just the fastest journey time in minutes."""
        result = self.get_commute_time(from_location, to_location, **kwargs)
        return result['fastest_mins'] if result else None


def test_client(api_key: str):
    """Test the Google Maps client"""
    client = GoogleMapsClient(api_key)

    print("Testing Google Maps Directions API...")
    print("-" * 50)

    # The classic test: Gravesend vs Grays
    print("\nGravesend to W1T 3JF (Fitzrovia):")
    result = client.get_commute_time("Gravesend, UK", "W1T 3JF, London")
    if result:
        print(f"  Time: {result['fastest_mins']} mins")
        print(f"  Changes: {result['num_changes']}")
        print(f"  Walking: {result['walking_mins']} mins")
        print(f"  Journey: {result['journey'].summary()}")
    else:
        print("  Could not calculate")

    print("\nGrays to W1T 3JF (Fitzrovia):")
    result = client.get_commute_time("Grays, Essex, UK", "W1T 3JF, London")
    if result:
        print(f"  Time: {result['fastest_mins']} mins")
        print(f"  Changes: {result['num_changes']}")
        print(f"  Walking: {result['walking_mins']} mins")
        print(f"  Journey: {result['journey'].summary()}")
    else:
        print("  Could not calculate")

    print("-" * 50)
    print("API test complete!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_client(sys.argv[1])
    else:
        print("Usage: python google_maps_client.py YOUR_API_KEY")
