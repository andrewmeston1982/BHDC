"""
Database of commuter locations around London

Includes:
- Known commuter towns
- Hidden gems with good transport links
- Coordinates for distance/value calculations
- Average property prices (rough guide, 2024 data)
- Character notes

Distance from central London helps identify "hidden gems" -
places that are far away but have surprisingly good transport links.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
import math


@dataclass
class Location:
    """A commuter location"""
    name: str
    postcode_area: str  # For property searches
    station: str  # Main station name for TfL API
    lat: float
    lon: float
    rail_line: str  # Which line serves it
    notes: str  # Character, pros/cons
    avg_price_2bed: Optional[int] = None  # Rough guide only
    hidden_gem_potential: int = 3  # 1-5 scale, 5 = most underrated


# Central London reference point (roughly Tottenham Court Road)
LONDON_CENTER = (51.5165, -0.1310)

# W1T 3JF (Fitzrovia) - User's workplace
FITZROVIA = (51.5195, -0.1370)

# Hackney Town Hall (Mare Street E8 1EA) - Wife's workplace
HACKNEY = (51.5465, -0.0555)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km"""
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat/2)**2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def distance_from_london(lat: float, lon: float) -> float:
    """Distance from central London in km"""
    return haversine_distance_km(lat, lon, LONDON_CENTER[0], LONDON_CENTER[1])


# ============================================================================
# KENT - High Speed 1 corridor (the Gravesend effect!)
# ============================================================================
KENT_LOCATIONS = [
    Location(
        name="Gravesend",
        postcode_area="DA11",
        station="Gravesend",
        lat=51.4419, lon=0.3681,
        rail_line="High Speed 1 (Southeastern)",
        notes="The poster child for time vs distance. 23 mins to St Pancras on HS1. "
              "Diverse, riverside, surprisingly cheap. Ebbsfleet nearby for even faster trains.",
        avg_price_2bed=250000,
        hidden_gem_potential=5,
    ),
    Location(
        name="Ebbsfleet",
        postcode_area="DA10",
        station="Ebbsfleet International",
        lat=51.4429, lon=0.3208,
        rail_line="High Speed 1",
        notes="17 mins to St Pancras! New development area, Bluewater nearby. "
              "Less character than Gravesend but insanely quick commute.",
        avg_price_2bed=280000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Strood",
        postcode_area="ME2",
        station="Strood",
        lat=51.3930, lon=0.4780,
        rail_line="High Speed 1 / Southeastern",
        notes="28 mins to St Pancras on HS1. Medway town, more affordable than Rochester. "
              "Riverside location, improving area.",
        avg_price_2bed=220000,
        hidden_gem_potential=5,
    ),
    Location(
        name="Rochester",
        postcode_area="ME1",
        station="Rochester",
        lat=51.3884, lon=0.5057,
        rail_line="High Speed 1 / Southeastern",
        notes="38 mins to St Pancras. Beautiful historic town, castle, cathedral. "
              "Dickens connection. Good high street, river views.",
        avg_price_2bed=280000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Chatham",
        postcode_area="ME4",
        station="Chatham",
        lat=51.3797, lon=0.5294,
        rail_line="High Speed 1 / Southeastern",
        notes="40 mins to St Pancras. Historic Dockyard, universities nearby. "
              "Rougher than Rochester but much cheaper. Gentrifying slowly.",
        avg_price_2bed=200000,
        hidden_gem_potential=5,
    ),
    Location(
        name="Rainham (Kent)",
        postcode_area="ME8",
        station="Rainham (Kent)",
        lat=51.3661, lon=0.6119,
        rail_line="High Speed 1 / Southeastern",
        notes="43 mins to St Pancras. Quieter Medway town, good for families. "
              "Less exciting but affordable and peaceful.",
        avg_price_2bed=240000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Sittingbourne",
        postcode_area="ME10",
        station="Sittingbourne",
        lat=51.3403, lon=0.7361,
        rail_line="High Speed 1 / Southeastern",
        notes="53 mins to St Pancras on HS1 (but not all trains are HS1). "
              "Market town, kent countryside nearby. Very affordable.",
        avg_price_2bed=220000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Faversham",
        postcode_area="ME13",
        station="Faversham",
        lat=51.3147, lon=0.8914,
        rail_line="High Speed 1 / Southeastern",
        notes="57 mins to St Pancras. Beautiful market town, oysters, breweries. "
              "More character than most Kent towns. Popular with Londoners.",
        avg_price_2bed=300000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Dartford",
        postcode_area="DA1",
        station="Dartford",
        lat=51.4463, lon=0.2194,
        rail_line="Southeastern",
        notes="35-45 mins to various London terminals. Not HS1 but still decent. "
              "Shopping centre, Bluewater nearby. Well connected but not pretty.",
        avg_price_2bed=270000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Sevenoaks",
        postcode_area="TN13",
        station="Sevenoaks",
        lat=51.2694, lon=0.1906,
        rail_line="Southeastern",
        notes="25 mins to London Bridge. Posh Kent town, good schools. "
              "Expensive but very quick commute for the countryside feel.",
        avg_price_2bed=400000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Tonbridge",
        postcode_area="TN9",
        station="Tonbridge",
        lat=51.1947, lon=0.2739,
        rail_line="Southeastern",
        notes="35-45 mins to London terminals. Historic market town, castle. "
              "Good schools, nice high street. Classic commuter town.",
        avg_price_2bed=350000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Ashford International",
        postcode_area="TN24",
        station="Ashford International",
        lat=51.1436, lon=0.8761,
        rail_line="High Speed 1",
        notes="38 mins to St Pancras! Crazy good for the distance. "
              "Modern town, Designer Outlet. Gateway to Kent countryside.",
        avg_price_2bed=250000,
        hidden_gem_potential=5,
    ),
    Location(
        name="Whitstable",
        postcode_area="CT5",
        station="Whitstable",
        lat=51.3614, lon=1.0256,
        rail_line="Southeastern",
        notes="1h15m to London. Trendy seaside town, oysters, independent shops. "
              "Very popular with Londoners. Lovely but longer commute.",
        avg_price_2bed=350000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Margate",
        postcode_area="CT9",
        station="Margate",
        lat=51.3861, lon=1.3869,
        rail_line="High Speed 1",
        notes="1h20m to St Pancras on HS1. Regenerating seaside town, Turner Contemporary. "
              "Hipster invasion, cheap Victorian houses. Seaside living!",
        avg_price_2bed=240000,
        hidden_gem_potential=4,
    ),
]


