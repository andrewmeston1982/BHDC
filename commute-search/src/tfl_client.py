"""
TfL Journey Planner API Client

Free API that covers:
- All TfL services (Tube, Bus, DLR, Overground, Elizabeth Line, Tram)
- National Rail services
- Walking and cycling routes
- Journey planning from anywhere in UK to London
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import time


@dataclass
class JourneyLeg:
    """A single leg of a journey"""
    mode: str
    line_name: str
    departure_point: str
    arrival_point: str
    duration_mins: int
    departure_time: str
    arrival_time: str


@dataclass
class JourneyOption:
    """A complete journey option"""
    total_duration_mins: int
    departure_time: str
    arrival_time: str
    legs: List[JourneyLeg]
    num_changes: int
    fare_estimate: Optional[float] = None

    def summary(self) -> str:
        """Human readable summary of the journey"""
        modes = [leg.mode for leg in self.legs]
        mode_summary = " → ".join(modes)
        return f"{self.total_duration_mins}min ({self.num_changes} changes): {mode_summary}"


class TfLJourneyPlanner:
    """
    Client for TfL Journey Planner API

    API is free to use, no key required for basic usage.
    Rate limited to ~500 requests per minute.
    """

    BASE_URL = "https://api.tfl.gov.uk/Journey/JourneyResults"

    def __init__(self, app_key: Optional[str] = None):
        """
        Initialize the client.

        Args:
            app_key: Optional TfL API key for higher rate limits.
                    Register free at https://api-portal.tfl.gov.uk/
        """
        self.app_key = app_key
        self.session = requests.Session()
        self._last_request_time = 0
        self._min_request_interval = 0.15  # ~6 requests per second max

    def _rate_limit(self):
        """Simple rate limiting to avoid hitting API limits"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make a rate-limited request to the API"""
        self._rate_limit()

        if self.app_key:
            params['app_key'] = self.app_key

        try:
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 300:
                # Disambiguation required - API returns multiple location matches
                return response.json()
            elif response.status_code == 429:
                # Rate limited - wait and retry
                time.sleep(2)
                return self._make_request(url, params)
            else:
                print(f"API Error {response.status_code}: {response.text[:200]}")
                return None

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def plan_journey(
        self,
        from_location: str,
        to_location: str,
        departure_time: Optional[datetime] = None,
        arrival_time: Optional[datetime] = None,
        modes: Optional[List[str]] = None,
        max_walking_mins: int = 15,
        include_cycling: bool = True
    ) -> Optional[List[JourneyOption]]:
        """
        Plan a journey between two locations.

        Args:
            from_location: Starting point (postcode, station name, or coordinates)
            to_location: Destination (postcode, station name, or coordinates)
            departure_time: When to depart (defaults to now)
            arrival_time: When to arrive by (alternative to departure_time)
            modes: List of modes to use. Options include:
                   'public-bus', 'tube', 'national-rail', 'dlr',
                   'overground', 'elizabeth-line', 'tram', 'walking', 'cycle'
            max_walking_mins: Maximum walking time in minutes
            include_cycling: Whether to include cycling options

        Returns:
            List of JourneyOption objects, or None if journey not possible
        """

        # Build URL
        url = f"{self.BASE_URL}/{from_location}/to/{to_location}"

        # Build parameters
        params = {
            'nationalSearch': 'true',  # Include National Rail
            'timeIs': 'departing',
            'maxWalkingMinutes': max_walking_mins,
            'walkingSpeed': 'average',
            'journeyPreference': 'leasttime',
            'accessibilityPreference': 'noRequirements',
        }

        # Handle time
        if arrival_time:
            params['timeIs'] = 'arriving'
            params['date'] = arrival_time.strftime('%Y%m%d')
            params['time'] = arrival_time.strftime('%H%M')
        elif departure_time:
            params['date'] = departure_time.strftime('%Y%m%d')
            params['time'] = departure_time.strftime('%H%M')
        else:
            # Default to tomorrow 8:30am for realistic commute time
            tomorrow = datetime.now() + timedelta(days=1)
            morning_commute = tomorrow.replace(hour=8, minute=30, second=0, microsecond=0)
            # Skip weekends
            while morning_commute.weekday() >= 5:
                morning_commute += timedelta(days=1)
            params['date'] = morning_commute.strftime('%Y%m%d')
            params['time'] = morning_commute.strftime('%H%M')

        # Handle modes
        if modes:
            params['mode'] = ','.join(modes)
        else:
            # Default: all public transport
            default_modes = [
                'tube', 'national-rail', 'dlr', 'overground',
                'elizabeth-line', 'tram', 'bus'
            ]
            if include_cycling:
                default_modes.append('cycle-hire')
            params['mode'] = ','.join(default_modes)

        # Make request
        data = self._make_request(url, params)

        if not data:
            return None

        # Handle disambiguation (multiple location matches)
        if 'disambiguationOptions' in data:
            print(f"Location ambiguous. Options: {data.get('disambiguationOptions', [])[:3]}")
            return None

        # Parse journeys
        journeys = data.get('journeys', [])
        if not journeys:
            return None

        results = []
        for journey in journeys:
            legs = []
            for leg in journey.get('legs', []):
                mode = leg.get('mode', {}).get('name', 'unknown')

                # Get line name
                route_options = leg.get('routeOptions', [{}])
                line_name = route_options[0].get('name', '') if route_options else ''

                legs.append(JourneyLeg(
                    mode=mode,
                    line_name=line_name,
                    departure_point=leg.get('departurePoint', {}).get('commonName', ''),
                    arrival_point=leg.get('arrivalPoint', {}).get('commonName', ''),
                    duration_mins=leg.get('duration', 0),
                    departure_time=leg.get('departureTime', ''),
                    arrival_time=leg.get('arrivalTime', ''),
                ))

            # Calculate changes (exclude walking legs)
            non_walk_legs = [l for l in legs if l.mode.lower() != 'walking']
            num_changes = max(0, len(non_walk_legs) - 1)

            # Get fare if available
            fare = None
            if 'fare' in journey:
                fare = journey['fare'].get('totalCost', 0) / 100  # Convert pence to pounds

            results.append(JourneyOption(
                total_duration_mins=journey.get('duration', 0),
                departure_time=journey.get('startDateTime', ''),
                arrival_time=journey.get('arrivalDateTime', ''),
                legs=legs,
                num_changes=num_changes,
                fare_estimate=fare,
            ))

        # Sort by duration
        results.sort(key=lambda x: x.total_duration_mins)

        return results

    def get_fastest_journey_time(
        self,
        from_location: str,
        to_location: str,
        **kwargs
    ) -> Optional[int]:
        """
        Get just the fastest journey time in minutes.

        Returns None if journey not possible.
        """
        journeys = self.plan_journey(from_location, to_location, **kwargs)

        if journeys:
            return journeys[0].total_duration_mins
        return None

    def get_typical_commute_time(
        self,
        from_location: str,
        to_location: str,
        arrival_hour: int = 9,
        arrival_minute: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        Get typical commute time arriving by a specific time.

        This simulates a real commute - arriving at work by 9am.

        Returns dict with:
            - fastest_mins: Fastest journey time
            - recommended_departure: When to leave
            - journey: The journey details
        """
        # Set arrival time to next weekday at specified time
        now = datetime.now()
        target = now.replace(hour=arrival_hour, minute=arrival_minute, second=0)

        # Move to tomorrow if time has passed
        if target <= now:
            target += timedelta(days=1)

        # Skip to Monday if weekend
        while target.weekday() >= 5:
            target += timedelta(days=1)

        journeys = self.plan_journey(
            from_location,
            to_location,
            arrival_time=target
        )

        if not journeys:
            return None

        best = journeys[0]

        return {
            'fastest_mins': best.total_duration_mins,
            'num_changes': best.num_changes,
            'departure_time': best.departure_time,
            'arrival_time': best.arrival_time,
            'journey': best,
        }


# Quick test function
def test_client():
    """Test the TfL client with a sample journey"""
    client = TfLJourneyPlanner()

    print("Testing TfL Journey Planner API...")
    print("-" * 50)

    # Test: Gravesend to St Pancras (should be ~23 mins on Javelin)
    print("\nGravesend to St Pancras:")
    result = client.get_typical_commute_time("Gravesend", "St Pancras")
    if result:
        print(f"  Time: {result['fastest_mins']} mins")
        print(f"  Changes: {result['num_changes']}")
        print(f"  Journey: {result['journey'].summary()}")

    # Test: Grays to St Pancras (should be much longer)
    print("\nGrays to St Pancras:")
    result = client.get_typical_commute_time("Grays", "St Pancras")
    if result:
        print(f"  Time: {result['fastest_mins']} mins")
        print(f"  Changes: {result['num_changes']}")
        print(f"  Journey: {result['journey'].summary()}")

    print("-" * 50)
    print("API test complete!")


if __name__ == "__main__":
    test_client()
