"""
Commute Time Property Search Tool

Finds the best places to live based on actual public transport commute times,
not just distance. Identifies hidden gems with surprisingly good transport links.

Your destinations:
- You: W1T 3JF (Fitzrovia, near Goodge Street)
- Wife: Hackney Council, Mare Street (E8 1EA)

Max commute: 1h15m ideal, 1h30m stretch for nice places
"""

import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Tuple
from pathlib import Path
import sys

from tfl_client import TfLJourneyPlanner, JourneyOption
from locations import (
    ALL_LOCATIONS, Location, distance_from_london,
    FITZROVIA, HACKNEY, haversine_distance_km
)


@dataclass
class CommuteResult:
    """Result for a single location"""
    location: Location
    distance_km: float

    # Your commute (to W1T 3JF / Fitzrovia)
    your_commute_mins: Optional[int] = None
    your_journey: Optional[JourneyOption] = None

    # Wife's commute (to Hackney)
    wife_commute_mins: Optional[int] = None
    wife_journey: Optional[JourneyOption] = None

    # Combined score
    combined_mins: Optional[int] = None  # Sum of both commutes
    avg_mins: Optional[float] = None  # Average of both

    # Hidden gem score: how good is the commute relative to distance?
    # Lower is better (fewer mins per km)
    mins_per_km: Optional[float] = None
    hidden_gem_score: int = 0  # 1-5, calculated based on mins_per_km

    # Property search URLs
    rightmove_url: Optional[str] = None
    zoopla_url: Optional[str] = None

    def passes_criteria(
        self,
        your_max_mins: int = 75,
        wife_max_mins: int = 90,
    ) -> bool:
        """Check if this location meets the commute criteria"""
        if self.your_commute_mins is None or self.wife_commute_mins is None:
            return False
        return (
            self.your_commute_mins <= your_max_mins and
            self.wife_commute_mins <= wife_max_mins
        )