# ============================================================================
# ESSEX - c2c and Greater Anglia lines
# ============================================================================
ESSEX_LOCATIONS = [
    Location(
        name="Grays",
        postcode_area="RM17",
        station="Grays",
        lat=51.4756, lon=0.3192,
        rail_line="c2c",
        notes="The anti-Gravesend! 50+ mins despite being closer as the crow flies. "
              "c2c is slower than HS1. Cheap though.",
        avg_price_2bed=230000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Leigh-on-Sea",
        postcode_area="SS9",
        station="Leigh-on-Sea",
        lat=51.5419, lon=0.6539,
        rail_line="c2c",
        notes="50 mins to Fenchurch Street. Lovely seaside village feel, cockles! "
              "Old town is charming. Popular with families.",
        avg_price_2bed=320000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Southend-on-Sea",
        postcode_area="SS1",
        station="Southend Central",
        lat=51.5375, lon=0.7128,
        rail_line="c2c",
        notes="55 mins to Fenchurch Street. Longest pier, seaside town. "
              "Cheaper than Leigh, more urban. Two stations for choice.",
        avg_price_2bed=220000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Benfleet",
        postcode_area="SS7",
        station="Benfleet",
        lat=51.5458, lon=0.5619,
        rail_line="c2c",
        notes="42 mins to Fenchurch Street. Quiet suburban, Hadleigh Castle nearby. "
              "Good value for South Essex.",
        avg_price_2bed=280000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Basildon",
        postcode_area="SS14",
        station="Basildon",
        lat=51.5761, lon=0.4886,
        rail_line="c2c",
        notes="35 mins to Fenchurch Street. New town, cheap but characterless. "
              "Good transport links, shopping centre.",
        avg_price_2bed=230000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Chelmsford",
        postcode_area="CM1",
        station="Chelmsford",
        lat=51.7356, lon=0.4685,
        rail_line="Greater Anglia",
        notes="35 mins to Liverpool Street. City status, good shops, riverside. "
              "Essex's county town. Popular commuter choice.",
        avg_price_2bed=300000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Shenfield",
        postcode_area="CM15",
        station="Shenfield",
        lat=51.6306, lon=0.3281,
        rail_line="Elizabeth Line / Greater Anglia",
        notes="Elizabeth Line terminus! Direct to Paddington, Bond Street etc. "
              "Game changer for this area. Pricey now.",
        avg_price_2bed=350000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Brentwood",
        postcode_area="CM14",
        station="Brentwood",
        lat=51.6211, lon=0.3050,
        rail_line="Elizabeth Line",
        notes="On Elizabeth Line. TOWIE town but actually quite nice. "
              "Good high street, Essex countryside.",
        avg_price_2bed=340000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Ingatestone",
        postcode_area="CM4",
        station="Ingatestone",
        lat=51.6669, lon=0.3839,
        rail_line="Greater Anglia",
        notes="35 mins to Liverpool Street. Pretty Essex village, good schools. "
              "Quiet, rural feel but good links.",
        avg_price_2bed=350000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Witham",
        postcode_area="CM8",
        station="Witham",
        lat=51.8000, lon=0.6333,
        rail_line="Greater Anglia",
        notes="45 mins to Liverpool Street. Small town, cheaper than Chelmsford. "
              "Some fast trains, good value.",
        avg_price_2bed=260000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Colchester",
        postcode_area="CO1",
        station="Colchester",
        lat=51.8894, lon=0.8972,
        rail_line="Greater Anglia",
        notes="50-60 mins to Liverpool Street. Britain's oldest recorded town! "
              "University, arts scene, Roman walls. Further out but characterful.",
        avg_price_2bed=250000,
        hidden_gem_potential=4,
    ),
]


