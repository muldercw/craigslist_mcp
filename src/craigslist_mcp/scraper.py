"""
Craigslist scraper — search listings, get details, list locations/categories.

Uses httpx + BeautifulSoup to query Craigslist's public HTML pages.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urljoin, urlencode, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("craigslist_mcp")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_LOCATION = "newyork"
MAX_RESULTS = 120
REQUEST_TIMEOUT = 30

# Common headers to look like a real browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# Craigslist locations (subdomain -> display name)
# This is a comprehensive list of US + major international locations.
# ---------------------------------------------------------------------------

LOCATIONS: dict[str, str] = {
    # --- United States ---
    "auburn": "Auburn, AL",
    "bham": "Birmingham, AL",
    "dothan": "Dothan, AL",
    "shoals": "Florence / Muscle Shoals, AL",
    "gadsden": "Gadsden-Anniston, AL",
    "huntsville": "Huntsville / Decatur, AL",
    "mobile": "Mobile, AL",
    "montgomery": "Montgomery, AL",
    "tuscaloosa": "Tuscaloosa, AL",
    "anchorage": "Anchorage / Mat-Su, AK",
    "fairbanks": "Fairbanks, AK",
    "kenai": "Kenai Peninsula, AK",
    "juneau": "Juneau, AK",
    "flagstaff": "Flagstaff / Sedona, AZ",
    "mohave": "Mohave County, AZ",
    "phoenix": "Phoenix, AZ",
    "prescott": "Prescott, AZ",
    "showlow": "Show Low, AZ",
    "sierravista": "Sierra Vista, AZ",
    "tucson": "Tucson, AZ",
    "yuma": "Yuma, AZ",
    "fayar": "Fayetteville, AR",
    "fortsmith": "Fort Smith, AR",
    "jonesboro": "Jonesboro, AR",
    "littlerock": "Little Rock, AR",
    "texarkana": "Texarkana, AR",
    "bakersfield": "Bakersfield, CA",
    "chico": "Chico, CA",
    "fresno": "Fresno / Madera, CA",
    "goldcountry": "Gold Country, CA",
    "hanford": "Hanford-Corcoran, CA",
    "humboldt": "Humboldt County, CA",
    "imperial": "Imperial County, CA",
    "inlandempire": "Inland Empire, CA",
    "losangeles": "Los Angeles, CA",
    "mendocino": "Mendocino County, CA",
    "merced": "Merced, CA",
    "modesto": "Modesto, CA",
    "monterey": "Monterey Bay, CA",
    "orangecounty": "Orange County, CA",
    "palmsprings": "Palm Springs, CA",
    "redding": "Redding, CA",
    "sacramento": "Sacramento, CA",
    "sandiego": "San Diego, CA",
    "sfbay": "San Francisco Bay Area, CA",
    "slo": "San Luis Obispo, CA",
    "santabarbara": "Santa Barbara, CA",
    "santamaria": "Santa Maria, CA",
    "siskiyou": "Siskiyou County, CA",
    "stockton": "Stockton, CA",
    "susanville": "Susanville, CA",
    "ventura": "Ventura County, CA",
    "visalia": "Visalia-Tulare, CA",
    "yubasutter": "Yuba-Sutter, CA",
    "boulder": "Boulder, CO",
    "cosprings": "Colorado Springs, CO",
    "denver": "Denver, CO",
    "eastco": "Eastern CO",
    "fortcollins": "Fort Collins / North CO",
    "pueblo": "Pueblo, CO",
    "rockies": "High Rockies, CO",
    "westslope": "Western Slope, CO",
    "newhaven": "New Haven, CT",
    "hartford": "Hartford, CT",
    "nwct": "Northwest CT",
    "eastern-ct": "Eastern CT",
    "delaware": "Delaware",
    "washingtondc": "Washington, DC",
    "daytona": "Daytona Beach, FL",
    "keys": "Florida Keys, FL",
    "fortlauderdale": "Fort Lauderdale, FL",
    "fortmyers": "Fort Myers / SW Florida, FL",
    "gainesville": "Gainesville, FL",
    "cfl": "Heartland Florida, FL",
    "jacksonville": "Jacksonville, FL",
    "lakeland": "Lakeland, FL",
    "lakecity": "Lake City, FL",
    "ocala": "Ocala, FL",
    "okaloosa": "Okaloosa / Walton, FL",
    "orlando": "Orlando, FL",
    "panama": "Panama City, FL",
    "pensacola": "Pensacola, FL",
    "sarasota": "Sarasota-Bradenton, FL",
    "miami": "South Florida / Miami, FL",
    "spacecoast": "Space Coast, FL",
    "staugustine": "St Augustine, FL",
    "tallahassee": "Tallahassee, FL",
    "tampa": "Tampa Bay Area, FL",
    "treasure": "Treasure Coast, FL",
    "albanyga": "Albany, GA",
    "athens": "Athens, GA",
    "atlanta": "Atlanta, GA",
    "augusta": "Augusta, GA",
    "brunswick": "Brunswick, GA",
    "columbus": "Columbus, GA",
    "macon": "Macon / Warner Robins, GA",
    "nwga": "Northwest GA",
    "savannah": "Savannah / Hinesville, GA",
    "statesboro": "Statesboro, GA",
    "valdosta": "Valdosta, GA",
    "honolulu": "Hawaii",
    "boise": "Boise, ID",
    "easternidaho": "East Idaho, ID",
    "lewiston": "Lewiston / Clarkston, ID",
    "twinfalls": "Twin Falls, ID",
    "bn": "Bloomington-Normal, IL",
    "chambana": "Champaign Urbana, IL",
    "chicago": "Chicago, IL",
    "decatur": "Decatur, IL",
    "lasalle": "La Salle Co, IL",
    "mattoon": "Mattoon-Charleston, IL",
    "peoria": "Peoria, IL",
    "rockford": "Rockford, IL",
    "carbondale": "Southern Illinois, IL",
    "springfieldil": "Springfield, IL",
    "quincy": "Western IL",
    "bloomington": "Bloomington, IN",
    "evansville": "Evansville, IN",
    "fortwayne": "Fort Wayne, IN",
    "indianapolis": "Indianapolis, IN",
    "kokomo": "Kokomo, IN",
    "lafayette": "Lafayette / West Lafayette, IN",
    "muncie": "Muncie / Anderson, IN",
    "richmondin": "Richmond, IN",
    "southbend": "South Bend / Michiana, IN",
    "terrehaute": "Terre Haute, IN",
    "ames": "Ames, IA",
    "cedarrapids": "Cedar Rapids, IA",
    "desmoines": "Des Moines, IA",
    "dubuque": "Dubuque, IA",
    "fortdodge": "Fort Dodge, IA",
    "iowacity": "Iowa City, IA",
    "masoncity": "Mason City, IA",
    "quadcities": "Quad Cities, IA/IL",
    "siouxcity": "Sioux City, IA",
    "ottumwa": "Southeast IA",
    "waterloo": "Waterloo / Cedar Falls, IA",
    "lawrence": "Lawrence, KS",
    "ksu": "Manhattan, KS",
    "nwks": "Northwest KS",
    "salina": "Salina, KS",
    "seks": "Southeast KS",
    "swks": "Southwest KS",
    "topeka": "Topeka, KS",
    "wichita": "Wichita, KS",
    "bgky": "Bowling Green, KY",
    "eastky": "Eastern Kentucky",
    "lexington": "Lexington, KY",
    "louisville": "Louisville, KY",
    "owensboro": "Owensboro, KY",
    "westky": "Western KY",
    "batonrouge": "Baton Rouge, LA",
    "cenla": "Central Louisiana, LA",
    "houma": "Houma, LA",
    "lafayette": "Lafayette, LA",
    "lakecharles": "Lake Charles, LA",
    "monroe": "Monroe, LA",
    "neworleans": "New Orleans, LA",
    "shreveport": "Shreveport, LA",
    "maine": "Maine",
    "annapolis": "Annapolis, MD",
    "baltimore": "Baltimore, MD",
    "easternshore": "Eastern Shore, MD",
    "frederick": "Frederick, MD",
    "smd": "Southern Maryland",
    "westmd": "Western Maryland",
    "boston": "Boston, MA",
    "capecod": "Cape Cod / Islands, MA",
    "southcoast": "South Coast, MA",
    "westernmass": "Western Massachusetts",
    "worcester": "Worcester / Central MA",
    "annarbor": "Ann Arbor, MI",
    "battlecreek": "Battle Creek, MI",
    "centralmich": "Central Michigan",
    "detroit": "Detroit Metro, MI",
    "flint": "Flint, MI",
    "grandrapids": "Grand Rapids, MI",
    "holland": "Holland, MI",
    "jxn": "Jackson, MI",
    "kalamazoo": "Kalamazoo, MI",
    "lansing": "Lansing, MI",
    "monroemi": "Monroe, MI",
    "muskegon": "Muskegon, MI",
    "nmi": "Northern Michigan",
    "porthuron": "Port Huron, MI",
    "saginaw": "Saginaw-Midland-Bay City, MI",
    "swmi": "Southwest Michigan",
    "thumb": "The Thumb, MI",
    "up": "Upper Peninsula, MI",
    "bemidji": "Bemidji, MN",
    "brainerd": "Brainerd, MN",
    "duluth": "Duluth / Superior, MN",
    "mankato": "Mankato, MN",
    "minneapolis": "Minneapolis / St Paul, MN",
    "rmn": "Rochester, MN",
    "marshall": "Southwest MN",
    "stcloud": "St Cloud, MN",
    "gulfport": "Gulfport / Biloxi, MS",
    "hattiesburg": "Hattiesburg, MS",
    "jackson": "Jackson, MS",
    "meridian": "Meridian, MS",
    "northmiss": "North Mississippi",
    "natchez": "Southwest MS",
    "columbiamo": "Columbia / Jeff City, MO",
    "joplin": "Joplin, MO",
    "kansascity": "Kansas City, MO",
    "kirksville": "Kirksville, MO",
    "loz": "Lake of the Ozarks, MO",
    "semo": "Southeast Missouri",
    "springfield": "Springfield, MO",
    "stjoseph": "St Joseph, MO",
    "stlouis": "St Louis, MO",
    "billings": "Billings, MT",
    "bozeman": "Bozeman, MT",
    "butte": "Butte, MT",
    "greatfalls": "Great Falls, MT",
    "helena": "Helena, MT",
    "kalispell": "Kalispell, MT",
    "missoula": "Missoula, MT",
    "montana": "Eastern Montana",
    "grandisland": "Grand Island, NE",
    "lincoln": "Lincoln, NE",
    "northplatte": "North Platte, NE",
    "omaha": "Omaha / Council Bluffs, NE",
    "scottsbluff": "Scottsbluff / Panhandle, NE",
    "elko": "Elko, NV",
    "lasvegas": "Las Vegas, NV",
    "reno": "Reno / Tahoe, NV",
    "nh": "New Hampshire",
    "cnj": "Central NJ",
    "jerseyshore": "Jersey Shore, NJ",
    "newjersey": "North Jersey, NJ",
    "southjersey": "South Jersey, NJ",
    "albuquerque": "Albuquerque, NM",
    "clovis": "Clovis / Portales, NM",
    "farmington": "Farmington, NM",
    "lascruces": "Las Cruces, NM",
    "roswell": "Roswell / Carlsbad, NM",
    "santafe": "Santa Fe / Taos, NM",
    "albany": "Albany, NY",
    "binghamton": "Binghamton, NY",
    "buffalo": "Buffalo, NY",
    "catskills": "Catskills, NY",
    "chautauqua": "Chautauqua, NY",
    "elmira": "Elmira-Corning, NY",
    "fingerlakes": "Finger Lakes, NY",
    "glensfalls": "Glens Falls, NY",
    "hudsonvalley": "Hudson Valley, NY",
    "ithaca": "Ithaca, NY",
    "longisland": "Long Island, NY",
    "newyork": "New York City, NY",
    "oneonta": "Oneonta, NY",
    "plattsburgh": "Plattsburgh-Adirondacks, NY",
    "potsdam": "Potsdam-Canton-Massena, NY",
    "rochester": "Rochester, NY",
    "syracuse": "Syracuse, NY",
    "utica": "Utica-Rome-Oneida, NY",
    "watertown": "Watertown, NY",
    "asheville": "Asheville, NC",
    "boone": "Boone, NC",
    "charlotte": "Charlotte, NC",
    "eastnc": "Eastern NC",
    "fayetteville": "Fayetteville, NC",
    "greensboro": "Greensboro, NC",
    "hickory": "Hickory / Lenoir, NC",
    "onslow": "Jacksonville, NC",
    "outerbanks": "Outer Banks, NC",
    "raleigh": "Raleigh / Durham / CH, NC",
    "wilmington": "Wilmington, NC",
    "winstonsalem": "Winston-Salem, NC",
    "bismarck": "Bismarck, ND",
    "fargo": "Fargo / Moorhead, ND",
    "grandforks": "Grand Forks, ND",
    "nd": "North Dakota",
    "akroncanton": "Akron / Canton, OH",
    "ashtabula": "Ashtabula, OH",
    "athensohio": "Athens, OH",
    "chillicothe": "Chillicothe, OH",
    "cincinnati": "Cincinnati, OH",
    "cleveland": "Cleveland, OH",
    "columbus": "Columbus, OH",
    "dayton": "Dayton / Springfield, OH",
    "limaohio": "Lima / Findlay, OH",
    "mansfield": "Mansfield, OH",
    "sandusky": "Sandusky, OH",
    "toledo": "Toledo, OH",
    "tuscarawas": "Tuscarawas Co, OH",
    "youngstown": "Youngstown, OH",
    "zanesville": "Zanesville / Cambridge, OH",
    "lawton": "Lawton, OK",
    "enid": "Northwest OK",
    "oklahomacity": "Oklahoma City, OK",
    "stillwater": "Stillwater, OK",
    "tulsa": "Tulsa, OK",
    "bend": "Bend, OR",
    "corvallis": "Corvallis/Albany, OR",
    "eastoregon": "East Oregon, OR",
    "eugene": "Eugene, OR",
    "klamath": "Klamath Falls, OR",
    "medford": "Medford-Ashland, OR",
    "oregoncoast": "Oregon Coast, OR",
    "portland": "Portland, OR",
    "roseburg": "Roseburg, OR",
    "salem": "Salem, OR",
    "allentown": "Allentown, PA",
    "altoona": "Altoona-Johnstown, PA",
    "chambersburg": "Cumberland Valley, PA",
    "erie": "Erie, PA",
    "harrisburg": "Harrisburg, PA",
    "lancaster": "Lancaster, PA",
    "meadville": "Meadville, PA",
    "philadelphia": "Philadelphia, PA",
    "pittsburgh": "Pittsburgh, PA",
    "poconos": "Poconos, PA",
    "reading": "Reading, PA",
    "scranton": "Scranton / Wilkes-Barre, PA",
    "pennstate": "State College, PA",
    "williamsport": "Williamsport, PA",
    "york": "York, PA",
    "providence": "Providence / Warwick, RI",
    "charleston": "Charleston, SC",
    "columbia": "Columbia, SC",
    "florencesc": "Florence, SC",
    "greenville": "Greenville / Upstate, SC",
    "hiltonhead": "Hilton Head, SC",
    "myrtlebeach": "Myrtle Beach, SC",
    "nesd": "Northeast SD",
    "pierresd": "Pierre / Central SD",
    "rapidcity": "Rapid City / West SD",
    "siouxfalls": "Sioux Falls / SE SD",
    "sd": "South Dakota",
    "chattanooga": "Chattanooga, TN",
    "clarksville": "Clarksville, TN",
    "cookeville": "Cookeville, TN",
    "jacksontn": "Jackson, TN",
    "knoxville": "Knoxville, TN",
    "memphis": "Memphis, TN",
    "nashville": "Nashville, TN",
    "tricities": "Tri-Cities, TN",
    "abilene": "Abilene, TX",
    "amarillo": "Amarillo, TX",
    "austin": "Austin, TX",
    "beaumont": "Beaumont / Port Arthur, TX",
    "brownsville": "Brownsville, TX",
    "collegestation": "College Station, TX",
    "corpuschristi": "Corpus Christi, TX",
    "dallas": "Dallas / Fort Worth, TX",
    "nacogdoches": "Deep East Texas, TX",
    "delrio": "Del Rio / Eagle Pass, TX",
    "elpaso": "El Paso, TX",
    "galveston": "Galveston, TX",
    "houston": "Houston, TX",
    "killeen": "Killeen / Temple / Ft Hood, TX",
    "laredo": "Laredo, TX",
    "lubbock": "Lubbock, TX",
    "mcallen": "McAllen / Edinburg, TX",
    "midland": "Midland / Odessa, TX",
    "sanangelo": "San Angelo, TX",
    "sanantonio": "San Antonio, TX",
    "sanmarcos": "San Marcos, TX",
    "bigbend": "Southwest TX",
    "texoma": "Texoma, TX",
    "easttexas": "Tyler / East TX",
    "victoriatx": "Victoria, TX",
    "waco": "Waco, TX",
    "wichitafalls": "Wichita Falls, TX",
    "logan": "Logan, UT",
    "ogden": "Ogden-Clearfield, UT",
    "provo": "Provo / Orem, UT",
    "saltlakecity": "Salt Lake City, UT",
    "stgeorge": "St George, UT",
    "burlington": "Burlington, VT",
    "charlottesville": "Charlottesville, VA",
    "danville": "Danville, VA",
    "fredericksburg": "Fredericksburg, VA",
    "harrisonburg": "Harrisonburg, VA",
    "lynchburg": "Lynchburg, VA",
    "blacksburg": "New River Valley, VA",
    "norfolk": "Norfolk / Hampton Roads, VA",
    "richmond": "Richmond, VA",
    "roanoke": "Roanoke, VA",
    "swva": "Southwest VA",
    "winchester": "Winchester, VA",
    "bellingham": "Bellingham, WA",
    "kpr": "Kennewick-Pasco-Richland, WA",
    "moseslake": "Moses Lake, WA",
    "olympic": "Olympic Peninsula, WA",
    "pullman": "Pullman / Moscow, WA",
    "seattle": "Seattle-Tacoma, WA",
    "skagit": "Skagit / Island / SJI, WA",
    "spokane": "Spokane / Coeur d'Alene, WA",
    "wenatchee": "Wenatchee, WA",
    "yakima": "Yakima, WA",
    "charlestonwv": "Charleston, WV",
    "martinsburg": "Eastern Panhandle, WV",
    "huntington": "Huntington-Ashland, WV",
    "morgantown": "Morgantown, WV",
    "ohiovalley": "Northern Panhandle, WV",
    "parkersburg": "Parkersburg-Marietta, WV",
    "swv": "Southern WV",
    "wv": "West Virginia (old)",
    "wheeling": "Wheeling, WV",
    "appleton": "Appleton-Oshkosh-FDL, WI",
    "eauclaire": "Eau Claire, WI",
    "greenbay": "Green Bay, WI",
    "janesville": "Janesville, WI",
    "racine": "Kenosha-Racine, WI",
    "lacrosse": "La Crosse, WI",
    "madison": "Madison, WI",
    "milwaukee": "Milwaukee, WI",
    "northernwi": "Northern WI",
    "sheboygan": "Sheboygan, WI",
    "wausau": "Wausau, WI",
    "wyoming": "Wyoming",
    # --- Canada ---
    "barrie": "Barrie, ON",
    "calgary": "Calgary, AB",
    "comoxvalley": "Comox Valley, BC",
    "edmonton": "Edmonton, AB",
    "ftmcmurray": "Fort McMurray, AB",
    "halifax": "Halifax, NS",
    "hamilton": "Hamilton-Burlington, ON",
    "kamloops": "Kamloops, BC",
    "kelowna": "Kelowna / Okanagan, BC",
    "kingston": "Kingston, ON",
    "kitchener": "Kitchener-Waterloo-Cambridge, ON",
    "lethbridge": "Lethbridge, AB",
    "london": "London, ON",
    "montreal": "Montreal, QC",
    "ottawa": "Ottawa-Hull-Gatineau, ON",
    "pei": "PEI",
    "quebec": "Quebec City, QC",
    "regina": "Regina, SK",
    "saskatoon": "Saskatoon, SK",
    "soo": "Sault Ste Marie, ON",
    "stcatharines": "St Catharines, ON",
    "sudbury": "Sudbury, ON",
    "thunderbay": "Thunder Bay, ON",
    "toronto": "Toronto, ON",
    "vancouver": "Vancouver, BC",
    "victoria": "Victoria, BC",
    "whistler": "Whistler, BC",
    "windsor": "Windsor, ON",
    "winnipeg": "Winnipeg, MB",
}

# ---------------------------------------------------------------------------
# Craigslist search categories (code -> display name)
# ---------------------------------------------------------------------------

CATEGORIES: dict[str, str] = {
    # -- For Sale --
    "sss": "All For Sale",
    "ata": "Antiques",
    "ppa": "Appliances",
    "ara": "Arts & Crafts",
    "sna": "ATV/UTV/Snowmobile",
    "pta": "Auto Parts",
    "baa": "Baby & Kid Stuff",
    "bar": "Barter",
    "haa": "Health & Beauty",
    "bip": "Bicycle Parts",
    "bia": "Bicycles",
    "boa": "Boats",
    "bka": "Books",
    "bfa": "Business/Commercial",
    "cta": "Cars & Trucks",
    "ema": "CDs/DVDs/VHS",
    "moa": "Cell Phones",
    "cla": "Clothing & Accessories",
    "cba": "Collectibles",
    "syp": "Computer Parts",
    "sya": "Computers",
    "ela": "Electronics",
    "gra": "Farm & Garden",
    "zip": "Free Stuff",
    "fua": "Furniture",
    "gms": "Garage & Moving Sales",
    "foa": "General For Sale",
    "hva": "Heavy Equipment",
    "hsa": "Household Items",
    "jwa": "Jewelry",
    "maa": "Materials",
    "mca": "Motorcycles/Scooters",
    "msa": "Musical Instruments",
    "pha": "Photo/Video",
    "rva": "Recreational Vehicles",
    "sga": "Sporting Goods",
    "tia": "Tickets",
    "tla": "Tools",
    "taa": "Toys & Games",
    "tra": "Trailers",
    "vga": "Video Gaming",
    "waa": "Wanted",
    # -- Housing --
    "hhh": "All Housing",
    "apa": "Apartments / Housing For Rent",
    "swp": "Housing Swap",
    "hsw": "Housing Wanted",
    "off": "Office & Commercial",
    "prk": "Parking & Storage",
    "rea": "Real Estate For Sale",
    "roo": "Rooms & Shares",
    "sha": "Rooms Wanted",
    "sbw": "Sublets & Temporary",
    "vac": "Vacation Rentals",
    # -- Jobs --
    "jjj": "All Jobs",
    # -- Services --
    "bbb": "All Services",
    # -- Gigs --
    "ggg": "All Gigs",
    # -- Community --
    "ccc": "All Community",
}

# ---------------------------------------------------------------------------
# Sort options
# ---------------------------------------------------------------------------

SORT_OPTIONS: dict[str, str] = {
    "relevant": "Most Relevant",
    "date": "Newest",
    "priceasc": "Price Low to High",
    "pricedsc": "Price High to Low",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _build_search_url(
    location: str,
    category: str = "sss",
    query: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    sort_by: str | None = None,
    has_image: bool = False,
    posted_today: bool = False,
    bundle_duplicates: bool = True,
    search_distance: int | None = None,
    postal_code: str | None = None,
    offset: int = 0,
) -> str:
    """Build a Craigslist search URL with the given parameters."""
    base = f"https://{location}.craigslist.org/search/{category}"
    params: dict[str, Any] = {}

    if query:
        params["query"] = query
    if min_price is not None:
        params["min_price"] = min_price
    if max_price is not None:
        params["max_price"] = max_price
    if sort_by and sort_by in SORT_OPTIONS:
        params["sort"] = sort_by
    if has_image:
        params["hasPic"] = 1
    if posted_today:
        params["postedToday"] = 1
    if bundle_duplicates:
        params["bundleDuplicates"] = 1
    if search_distance is not None:
        params["search_distance"] = search_distance
    if postal_code:
        params["postal"] = postal_code
    if offset > 0:
        params["s"] = offset

    if params:
        return f"{base}?{urlencode(params)}"
    return base


def _fetch_page(url: str) -> str:
    """Fetch a page and return the HTML content."""
    logger.debug("Fetching URL: %s", url)
    with httpx.Client(
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text


def _parse_search_results(html: str, location: str) -> list[dict]:
    """Parse Craigslist search results HTML into a list of listing dicts."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict] = []

    # Modern Craigslist (2024+) uses <li class="cl-static-search-result">
    # or <div class="cl-search-result"> patterns
    listings = soup.select("li.cl-static-search-result")

    if not listings:
        # Try alternate selectors for different page structures
        listings = soup.select("div.result-row")

    if not listings:
        # Try the gallery card layout
        listings = soup.select("li.cl-search-result")

    if not listings:
        # Try even more generic approach
        listings = soup.select(".result-info")

    for item in listings:
        try:
            listing = _parse_single_result(item, location)
            if listing:
                results.append(listing)
        except Exception as e:
            logger.debug("Error parsing listing: %s", e)
            continue

    # If none of the structured selectors work, try finding all links
    # that look like listing URLs
    if not results:
        results = _parse_results_fallback(soup, location)

    return results


