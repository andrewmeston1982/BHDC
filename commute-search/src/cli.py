#!/usr/bin/env python3
"""
Commute Time Property Search - Command Line Interface

Find the best places to live based on actual public transport commute times,
not just distance. Perfect for finding hidden gems with great transport links.

Usage:
    python cli.py search                    # Run full search with defaults
    python cli.py search --your-max 60      # Custom max commute for you
    python cli.py search --gems-only        # Only show hidden gems
    python cli.py check "Gravesend"         # Check a specific location
    python cli.py compare "Gravesend" "Grays"  # Compare two locations
"""

import argparse
import sys
from typing import List, Optional

from commute_search import CommuteSearch, CommuteResult, GOOGLE_MAPS_API_KEY
from locations import ALL_LOCATIONS, Location, distance_from_london
from tfl_client import TfLJourneyPlanner
from google_maps_client import GoogleMapsClient


def progress_bar(current: int, total: int, location: str, width: int = 40):
    """Display a progress bar"""
    percent = current / total
    filled = int(width * percent)
    bar = "█" * filled + "░" * (width - filled)
    print(f"\r[{bar}] {current}/{total} - {location:<30}", end="", flush=True)


def cmd_search(args):
    """Run the main search"""
    print("=" * 70)
    print("COMMUTE TIME PROPERTY SEARCH")
    print("Finding places based on ACTUAL transport times, not just distance!")
    print("=" * 70)
    print()

    # Determine which API to use
    use_google = not getattr(args, 'tfl_only', False)
    search = CommuteSearch(use_google=use_google)

    print(f"Your workplace: {search.YOUR_WORKPLACE_NAME}")
    print(f"Wife's workplace: {search.WIFE_WORKPLACE_NAME}")
    print(f"Your max commute: {args.your_max} mins")
    print(f"Wife's max commute: {args.wife_max} mins")
    print()

    api_name = "Google Maps" if search.use_google else "TfL"
    print(f"Searching {len(ALL_LOCATIONS)} locations using {api_name} API...")
    print("Using cached data where available, querying API for new locations.\n")

    # Run search with progress
    def progress(current, total, name):
        progress_bar(current, total, name)

    all_results = search.search_all_locations(progress_callback=progress)
    print("\n")  # New line after progress bar

    # Filter results
    if args.gems_only:
        print(f"\n=== HIDDEN GEMS ONLY (score >= 4) ===\n")
        matching = search.filter_results(
            your_max_mins=args.your_max,
            wife_max_mins=args.wife_max,
            min_gem_score=4,
        )
    else:
        print(f"\n=== ALL MATCHING LOCATIONS ===\n")
        matching = search.filter_results(
            your_max_mins=args.your_max,
            wife_max_mins=args.wife_max,
        )

    # Sort
    sort_by = args.sort or "your_commute"
    matching = search.sort_results(matching, by=sort_by)

    if not matching:
        print("No locations found matching your criteria.")
        print("Try increasing --your-max or --wife-max")
        return

    # Print results
    search.print_results(matching)

    # Export
    if args.export:
        search.export_csv(matching, "commute_results.csv")
        search.export_results(matching, "commute_results.json")
        print(f"\nResults exported to commute_results.csv and commute_results.json")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total locations searched: {len(ALL_LOCATIONS)}")
    print(f"Locations matching your criteria: {len(matching)}")

    if matching:
        fastest_for_you = min(matching, key=lambda r: r.your_commute_mins or 999)
        fastest_for_wife = min(matching, key=lambda r: r.wife_commute_mins or 999)
        best_combined = min(matching, key=lambda r: r.combined_mins or 999)

        print(f"\nFastest for you: {fastest_for_you.location.name} ({fastest_for_you.your_commute_mins} mins)")
        print(f"Fastest for wife: {fastest_for_wife.location.name} ({fastest_for_wife.wife_commute_mins} mins)")
        print(f"Best combined: {best_combined.location.name} ({best_combined.combined_mins} mins total)")

        # Best hidden gem
        gems = [r for r in matching if r.hidden_gem_score >= 4]
        if gems:
            best_gem = min(gems, key=lambda r: r.mins_per_km or 999)
            print(f"Best hidden gem: {best_gem.location.name} (only {best_gem.mins_per_km:.1f} mins per km!)")