# ============================================================================
# HERTFORDSHIRE - Thameslink and Great Northern
# ============================================================================
HERTS_LOCATIONS = [
    Location(
        name="St Albans",
        postcode_area="AL1",
        station="St Albans City",
        lat=51.7500, lon=-0.3361,
        rail_line="Thameslink",
        notes="20 mins to St Pancras! Beautiful cathedral city, Roman ruins. "
              "Expensive but gorgeous. Great pubs and restaurants.",
        avg_price_2bed=400000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Harpenden",
        postcode_area="AL5",
        station="Harpenden",
        lat=51.8147, lon=-0.3569,
        rail_line="Thameslink",
        notes="28 mins to St Pancras. Very posh, excellent schools. "
              "Village feel, commons, expensive but lovely.",
        avg_price_2bed=500000,
        hidden_gem_potential=1,
    ),
    Location(
        name="Luton",
        postcode_area="LU1",
        station="Luton",
        lat=51.8797, lon=-0.4147,
        rail_line="Thameslink",
        notes="25 mins to St Pancras! Incredibly underrated for commute time. "
              "Reputation precedes it but genuinely quick and cheap.",
        avg_price_2bed=220000,
        hidden_gem_potential=5,
    ),
    Location(
        name="Hitchin",
        postcode_area="SG5",
        station="Hitchin",
        lat=51.9478, lon=-0.2831,
        rail_line="Great Northern",
        notes="35 mins to King's Cross. Beautiful market town, river, character. "
              "Good schools, nice pubs. Hidden gem of North Herts.",
        avg_price_2bed=350000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Stevenage",
        postcode_area="SG1",
        station="Stevenage",
        lat=51.9019, lon=-0.2019,
        rail_line="Great Northern",
        notes="25 mins to King's Cross! New town, not pretty but incredibly fast. "
              "Cheap for the commute time. Cycle paths everywhere.",
        avg_price_2bed=260000,
        hidden_gem_potential=5,
    ),
    Location(
        name="Welwyn Garden City",
        postcode_area="AL7",
        station="Welwyn Garden City",
        lat=51.8011, lon=-0.2067,
        rail_line="Great Northern",
        notes="25 mins to King's Cross. Planned garden city, green spaces. "
              "Nice architecture, good community feel.",
        avg_price_2bed=330000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Hatfield",
        postcode_area="AL10",
        station="Hatfield",
        lat=51.7636, lon=-0.2283,
        rail_line="Great Northern",
        notes="22 mins to King's Cross. University town, Galleria shopping. "
              "Mix of old and new. Good value for the commute.",
        avg_price_2bed=300000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Potters Bar",
        postcode_area="EN6",
        station="Potters Bar",
        lat=51.6917, lon=-0.1750,
        rail_line="Great Northern",
        notes="20 mins to King's Cross. Suburban but quick commute. "
              "Edge of countryside, decent shopping.",
        avg_price_2bed=350000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Letchworth Garden City",
        postcode_area="SG6",
        station="Letchworth Garden City",
        lat=51.9789, lon=-0.2300,
        rail_line="Great Northern",
        notes="40 mins to King's Cross. First garden city, interesting architecture. "
              "Quirky, independent shops, good community.",
        avg_price_2bed=300000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Baldock",
        postcode_area="SG7",
        station="Baldock",
        lat=51.9900, lon=-0.1894,
        rail_line="Great Northern",
        notes="42 mins to King's Cross. Small historic town, market square. "
              "Quieter alternative to Hitchin, cheaper too.",
        avg_price_2bed=300000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Royston",
        postcode_area="SG8",
        station="Royston",
        lat=52.0472, lon=-0.0217,
        rail_line="Great Northern",
        notes="45 mins to King's Cross. Edge of Cambridgeshire, cave system! "
              "Small market town, rural surroundings.",
        avg_price_2bed=290000,
        hidden_gem_potential=4,
    ),
]


