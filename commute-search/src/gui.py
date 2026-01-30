#!/usr/bin/env python3
"""
Commute Time Property Search - GUI Application

Search ANY location - not just a fixed list!
Find the real hidden gems by checking any postcode or town.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import webbrowser
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
from pathlib import Path

from google_maps_client import GoogleMapsClient
from tfl_client import TfLJourneyPlanner

# Your Google Maps API key
GOOGLE_MAPS_API_KEY = "AIzaSyDSrJIn4ckG430oRbwjQg6TAgg46DhEi1Y"


@dataclass
class SearchResult:
    """Result for a searched location"""
    name: str
    your_commute_mins: Optional[int] = None
    partner_commute_mins: Optional[int] = None
    combined_mins: Optional[int] = None
    your_changes: int = 0
    partner_changes: int = 0
    notes: str = ""


@dataclass
class PropertyFilters:
    """Property search filters"""
    detached: bool = True
    semi_detached: bool = True
    terraced: bool = True
    bungalow: bool = True
    garden: bool = True
    parking: bool = True
    garage: bool = False
    freehold_only: bool = True
    no_new_homes: bool = True
    no_retirement: bool = True
    no_auction: bool = True
    no_shared_ownership: bool = True
    chain_free_only: bool = False
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_beds: int = 2
    max_beds: int = 5


class PropertySearchGUI:
    """Main GUI Application - Search ANY location!"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Commute Time Property Search - Find Hidden Gems!")
        self.root.geometry("1300x850")
        self.root.minsize(1100, 750)

        # API clients
        self.google = GoogleMapsClient(GOOGLE_MAPS_API_KEY)
        self.tfl = TfLJourneyPlanner()

        # Results storage
        self.results: List[SearchResult] = []
        self.saved_locations: List[SearchResult] = []

        # Create UI
        self._create_widgets()
        self._load_saved_locations()

    def _create_widgets(self):
        """Create all GUI widgets"""

        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        # === TOP SECTION: Quick Search ===
        search_frame = ttk.LabelFrame(main_frame, text="🔍 Search ANY Location", padding="15")
        search_frame.pack(fill="x", pady=(0, 10))

        # Location entry
        entry_frame = ttk.Frame(search_frame)
        entry_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(entry_frame, text="Enter postcode or town:", font=("", 11)).pack(side="left")

        self.location_var = tk.StringVar()
        self.location_entry = ttk.Entry(entry_frame, textvariable=self.location_var, width=40, font=("", 11))
        self.location_entry.pack(side="left", padx=10)
        self.location_entry.bind("<Return>", lambda e: self._quick_search())

        self.search_btn = ttk.Button(entry_frame, text="Check Commute", command=self._quick_search)
        self.search_btn.pack(side="left", padx=5)

        self.add_to_list_btn = ttk.Button(entry_frame, text="+ Add to List", command=self._add_to_saved, state="disabled")
        self.add_to_list_btn.pack(side="left", padx=5)

        # Results display
        result_frame = ttk.Frame(search_frame)
        result_frame.pack(fill="x")

        self.result_var = tk.StringVar(value="Enter a postcode (e.g., ME4 5DL) or town name (e.g., Gravesend) and click 'Check Commute'")
        self.result_label = ttk.Label(result_frame, textvariable=self.result_var, font=("", 10), wraplength=900)
        self.result_label.pack(anchor="w")

        # === MIDDLE SECTION: Two columns ===
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill="both", expand=True, pady=10)
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.columnconfigure(1, weight=2)
        middle_frame.rowconfigure(0, weight=1)

        # --- LEFT COLUMN: Settings ---
        left_frame = ttk.Frame(middle_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Notebook for settings tabs
        notebook = ttk.Notebook(left_frame)
        notebook.pack(fill="both", expand=True)

        # Tab 1: Workplaces
        work_tab = ttk.Frame(notebook, padding="10")
        notebook.add(work_tab, text="📍 Workplaces")

        ttk.Label(work_tab, text="Your Workplace", font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))
        ttk.Label(work_tab, text="Postcode:").pack(anchor="w")
        self.your_workplace_var = tk.StringVar(value="W1T 3JF")
        ttk.Entry(work_tab, textvariable=self.your_workplace_var, width=25).pack(anchor="w", pady=(0, 5))
        ttk.Label(work_tab, text="Max commute (mins):").pack(anchor="w")
        self.your_max_var = tk.IntVar(value=75)
        ttk.Spinbox(work_tab, from_=15, to=150, textvariable=self.your_max_var, width=10).pack(anchor="w", pady=(0, 15))

        ttk.Label(work_tab, text="Partner's Workplace", font=("", 10, "bold")).pack(anchor="w", pady=(10, 5))
        ttk.Label(work_tab, text="Postcode:").pack(anchor="w")
        self.partner_workplace_var = tk.StringVar(value="E8 1EA")
        ttk.Entry(work_tab, textvariable=self.partner_workplace_var, width=25).pack(anchor="w", pady=(0, 5))
        ttk.Label(work_tab, text="Max commute (mins):").pack(anchor="w")
        self.partner_max_var = tk.IntVar(value=90)
        ttk.Spinbox(work_tab, from_=15, to=150, textvariable=self.partner_max_var, width=10).pack(anchor="w", pady=(0, 15))

        ttk.Label(work_tab, text="Arrive at work by:").pack(anchor="w", pady=(10, 0))
        self.arrival_hour_var = tk.IntVar(value=9)
        ttk.Spinbox(work_tab, from_=6, to=12, textvariable=self.arrival_hour_var, width=10).pack(anchor="w")

        # Tab 2: Property Types
        prop_tab = ttk.Frame(notebook, padding="10")
        notebook.add(prop_tab, text="🏠 Property")

        ttk.Label(prop_tab, text="Property Types", font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.detached_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prop_tab, text="Detached", variable=self.detached_var).pack(anchor="w")
        self.semi_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prop_tab, text="Semi-detached", variable=self.semi_var).pack(anchor="w")
        self.terraced_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prop_tab, text="Terraced", variable=self.terraced_var).pack(anchor="w")
        self.bungalow_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prop_tab, text="Bungalow", variable=self.bungalow_var).pack(anchor="w")

        ttk.Label(prop_tab, text="Must Have", font=("", 10, "bold")).pack(anchor="w", pady=(15, 5))
        self.garden_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prop_tab, text="Garden", variable=self.garden_var).pack(anchor="w")
        self.parking_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prop_tab, text="Parking", variable=self.parking_var).pack(anchor="w")
        self.garage_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(prop_tab, text="Garage/Driveway", variable=self.garage_var).pack(anchor="w")

        ttk.Label(prop_tab, text="Tenure", font=("", 10, "bold")).pack(anchor="w", pady=(15, 5))
        self.freehold_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prop_tab, text="Freehold only", variable=self.freehold_var).pack(anchor="w")

        self.chain_free_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(prop_tab, text="Chain-free only (Zoopla)", variable=self.chain_free_var).pack(anchor="w", pady=(10, 0))

        # Tab 3: Exclusions & Price
        excl_tab = ttk.Frame(notebook, padding="10")
        notebook.add(excl_tab, text="🚫 Exclude")

        ttk.Label(excl_tab, text="Don't Show", font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.no_new_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(excl_tab, text="New homes", variable=self.no_new_var).pack(anchor="w")
        self.no_retirement_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(excl_tab, text="Retirement homes", variable=self.no_retirement_var).pack(anchor="w")
        self.no_auction_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(excl_tab, text="Auction properties", variable=self.no_auction_var).pack(anchor="w")
        self.no_shared_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(excl_tab, text="Shared ownership", variable=self.no_shared_var).pack(anchor="w")

        ttk.Label(excl_tab, text="Price Range (£)", font=("", 10, "bold")).pack(anchor="w", pady=(15, 5))
        price_frame = ttk.Frame(excl_tab)
        price_frame.pack(anchor="w")
        ttk.Label(price_frame, text="Min:").pack(side="left")
        self.min_price_var = tk.StringVar(value="")
        ttk.Entry(price_frame, textvariable=self.min_price_var, width=10).pack(side="left", padx=(5, 15))
        ttk.Label(price_frame, text="Max:").pack(side="left")
        self.max_price_var = tk.StringVar(value="")
        ttk.Entry(price_frame, textvariable=self.max_price_var, width=10).pack(side="left", padx=5)

        ttk.Label(excl_tab, text="Bedrooms", font=("", 10, "bold")).pack(anchor="w", pady=(15, 5))
        bed_frame = ttk.Frame(excl_tab)
        bed_frame.pack(anchor="w")
        ttk.Label(bed_frame, text="Min:").pack(side="left")
        self.min_beds_var = tk.IntVar(value=2)
        ttk.Spinbox(bed_frame, from_=1, to=6, textvariable=self.min_beds_var, width=5).pack(side="left", padx=(5, 15))
        ttk.Label(bed_frame, text="Max:").pack(side="left")
        self.max_beds_var = tk.IntVar(value=5)
        ttk.Spinbox(bed_frame, from_=1, to=10, textvariable=self.max_beds_var, width=5).pack(side="left", padx=5)

        # --- RIGHT COLUMN: Saved Locations ---
        right_frame = ttk.LabelFrame(middle_frame, text="📋 Saved Locations (click to open property searches)", padding="10")
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        # Treeview for saved locations
        columns = ("name", "your_commute", "partner_commute", "combined", "status")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Location")
        self.tree.heading("your_commute", text="You")
        self.tree.heading("partner_commute", text="Partner")
        self.tree.heading("combined", text="Combined")
        self.tree.heading("status", text="Status")

        self.tree.column("name", width=200)
        self.tree.column("your_commute", width=80)
        self.tree.column("partner_commute", width=80)
        self.tree.column("combined", width=80)
        self.tree.column("status", width=100)

        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Buttons below tree
        btn_frame = ttk.Frame(right_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.rightmove_btn = ttk.Button(btn_frame, text="🏠 Rightmove", command=self._open_rightmove, state="disabled")
        self.rightmove_btn.pack(side="left", padx=(0, 5))

        self.zoopla_btn = ttk.Button(btn_frame, text="🏡 Zoopla", command=self._open_zoopla, state="disabled")
        self.zoopla_btn.pack(side="left", padx=5)

        self.onthemarket_btn = ttk.Button(btn_frame, text="🏘️ OnTheMarket", command=self._open_onthemarket, state="disabled")
        self.onthemarket_btn.pack(side="left", padx=5)

        ttk.Button(btn_frame, text="🗑️ Remove", command=self._remove_selected).pack(side="left", padx=5)

        ttk.Button(btn_frame, text="📊 Export CSV", command=self._export_csv).pack(side="right")

        # === BOTTOM: Bulk Search ===
        bulk_frame = ttk.LabelFrame(main_frame, text="🔎 Bulk Search - Check Multiple Locations", padding="10")
        bulk_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(bulk_frame, text="Enter multiple postcodes/towns (one per line or comma-separated):").pack(anchor="w")

        bulk_input_frame = ttk.Frame(bulk_frame)
        bulk_input_frame.pack(fill="x", pady=5)

        self.bulk_text = tk.Text(bulk_input_frame, height=3, width=80)
        self.bulk_text.pack(side="left", fill="x", expand=True)
        self.bulk_text.insert("1.0", "e.g., ME4 5DL, DA11 0TA, Rochester, Strood, Chatham")

        bulk_btn_frame = ttk.Frame(bulk_input_frame)
        bulk_btn_frame.pack(side="left", padx=(10, 0))

        self.bulk_search_btn = ttk.Button(bulk_btn_frame, text="Check All", command=self._bulk_search)
        self.bulk_search_btn.pack(pady=2)

        self.bulk_progress_var = tk.StringVar(value="")
        ttk.Label(bulk_btn_frame, textvariable=self.bulk_progress_var).pack(pady=2)

    def _quick_search(self):
        """Search a single location"""
        location = self.location_var.get().strip()
        if not location:
            messagebox.showwarning("No Location", "Please enter a postcode or town name")
            return

        self.search_btn.config(state="disabled")
        self.result_var.set(f"Searching {location}...")
        self.root.update()

        # Run in background
        thread = threading.Thread(target=self._do_quick_search, args=(location,))
        thread.daemon = True
        thread.start()

    def _do_quick_search(self, location: str):
        """Perform the search (background thread)"""
        your_workplace = self.your_workplace_var.get()
        partner_workplace = self.partner_workplace_var.get()
        arrival_hour = self.arrival_hour_var.get()

        your_result = None
        partner_result = None

        # Try Google first
        try:
            your_result = self.google.get_commute_time(
                f"{location}, UK",
                f"{your_workplace}, London, UK",
                arrival_hour=arrival_hour
            )
        except Exception as e:
            print(f"Google error (your commute): {e}")

        try:
            partner_result = self.google.get_commute_time(
                f"{location}, UK",
                f"{partner_workplace}, London, UK",
                arrival_hour=arrival_hour
            )
        except Exception as e:
            print(f"Google error (partner commute): {e}")

        # Fall back to TfL if needed
        if not your_result:
            your_result = self.tfl.get_typical_commute_time(location, your_workplace, arrival_hour)
        if not partner_result:
            partner_result = self.tfl.get_typical_commute_time(location, partner_workplace, arrival_hour)

        # Build result
        result = SearchResult(name=location)

        if your_result:
            result.your_commute_mins = your_result['fastest_mins']
            result.your_changes = your_result.get('num_changes', 0)

        if partner_result:
            result.partner_commute_mins = partner_result['fastest_mins']
            result.partner_changes = partner_result.get('num_changes', 0)

        if result.your_commute_mins and result.partner_commute_mins:
            result.combined_mins = result.your_commute_mins + result.partner_commute_mins

        self.last_result = result

        # Update UI
        self.root.after(0, lambda: self._show_result(result))

    def _show_result(self, result: SearchResult):
        """Display search result"""
        self.search_btn.config(state="normal")

        if not result.your_commute_mins and not result.partner_commute_mins:
            self.result_var.set(f"❌ Could not find commute times for '{result.name}'. Try a more specific postcode or town name.")
            self.add_to_list_btn.config(state="disabled")
            return

        your_max = self.your_max_var.get()
        partner_max = self.partner_max_var.get()

        # Build result text
        lines = [f"📍 {result.name}:"]

        if result.your_commute_mins:
            status = "✅" if result.your_commute_mins <= your_max else "⚠️"
            lines.append(f"   {status} Your commute: {result.your_commute_mins} mins ({result.your_changes} changes)")

        if result.partner_commute_mins:
            status = "✅" if result.partner_commute_mins <= partner_max else "⚠️"
            lines.append(f"   {status} Partner commute: {result.partner_commute_mins} mins ({result.partner_changes} changes)")

        if result.combined_mins:
            lines.append(f"   📊 Combined: {result.combined_mins} mins")

        # Check if meets criteria
        meets_yours = result.your_commute_mins and result.your_commute_mins <= your_max
        meets_partner = result.partner_commute_mins and result.partner_commute_mins <= partner_max

        if meets_yours and meets_partner:
            lines.append(f"\n   🎉 MEETS YOUR CRITERIA! Click '+ Add to List' to save.")
            result.notes = "Meets criteria"
        elif meets_yours or meets_partner:
            lines.append(f"\n   ⚠️ Partially meets criteria (one commute too long)")
            result.notes = "Partial match"
        else:
            lines.append(f"\n   ❌ Both commutes exceed your limits")
            result.notes = "Too far"

        self.result_var.set("\n".join(lines))
        self.add_to_list_btn.config(state="normal")

    def _add_to_saved(self):
        """Add last result to saved list"""
        if not hasattr(self, 'last_result') or not self.last_result:
            return

        result = self.last_result

        # Check if already in list
        for r in self.saved_locations:
            if r.name.lower() == result.name.lower():
                messagebox.showinfo("Already Saved", f"{result.name} is already in your list")
                return

        self.saved_locations.append(result)
        self._refresh_tree()
        self._save_locations()

        messagebox.showinfo("Added", f"{result.name} added to your list!")

    def _refresh_tree(self):
        """Refresh the treeview with saved locations"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        your_max = self.your_max_var.get()
        partner_max = self.partner_max_var.get()

        for r in self.saved_locations:
            your_str = f"{r.your_commute_mins} mins" if r.your_commute_mins else "N/A"
            partner_str = f"{r.partner_commute_mins} mins" if r.partner_commute_mins else "N/A"
            combined_str = f"{r.combined_mins} mins" if r.combined_mins else "N/A"

            # Determine status
            meets_yours = r.your_commute_mins and r.your_commute_mins <= your_max
            meets_partner = r.partner_commute_mins and r.partner_commute_mins <= partner_max

            if meets_yours and meets_partner:
                status = "✅ Good"
            elif meets_yours or meets_partner:
                status = "⚠️ Partial"
            else:
                status = "❌ Too far"

            self.tree.insert("", "end", values=(r.name, your_str, partner_str, combined_str, status))

    def _on_select(self, event):
        """Handle selection"""
        selection = self.tree.selection()
        if selection:
            self.rightmove_btn.config(state="normal")
            self.zoopla_btn.config(state="normal")
            self.onthemarket_btn.config(state="normal")

    def _on_double_click(self, event):
        """Open all property sites on double-click"""
        self._open_rightmove()
        self._open_zoopla()

    def _get_selected_location(self) -> Optional[str]:
        """Get the selected location name"""
        selection = self.tree.selection()
        if not selection:
            return None
        item = self.tree.item(selection[0])
        return item["values"][0]

    def _generate_rightmove_url(self, location: str) -> str:
        """Generate Rightmove URL with filters"""
        # Try to extract postcode area or use location name
        loc_clean = location.upper().replace(" ", "")

        # Check if it looks like a postcode
        if len(loc_clean) >= 2 and loc_clean[0].isalpha():
            # Extract outcode (first part of postcode)
            outcode = ""
            for i, c in enumerate(loc_clean):
                if c.isdigit():
                    outcode = loc_clean[:i+1]
                    # Take up to first digit and one more char if letter follows
                    if i + 1 < len(loc_clean) and loc_clean[i+1].isalpha():
                        outcode = loc_clean[:i+2]
                    break
            if not outcode:
                outcode = loc_clean[:3]
        else:
            outcode = location.replace(" ", "-").lower()

        url = f"https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=OUTCODE%5E{outcode}&searchType=SALE"

        # Property types
        types = []
        if self.detached_var.get(): types.append("detached")
        if self.semi_var.get(): types.append("semi-detached")
        if self.terraced_var.get(): types.append("terraced")
        if self.bungalow_var.get(): types.append("bungalow")
        if types:
            url += f"&propertyTypes={','.join(types)}"

        # Must have
        must_have = []
        if self.garden_var.get(): must_have.append("garden")
        if self.parking_var.get(): must_have.append("parking")
        if must_have:
            url += f"&mustHave={','.join(must_have)}"

        # Don't show
        dont_show = []
        if self.no_new_var.get(): dont_show.append("newHome")
        if self.no_retirement_var.get(): dont_show.append("retirement")
        if self.no_shared_var.get(): dont_show.append("sharedOwnership")
        if self.no_auction_var.get(): dont_show.append("auction")
        if dont_show:
            url += f"&dontShow={','.join(dont_show)}"

        # Tenure
        if self.freehold_var.get():
            url += "&tenure=freehold"

        # Price
        try:
            if self.min_price_var.get():
                url += f"&minPrice={int(self.min_price_var.get().replace(',', ''))}"
            if self.max_price_var.get():
                url += f"&maxPrice={int(self.max_price_var.get().replace(',', ''))}"
        except ValueError:
            pass

        # Bedrooms
        url += f"&minBedrooms={self.min_beds_var.get()}&maxBedrooms={self.max_beds_var.get()}"

        return url

    def _generate_zoopla_url(self, location: str) -> str:
        """Generate Zoopla URL with filters"""
        loc_encoded = location.lower().replace(" ", "-")

        url = f"https://www.zoopla.co.uk/for-sale/property/{loc_encoded}/?q={location.replace(' ', '%20')}"

        # Property types
        types = []
        if self.detached_var.get(): types.append("detached")
        if self.semi_var.get(): types.append("semi_detached")
        if self.terraced_var.get(): types.append("terraced")
        if self.bungalow_var.get(): types.append("bungalow")
        if types:
            url += f"&property_sub_type={','.join(types)}"

        # Features
        if self.garden_var.get(): url += "&feature=has_garden"
        if self.parking_var.get(): url += "&feature=has_parking"

        # Chain free
        if self.chain_free_var.get(): url += "&is_chain_free=true"

        # Tenure
        if self.freehold_var.get(): url += "&tenure=freehold"

        # Exclusions
        if self.no_new_var.get(): url += "&new_homes=exclude"
        if self.no_retirement_var.get(): url += "&is_retirement_home=false"
        if self.no_shared_var.get(): url += "&is_shared_ownership=false"
        if self.no_auction_var.get(): url += "&is_auction=false"

        # Price
        try:
            if self.min_price_var.get():
                url += f"&price_min={int(self.min_price_var.get().replace(',', ''))}"
            if self.max_price_var.get():
                url += f"&price_max={int(self.max_price_var.get().replace(',', ''))}"
        except ValueError:
            pass

        # Bedrooms
        url += f"&beds_min={self.min_beds_var.get()}&beds_max={self.max_beds_var.get()}"

        return url

    def _generate_onthemarket_url(self, location: str) -> str:
        """Generate OnTheMarket URL"""
        loc_encoded = location.lower().replace(" ", "-")
        url = f"https://www.onthemarket.com/for-sale/property/{loc_encoded}/?view=grid"

        # Bedrooms
        url += f"&min-bedrooms={self.min_beds_var.get()}&max-bedrooms={self.max_beds_var.get()}"

        # Price
        try:
            if self.min_price_var.get():
                url += f"&min-price={int(self.min_price_var.get().replace(',', ''))}"
            if self.max_price_var.get():
                url += f"&max-price={int(self.max_price_var.get().replace(',', ''))}"
        except ValueError:
            pass

        if self.no_retirement_var.get():
            url += "&retirement=false"

        return url

    def _open_rightmove(self):
        """Open Rightmove"""
        location = self._get_selected_location()
        if location:
            webbrowser.open(self._generate_rightmove_url(location))

    def _open_zoopla(self):
        """Open Zoopla"""
        location = self._get_selected_location()
        if location:
            webbrowser.open(self._generate_zoopla_url(location))

    def _open_onthemarket(self):
        """Open OnTheMarket"""
        location = self._get_selected_location()
        if location:
            webbrowser.open(self._generate_onthemarket_url(location))

    def _remove_selected(self):
        """Remove selected location"""
        location = self._get_selected_location()
        if location:
            self.saved_locations = [r for r in self.saved_locations if r.name != location]
            self._refresh_tree()
            self._save_locations()

    def _bulk_search(self):
        """Search multiple locations"""
        text = self.bulk_text.get("1.0", "end").strip()
        if not text or text.startswith("e.g.,"):
            messagebox.showwarning("No Locations", "Enter some postcodes or towns to search")
            return

        # Parse locations
        locations = []
        for part in text.replace("\n", ",").split(","):
            loc = part.strip()
            if loc and not loc.startswith("e.g."):
                locations.append(loc)

        if not locations:
            return

        self.bulk_search_btn.config(state="disabled")
        thread = threading.Thread(target=self._do_bulk_search, args=(locations,))
        thread.daemon = True
        thread.start()

    def _do_bulk_search(self, locations: List[str]):
        """Perform bulk search"""
        total = len(locations)
        your_max = self.your_max_var.get()
        partner_max = self.partner_max_var.get()
        found_count = 0

        for i, location in enumerate(locations):
            self.root.after(0, lambda l=location, n=i+1, t=total:
                self.bulk_progress_var.set(f"Checking {n}/{t}: {l}"))

            result = SearchResult(name=location)

            # Try Google
            try:
                your_result = self.google.get_commute_time(
                    f"{location}, UK",
                    f"{self.your_workplace_var.get()}, London, UK",
                    arrival_hour=self.arrival_hour_var.get()
                )
                if your_result:
                    result.your_commute_mins = your_result['fastest_mins']
                    result.your_changes = your_result.get('num_changes', 0)
            except:
                pass

            try:
                partner_result = self.google.get_commute_time(
                    f"{location}, UK",
                    f"{self.partner_workplace_var.get()}, London, UK",
                    arrival_hour=self.arrival_hour_var.get()
                )
                if partner_result:
                    result.partner_commute_mins = partner_result['fastest_mins']
                    result.partner_changes = partner_result.get('num_changes', 0)
            except:
                pass

            if result.your_commute_mins and result.partner_commute_mins:
                result.combined_mins = result.your_commute_mins + result.partner_commute_mins

                # Check if meets criteria
                if result.your_commute_mins <= your_max and result.partner_commute_mins <= partner_max:
                    # Add to saved if not already there
                    exists = any(r.name.lower() == result.name.lower() for r in self.saved_locations)
                    if not exists:
                        self.saved_locations.append(result)
                        found_count += 1

        self.root.after(0, lambda: self._finish_bulk_search(found_count, total))

    def _finish_bulk_search(self, found: int, total: int):
        """Finish bulk search"""
        self.bulk_search_btn.config(state="normal")
        self.bulk_progress_var.set(f"Done! Found {found}/{total} matching locations")
        self._refresh_tree()
        self._save_locations()

    def _save_locations(self):
        """Save locations to file"""
        save_file = Path(__file__).parent / "saved_locations.json"
        data = []
        for r in self.saved_locations:
            data.append({
                'name': r.name,
                'your_commute_mins': r.your_commute_mins,
                'partner_commute_mins': r.partner_commute_mins,
                'combined_mins': r.combined_mins,
                'your_changes': r.your_changes,
                'partner_changes': r.partner_changes,
                'notes': r.notes,
            })
        try:
            with open(save_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving: {e}")

    def _load_saved_locations(self):
        """Load saved locations"""
        save_file = Path(__file__).parent / "saved_locations.json"
        if save_file.exists():
            try:
                with open(save_file, 'r') as f:
                    data = json.load(f)
                for item in data:
                    self.saved_locations.append(SearchResult(
                        name=item['name'],
                        your_commute_mins=item.get('your_commute_mins'),
                        partner_commute_mins=item.get('partner_commute_mins'),
                        combined_mins=item.get('combined_mins'),
                        your_changes=item.get('your_changes', 0),
                        partner_changes=item.get('partner_changes', 0),
                        notes=item.get('notes', ''),
                    ))
                self._refresh_tree()
            except Exception as e:
                print(f"Error loading: {e}")

    def _export_csv(self):
        """Export to CSV"""
        if not self.saved_locations:
            messagebox.showwarning("No Data", "No saved locations to export")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfilename="property_search_locations.csv"
        )

        if filename:
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Location', 'Your Commute (mins)', 'Partner Commute (mins)',
                                'Combined (mins)', 'Your Changes', 'Partner Changes', 'Notes'])
                for r in self.saved_locations:
                    writer.writerow([r.name, r.your_commute_mins, r.partner_commute_mins,
                                   r.combined_mins, r.your_changes, r.partner_changes, r.notes])
            messagebox.showinfo("Exported", f"Saved to {filename}")

    def run(self):
        """Run the app"""
        self.root.mainloop()


def main():
    app = PropertySearchGUI()
    app.run()


if __name__ == "__main__":
    main()
