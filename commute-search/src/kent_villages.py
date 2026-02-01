"""
Kent Villages and Towns Database

Places that could be within driving distance of hub stations like Ebbsfleet.
These are the hidden gems - no direct fast train, but driveable to one.
"""

# Hub stations with their coordinates
HUB_STATIONS = {
    "Ebbsfleet International": (51.443, 0.321),
    "Stratford International": (51.545, -0.009),
    "Ashford International": (51.144, 0.876),
    "Dartford": (51.447, 0.219),
    "Gravesend": (51.442, 0.368),
}

# Kent villages and towns - potential driving destinations
# Format: (name, postcode, lat, lon)
# These are places WITHOUT their own fast train links but near major stations

KENT_VILLAGES = [
    # === South of Gravesend / Ebbsfleet ===
    ("Meopham", "DA13", 51.388, 0.367),
    ("Sole Street", "DA13", 51.378, 0.390),
    ("Cobham (Kent)", "DA12", 51.402, 0.407),
    ("Luddesdown", "DA13", 51.375, 0.412),
    ("Harvel", "DA13", 51.360, 0.410),
    ("Vigo Village", "DA13", 51.355, 0.380),
    ("Culverstone Green", "DA13", 51.350, 0.395),

    # === Longfield / Hartley area ===
    ("Longfield", "DA3", 51.395, 0.300),
    ("Hartley", "DA3", 51.385, 0.320),
    ("New Ash Green", "DA3", 51.370, 0.300),
    ("Ash (Kent)", "DA3", 51.360, 0.280),
    ("Ridley", "DA3", 51.365, 0.310),
    ("Fawkham", "DA3", 51.375, 0.290),
    ("West Kingsdown", "TN15", 51.345, 0.265),

    # === Shorne / Higham area ===
    ("Shorne", "DA12", 51.420, 0.420),
    ("Shorne Ridgeway", "DA12", 51.410, 0.430),
    ("Higham", "ME3", 51.425, 0.455),
    ("Lower Higham", "ME3", 51.435, 0.470),
    ("Chalk", "DA12", 51.430, 0.395),
    ("Riverview Park", "DA12", 51.435, 0.385),

    # === Medway area (cheaper) ===
    ("Strood", "ME2", 51.393, 0.478),
    ("Frindsbury", "ME2", 51.400, 0.495),
    ("Wainscott", "ME2", 51.410, 0.510),
    ("Hoo St Werburgh", "ME3", 51.420, 0.545),
    ("High Halstow", "ME3", 51.455, 0.530),
    ("Cliffe", "ME3", 51.465, 0.485),
    ("Cliffe Woods", "ME3", 51.450, 0.495),
    ("Cooling", "ME3", 51.470, 0.520),
    ("Allhallows", "ME3", 51.475, 0.630),
    ("Grain", "ME3", 51.450, 0.710),
    ("Stoke (Kent)", "ME3", 51.460, 0.595),

    # === Cuxton / Halling valley ===
    ("Cuxton", "ME2", 51.375, 0.460),
    ("Halling", "ME2", 51.360, 0.450),
    ("Upper Halling", "ME2", 51.355, 0.445),
    ("Wouldham", "ME1", 51.350, 0.465),
    ("Burham", "ME1", 51.340, 0.475),
    ("Eccles", "ME20", 51.325, 0.485),

    # === Snodland / Aylesford area ===
    ("Snodland", "ME6", 51.330, 0.450),
    ("Larkfield", "ME20", 51.305, 0.440),
    ("Aylesford", "ME20", 51.300, 0.475),
    ("Ditton", "ME20", 51.295, 0.455),
    ("East Malling", "ME19", 51.290, 0.435),
    ("West Malling", "ME19", 51.290, 0.410),
    ("Kings Hill", "ME19", 51.275, 0.400),
    ("Leybourne", "ME19", 51.300, 0.420),

    # === Blue Bell Hill / Walderslade ===
    ("Blue Bell Hill", "ME5", 51.335, 0.505),
    ("Walderslade", "ME5", 51.345, 0.530),
    ("Lordswood", "ME5", 51.340, 0.545),
    ("Princes Park", "ME5", 51.355, 0.540),

    # === Rochester outskirts ===
    ("Borstal", "ME1", 51.380, 0.505),
    ("Nashenden", "ME1", 51.370, 0.495),

    # === South towards Maidstone ===
    ("Boxley", "ME14", 51.295, 0.535),
    ("Sandling", "ME14", 51.280, 0.520),
    ("Penenden Heath", "ME14", 51.285, 0.515),
    ("Bearsted", "ME14", 51.270, 0.570),
    ("Thurnham", "ME14", 51.285, 0.575),
    ("Hollingbourne", "ME17", 51.265, 0.630),
    ("Harrietsham", "ME17", 51.245, 0.670),
    ("Lenham", "ME17", 51.235, 0.715),

    # === Wrotham / Borough Green ===
    ("Wrotham", "TN15", 51.320, 0.310),
    ("Wrotham Heath", "TN15", 51.305, 0.295),
    ("Borough Green", "TN15", 51.295, 0.305),
    ("Platt", "TN15", 51.280, 0.315),
    ("Plaxtol", "TN15", 51.265, 0.330),
    ("Ightham", "TN15", 51.280, 0.285),
    ("Seal", "TN15", 51.275, 0.235),

    # === Sevenoaks area (pricier but options) ===
    ("Kemsing", "TN15", 51.295, 0.240),
    ("Otford", "TN14", 51.310, 0.195),
    ("Shoreham (Kent)", "TN14", 51.325, 0.185),
    ("Eynsford", "DA4", 51.360, 0.210),
    ("Farningham", "DA4", 51.375, 0.220),
    ("Horton Kirby", "DA4", 51.385, 0.235),
    ("South Darenth", "DA4", 51.395, 0.240),
    ("Sutton at Hone", "DA4", 51.415, 0.230),
    ("Swanley Village", "BR8", 51.400, 0.175),
    ("Crockenhill", "BR8", 51.375, 0.160),

    # === Essex side (for comparison) ===
    ("South Ockendon", "RM15", 51.515, 0.300),
    ("North Stifford", "RM16", 51.490, 0.335),
    ("Orsett", "RM16", 51.505, 0.365),
    ("Bulphan", "RM14", 51.535, 0.355),
    ("Horndon on the Hill", "SS17", 51.510, 0.400),
    ("Stanford le Hope", "SS17", 51.515, 0.420),
    ("Corringham", "SS17", 51.515, 0.445),
    ("Fobbing", "SS17", 51.520, 0.470),

    # === Further into Kent (longer drive but cheaper) ===
    ("Paddock Wood", "TN12", 51.185, 0.390),
    ("Five Oak Green", "TN12", 51.195, 0.375),
    ("Capel", "TN12", 51.195, 0.345),
    ("Tudeley", "TN11", 51.200, 0.330),
    ("Tonbridge outskirts", "TN9", 51.195, 0.275),
    ("Hadlow", "TN11", 51.220, 0.335),
    ("East Peckham", "TN12", 51.220, 0.385),
    ("Wateringbury", "ME18", 51.255, 0.415),
    ("Teston", "ME18", 51.265, 0.430),
    ("Barming", "ME16", 51.275, 0.480),

    # === Sittingbourne direction ===
    ("Bobbing", "ME9", 51.355, 0.695),
    ("Iwade", "ME9", 51.385, 0.720),
    ("Kemsley", "ME10", 51.360, 0.745),
    ("Milton Regis", "ME10", 51.350, 0.755),
    ("Murston", "ME10", 51.340, 0.760),
    ("Bapchild", "ME9", 51.340, 0.790),
    ("Rodmersham", "ME9", 51.325, 0.805),
    ("Tunstall", "ME9", 51.330, 0.775),
    ("Bredgar", "ME9", 51.305, 0.760),
    ("Doddington", "ME9", 51.295, 0.785),

    # === Swale area ===
    ("Minster on Sea", "ME12", 51.420, 0.815),
    ("Halfway Houses", "ME12", 51.415, 0.780),
    ("Sheerness", "ME12", 51.445, 0.760),
    ("Queenborough", "ME11", 51.415, 0.750),
    ("Rushenden", "ME11", 51.405, 0.745),
    ("Eastchurch", "ME12", 51.405, 0.870),
    ("Leysdown", "ME12", 51.390, 0.920),
]


def get_villages_near_hub(hub_name: str, max_distance_km: float = 50) -> list:
    """Get all villages within a certain distance of a hub station."""
    import math

    if hub_name not in HUB_STATIONS:
        return []

    hub_lat, hub_lon = HUB_STATIONS[hub_name]

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    results = []
    for name, postcode, lat, lon in KENT_VILLAGES:
        dist = haversine(hub_lat, hub_lon, lat, lon)
        if dist <= max_distance_km:
            results.append((name, postcode, lat, lon, dist))

    results.sort(key=lambda x: x[4])  # Sort by distance
    return results