def _parse_single_result(item: Any, location: str) -> dict | None:
    """Parse a single search result element into a dict."""
    result: dict[str, Any] = {}

    # Try to find the title/link
    title_el = item.select_one("a.titlestring, a.result-title, a.posting-title, .title a, a[href*='/d/']")
    if not title_el:
        # For cl-static-search-result, the link is the <a> child
        title_el = item.select_one("a")

    if not title_el:
        return None

    href = title_el.get("href", "")
    if href and not href.startswith("http"):
        href = f"https://{location}.craigslist.org{href}"
    result["url"] = href

    # --- Try dedicated child elements first (modern CL layout) ---
    # cl-static-search-result often has .title, .price, .location divs
    title_div = item.select_one("div.title, .result-title, span.title")
    price_el = item.select_one("div.price, .priceinfo, .result-price, span.price, .price")
    hood_el = item.select_one("div.location, .result-hood, .neighborhood, .surlabel, .meta .area")

    if title_div:
        result["title"] = title_div.get_text(strip=True)
    if price_el:
        result["price"] = price_el.get_text(strip=True)
    if hood_el:
        result["neighborhood"] = hood_el.get_text(strip=True).strip("() ")

    # --- Fallback: if we couldn't get structured children, parse from raw text ---
    raw_text = title_el.get_text(strip=True)

    if "title" not in result or not result.get("title"):
        if "price" not in result:
            # No child elements at all — split on price pattern
            price_match = re.search(r"(\$[\d,]+)", raw_text)
            if price_match:
                result["price"] = price_match.group(1)
                before_price = raw_text[: price_match.start()].strip()
                after_price = raw_text[price_match.end() :].strip()
                result["title"] = before_price or raw_text
                if after_price and "neighborhood" not in result:
                    result["neighborhood"] = after_price
            else:
                result["title"] = raw_text
                result["price"] = None
        else:
            # Have price but no title div — strip price from raw text
            price_text = result["price"]
            clean = raw_text.replace(price_text, "").strip()
            if "neighborhood" in result:
                clean = clean.replace(result["neighborhood"], "").strip()
            result["title"] = clean if clean else raw_text

    # Ensure all keys exist
    result.setdefault("title", raw_text)
    result.setdefault("price", None)
    result.setdefault("neighborhood", None)

    # Try to extract date
    date_el = item.select_one("time, .result-date, .date, .meta .date")
    if date_el:
        result["date"] = date_el.get("datetime") or date_el.get_text(strip=True)
    else:
        result["date"] = None

    # Try to extract image
    img_el = item.select_one("img")
    if img_el:
        result["thumbnail"] = img_el.get("src") or img_el.get("data-src")
    else:
        result["thumbnail"] = None

    return result