class CommuteSearch:
    """Main search engine for finding commutable locations"""

    # Your workplace - W1T 3JF (Fitzrovia)
    YOUR_WORKPLACE = "W1T 3JF"
    YOUR_WORKPLACE_NAME = "Fitzrovia (W1T 3JF)"

    # Wife's workplace - Hackney Council, Mare Street
    WIFE_WORKPLACE = "E8 1EA"  # Hackney Town Hall
    WIFE_WORKPLACE_NAME = "Hackney Council (Mare Street)"

    def __init__(self, tfl_api_key: Optional[str] = None):
        """Initialize the search engine"""
        self.tfl = TfLJourneyPlanner(app_key=tfl_api_key)
        self.results: List[CommuteResult] = []
        self.cache_file = Path(__file__).parent / "commute_cache.json"
        self._load_cache()

    def _load_cache(self):
        """Load cached journey times to avoid re-querying"""
        self.cache: Dict[str, Dict] = {}
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                print(f"Loaded {len(self.cache)} cached journey times")
            except Exception as e:
                print(f"Could not load cache: {e}")

    def _save_cache(self):
        """Save journey times to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Could not save cache: {e}")

    def _get_cache_key(self, from_loc: str, to_loc: str) -> str:
        """Generate cache key for a journey"""
        return f"{from_loc}|{to_loc}"

    def _get_journey_time(
        self,
        from_station: str,
        to_location: str,
        arrival_hour: int = 9
    ) -> Tuple[Optional[int], Optional[JourneyOption]]:
        """
        Get journey time from a station to a destination.
        Uses cache if available.
        """
        cache_key = self._get_cache_key(from_station, to_location)

        # Check cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return cached.get('mins'), None  # Don't cache full journey object

        # Query TfL API
        result = self.tfl.get_typical_commute_time(
            from_station,
            to_location,
            arrival_hour=arrival_hour
        )

        if result:
            mins = result['fastest_mins']
            # Cache the result
            self.cache[cache_key] = {
                'mins': mins,
                'changes': result['num_changes'],
                'queried': datetime.now().isoformat()
            }
            self._save_cache()
            return mins, result.get('journey')

        return None, None

    def search_all_locations(
        self,
        locations: Optional[List[Location]] = None,
        your_arrival_hour: int = 9,
        wife_arrival_hour: int = 9,
        progress_callback=None
    ) -> List[CommuteResult]:
        """
        Search all locations and calculate commute times.

        Args:
            locations: List of locations to search (defaults to ALL_LOCATIONS)
            your_arrival_hour: What time you need to arrive at work
            wife_arrival_hour: What time wife needs to arrive
            progress_callback: Function to call with progress updates
        """
        if locations is None:
            locations = ALL_LOCATIONS

        self.results = []
        total = len(locations)

        for i, loc in enumerate(locations):
            if progress_callback:
                progress_callback(i + 1, total, loc.name)
            else:
                print(f"[{i+1}/{total}] Checking {loc.name}...", end=" ", flush=True)

            # Calculate distance from London
            dist_km = distance_from_london(loc.lat, loc.lon)

            # Get your commute time
            your_mins, your_journey = self._get_journey_time(
                loc.station,
                self.YOUR_WORKPLACE,
                arrival_hour=your_arrival_hour
            )

            # Get wife's commute time
            wife_mins, wife_journey = self._get_journey_time(
                loc.station,
                self.WIFE_WORKPLACE,
                arrival_hour=wife_arrival_hour
            )

            # Calculate combined metrics
            combined = None
            avg = None
            mins_per_km = None
            gem_score = 0

            if your_mins is not None and wife_mins is not None:
                combined = your_mins + wife_mins
                avg = combined / 2

                # Calculate mins per km (using your commute as primary)
                if dist_km > 0:
                    mins_per_km = your_mins / dist_km

                    # Calculate hidden gem score
                    # Lower mins_per_km = better transport links for the distance
                    if mins_per_km < 1.0:
                        gem_score = 5  # Exceptional
                    elif mins_per_km < 1.5:
                        gem_score = 4  # Very good
                    elif mins_per_km < 2.0:
                        gem_score = 3  # Good
                    elif mins_per_km < 2.5:
                        gem_score = 2  # Average
                    else:
                        gem_score = 1  # Poor value

            # Generate property search URLs
            rightmove_url = self._generate_rightmove_url(loc)
            zoopla_url = self._generate_zoopla_url(loc)

            result = CommuteResult(
                location=loc,
                distance_km=dist_km,
                your_commute_mins=your_mins,
                your_journey=your_journey,
                wife_commute_mins=wife_mins,
                wife_journey=wife_journey,
                combined_mins=combined,
                avg_mins=avg,
                mins_per_km=mins_per_km,
                hidden_gem_score=gem_score,
                rightmove_url=rightmove_url,
                zoopla_url=zoopla_url,
            )

            self.results.append(result)

            if not progress_callback:
                if your_mins and wife_mins:
                    print(f"You: {your_mins}min, Wife: {wife_mins}min")
                else:
                    print("Could not calculate journey")

        return self.results

    def _generate_rightmove_url(self, loc: Location) -> str:
        """Generate Rightmove search URL for a location"""
        # Rightmove uses OUTCODE format (first part of postcode)
        outcode = loc.postcode_area.split()[0]
        # URL encode the location name
        location_encoded = loc.name.replace(" ", "-").lower()
        return (
            f"https://www.rightmove.co.uk/property-for-sale/find.html"
            f"?locationIdentifier=OUTCODE%5E{outcode}"
            f"&propertyTypes=detached%2Csemi-detached%2Cterraced"
            f"&mustHave=&dontShow=&furnishTypes=&keywords="
        )

    def _generate_zoopla_url(self, loc: Location) -> str:
        """Generate Zoopla search URL for a location"""
        outcode = loc.postcode_area.split()[0].lower()
        return (
            f"https://www.zoopla.co.uk/for-sale/property/{outcode}/"
            f"?q={loc.name.replace(' ', '%20')}"
        )

    def filter_results(
        self,
        your_max_mins: int = 75,
        wife_max_mins: int = 90,
        max_price: Optional[int] = None,
        min_gem_score: int = 0,
    ) -> List[CommuteResult]:
        """
        Filter results by criteria.

        Args:
            your_max_mins: Your maximum commute (default 1h15m)
            wife_max_mins: Wife's maximum commute (default 1h30m)
            max_price: Maximum property price (optional)
            min_gem_score: Minimum hidden gem score (1-5)
        """
        filtered = []

        for result in self.results:
            # Skip if we couldn't get journey times
            if result.your_commute_mins is None or result.wife_commute_mins is None:
                continue

            # Check commute times
            if result.your_commute_mins > your_max_mins:
                continue
            if result.wife_commute_mins > wife_max_mins:
                continue

            # Check price
            if max_price and result.location.avg_price_2bed:
                if result.location.avg_price_2bed > max_price:
                    continue

            # Check gem score
            if result.hidden_gem_score < min_gem_score:
                continue

            filtered.append(result)

        return filtered

    def sort_results(
        self,
        results: List[CommuteResult],
        by: str = "your_commute"
    ) -> List[CommuteResult]:
        """
        Sort results by various criteria.

        Args:
            by: Sort key - "your_commute", "wife_commute", "combined",
                "distance", "gem_score", "price"
        """
        if by == "your_commute":
            return sorted(results, key=lambda r: r.your_commute_mins or 999)
        elif by == "wife_commute":
            return sorted(results, key=lambda r: r.wife_commute_mins or 999)
        elif by == "combined":
            return sorted(results, key=lambda r: r.combined_mins or 999)
        elif by == "distance":
            return sorted(results, key=lambda r: r.distance_km)
        elif by == "gem_score":
            return sorted(results, key=lambda r: -r.hidden_gem_score)
        elif by == "price":
            return sorted(
                results,
                key=lambda r: r.location.avg_price_2bed or 999999
            )
        elif by == "mins_per_km":
            return sorted(results, key=lambda r: r.mins_per_km or 999)
        else:
            return results

    def print_results(
        self,
        results: List[CommuteResult],
        detailed: bool = False
    ):
        """Print results in a nice format"""
        if not results:
            print("No locations found matching your criteria.")
            return

        print("\n" + "=" * 80)
        print("COMMUTE SEARCH RESULTS")
        print("=" * 80)
        print(f"Your workplace: {self.YOUR_WORKPLACE_NAME}")
        print(f"Wife's workplace: {self.WIFE_WORKPLACE_NAME}")
        print("=" * 80 + "\n")

        for i, result in enumerate(results, 1):
            loc = result.location

            # Header
            gem_stars = "★" * result.hidden_gem_score + "☆" * (5 - result.hidden_gem_score)
            print(f"{i}. {loc.name} ({loc.rail_line})")
            print(f"   Hidden Gem Score: {gem_stars}")
            print(f"   Distance from London: {result.distance_km:.1f} km")

            # Commute times
            print(f"   Your commute: {result.your_commute_mins} mins")
            print(f"   Wife's commute: {result.wife_commute_mins} mins")
            print(f"   Combined: {result.combined_mins} mins")

            # Value metric
            if result.mins_per_km:
                print(f"   Minutes per km: {result.mins_per_km:.2f} (lower = better transport links)")

            # Price
            if loc.avg_price_2bed:
                print(f"   Avg 2-bed price: £{loc.avg_price_2bed:,}")

            # Notes
            print(f"   Notes: {loc.notes}")

            # URLs
            print(f"   Rightmove: {result.rightmove_url}")
            print(f"   Zoopla: {result.zoopla_url}")

            print()

    def export_results(
        self,
        results: List[CommuteResult],
        filename: str = "commute_results.json"
    ):
        """Export results to JSON"""
        output = []
        for r in results:
            output.append({
                'name': r.location.name,
                'postcode_area': r.location.postcode_area,
                'station': r.location.station,
                'rail_line': r.location.rail_line,
                'distance_km': round(r.distance_km, 1),
                'your_commute_mins': r.your_commute_mins,
                'wife_commute_mins': r.wife_commute_mins,
                'combined_mins': r.combined_mins,
                'hidden_gem_score': r.hidden_gem_score,
                'mins_per_km': round(r.mins_per_km, 2) if r.mins_per_km else None,
                'avg_2bed_price': r.location.avg_price_2bed,
                'notes': r.location.notes,
                'rightmove_url': r.rightmove_url,
                'zoopla_url': r.zoopla_url,
            })

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Exported {len(output)} results to {filename}")

    def export_csv(
        self,
        results: List[CommuteResult],
        filename: str = "commute_results.csv"
    ):
        """Export results to CSV for spreadsheet analysis"""
        import csv

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Name', 'Station', 'Rail Line', 'Distance (km)',
                'Your Commute (mins)', 'Wife Commute (mins)', 'Combined (mins)',
                'Mins per km', 'Hidden Gem Score', 'Avg 2-bed Price',
                'Notes', 'Rightmove URL', 'Zoopla URL'
            ])

            for r in results:
                writer.writerow([
                    r.location.name,
                    r.location.station,
                    r.location.rail_line,
                    round(r.distance_km, 1),
                    r.your_commute_mins,
                    r.wife_commute_mins,
                    r.combined_mins,
                    round(r.mins_per_km, 2) if r.mins_per_km else '',
                    r.hidden_gem_score,
                    r.location.avg_price_2bed or '',
                    r.location.notes,
                    r.rightmove_url,
                    r.zoopla_url,
                ])

        print(f"Exported {len(results)} results to {filename}")


def main():
    """Main entry point - run a full search"""
    print("=" * 60)
    print("COMMUTE TIME PROPERTY SEARCH")
    print("Finding the best places to live based on ACTUAL commute times")
    print("=" * 60)
    print()

    # Initialize search
    search = CommuteSearch()

    print(f"Searching {len(ALL_LOCATIONS)} locations...")
    print(f"Your workplace: {search.YOUR_WORKPLACE_NAME}")
    print(f"Wife's workplace: {search.WIFE_WORKPLACE_NAME}")
    print()

    # Run search
    all_results = search.search_all_locations()

    print("\n" + "-" * 60)

    # Filter by your criteria
    # You: max 1h15m (75 mins), stretch to 1h30m (90 mins) for nice places
    # Wife: more flexible, let's say 1h30m (90 mins) default

    print("\n=== LOCATIONS WITHIN YOUR CRITERIA ===")
    print("(You: max 75 mins, Wife: max 90 mins)")

    matching = search.filter_results(
        your_max_mins=75,
        wife_max_mins=90,
    )

    # Sort by your commute time
    matching = search.sort_results(matching, by="your_commute")

    search.print_results(matching)

    # Also show hidden gems
    print("\n=== HIDDEN GEMS (best commute for distance) ===")
    print("(sorted by minutes per km - lower = better transport links)")

    gems = search.filter_results(
        your_max_mins=90,  # Slightly relaxed
        wife_max_mins=105,
        min_gem_score=4,
    )
    gems = search.sort_results(gems, by="mins_per_km")
    search.print_results(gems[:10])  # Top 10

    # Export results
    search.export_csv(matching, "matching_locations.csv")
    search.export_results(matching, "matching_locations.json")

    print("\nDone! Check matching_locations.csv for a spreadsheet-friendly version.")


if __name__ == "__main__":
    main()
