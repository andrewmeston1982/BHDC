#!/usr/bin/env python3
"""
Commute Time Property Search - GUI Application

A visual interface for finding properties based on actual commute times,
with comprehensive property filters for Rightmove and Zoopla.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import webbrowser
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
from pathlib import Path

from commute_search import CommuteSearch, CommuteResult, GOOGLE_MAPS_API_KEY
from locations import ALL_LOCATIONS, Location, distance_from_london


@dataclass
class PropertyFilters:
    """Property search filters"""
    # Property types
    detached: bool = True
    semi_detached: bool = True
    terraced: bool = True
    bungalow: bool = True

    # Must have
    garden: bool = True
    parking: bool = True
    driveway_garage: bool = False

    # Tenure
    freehold_only: bool = True

    # Exclusions
    no_new_homes: bool = True
    no_retirement: bool = True
    no_auction: bool = True
    no_shared_ownership: bool = True

    # Special
    chain_free_only: bool = False

    # Price
    min_price: Optional[int] = None
    max_price: Optional[int] = None

    # Bedrooms
    min_beds: int = 2
    max_beds: int = 5


class PropertySearchGUI:
    """Main GUI Application"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Commute Time Property Search")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Configure grid weights for resizing
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Search engine
        self.search = None
        self.results: List[CommuteResult] = []
        self.filters = PropertyFilters()

        # Create UI
        self._create_widgets()
        self._load_settings()

    def _create_widgets(self):
        """Create all GUI widgets"""

        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        # === LEFT PANEL: Settings & Filters ===
        left_panel = ttk.Frame(main_frame, width=350)
        left_panel.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 10))
        left_panel.grid_propagate(False)

        # Notebook for tabs
        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill="both", expand=True)

        # --- Tab 1: Commute Settings ---
        commute_tab = ttk.Frame(notebook, padding="10")
        notebook.add(commute_tab, text="Commute")

        # Your workplace
        ttk.Label(commute_tab, text="Your Workplace", font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))

        ttk.Label(commute_tab, text="Postcode:").pack(anchor="w")
        self.your_workplace_var = tk.StringVar(value="W1T 3JF")
        ttk.Entry(commute_tab, textvariable=self.your_workplace_var, width=20).pack(anchor="w", pady=(0, 5))

        ttk.Label(commute_tab, text="Max commute (mins):").pack(anchor="w")
        self.your_max_var = tk.IntVar(value=75)
        ttk.Spinbox(commute_tab, from_=15, to=120, textvariable=self.your_max_var, width=10).pack(anchor="w", pady=(0, 10))

        # Wife's workplace
        ttk.Label(commute_tab, text="Partner's Workplace", font=("", 10, "bold")).pack(anchor="w", pady=(10, 5))

        ttk.Label(commute_tab, text="Postcode:").pack(anchor="w")
        self.wife_workplace_var = tk.StringVar(value="E8 1EA")
        ttk.Entry(commute_tab, textvariable=self.wife_workplace_var, width=20).pack(anchor="w", pady=(0, 5))

        ttk.Label(commute_tab, text="Max commute (mins):").pack(anchor="w")
        self.wife_max_var = tk.IntVar(value=90)
        ttk.Spinbox(commute_tab, from_=15, to=120, textvariable=self.wife_max_var, width=10).pack(anchor="w", pady=(0, 10))

        # Arrival time
        ttk.Label(commute_tab, text="Arrival Time", font=("", 10, "bold")).pack(anchor="w", pady=(10, 5))
        ttk.Label(commute_tab, text="Arrive at work by:").pack(anchor="w")
        self.arrival_hour_var = tk.IntVar(value=9)
        ttk.Spinbox(commute_tab, from_=6, to=11, textvariable=self.arrival_hour_var, width=10).pack(anchor="w")

        # API Settings
        ttk.Label(commute_tab, text="API Settings", font=("", 10, "bold")).pack(anchor="w", pady=(20, 5))
        self.use_google_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(commute_tab, text="Use Google Maps API", variable=self.use_google_var).pack(anchor="w")
        self.refresh_cache_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(commute_tab, text="Refresh cached data", variable=self.refresh_cache_var).pack(anchor="w")

        # --- Tab 2: Property Filters ---
        property_tab = ttk.Frame(notebook, padding="10")
        notebook.add(property_tab, text="Property")

        # Property Types
        ttk.Label(property_tab, text="Property Types", font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))

        self.detached_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(property_tab, text="Detached", variable=self.detached_var).pack(anchor="w")

        self.semi_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(property_tab, text="Semi-detached", variable=self.semi_var).pack(anchor="w")

        self.terraced_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(property_tab, text="Terraced", variable=self.terraced_var).pack(anchor="w")

        self.bungalow_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(property_tab, text="Bungalow", variable=self.bungalow_var).pack(anchor="w")

        # Must Have
        ttk.Label(property_tab, text="Must Have", font=("", 10, "bold")).pack(anchor="w", pady=(15, 5))

        self.garden_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(property_tab, text="Garden", variable=self.garden_var).pack(anchor="w")

        self.parking_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(property_tab, text="Parking", variable=self.parking_var).pack(anchor="w")

        self.garage_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(property_tab, text="Garage/Driveway", variable=self.garage_var).pack(anchor="w")

        # Tenure
        ttk.Label(property_tab, text="Tenure", font=("", 10, "bold")).pack(anchor="w", pady=(15, 5))

        self.freehold_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(property_tab, text="Freehold only", variable=self.freehold_var).pack(anchor="w")

        # Chain
        ttk.Label(property_tab, text="Chain Status", font=("", 10, "bold")).pack(anchor="w", pady=(15, 5))

        self.chain_free_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(property_tab, text="Chain-free only (Zoopla)", variable=self.chain_free_var).pack(anchor="w")

        # --- Tab 3: Exclusions ---
        exclude_tab = ttk.Frame(notebook, padding="10")
        notebook.add(exclude_tab, text="Exclude")

        ttk.Label(exclude_tab, text="Don't Show", font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))

        self.no_new_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(exclude_tab, text="New homes", variable=self.no_new_var).pack(anchor="w")

        self.no_retirement_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(exclude_tab, text="Retirement homes", variable=self.no_retirement_var).pack(anchor="w")

        self.no_auction_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(exclude_tab, text="Auction properties", variable=self.no_auction_var).pack(anchor="w")

        self.no_shared_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(exclude_tab, text="Shared ownership", variable=self.no_shared_var).pack(anchor="w")

        # Price Range
        ttk.Label(exclude_tab, text="Price Range", font=("", 10, "bold")).pack(anchor="w", pady=(20, 5))

        ttk.Label(exclude_tab, text="Min price (£):").pack(anchor="w")
        self.min_price_var = tk.StringVar(value="")
        ttk.Entry(exclude_tab, textvariable=self.min_price_var, width=15).pack(anchor="w", pady=(0, 5))

        ttk.Label(exclude_tab, text="Max price (£):").pack(anchor="w")
        self.max_price_var = tk.StringVar(value="")
        ttk.Entry(exclude_tab, textvariable=self.max_price_var, width=15).pack(anchor="w", pady=(0, 5))

        # Bedrooms
        ttk.Label(exclude_tab, text="Bedrooms", font=("", 10, "bold")).pack(anchor="w", pady=(20, 5))

        bed_frame = ttk.Frame(exclude_tab)
        bed_frame.pack(anchor="w")

        ttk.Label(bed_frame, text="Min:").pack(side="left")
        self.min_beds_var = tk.IntVar(value=2)
        ttk.Spinbox(bed_frame, from_=1, to=6, textvariable=self.min_beds_var, width=5).pack(side="left", padx=(5, 15))

        ttk.Label(bed_frame, text="Max:").pack(side="left")
        self.max_beds_var = tk.IntVar(value=5)
        ttk.Spinbox(bed_frame, from_=1, to=10, textvariable=self.max_beds_var, width=5).pack(side="left", padx=5)

        # === TOP RIGHT: Search Button & Progress ===
        top_right = ttk.Frame(main_frame)
        top_right.grid(row=0, column=1, sticky="ew", pady=(0, 10))

        self.search_btn = ttk.Button(top_right, text="🔍 Search Locations", command=self._start_search)
        self.search_btn.pack(side="left")

        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(top_right, textvariable=self.progress_var).pack(side="left", padx=20)

        self.progress_bar = ttk.Progressbar(top_right, mode="determinate", length=300)
        self.progress_bar.pack(side="left", fill="x", expand=True)

        # === MIDDLE RIGHT: Results List ===
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="5")
        results_frame.grid(row=1, column=1, sticky="nsew", pady=(0, 10))
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)

        # Treeview for results
        columns = ("name", "your_commute", "wife_commute", "combined", "distance", "gem_score", "price")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Location")
        self.tree.heading("your_commute", text="Your Commute")
        self.tree.heading("wife_commute", text="Partner Commute")
        self.tree.heading("combined", text="Combined")
        self.tree.heading("distance", text="Distance")
        self.tree.heading("gem_score", text="Gem Score")
        self.tree.heading("price", text="Avg Price")

        self.tree.column("name", width=150)
        self.tree.column("your_commute", width=100)
        self.tree.column("wife_commute", width=110)
        self.tree.column("combined", width=80)
        self.tree.column("distance", width=80)
        self.tree.column("gem_score", width=80)
        self.tree.column("price", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # === BOTTOM RIGHT: Details & Links ===
        details_frame = ttk.LabelFrame(main_frame, text="Property Search Links", padding="10")
        details_frame.grid(row=2, column=1, sticky="nsew")
        details_frame.grid_columnconfigure(0, weight=1)

        # Selected location info
        self.selected_label = ttk.Label(details_frame, text="Select a location to see property search links", font=("", 10))
        self.selected_label.pack(anchor="w", pady=(0, 10))

        # Notes
        self.notes_text = scrolledtext.ScrolledText(details_frame, height=4, wrap="word", state="disabled")
        self.notes_text.pack(fill="x", pady=(0, 10))

        # Buttons frame
        btn_frame = ttk.Frame(details_frame)
        btn_frame.pack(fill="x")

        self.rightmove_btn = ttk.Button(btn_frame, text="🏠 Open Rightmove", command=self._open_rightmove, state="disabled")
        self.rightmove_btn.pack(side="left", padx=(0, 10))

        self.zoopla_btn = ttk.Button(btn_frame, text="🏡 Open Zoopla", command=self._open_zoopla, state="disabled")
        self.zoopla_btn.pack(side="left", padx=(0, 10))

        self.onthemarket_btn = ttk.Button(btn_frame, text="🏘️ Open OnTheMarket", command=self._open_onthemarket, state="disabled")
        self.onthemarket_btn.pack(side="left")

        # Export button
        ttk.Button(btn_frame, text="📊 Export to CSV", command=self._export_csv).pack(side="right")

    def _get_filters(self) -> PropertyFilters:
        """Get current filter settings"""
        min_price = None
        max_price = None
        try:
            if self.min_price_var.get():
                min_price = int(self.min_price_var.get().replace(",", "").replace("£", ""))
            if self.max_price_var.get():
                max_price = int(self.max_price_var.get().replace(",", "").replace("£", ""))
        except ValueError:
            pass

        return PropertyFilters(
            detached=self.detached_var.get(),
            semi_detached=self.semi_var.get(),
            terraced=self.terraced_var.get(),
            bungalow=self.bungalow_var.get(),
            garden=self.garden_var.get(),
            parking=self.parking_var.get(),
            driveway_garage=self.garage_var.get(),
            freehold_only=self.freehold_var.get(),
            no_new_homes=self.no_new_var.get(),
            no_retirement=self.no_retirement_var.get(),
            no_auction=self.no_auction_var.get(),
            no_shared_ownership=self.no_shared_var.get(),
            chain_free_only=self.chain_free_var.get(),
            min_price=min_price,
            max_price=max_price,
            min_beds=self.min_beds_var.get(),
            max_beds=self.max_beds_var.get(),
        )

    def _generate_rightmove_url(self, location: Location) -> str:
        """Generate Rightmove URL with all filters"""
        filters = self._get_filters()
        outcode = location.postcode_area.split()[0].upper()

        # Base URL
        url = f"https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=OUTCODE%5E{outcode}"

        # Property types
        types = []
        if filters.detached:
            types.append("detached")
        if filters.semi_detached:
            types.append("semi-detached")
        if filters.terraced:
            types.append("terraced")
        if filters.bungalow:
            types.append("bungalow")
        if types:
            url += f"&propertyTypes={','.join(types)}"

        # Must have
        must_have = []
        if filters.garden:
            must_have.append("garden")
        if filters.parking:
            must_have.append("parking")
        if must_have:
            url += f"&mustHave={','.join(must_have)}"

        # Don't show
        dont_show = []
        if filters.no_new_homes:
            dont_show.append("newHome")
        if filters.no_retirement:
            dont_show.append("retirement")
        if filters.no_shared_ownership:
            dont_show.append("sharedOwnership")
        if filters.no_auction:
            dont_show.append("auction")
        if dont_show:
            url += f"&dontShow={','.join(dont_show)}"

        # Tenure
        if filters.freehold_only:
            url += "&tenure=freehold"

        # Price
        if filters.min_price:
            url += f"&minPrice={filters.min_price}"
        if filters.max_price:
            url += f"&maxPrice={filters.max_price}"

        # Bedrooms
        url += f"&minBedrooms={filters.min_beds}&maxBedrooms={filters.max_beds}"

        return url

    def _generate_zoopla_url(self, location: Location) -> str:
        """Generate Zoopla URL with all filters"""
        filters = self._get_filters()
        outcode = location.postcode_area.split()[0].lower()

        # Base URL
        url = f"https://www.zoopla.co.uk/for-sale/property/{outcode}/?q={location.name.replace(' ', '%20')}"

        # Property types
        types = []
        if filters.detached:
            types.append("detached")
        if filters.semi_detached:
            types.append("semi_detached")
        if filters.terraced:
            types.append("terraced")
        if filters.bungalow:
            types.append("bungalow")
        if types:
            url += f"&property_sub_type={','.join(types)}"

        # Must have
        if filters.garden:
            url += "&feature=has_garden"
        if filters.parking:
            url += "&feature=has_parking"

        # Chain free (Zoopla specific!)
        if filters.chain_free_only:
            url += "&is_chain_free=true"

        # Tenure
        if filters.freehold_only:
            url += "&tenure=freehold"

        # Exclusions
        if filters.no_new_homes:
            url += "&new_homes=exclude"
        if filters.no_retirement:
            url += "&is_retirement_home=false"
        if filters.no_shared_ownership:
            url += "&is_shared_ownership=false"
        if filters.no_auction:
            url += "&is_auction=false"

        # Price
        if filters.min_price:
            url += f"&price_min={filters.min_price}"
        if filters.max_price:
            url += f"&price_max={filters.max_price}"

        # Bedrooms
        url += f"&beds_min={filters.min_beds}&beds_max={filters.max_beds}"

        return url

    def _generate_onthemarket_url(self, location: Location) -> str:
        """Generate OnTheMarket URL with filters"""
        filters = self._get_filters()

        # OnTheMarket uses location search
        url = f"https://www.onthemarket.com/for-sale/property/{location.name.lower().replace(' ', '-')}/"

        # Add basic filters
        url += "?"

        # Property types
        types = []
        if filters.detached:
            types.append("detached")
        if filters.semi_detached:
            types.append("semi-detached")
        if filters.terraced:
            types.append("terraced")
        if filters.bungalow:
            types.append("bungalow")
        if types:
            url += f"&property-types={','.join(types)}"

        # Price
        if filters.min_price:
            url += f"&min-price={filters.min_price}"
        if filters.max_price:
            url += f"&max-price={filters.max_price}"

        # Bedrooms
        url += f"&min-bedrooms={filters.min_beds}&max-bedrooms={filters.max_beds}"

        # Retirement
        if filters.no_retirement:
            url += "&retirement=false"

        return url

    def _start_search(self):
        """Start the search in a background thread"""
        self.search_btn.config(state="disabled")
        self.progress_bar["value"] = 0
        self.progress_var.set("Initializing...")

        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Start search in background thread
        thread = threading.Thread(target=self._run_search)
        thread.daemon = True
        thread.start()

    def _run_search(self):
        """Run the search (in background thread)"""
        try:
            # Initialize search engine
            use_google = self.use_google_var.get()
            self.search = CommuteSearch(use_google=use_google)

            # Update workplace settings
            self.search.YOUR_WORKPLACE = self.your_workplace_var.get()
            self.search.WIFE_WORKPLACE = self.wife_workplace_var.get()

            # Clear cache if requested
            if self.refresh_cache_var.get():
                self.search.cache = {}

            total = len(ALL_LOCATIONS)

            def progress_callback(current, total, name):
                self.root.after(0, lambda: self._update_progress(current, total, name))

            # Run search
            self.results = self.search.search_all_locations(
                your_arrival_hour=self.arrival_hour_var.get(),
                wife_arrival_hour=self.arrival_hour_var.get(),
                progress_callback=progress_callback
            )

            # Filter results
            filtered = self.search.filter_results(
                your_max_mins=self.your_max_var.get(),
                wife_max_mins=self.wife_max_var.get(),
            )

            # Sort by your commute
            filtered = self.search.sort_results(filtered, by="your_commute")

            # Update UI
            self.root.after(0, lambda: self._display_results(filtered))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, lambda: self.search_btn.config(state="normal"))

    def _update_progress(self, current: int, total: int, name: str):
        """Update progress bar"""
        percent = (current / total) * 100
        self.progress_bar["value"] = percent
        self.progress_var.set(f"Checking {name}... ({current}/{total})")

    def _display_results(self, results: List[CommuteResult]):
        """Display results in the treeview"""
        self.progress_var.set(f"Found {len(results)} matching locations")
        self.progress_bar["value"] = 100

        self.filtered_results = results

        for r in results:
            gem_display = "★" * r.hidden_gem_score + "☆" * (5 - r.hidden_gem_score)
            price_display = f"£{r.location.avg_price_2bed:,}" if r.location.avg_price_2bed else "N/A"

            self.tree.insert("", "end", values=(
                r.location.name,
                f"{r.your_commute_mins} mins",
                f"{r.wife_commute_mins} mins",
                f"{r.combined_mins} mins",
                f"{r.distance_km:.1f} km",
                gem_display,
                price_display,
            ))

    def _on_select(self, event):
        """Handle selection in treeview"""
        selection = self.tree.selection()
        if not selection:
            return

        # Get selected item
        item = self.tree.item(selection[0])
        name = item["values"][0]

        # Find the result
        result = None
        for r in self.filtered_results:
            if r.location.name == name:
                result = r
                break

        if result:
            self.selected_result = result
            self.selected_label.config(text=f"📍 {result.location.name} - {result.location.rail_line}")

            # Update notes
            self.notes_text.config(state="normal")
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", result.location.notes)
            self.notes_text.config(state="disabled")

            # Enable buttons
            self.rightmove_btn.config(state="normal")
            self.zoopla_btn.config(state="normal")
            self.onthemarket_btn.config(state="normal")

    def _open_rightmove(self):
        """Open Rightmove search in browser"""
        if hasattr(self, 'selected_result'):
            url = self._generate_rightmove_url(self.selected_result.location)
            webbrowser.open(url)

    def _open_zoopla(self):
        """Open Zoopla search in browser"""
        if hasattr(self, 'selected_result'):
            url = self._generate_zoopla_url(self.selected_result.location)
            webbrowser.open(url)

    def _open_onthemarket(self):
        """Open OnTheMarket search in browser"""
        if hasattr(self, 'selected_result'):
            url = self._generate_onthemarket_url(self.selected_result.location)
            webbrowser.open(url)

    def _export_csv(self):
        """Export results to CSV"""
        if not hasattr(self, 'filtered_results') or not self.filtered_results:
            messagebox.showwarning("No Results", "Run a search first!")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfilename="commute_results.csv"
        )

        if filename:
            if self.search:
                self.search.export_csv(self.filtered_results, filename)
                messagebox.showinfo("Exported", f"Results saved to {filename}")

    def _load_settings(self):
        """Load saved settings"""
        settings_file = Path(__file__).parent / "gui_settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.your_workplace_var.set(settings.get('your_workplace', 'W1T 3JF'))
                    self.wife_workplace_var.set(settings.get('wife_workplace', 'E8 1EA'))
                    self.your_max_var.set(settings.get('your_max', 75))
                    self.wife_max_var.set(settings.get('wife_max', 90))
            except:
                pass

    def _save_settings(self):
        """Save settings for next time"""
        settings_file = Path(__file__).parent / "gui_settings.json"
        settings = {
            'your_workplace': self.your_workplace_var.get(),
            'wife_workplace': self.wife_workplace_var.get(),
            'your_max': self.your_max_var.get(),
            'wife_max': self.wife_max_var.get(),
        }
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f)
        except:
            pass

    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        """Handle window close"""
        self._save_settings()
        self.root.destroy()


def main():
    app = PropertySearchGUI()
    app.run()


if __name__ == "__main__":
    main()