def _parse_results_fallback(soup: BeautifulSoup, location: str) -> list[dict]:
    """Fallback parser: find listing links from the page."""
    results: list[dict] = []
    seen_urls: set[str] = set()

    # Look for links that match craigslist listing URL patterns
    # e.g. https://newyork.craigslist.org/mnh/mcy/d/listing-title/1234567890.html
    pattern = re.compile(r"/[a-z]{3}/d/[^/]+/\d+\.html")

    for a_tag in soup.find_all("a", href=pattern):
        href = a_tag.get("href", "")
        if not href.startswith("http"):
            href = f"https://{location}.craigslist.org{href}"

        if href in seen_urls:
            continue
        seen_urls.add(href)

        title = a_tag.get_text(strip=True)
        if not title or len(title) < 3:
            continue

        # Try to find price near this element
        parent = a_tag.parent
        price = None
        if parent:
            price_match = re.search(r"\$[\d,]+", parent.get_text())
            if price_match:
                price = price_match.group(0)

        results.append({
            "title": title,
            "url": href,
            "price": price,
            "neighborhood": None,
            "date": None,
            "thumbnail": None,
        })

    return results


def _parse_listing_detail(html: str, url: str) -> dict:
    """Parse a single Craigslist listing page into a detail dict."""
    soup = BeautifulSoup(html, "html.parser")
    result: dict[str, Any] = {"url": url}

    # Title — prefer the text-only element to avoid price/location in it
    title_only_el = soup.select_one("#titletextonly")
    if title_only_el:
        result["title"] = title_only_el.get_text(strip=True)
    else:
        title_el = soup.select_one(".postingtitletext, h1.postingtitle")
        if title_el:
            raw = title_el.get_text(strip=True)
            # Strip embedded price + location suffix like "-$1,200(Covington)"
            cleaned = re.sub(r"\s*-?\s*\$[\d,]+\s*(\([^)]*\))?\s*$", "", raw).strip()
            result["title"] = cleaned if cleaned else raw
        else:
            title_el = soup.select_one("title")
            result["title"] = title_el.get_text(strip=True) if title_el else "Unknown"

    # Price
    price_el = soup.select_one(".price, .postingtitletext .price")
    if price_el:
        result["price"] = price_el.get_text(strip=True)
    else:
        result["price"] = None

    # Body / description
    body_el = soup.select_one("#postingbody")
    if body_el:
        # Remove the "QR Code Link to This Post" text
        for qr in body_el.select(".print-information"):
            qr.decompose()
        result["description"] = body_el.get_text(strip=True)
    else:
        result["description"] = None

    # Attributes (condition, make, model, etc.)
    # Craigslist uses paired <span class="labl"> / <span class="valu"> siblings
    attrs: dict[str, str] = {}
    for group in soup.select(".attrgroup"):
        spans = group.select("span")
        i = 0
        while i < len(spans):
            span = spans[i]
            classes = span.get("class", [])

            if "labl" in classes:
                # This is a label span — the next sibling should be the value
                label = span.get_text(strip=True).rstrip(":").strip().lower()
                if i + 1 < len(spans) and "valu" in spans[i + 1].get("class", []):
                    val = spans[i + 1].get_text(strip=True)
                    if label and val:
                        attrs[label] = val
                    i += 2
                    continue
                elif label:
                    attrs[label] = ""
            elif "valu" in classes:
                # Standalone value span (no preceding label)
                val = span.get_text(strip=True)
                # Check for special classes like "year", "makemodel"
                if "year" in classes and val:
                    attrs["year"] = val
                elif "makemodel" in classes and val:
                    attrs["make/model"] = val
                elif val:
                    # Could be a note like "odometer broken"
                    attrs[val.lower()] = "yes"
            else:
                # Generic span — try key:value or standalone
                text = span.get_text(" ", strip=True)
                if ":" in text:
                    key, _, val = text.partition(":")
                    key = key.strip().lower()
                    val = val.strip()
                    if key and val:
                        attrs[key] = val
                elif text:
                    attrs[text.lower()] = "yes"
            i += 1
    result["attributes"] = attrs if attrs else None

    # Location
    # Try map address
    map_addr = soup.select_one(".mapaddress, div.mapAndAttrs small")
    if map_addr:
        result["location"] = map_addr.get_text(strip=True)
    else:
        result["location"] = None

    # Google Maps link (lat/long)
    map_el = soup.select_one("#map")
    if map_el:
        lat = map_el.get("data-latitude")
        lon = map_el.get("data-longitude")
        if lat and lon:
            result["latitude"] = float(lat)
            result["longitude"] = float(lon)

    # Posted date
    time_el = soup.select_one("time.date, time.timeago")
    if time_el:
        result["posted"] = time_el.get("datetime") or time_el.get_text(strip=True)
    else:
        result["posted"] = None

    # Images
    images: list[str] = []
    for img_link in soup.select("a.thumb, .gallery img, .swipe img"):
        src = img_link.get("href") or img_link.get("src") or img_link.get("data-src")
        if src and src not in images:
            images.append(src)
    # Also check the thumbs data attribute
    thumb_div = soup.select_one("#thumbs")
    if thumb_div:
        for a_tag in thumb_div.select("a"):
            href = a_tag.get("href")
            if href and href not in images:
                images.append(href)
    result["images"] = images if images else None

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def search_listings(
    query: str,
    location: str = DEFAULT_LOCATION,
    category: str = "sss",
    min_price: int | None = None,
    max_price: int | None = None,
    sort_by: str = "relevant",
    has_image: bool = False,
    posted_today: bool = False,
    bundle_duplicates: bool = True,
    search_distance: int | None = None,
    postal_code: str | None = None,
    max_results: int = 25,
) -> dict:
    """
    Search Craigslist listings and return parsed results.

    Returns a dict with:
      - query: the search query
      - location: location code used
      - location_name: human-readable location name
      - category: category code used
      - category_name: human-readable category name
      - url: the search URL
      - total_results: approximate number of results found
      - results: list of listing dicts
    """
    loc = location.lower().strip()
    if loc not in LOCATIONS:
        # Try to find a matching location
        matches = [k for k, v in LOCATIONS.items() if loc in k or loc in v.lower()]
        if matches:
            loc = matches[0]
        else:
            return {
                "error": f"Unknown location: '{location}'. Use list_locations to see valid options.",
                "suggestion": "Try a location like 'newyork', 'losangeles', 'chicago', 'seattle', etc.",
            }

    cat = category.lower().strip()
    if cat not in CATEGORIES:
        return {
            "error": f"Unknown category: '{category}'. Use list_categories to see valid options.",
            "suggestion": "Try 'sss' (All For Sale), 'mca' (Motorcycles), 'cta' (Cars & Trucks), etc.",
        }

    all_results: list[dict] = []
    offset = 0
    url = ""

    while len(all_results) < max_results:
        url = _build_search_url(
            location=loc,
            category=cat,
            query=query,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            has_image=has_image,
            posted_today=posted_today,
            bundle_duplicates=bundle_duplicates,
            search_distance=search_distance,
            postal_code=postal_code,
            offset=offset,
        )

        try:
            html = _fetch_page(url)
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error {e.response.status_code}: {e.response.reason_phrase}", "url": url}
        except httpx.RequestError as e:
            return {"error": f"Request failed: {e}", "url": url}

        page_results = _parse_search_results(html, loc)

        if not page_results:
            break

        all_results.extend(page_results)
        offset += len(page_results)

        # Craigslist typically returns ~120 results per page
        if len(page_results) < 20:
            break

    # Trim to max_results
    all_results = all_results[:max_results]

    # Build first page URL for reference
    first_url = _build_search_url(
        location=loc,
        category=cat,
        query=query,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        has_image=has_image,
        posted_today=posted_today,
        bundle_duplicates=bundle_duplicates,
        search_distance=search_distance,
        postal_code=postal_code,
    )

    return {
        "query": query,
        "location": loc,
        "location_name": LOCATIONS.get(loc, loc),
        "category": cat,
        "category_name": CATEGORIES.get(cat, cat),
        "url": first_url,
        "result_count": len(all_results),
        "results": all_results,
    }