# ============================================================================
# SURREY & SUSSEX - South Western, Southern, Thameslink
# ============================================================================
SURREY_SUSSEX_LOCATIONS = [
    Location(
        name="Guildford",
        postcode_area="GU1",
        station="Guildford",
        lat=51.2362, lon=-0.5703,
        rail_line="South Western Railway",
        notes="35 mins to Waterloo. Beautiful town, cobbled high street. "
              "University, cathedral. Expensive but lovely.",
        avg_price_2bed=400000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Woking",
        postcode_area="GU21",
        station="Woking",
        lat=51.3181, lon=-0.5569,
        rail_line="South Western Railway",
        notes="24 mins to Waterloo! Very fast trains. Modern town centre. "
              "Good value for the commute time.",
        avg_price_2bed=350000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Farnham",
        postcode_area="GU9",
        station="Farnham",
        lat=51.2139, lon=-0.7981,
        rail_line="South Western Railway",
        notes="55 mins to Waterloo. Georgian market town, castle, hops. "
              "Very pretty, good pubs. Further out but characterful.",
        avg_price_2bed=380000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Dorking",
        postcode_area="RH4",
        station="Dorking",
        lat=51.2317, lon=-0.3331,
        rail_line="Southern / Thameslink",
        notes="50 mins to Victoria/London Bridge. Pretty market town, Box Hill. "
              "Surrey Hills AONB, good walking.",
        avg_price_2bed=380000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Redhill",
        postcode_area="RH1",
        station="Redhill",
        lat=51.2400, lon=-0.1650,
        rail_line="Southern / Thameslink",
        notes="30 mins to London Bridge/Victoria. Major junction, improving. "
              "Not pretty but functional and well-connected.",
        avg_price_2bed=300000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Reigate",
        postcode_area="RH2",
        station="Reigate",
        lat=51.2375, lon=-0.2050,
        rail_line="Southern",
        notes="40 mins to London Bridge. Historic town, castle grounds. "
              "Better than Redhill, pricier too.",
        avg_price_2bed=400000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Epsom",
        postcode_area="KT18",
        station="Epsom",
        lat=51.3361, lon=-0.2675,
        rail_line="Southern / South Western",
        notes="35 mins to Victoria/Waterloo. Famous racecourse, Epsom salts! "
              "Good high street, edge of Downs.",
        avg_price_2bed=380000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Brighton",
        postcode_area="BN1",
        station="Brighton",
        lat=51.4816, lon=-0.1419,
        rail_line="Southern / Thameslink",
        notes="55 mins to Victoria/London Bridge. The big one - seaside city! "
              "Culture, nightlife, beach. Many commuters do it.",
        avg_price_2bed=380000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Haywards Heath",
        postcode_area="RH16",
        station="Haywards Heath",
        lat=51.0050, lon=-0.1050,
        rail_line="Thameslink / Southern",
        notes="45 mins to London Bridge. Gateway to Sussex Weald. "
              "Surprisingly good commute, pleasant town.",
        avg_price_2bed=350000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Horsham",
        postcode_area="RH12",
        station="Horsham",
        lat=51.0622, lon=-0.3256,
        rail_line="Southern / Thameslink",
        notes="55 mins to Victoria. Historic market town, The Carfax. "
              "Good schools, nice centre. Sussex commuter belt.",
        avg_price_2bed=350000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Crawley",
        postcode_area="RH10",
        station="Three Bridges",
        lat=51.1172, lon=-0.1406,
        rail_line="Thameslink / Southern",
        notes="35 mins to London Bridge. New town, Gatwick nearby. "
              "Not charming but practical and quick.",
        avg_price_2bed=280000,
        hidden_gem_potential=3,
    ),
    Location(
        name="East Croydon",
        postcode_area="CR0",
        station="East Croydon",
        lat=51.3756, lon=-0.0925,
        rail_line="Southern / Thameslink",
        notes="15 mins to London Bridge! Basically London prices though. "
              "Big regeneration, good food scene now.",
        avg_price_2bed=350000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Lewes",
        postcode_area="BN7",
        station="Lewes",
        lat=50.8750, lon=0.0089,
        rail_line="Southern",
        notes="1h5m to Victoria. Beautiful county town, castle, bonfire night! "
              "Independent shops, character. Worth the longer commute.",
        avg_price_2bed=380000,
        hidden_gem_potential=3,
    ),
]