def cmd_check(args):
    """Check a specific location"""
    location_name = args.location.lower()

    # Find the location
    loc = None
    for l in ALL_LOCATIONS:
        if l.name.lower() == location_name or l.station.lower() == location_name:
            loc = l
            break

    if not loc:
        print(f"Location '{args.location}' not found in database.")
        print("\nAvailable locations:")
        for l in sorted(ALL_LOCATIONS, key=lambda x: x.name):
            print(f"  - {l.name}")
        return

    print(f"\n=== {loc.name.upper()} ===\n")
    print(f"Station: {loc.station}")
    print(f"Postcode area: {loc.postcode_area}")
    print(f"Rail line: {loc.rail_line}")

    dist = distance_from_london(loc.lat, loc.lon)
    print(f"Distance from London: {dist:.1f} km")

    if loc.avg_price_2bed:
        print(f"Avg 2-bed price: £{loc.avg_price_2bed:,}")

    print(f"\nNotes: {loc.notes}")

    # Query commute times
    print("\nQuerying TfL for commute times...")
    search = CommuteSearch()

    your_mins, _ = search._get_journey_time(loc.station, search.YOUR_WORKPLACE)
    wife_mins, _ = search._get_journey_time(loc.station, search.WIFE_WORKPLACE)

    print(f"\nCommute to {search.YOUR_WORKPLACE_NAME}: ", end="")
    if your_mins:
        print(f"{your_mins} mins")
    else:
        print("Could not calculate")

    print(f"Commute to {search.WIFE_WORKPLACE_NAME}: ", end="")
    if wife_mins:
        print(f"{wife_mins} mins")
    else:
        print("Could not calculate")

    if your_mins and wife_mins:
        combined = your_mins + wife_mins
        mins_per_km = your_mins / dist if dist > 0 else 0
        print(f"\nCombined commute: {combined} mins")
        print(f"Minutes per km: {mins_per_km:.2f} (lower = better transport links)")

    # Property URLs
    print(f"\nProperty searches:")
    print(f"  Rightmove: https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=OUTCODE%5E{loc.postcode_area}")
    print(f"  Zoopla: https://www.zoopla.co.uk/for-sale/property/{loc.postcode_area.lower()}/")


def cmd_compare(args):
    """Compare two or more locations"""
    locations = []

    for name in args.locations:
        found = None
        for l in ALL_LOCATIONS:
            if l.name.lower() == name.lower() or l.station.lower() == name.lower():
                found = l
                break
        if found:
            locations.append(found)
        else:
            print(f"Warning: '{name}' not found in database, skipping.")

    if len(locations) < 2:
        print("Need at least 2 valid locations to compare.")
        return

    print(f"\n=== COMPARING {len(locations)} LOCATIONS ===\n")

    search = CommuteSearch()
    results = []

    for loc in locations:
        dist = distance_from_london(loc.lat, loc.lon)
        your_mins, _ = search._get_journey_time(loc.station, search.YOUR_WORKPLACE)
        wife_mins, _ = search._get_journey_time(loc.station, search.WIFE_WORKPLACE)

        results.append({
            'name': loc.name,
            'distance': dist,
            'your_mins': your_mins,
            'wife_mins': wife_mins,
            'combined': (your_mins or 0) + (wife_mins or 0) if your_mins and wife_mins else None,
            'price': loc.avg_price_2bed,
            'line': loc.rail_line,
        })

    # Print comparison table
    print(f"{'Location':<20} {'Distance':<12} {'Your Commute':<14} {'Wife Commute':<14} {'Combined':<10} {'Line'}")
    print("-" * 95)

    for r in results:
        dist_str = f"{r['distance']:.1f} km"
        your_str = f"{r['your_mins']} mins" if r['your_mins'] else "N/A"
        wife_str = f"{r['wife_mins']} mins" if r['wife_mins'] else "N/A"
        combined_str = f"{r['combined']} mins" if r['combined'] else "N/A"

        print(f"{r['name']:<20} {dist_str:<12} {your_str:<14} {wife_str:<14} {combined_str:<10} {r['line']}")

    # Winner
    valid = [r for r in results if r['combined']]
    if valid:
        winner = min(valid, key=lambda x: x['combined'])
        print(f"\n★ Best overall: {winner['name']} with {winner['combined']} mins combined commute")


