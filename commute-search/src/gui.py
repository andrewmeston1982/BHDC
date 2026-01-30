#!/usr/bin/env python3
"""
Commute Time Property Search - AUTOMATIC SCANNER

Scans ALL 500+ railway stations and finds the ones within your commute time.
No more guessing - it finds the hidden gems FOR YOU.

Now with TravelTime API support for MUCH faster scanning!
- TravelTime can check 2000 locations in ONE request
- Google Maps as fallback (slower, one at a time)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
from typing import List, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path
import time

from google_maps_client import GoogleMapsClient
from tfl_client import TfLJourneyPlanner
from uk_stations import UK_STATIONS, get_stations_within_distance

# Try to import TravelTime client
try:
    from traveltime_client import TravelTimeClient, geocode_postcode
    TRAVELTIME_AVAILABLE = True
except ImportError:
    TRAVELTIME_AVAILABLE = False

# Your API keys (update these)
GOOGLE_MAPS_API_KEY = "AIzaSyDSrJIn4ckG430oRbwjQg6TAgg46DhEi1Y"

# TravelTime credentials
TRAVELTIME_APP_ID = "83084a5c"
TRAVELTIME_API_KEY = "ac765163ccc6e231d5365fed17489c45"


@dataclass
class StationResult:
    """Result for a scanned station"""
    name: str
    postcode: str
    lat: float
    lon: float
    distance_km: float
    your_commute_mins: Optional[int] = None
    partner_commute_mins: Optional[int] = None
    combined_mins: Optional[int] = None
    your_changes: int = 0
    partner_changes: int = 0


class AutoScannerGUI:
    """Automatically scans all stations to find ones within your commute time"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Commute Property Search - Auto Scanner")
        self.root.geometry("1400x950")
        self.root.minsize(1200, 850)

        # API clients
        self.google = GoogleMapsClient(GOOGLE_MAPS_API_KEY)
        self.tfl = TfLJourneyPlanner()
        self.traveltime = None  # Will be initialized if credentials provided

        # Results & cache
        self.results: List[StationResult] = []
        self.cache = self._load_cache()
        self.scanning = False

        # Geocoded work coordinates (for TravelTime)
        self.your_work_coords: Optional[Tuple[float, float]] = None
        self.partner_work_coords: Optional[Tuple[float, float]] = None

        self._create_widgets()
        self._load_api_settings()

    def _load_cache(self) -> dict:
        """Load cached journey times"""
        cache_file = Path(__file__).parent / "station_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_cache(self):
        """Save cache"""
        cache_file = Path(__file__).parent / "station_cache.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.cache, f)
        except:
            pass

    def _load_api_settings(self):
        """Load saved API settings"""
        settings_file = Path(__file__).parent / "api_settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    if settings.get('traveltime_app_id'):
                        self.tt_app_id_var.set(settings['traveltime_app_id'])
                    if settings.get('traveltime_api_key'):
                        self.tt_api_key_var.set(settings['traveltime_api_key'])
                    self._init_traveltime()
            except:
                pass

    def _save_api_settings(self):
        """Save API settings"""
        settings_file = Path(__file__).parent / "api_settings.json"
        try:
            with open(settings_file, 'w') as f:
                json.dump({
                    'traveltime_app_id': self.tt_app_id_var.get(),
                    'traveltime_api_key': self.tt_api_key_var.get()
                }, f)
        except:
            pass

    def _init_traveltime(self):
        """Initialize TravelTime client if credentials provided"""
        if not TRAVELTIME_AVAILABLE:
            return False

        app_id = self.tt_app_id_var.get().strip()
        api_key = self.tt_api_key_var.get().strip()

        if app_id and api_key:
            self.traveltime = TravelTimeClient(app_id, api_key)
            self._save_api_settings()
            return True
        return False

    def _create_widgets(self):
        """Create the UI"""

        # Main container
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill="both", expand=True)

        # === API Settings ===
        api_frame = ttk.LabelFrame(main, text="TravelTime API (FAST - checks 2000 locations at once!) - Get free key at traveltime.com", padding="5")
        api_frame.pack(fill="x", pady=(0, 5))

        api_row = ttk.Frame(api_frame)
        api_row.pack(fill="x")

        ttk.Label(api_row, text="App ID:").pack(side="left")
        self.tt_app_id_var = tk.StringVar(value=TRAVELTIME_APP_ID)
        ttk.Entry(api_row, textvariable=self.tt_app_id_var, width=35, show="*").pack(side="left", padx=(5, 15))

        ttk.Label(api_row, text="API Key:").pack(side="left")
        self.tt_api_key_var = tk.StringVar(value=TRAVELTIME_API_KEY)
        ttk.Entry(api_row, textvariable=self.tt_api_key_var, width=50, show="*").pack(side="left", padx=(5, 15))

        self.api_status_var = tk.StringVar(value="TravelTime: Not configured (using slower Google Maps)")
        self.api_status_label = ttk.Label(api_row, textvariable=self.api_status_var, foreground="gray")
        self.api_status_label.pack(side="left", padx=10)

        ttk.Button(api_row, text="Test & Save", command=self._test_traveltime).pack(side="left")

        # === TOP: Settings ===
        settings_frame = ttk.LabelFrame(main, text="Settings - Set your workplaces and max commute times", padding="10")
        settings_frame.pack(fill="x", pady=(0, 10))

        # Row 1: Workplaces
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill="x", pady=5)

        ttk.Label(row1, text="Your workplace:", font=("", 10, "bold")).pack(side="left")
        self.your_work_var = tk.StringVar(value="W1T 3JF")
        ttk.Entry(row1, textvariable=self.your_work_var, width=15).pack(side="left", padx=(5, 20))

        ttk.Label(row1, text="Max commute (mins):").pack(side="left")
        self.your_max_var = tk.IntVar(value=75)
        ttk.Spinbox(row1, from_=30, to=150, textvariable=self.your_max_var, width=6).pack(side="left", padx=(5, 40))

        ttk.Label(row1, text="Partner workplace:", font=("", 10, "bold")).pack(side="left")
        self.partner_work_var = tk.StringVar(value="E8 1EA")
        ttk.Entry(row1, textvariable=self.partner_work_var, width=15).pack(side="left", padx=(5, 20))

        ttk.Label(row1, text="Max commute (mins):").pack(side="left")
        self.partner_max_var = tk.IntVar(value=90)
        ttk.Spinbox(row1, from_=30, to=150, textvariable=self.partner_max_var, width=6).pack(side="left", padx=5)

        # Row 2: Scan settings & button
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill="x", pady=10)

        ttk.Label(row2, text="Scan radius from London:").pack(side="left")
        self.radius_var = tk.IntVar(value=80)
        ttk.Spinbox(row2, from_=30, to=150, textvariable=self.radius_var, width=6).pack(side="left", padx=5)
        ttk.Label(row2, text="km").pack(side="left", padx=(0, 30))

        ttk.Label(row2, text="Arrive by:").pack(side="left")
        self.arrival_var = tk.IntVar(value=9)
        ttk.Spinbox(row2, from_=6, to=12, textvariable=self.arrival_var, width=4).pack(side="left", padx=5)
        ttk.Label(row2, text=":00").pack(side="left", padx=(0, 30))

        self.scan_btn = ttk.Button(row2, text="🔍 SCAN ALL STATIONS", command=self._start_scan, style="Accent.TButton")
        self.scan_btn.pack(side="left", padx=20)

        self.stop_btn = ttk.Button(row2, text="⏹ Stop", command=self._stop_scan, state="disabled")
        self.stop_btn.pack(side="left")

        self.progress_var = tk.StringVar(value="Ready - Click 'SCAN ALL STATIONS' to find locations within your commute time")
        ttk.Label(row2, textvariable=self.progress_var, font=("", 9)).pack(side="left", padx=20)

        # Progress bar
        self.progress_bar = ttk.Progressbar(settings_frame, mode="determinate", length=500)
        self.progress_bar.pack(fill="x", pady=(5, 0))

        # === MIDDLE: Results ===
        results_frame = ttk.LabelFrame(main, text="Results - Stations within your commute time (click to open property searches)", padding="10")
        results_frame.pack(fill="both", expand=True, pady=10)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Treeview
        columns = ("name", "postcode", "distance", "your_commute", "partner_commute", "combined")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Station / Area", command=lambda: self._sort_by("name"))
        self.tree.heading("postcode", text="Postcode", command=lambda: self._sort_by("postcode"))
        self.tree.heading("distance", text="Distance (km)", command=lambda: self._sort_by("distance"))
        self.tree.heading("your_commute", text="Your Commute", command=lambda: self._sort_by("your_commute"))
        self.tree.heading("partner_commute", text="Partner Commute", command=lambda: self._sort_by("partner_commute"))
        self.tree.heading("combined", text="Combined", command=lambda: self._sort_by("combined"))

        self.tree.column("name", width=200)
        self.tree.column("postcode", width=80)
        self.tree.column("distance", width=100)
        self.tree.column("your_commute", width=120)
        self.tree.column("partner_commute", width=120)
        self.tree.column("combined", width=100)

        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Stats bar
        stats_frame = ttk.Frame(results_frame)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.stats_var = tk.StringVar(value="")
        ttk.Label(stats_frame, textvariable=self.stats_var, font=("", 10, "bold")).pack(side="left")

        # === BOTTOM: Property Filters & Buttons ===
        bottom_frame = ttk.Frame(main)
        bottom_frame.pack(fill="x")

        # Left: Filters
        filter_frame = ttk.LabelFrame(bottom_frame, text="Property Filters (applied when opening search)", padding="10")
        filter_frame.pack(side="left", fill="both", expand=True)

        # Filter row 1
        f1 = ttk.Frame(filter_frame)
        f1.pack(fill="x")

        self.detached_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f1, text="Detached", variable=self.detached_var).pack(side="left", padx=5)
        self.semi_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f1, text="Semi", variable=self.semi_var).pack(side="left", padx=5)
        self.terraced_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f1, text="Terraced", variable=self.terraced_var).pack(side="left", padx=5)
        self.bungalow_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f1, text="Bungalow", variable=self.bungalow_var).pack(side="left", padx=5)

        ttk.Separator(f1, orient="vertical").pack(side="left", fill="y", padx=10)

        self.garden_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f1, text="Garden", variable=self.garden_var).pack(side="left", padx=5)
        self.parking_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f1, text="Parking", variable=self.parking_var).pack(side="left", padx=5)
        self.freehold_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f1, text="Freehold", variable=self.freehold_var).pack(side="left", padx=5)
        self.chain_free_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f1, text="Chain-free", variable=self.chain_free_var).pack(side="left", padx=5)

        # Filter row 2
        f2 = ttk.Frame(filter_frame)
        f2.pack(fill="x", pady=(5, 0))

        self.no_new_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f2, text="No new homes", variable=self.no_new_var).pack(side="left", padx=5)
        self.no_retirement_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f2, text="No retirement", variable=self.no_retirement_var).pack(side="left", padx=5)
        self.no_auction_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f2, text="No auction", variable=self.no_auction_var).pack(side="left", padx=5)
        self.no_shared_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f2, text="No shared ownership", variable=self.no_shared_var).pack(side="left", padx=5)

        ttk.Separator(f2, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Label(f2, text="Beds:").pack(side="left")
        self.min_beds_var = tk.IntVar(value=2)
        ttk.Spinbox(f2, from_=1, to=6, textvariable=self.min_beds_var, width=3).pack(side="left", padx=2)
        ttk.Label(f2, text="-").pack(side="left")
        self.max_beds_var = tk.IntVar(value=5)
        ttk.Spinbox(f2, from_=1, to=10, textvariable=self.max_beds_var, width=3).pack(side="left", padx=2)

        ttk.Label(f2, text="  Price £:").pack(side="left", padx=(10, 0))
        self.min_price_var = tk.StringVar(value="")
        ttk.Entry(f2, textvariable=self.min_price_var, width=8).pack(side="left", padx=2)
        ttk.Label(f2, text="-").pack(side="left")
        self.max_price_var = tk.StringVar(value="")
        ttk.Entry(f2, textvariable=self.max_price_var, width=8).pack(side="left", padx=2)

        # Right: Buttons
        btn_frame = ttk.LabelFrame(bottom_frame, text="Open Property Search", padding="10")
        btn_frame.pack(side="right", fill="y", padx=(10, 0))

        self.rightmove_btn = ttk.Button(btn_frame, text="🏠 Rightmove", command=self._open_rightmove, state="disabled", width=15)
        self.rightmove_btn.pack(pady=2)

        self.zoopla_btn = ttk.Button(btn_frame, text="🏡 Zoopla", command=self._open_zoopla, state="disabled", width=15)
        self.zoopla_btn.pack(pady=2)

        self.otm_btn = ttk.Button(btn_frame, text="🏘️ OnTheMarket", command=self._open_otm, state="disabled", width=15)
        self.otm_btn.pack(pady=2)

        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="📊 Export CSV", command=self._export, width=15).pack(pady=2)

        ttk.Button(btn_frame, text="🗺️ View Map", command=self._show_map, width=15).pack(pady=2)

    def _test_traveltime(self):
        """Test TravelTime API connection"""
        if not TRAVELTIME_AVAILABLE:
            messagebox.showerror("Not Available", "TravelTime client module not found")
            return

        app_id = self.tt_app_id_var.get().strip()
        api_key = self.tt_api_key_var.get().strip()

        if not app_id or not api_key:
            messagebox.showwarning("Missing Credentials", "Please enter both App ID and API Key")
            return

        self.api_status_var.set("Testing connection...")
        self.root.update()

        try:
            self.traveltime = TravelTimeClient(app_id, api_key)

            # Test with a simple geocode + time filter
            test_coords = geocode_postcode("W1T3JF")
            if not test_coords:
                raise Exception("Could not geocode test postcode")

            # Test a quick time filter
            result = self.traveltime.time_filter_many(
                test_coords,
                [("test", 51.5, -0.1)],  # Central London
                max_travel_time_mins=60
            )

            if result is not None:
                self._save_api_settings()
                self.api_status_var.set("TravelTime: Connected (FAST mode enabled)")
                self.api_status_label.config(foreground="green")
                messagebox.showinfo("Success", "TravelTime API connected!\n\nYou can now scan ALL stations very quickly.")
            else:
                raise Exception("API returned no results")

        except Exception as e:
            self.traveltime = None
            self.api_status_var.set(f"TravelTime: Error - {str(e)[:30]}")
            self.api_status_label.config(foreground="red")
            messagebox.showerror("Connection Failed", f"Could not connect to TravelTime API:\n{e}")

    def _geocode_workplaces(self) -> bool:
        """Geocode workplaces for TravelTime API"""
        your_work = self.your_work_var.get().strip()
        partner_work = self.partner_work_var.get().strip()

        if TRAVELTIME_AVAILABLE:
            self.your_work_coords = geocode_postcode(your_work.replace(" ", ""))
            self.partner_work_coords = geocode_postcode(partner_work.replace(" ", ""))

            if not self.your_work_coords:
                messagebox.showerror("Error", f"Could not geocode your workplace: {your_work}")
                return False
            if not self.partner_work_coords:
                messagebox.showerror("Error", f"Could not geocode partner workplace: {partner_work}")
                return False

        return True

    def _start_scan(self):
        """Start scanning all stations"""
        # Geocode workplaces first if using TravelTime
        if self.traveltime and not self._geocode_workplaces():
            return

        self.scanning = True
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.results = []

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Start background thread
        if self.traveltime and self.your_work_coords and self.partner_work_coords:
            thread = threading.Thread(target=self._do_scan_traveltime)
        else:
            thread = threading.Thread(target=self._do_scan)
        thread.daemon = True
        thread.start()

    def _stop_scan(self):
        """Stop scanning"""
        self.scanning = False

    def _do_scan_traveltime(self):
        """Perform scan using TravelTime API (FAST - bulk queries)"""
        your_max = self.your_max_var.get()
        partner_max = self.partner_max_var.get()
        arrival = self.arrival_var.get()
        radius = self.radius_var.get()

        # Get stations within radius
        stations = get_stations_within_distance(radius)
        total = len(stations)

        self.root.after(0, lambda: self.progress_var.set(f"TravelTime: Checking {total} stations in bulk (this is FAST!)..."))
        self.root.after(0, lambda: self.progress_bar.configure(mode="indeterminate"))
        self.root.after(0, lambda: self.progress_bar.start(10))

        # Prepare stations for TravelTime
        station_list = [(f"{name}|{postcode}", lat, lon) for name, postcode, lat, lon in stations]

        # Step 1: Get times to YOUR workplace (bulk)
        self.root.after(0, lambda: self.progress_var.set(f"Step 1/2: Checking {total} stations → your workplace..."))

        your_times = self.traveltime.time_filter_batch(
            self.your_work_coords,
            station_list,
            max_travel_time_mins=your_max,
            arrival_hour=arrival
        )

        if not self.scanning:
            self.root.after(0, lambda: self._finish_scan([]))
            return

        # Filter to only those within your limit
        reachable_your = {k: v for k, v in your_times.items() if v is not None and v <= your_max}

        self.root.after(0, lambda: self.progress_var.set(f"Found {len(reachable_your)} within your limit. Step 2/2: Checking partner's workplace..."))

        # Step 2: Get times to PARTNER's workplace (only for stations that passed step 1)
        filtered_stations = [(sid, lat, lon) for sid, lat, lon in station_list if sid in reachable_your]

        partner_times = self.traveltime.time_filter_batch(
            self.partner_work_coords,
            filtered_stations,
            max_travel_time_mins=partner_max,
            arrival_hour=arrival
        )

        if not self.scanning:
            self.root.after(0, lambda: self._finish_scan([]))
            return

        # Build results for stations that meet BOTH criteria
        matches = []
        station_dict = {f"{name}|{postcode}": (name, postcode, lat, lon) for name, postcode, lat, lon in stations}

        import math
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        for station_id, your_mins in reachable_your.items():
            partner_mins = partner_times.get(station_id)
            if partner_mins is not None and partner_mins <= partner_max:
                name, postcode, lat, lon = station_dict[station_id]
                dist = haversine(51.5, -0.1, lat, lon)

                result = StationResult(
                    name=name,
                    postcode=postcode,
                    lat=lat,
                    lon=lon,
                    distance_km=dist,
                    your_commute_mins=your_mins,
                    partner_commute_mins=partner_mins,
                    combined_mins=your_mins + partner_mins,
                    your_changes=0,  # TravelTime doesn't give change count
                    partner_changes=0
                )
                matches.append(result)

                # Add to tree immediately
                self.root.after(0, lambda r=result: self._add_result(r))

        # Stop progress bar
        self.root.after(0, lambda: self.progress_bar.stop())
        self.root.after(0, lambda: self.progress_bar.configure(mode="determinate"))

        # Done
        self.root.after(0, lambda: self._finish_scan(matches))

    def _do_scan(self):
        """Perform the scan"""
        your_work = self.your_work_var.get()
        partner_work = self.partner_work_var.get()
        your_max = self.your_max_var.get()
        partner_max = self.partner_max_var.get()
        arrival = self.arrival_var.get()
        radius = self.radius_var.get()

        # Get stations within radius
        stations = get_stations_within_distance(radius)
        total = len(stations)

        self.root.after(0, lambda: self.progress_var.set(f"Scanning {total} stations within {radius}km of London..."))

        matches = []

        for i, (name, postcode, lat, lon) in enumerate(stations):
            if not self.scanning:
                break

            # Update progress
            pct = ((i + 1) / total) * 100
            self.root.after(0, lambda n=name, p=pct, c=i+1, t=total:
                self._update_progress(n, p, c, t))

            # Check cache first
            cache_key_you = f"{name}|{your_work}"
            cache_key_partner = f"{name}|{partner_work}"

            your_mins = None
            partner_mins = None
            your_changes = 0
            partner_changes = 0

            # Your commute
            if cache_key_you in self.cache:
                your_mins = self.cache[cache_key_you].get('mins')
                your_changes = self.cache[cache_key_you].get('changes', 0)
            else:
                try:
                    result = self.google.get_commute_time(f"{name}, UK", f"{your_work}, London, UK", arrival)
                    if result:
                        your_mins = result['fastest_mins']
                        your_changes = result.get('num_changes', 0)
                        self.cache[cache_key_you] = {'mins': your_mins, 'changes': your_changes}
                except:
                    pass

            # Skip if already over your limit
            if your_mins is None or your_mins > your_max:
                continue

            # Partner commute
            if cache_key_partner in self.cache:
                partner_mins = self.cache[cache_key_partner].get('mins')
                partner_changes = self.cache[cache_key_partner].get('changes', 0)
            else:
                try:
                    result = self.google.get_commute_time(f"{name}, UK", f"{partner_work}, London, UK", arrival)
                    if result:
                        partner_mins = result['fastest_mins']
                        partner_changes = result.get('num_changes', 0)
                        self.cache[cache_key_partner] = {'mins': partner_mins, 'changes': partner_changes}
                except:
                    pass

            # Check if both within limits
            if partner_mins is None or partner_mins > partner_max:
                continue

            # Calculate distance
            import math
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
                return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

            dist = haversine(51.5, -0.1, lat, lon)

            # This one matches!
            result = StationResult(
                name=name,
                postcode=postcode,
                lat=lat,
                lon=lon,
                distance_km=dist,
                your_commute_mins=your_mins,
                partner_commute_mins=partner_mins,
                combined_mins=your_mins + partner_mins,
                your_changes=your_changes,
                partner_changes=partner_changes
            )
            matches.append(result)

            # Add to tree immediately
            self.root.after(0, lambda r=result: self._add_result(r))

        # Done
        self.root.after(0, lambda: self._finish_scan(matches))
        self._save_cache()

    def _update_progress(self, name: str, pct: float, current: int, total: int):
        """Update progress display"""
        self.progress_bar["value"] = pct
        self.progress_var.set(f"[{current}/{total}] Checking {name}...")

    def _add_result(self, r: StationResult):
        """Add a result to the tree"""
        self.tree.insert("", "end", values=(
            r.name,
            r.postcode,
            f"{r.distance_km:.1f}",
            f"{r.your_commute_mins} mins ({r.your_changes} chg)",
            f"{r.partner_commute_mins} mins ({r.partner_changes} chg)",
            f"{r.combined_mins} mins"
        ))
        self.results.append(r)
        self.stats_var.set(f"Found {len(self.results)} matching locations so far...")

    def _finish_scan(self, matches: List[StationResult]):
        """Finish the scan"""
        self.scanning = False
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.progress_bar["value"] = 100

        if matches:
            self.progress_var.set(f"DONE! Found {len(matches)} stations within your commute limits!")
            self.stats_var.set(f"Found {len(matches)} locations - click one to open property searches")
        else:
            self.progress_var.set("No stations found within your commute limits. Try increasing max commute time or scan radius.")
            self.stats_var.set("")

    def _sort_by(self, col: str):
        """Sort results by column"""
        if not self.results:
            return

        if col == "name":
            self.results.sort(key=lambda r: r.name)
        elif col == "postcode":
            self.results.sort(key=lambda r: r.postcode)
        elif col == "distance":
            self.results.sort(key=lambda r: r.distance_km)
        elif col == "your_commute":
            self.results.sort(key=lambda r: r.your_commute_mins or 999)
        elif col == "partner_commute":
            self.results.sort(key=lambda r: r.partner_commute_mins or 999)
        elif col == "combined":
            self.results.sort(key=lambda r: r.combined_mins or 999)

        # Refresh tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in self.results:
            self.tree.insert("", "end", values=(
                r.name, r.postcode, f"{r.distance_km:.1f}",
                f"{r.your_commute_mins} mins ({r.your_changes} chg)",
                f"{r.partner_commute_mins} mins ({r.partner_changes} chg)",
                f"{r.combined_mins} mins"
            ))

    def _on_select(self, event):
        """Enable buttons when something selected"""
        if self.tree.selection():
            self.rightmove_btn.config(state="normal")
            self.zoopla_btn.config(state="normal")
            self.otm_btn.config(state="normal")

    def _on_double_click(self, event):
        """Open Rightmove + Zoopla on double-click"""
        self._open_rightmove()
        self._open_zoopla()

    def _get_selected(self) -> Optional[StationResult]:
        """Get selected result"""
        sel = self.tree.selection()
        if not sel:
            return None
        item = self.tree.item(sel[0])
        name = item["values"][0]
        for r in self.results:
            if r.name == name:
                return r
        return None

    def _generate_rightmove_url(self, r: StationResult) -> str:
        """Generate Rightmove URL"""
        url = f"https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=OUTCODE%5E{r.postcode}&searchType=SALE"

        types = []
        if self.detached_var.get(): types.append("detached")
        if self.semi_var.get(): types.append("semi-detached")
        if self.terraced_var.get(): types.append("terraced")
        if self.bungalow_var.get(): types.append("bungalow")
        if types: url += f"&propertyTypes={','.join(types)}"

        must = []
        if self.garden_var.get(): must.append("garden")
        if self.parking_var.get(): must.append("parking")
        if must: url += f"&mustHave={','.join(must)}"

        dont = []
        if self.no_new_var.get(): dont.append("newHome")
        if self.no_retirement_var.get(): dont.append("retirement")
        if self.no_shared_var.get(): dont.append("sharedOwnership")
        if self.no_auction_var.get(): dont.append("auction")
        if dont: url += f"&dontShow={','.join(dont)}"

        if self.freehold_var.get(): url += "&tenure=freehold"

        url += f"&minBedrooms={self.min_beds_var.get()}&maxBedrooms={self.max_beds_var.get()}"

        try:
            if self.min_price_var.get(): url += f"&minPrice={int(self.min_price_var.get().replace(',',''))}"
            if self.max_price_var.get(): url += f"&maxPrice={int(self.max_price_var.get().replace(',',''))}"
        except: pass

        return url

    def _generate_zoopla_url(self, r: StationResult) -> str:
        """Generate Zoopla URL"""
        url = f"https://www.zoopla.co.uk/for-sale/property/{r.postcode.lower()}/?q={r.name.replace(' ','%20')}"

        types = []
        if self.detached_var.get(): types.append("detached")
        if self.semi_var.get(): types.append("semi_detached")
        if self.terraced_var.get(): types.append("terraced")
        if self.bungalow_var.get(): types.append("bungalow")
        if types: url += f"&property_sub_type={','.join(types)}"

        if self.garden_var.get(): url += "&feature=has_garden"
        if self.parking_var.get(): url += "&feature=has_parking"
        if self.chain_free_var.get(): url += "&is_chain_free=true"
        if self.freehold_var.get(): url += "&tenure=freehold"
        if self.no_new_var.get(): url += "&new_homes=exclude"
        if self.no_retirement_var.get(): url += "&is_retirement_home=false"
        if self.no_shared_var.get(): url += "&is_shared_ownership=false"
        if self.no_auction_var.get(): url += "&is_auction=false"

        url += f"&beds_min={self.min_beds_var.get()}&beds_max={self.max_beds_var.get()}"

        try:
            if self.min_price_var.get(): url += f"&price_min={int(self.min_price_var.get().replace(',',''))}"
            if self.max_price_var.get(): url += f"&price_max={int(self.max_price_var.get().replace(',',''))}"
        except: pass

        return url

    def _open_rightmove(self):
        r = self._get_selected()
        if r: webbrowser.open(self._generate_rightmove_url(r))

    def _open_zoopla(self):
        r = self._get_selected()
        if r: webbrowser.open(self._generate_zoopla_url(r))

    def _open_otm(self):
        r = self._get_selected()
        if r:
            url = f"https://www.onthemarket.com/for-sale/property/{r.name.lower().replace(' ','-')}/"
            url += f"?min-bedrooms={self.min_beds_var.get()}&max-bedrooms={self.max_beds_var.get()}"
            webbrowser.open(url)

    def _export(self):
        """Export to CSV"""
        if not self.results:
            messagebox.showwarning("No Results", "Run a scan first!")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfilename="commute_search_results.csv"
        )
        if filename:
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Station', 'Postcode', 'Distance (km)', 'Your Commute', 'Partner Commute', 'Combined'])
                for r in self.results:
                    writer.writerow([r.name, r.postcode, f"{r.distance_km:.1f}",
                                   f"{r.your_commute_mins}", f"{r.partner_commute_mins}", f"{r.combined_mins}"])
            messagebox.showinfo("Exported", f"Saved {len(self.results)} results to {filename}")

    def _show_map(self):
        """Generate and show an interactive map with isochrones and stations"""
        if not self.results:
            messagebox.showwarning("No Results", "Run a scan first!")
            return

        # Get work coordinates
        if not self._geocode_workplaces():
            return

        self.progress_var.set("Generating map with isochrones...")
        self.root.update()

        # Get isochrones if TravelTime available
        your_isochrone = None
        partner_isochrone = None

        if self.traveltime:
            try:
                your_isochrone = self.traveltime.get_isochrone(
                    self.your_work_coords,
                    self.your_max_var.get(),
                    self.arrival_var.get()
                )
                partner_isochrone = self.traveltime.get_isochrone(
                    self.partner_work_coords,
                    self.partner_max_var.get(),
                    self.arrival_var.get()
                )
            except Exception as e:
                print(f"Could not get isochrones: {e}")

        # Generate HTML map
        html = self._generate_map_html(your_isochrone, partner_isochrone)

        # Save and open
        map_file = Path(__file__).parent / "commute_map.html"
        with open(map_file, 'w') as f:
            f.write(html)

        webbrowser.open(f"file://{map_file.absolute()}")
        self.progress_var.set(f"Map opened in browser - saved to {map_file.name}")

    def _generate_map_html(self, your_isochrone, partner_isochrone) -> str:
        """Generate Leaflet HTML map"""

        # Station markers
        markers_js = ""
        for r in self.results:
            popup = f"{r.name} ({r.postcode})<br>You: {r.your_commute_mins}min | Partner: {r.partner_commute_mins}min"
            markers_js += f"""
        L.marker([{r.lat}, {r.lon}])
            .addTo(map)
            .bindPopup("{popup}");
"""

        # Work location markers
        if self.your_work_coords:
            markers_js += f"""
        L.marker([{self.your_work_coords[0]}, {self.your_work_coords[1]}], {{
            icon: L.divIcon({{className: 'work-marker', html: '🏢', iconSize: [30, 30]}})
        }}).addTo(map).bindPopup("Your workplace: {self.your_work_var.get()}");
"""
        if self.partner_work_coords:
            markers_js += f"""
        L.marker([{self.partner_work_coords[0]}, {self.partner_work_coords[1]}], {{
            icon: L.divIcon({{className: 'work-marker', html: '🏛️', iconSize: [30, 30]}})
        }}).addTo(map).bindPopup("Partner workplace: {self.partner_work_var.get()}");
"""

        # Isochrone polygons
        isochrone_js = ""
        if your_isochrone:
            for polygon in your_isochrone:
                coords = [[p[0], p[1]] for p in polygon]
                isochrone_js += f"""
        L.polygon({coords}, {{color: 'blue', fillOpacity: 0.15, weight: 2}})
            .addTo(map)
            .bindPopup("Your commute zone: {self.your_max_var.get()} mins");
"""
        if partner_isochrone:
            for polygon in partner_isochrone:
                coords = [[p[0], p[1]] for p in polygon]
                isochrone_js += f"""
        L.polygon({coords}, {{color: 'red', fillOpacity: 0.15, weight: 2}})
            .addTo(map)
            .bindPopup("Partner commute zone: {self.partner_max_var.get()} mins");
"""

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Commute Search Results Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ width: 100%; height: 100vh; }}
        .work-marker {{ font-size: 24px; text-align: center; }}
        .legend {{
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
        }}
        .legend h4 {{ margin: 0 0 10px 0; }}
        .legend-item {{ margin: 5px 0; }}
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 10px;
            margin-right: 5px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([51.5, 0.0], 9);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        // Isochrones (draw first so stations appear on top)
        {isochrone_js}

        // Station markers
        {markers_js}

        // Legend
        var legend = L.control({{position: 'bottomright'}});
        legend.onAdd = function(map) {{
            var div = L.DomUtil.create('div', 'legend');
            div.innerHTML = '<h4>Commute Zones</h4>' +
                '<div class="legend-item"><span class="legend-color" style="background: blue; opacity: 0.3;"></span> Your zone ({self.your_max_var.get()} mins)</div>' +
                '<div class="legend-item"><span class="legend-color" style="background: red; opacity: 0.3;"></span> Partner zone ({self.partner_max_var.get()} mins)</div>' +
                '<div class="legend-item"><span class="legend-color" style="background: purple; opacity: 0.3;"></span> Overlap (sweet spot!)</div>' +
                '<div class="legend-item">📍 {len(self.results)} matching stations</div>';
            return div;
        }};
        legend.addTo(map);

        // Fit bounds to show all markers
        var bounds = L.latLngBounds([
            {[[r.lat, r.lon] for r in self.results]}
        ]);
        if (bounds.isValid()) {{
            map.fitBounds(bounds.pad(0.1));
        }}
    </script>
</body>
</html>"""
        return html

    def run(self):
        self.root.mainloop()


def main():
    app = AutoScannerGUI()
    app.run()


if __name__ == "__main__":
    main()