def get_listing_details(url: str) -> dict:
    """
    Fetch and parse a single Craigslist listing page.

    Parameters
    ----------
    url : str
        Full URL to a Craigslist listing page.

    Returns
    -------
    dict
        Listing details including title, price, description, attributes,
        location, images, and posting date.
    """
    try:
        html = _fetch_page(url)
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.reason_phrase}", "url": url}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {e}", "url": url}

    return _parse_listing_detail(html, url)


def get_locations(filter_text: str | None = None) -> dict:
    """
    Return available Craigslist locations.

    Parameters
    ----------
    filter_text : str, optional
        Filter locations by name (case-insensitive substring match).

    Returns
    -------
    dict
        A dict with total count and list of {code, name} dicts.
    """
    if filter_text:
        ft = filter_text.lower()
        filtered = {k: v for k, v in LOCATIONS.items() if ft in k or ft in v.lower()}
    else:
        filtered = LOCATIONS

    return {
        "total": len(filtered),
        "locations": [{"code": k, "name": v} for k, v in sorted(filtered.items(), key=lambda x: x[1])],
    }


def get_categories() -> dict:
    """
    Return available Craigslist search categories.

    Returns
    -------
    dict
        A dict with total count and list of {code, name} dicts.
    """
    return {
        "total": len(CATEGORIES),
        "categories": [{"code": k, "name": v} for k, v in CATEGORIES.items()],
    }