def cmd_quick(args):
    """Quick journey time check without the full database"""
    tfl = TfLJourneyPlanner()

    print(f"\nChecking journey from {args.from_loc} to {args.to_loc}...")

    result = tfl.get_typical_commute_time(args.from_loc, args.to_loc)

    if result:
        print(f"\nFastest journey: {result['fastest_mins']} mins")
        print(f"Changes: {result['num_changes']}")
        print(f"Journey: {result['journey'].summary()}")
    else:
        print("Could not find a journey. Check the location names.")


def cmd_list(args):
    """List all locations in the database"""
    print(f"\n=== ALL {len(ALL_LOCATIONS)} LOCATIONS IN DATABASE ===\n")

    # Group by region
    regions = {
        'Kent': [],
        'Essex': [],
        'Hertfordshire': [],
        'Surrey/Sussex': [],
        'Berkshire/Bucks': [],
        'Beds/Cambs': [],
    }

    for loc in ALL_LOCATIONS:
        line = loc.rail_line.lower()
        if 'high speed' in line or 'southeastern' in line and loc.lat < 51.5:
            regions['Kent'].append(loc)
        elif 'c2c' in line or ('greater anglia' in line and loc.lon > 0):
            regions['Essex'].append(loc)
        elif 'thameslink' in line or 'great northern' in line:
            if loc.lat > 51.7:
                regions['Hertfordshire'].append(loc)
            else:
                regions['Beds/Cambs'].append(loc)
        elif 'south western' in line or 'southern' in line:
            regions['Surrey/Sussex'].append(loc)
        elif 'chiltern' in line or 'elizabeth' in line or 'gwr' in line or 'west midlands' in line:
            regions['Berkshire/Bucks'].append(loc)
        else:
            # Default based on coordinates
            if loc.lat > 51.7:
                regions['Beds/Cambs'].append(loc)
            else:
                regions['Kent'].append(loc)

    for region, locs in regions.items():
        if locs:
            print(f"\n{region}:")
            for loc in sorted(locs, key=lambda x: x.name):
                dist = distance_from_london(loc.lat, loc.lon)
                gem = "★" if loc.hidden_gem_potential >= 4 else " "
                print(f"  {gem} {loc.name:<25} ({loc.station:<25}) - {dist:.0f}km - {loc.rail_line}")


def main():
    parser = argparse.ArgumentParser(
        description="Find the best places to live based on actual commute times",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search                          Run full search with defaults
  %(prog)s search --your-max 60            Set your max commute to 60 mins
  %(prog)s search --gems-only              Only show hidden gems
  %(prog)s search --sort combined          Sort by combined commute time
  %(prog)s check "Gravesend"               Check details for Gravesend
  %(prog)s compare "Gravesend" "Grays"     Compare two locations
  %(prog)s quick "ME4 5DL" "W1T 3JF"       Quick journey time check
  %(prog)s list                            List all locations in database
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search all locations")
    search_parser.add_argument(
        "--your-max", type=int, default=75,
        help="Your maximum commute in minutes (default: 75)"
    )
    search_parser.add_argument(
        "--wife-max", type=int, default=90,
        help="Wife's maximum commute in minutes (default: 90)"
    )
    search_parser.add_argument(
        "--gems-only", action="store_true",
        help="Only show hidden gems (score >= 4)"
    )
    search_parser.add_argument(
        "--sort", choices=["your_commute", "wife_commute", "combined", "distance", "gem_score", "price", "mins_per_km"],
        help="Sort results by this field"
    )
    search_parser.add_argument(
        "--export", action="store_true",
        help="Export results to CSV and JSON"
    )
    search_parser.add_argument(
        "--tfl-only", action="store_true",
        help="Use TfL API only (skip Google Maps)"
    )
    search_parser.add_argument(
        "--refresh", action="store_true",
        help="Ignore cache and fetch fresh journey times"
    )
    search_parser.set_defaults(func=cmd_search)

    # Check command
    check_parser = subparsers.add_parser("check", help="Check a specific location")
    check_parser.add_argument("location", help="Location name to check")
    check_parser.set_defaults(func=cmd_check)

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare multiple locations")
    compare_parser.add_argument("locations", nargs="+", help="Locations to compare")
    compare_parser.set_defaults(func=cmd_compare)

    # Quick journey check
    quick_parser = subparsers.add_parser("quick", help="Quick journey time check")
    quick_parser.add_argument("from_loc", help="Starting location/postcode")
    quick_parser.add_argument("to_loc", help="Destination location/postcode")
    quick_parser.set_defaults(func=cmd_quick)

    # List command
    list_parser = subparsers.add_parser("list", help="List all locations")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