# ============================================================================
# BERKSHIRE & BUCKS - GWR, Elizabeth Line, Chiltern
# ============================================================================
BERKS_BUCKS_LOCATIONS = [
    Location(
        name="Reading",
        postcode_area="RG1",
        station="Reading",
        lat=51.4542, lon=-0.9731,
        rail_line="Elizabeth Line / GWR",
        notes="25 mins to Paddington! Elizabeth Line now goes direct. "
              "Big town, riverside, festivals. Major hub.",
        avg_price_2bed=320000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Slough",
        postcode_area="SL1",
        station="Slough",
        lat=51.5106, lon=-0.5950,
        rail_line="Elizabeth Line / GWR",
        notes="17 mins to Paddington! Butt of jokes but genuinely quick. "
              "Trading estate wealth, diverse, cheap for the commute.",
        avg_price_2bed=300000,
        hidden_gem_potential=5,
    ),
    Location(
        name="Maidenhead",
        postcode_area="SL6",
        station="Maidenhead",
        lat=51.5217, lon=-0.7194,
        rail_line="Elizabeth Line / GWR",
        notes="23 mins to Paddington. Riverside, nice parts near Boulters Lock. "
              "Elizabeth Line improved it massively.",
        avg_price_2bed=380000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Windsor",
        postcode_area="SL4",
        station="Windsor & Eton Central",
        lat=51.4833, lon=-0.6128,
        rail_line="GWR / South Western",
        notes="50 mins to Paddington (change at Slough) or Waterloo direct. "
              "Castle, tourists, but surprisingly liveable.",
        avg_price_2bed=420000,
        hidden_gem_potential=2,
    ),
    Location(
        name="High Wycombe",
        postcode_area="HP11",
        station="High Wycombe",
        lat=51.6292, lon=-0.7489,
        rail_line="Chiltern Railways",
        notes="25-35 mins to Marylebone. Chilterns AONB doorstep. "
              "Big town, improving centre. Good value.",
        avg_price_2bed=300000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Beaconsfield",
        postcode_area="HP9",
        station="Beaconsfield",
        lat=51.6028, lon=-0.6431,
        rail_line="Chiltern Railways",
        notes="23 mins to Marylebone. Old Town is lovely, good pubs. "
              "Stockbroker belt, pricey but pretty.",
        avg_price_2bed=500000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Gerrards Cross",
        postcode_area="SL9",
        station="Gerrards Cross",
        lat=51.5881, lon=-0.5553,
        rail_line="Chiltern Railways",
        notes="20 mins to Marylebone. Very posh, good schools. "
              "Expensive but excellent commute.",
        avg_price_2bed=550000,
        hidden_gem_potential=1,
    ),
    Location(
        name="Amersham",
        postcode_area="HP6",
        station="Amersham",
        lat=51.6742, lon=-0.6072,
        rail_line="Metropolitan Line / Chiltern",
        notes="40 mins on Met Line to Baker Street! Zone 9 but feels rural. "
              "Old Town is beautiful. Chilterns walks.",
        avg_price_2bed=450000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Chesham",
        postcode_area="HP5",
        station="Chesham",
        lat=51.7050, lon=-0.6111,
        rail_line="Metropolitan Line",
        notes="45 mins on Met Line. End of the line, proper market town. "
              "Chess valley, independent shops. Quieter than Amersham.",
        avg_price_2bed=400000,
        hidden_gem_potential=3,
    ),
    Location(
        name="Aylesbury",
        postcode_area="HP20",
        station="Aylesbury Vale Parkway",
        lat=51.8147, lon=-0.8147,
        rail_line="Chiltern Railways",
        notes="55 mins to Marylebone. County town, duck! "
              "New builds everywhere. Further out but affordable.",
        avg_price_2bed=280000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Tring",
        postcode_area="HP23",
        station="Tring",
        lat=51.7967, lon=-0.6606,
        rail_line="West Midlands Railway",
        notes="35 mins to Euston. Natural History Museum outpost! "
              "Chilterns walks, Grand Union Canal. Hidden gem.",
        avg_price_2bed=380000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Berkhamsted",
        postcode_area="HP4",
        station="Berkhamsted",
        lat=51.7622, lon=-0.5611,
        rail_line="West Midlands Railway",
        notes="30 mins to Euston. Beautiful, castle, canal, High Street. "
              "Expensive but worth it. Great pubs.",
        avg_price_2bed=450000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Hemel Hempstead",
        postcode_area="HP1",
        station="Hemel Hempstead",
        lat=51.7522, lon=-0.4728,
        rail_line="West Midlands Railway",
        notes="30 mins to Euston. New Town, Magic Roundabout! "
              "Old Town has character. Cheaper than neighbours.",
        avg_price_2bed=300000,
        hidden_gem_potential=4,
    ),
]


# ============================================================================
# BEDS & CAMBS - Thameslink, Great Northern, Greater Anglia
# ============================================================================
BEDS_CAMBS_LOCATIONS = [
    Location(
        name="Bedford",
        postcode_area="MK40",
        station="Bedford",
        lat=52.1369, lon=-0.4600,
        rail_line="Thameslink",
        notes="40 mins to St Pancras! Thameslink direct. River Ouse, parks. "
              "Italian community, good food. Underrated.",
        avg_price_2bed=240000,
        hidden_gem_potential=5,
    ),
    Location(
        name="Flitwick",
        postcode_area="MK45",
        station="Flitwick",
        lat=52.0036, lon=-0.4953,
        rail_line="Thameslink",
        notes="35 mins to St Pancras. Small town, quieter than Bedford. "
              "Good value, peaceful.",
        avg_price_2bed=280000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Leighton Buzzard",
        postcode_area="LU7",
        station="Leighton Buzzard",
        lat=51.9167, lon=-0.6617,
        rail_line="West Midlands Railway",
        notes="35 mins to Euston. Pretty market town, canal, narrow gauge railway. "
              "Good schools, nice centre.",
        avg_price_2bed=300000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Cambridge",
        postcode_area="CB1",
        station="Cambridge",
        lat=51.0333, lon=0.1167,
        rail_line="Greater Anglia / Thameslink",
        notes="50 mins to King's Cross / Liverpool Street. The famous one! "
              "Colleges, cycling, punting. Expensive but incredible.",
        avg_price_2bed=400000,
        hidden_gem_potential=2,
    ),
    Location(
        name="Ely",
        postcode_area="CB6",
        station="Ely",
        lat=52.3992, lon=0.2622,
        rail_line="Greater Anglia",
        notes="1h10m to King's Cross (1h to Liverpool Street). Cathedral city! "
              "Fenland beauty, riverside, Oliver Cromwell house.",
        avg_price_2bed=280000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Huntingdon",
        postcode_area="PE29",
        station="Huntingdon",
        lat=52.3311, lon=-0.1850,
        rail_line="Great Northern",
        notes="50 mins to King's Cross. Historic market town, Cromwell birthplace. "
              "River Ouse, good pubs.",
        avg_price_2bed=260000,
        hidden_gem_potential=4,
    ),
    Location(
        name="St Neots",
        postcode_area="PE19",
        station="St Neots",
        lat=52.2286, lon=-0.2700,
        rail_line="Great Northern",
        notes="45 mins to King's Cross. Market town, riverside, biggest market square. "
              "Growing fast, good value.",
        avg_price_2bed=260000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Sandy",
        postcode_area="SG19",
        station="Sandy",
        lat=52.1306, lon=-0.2908,
        rail_line="Great Northern",
        notes="40 mins to King's Cross. RSPB headquarters, The Lodge nature reserve. "
              "Small town, nature lovers paradise.",
        avg_price_2bed=270000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Biggleswade",
        postcode_area="SG18",
        station="Biggleswade",
        lat=52.0867, lon=-0.2583,
        rail_line="Great Northern",
        notes="40 mins to King's Cross. Market town, antiques centre. "
              "Quiet, good value, growing.",
        avg_price_2bed=270000,
        hidden_gem_potential=4,
    ),
    Location(
        name="Arlesey",
        postcode_area="SG15",
        station="Arlesey",
        lat=52.0133, lon=-0.2642,
        rail_line="Great Northern",
        notes="35 mins to King's Cross! Small village, surprisingly quick. "
              "Very affordable, rural feel.",
        avg_price_2bed=260000,
        hidden_gem_potential=5,
    ),
]


# ============================================================================
# ALL LOCATIONS COMBINED
# ============================================================================
ALL_LOCATIONS: List[Location] = (
    KENT_LOCATIONS +
    ESSEX_LOCATIONS +
    HERTS_LOCATIONS +
    SURREY_SUSSEX_LOCATIONS +
    BERKS_BUCKS_LOCATIONS +
    BEDS_CAMBS_LOCATIONS
)


def get_locations_by_max_distance(max_km: float) -> List[Location]:
    """Get locations within a certain distance of central London"""
    return [
        loc for loc in ALL_LOCATIONS
        if distance_from_london(loc.lat, loc.lon) <= max_km
    ]


def get_locations_by_price(max_price: int) -> List[Location]:
    """Get locations under a certain price point"""
    return [
        loc for loc in ALL_LOCATIONS
        if loc.avg_price_2bed and loc.avg_price_2bed <= max_price
    ]


def get_hidden_gems(min_rating: int = 4) -> List[Location]:
    """Get locations marked as hidden gems"""
    return [
        loc for loc in ALL_LOCATIONS
        if loc.hidden_gem_potential >= min_rating
    ]


def get_locations_by_line(line_contains: str) -> List[Location]:
    """Get locations on a specific rail line"""
    return [
        loc for loc in ALL_LOCATIONS
        if line_contains.lower() in loc.rail_line.lower()
    ]


# Quick summary
if __name__ == "__main__":
    print(f"Total locations in database: {len(ALL_LOCATIONS)}")
    print(f"\nBy region:")
    print(f"  Kent: {len(KENT_LOCATIONS)}")
    print(f"  Essex: {len(ESSEX_LOCATIONS)}")
    print(f"  Hertfordshire: {len(HERTS_LOCATIONS)}")
    print(f"  Surrey/Sussex: {len(SURREY_SUSSEX_LOCATIONS)}")
    print(f"  Berkshire/Bucks: {len(BERKS_BUCKS_LOCATIONS)}")
    print(f"  Beds/Cambs: {len(BEDS_CAMBS_LOCATIONS)}")

    print(f"\nHidden gems (rating 5):")
    for loc in get_hidden_gems(5):
        dist = distance_from_london(loc.lat, loc.lon)
        print(f"  {loc.name} ({dist:.0f}km from London) - {loc.rail_line}")
