"""
craigslist-mcp Server — search Craigslist listings by location, category,
and keyword.

Tools exposed:
  • search_craigslist   — search listings with filters
  • get_listing         — get full details of a single listing
  • list_locations      — list available Craigslist locations
  • list_categories     — list available search categories
"""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from craigslist_mcp.scraper import (
    search_listings,
    get_listing_details,
    get_locations,
    get_categories,
    LOCATIONS,
    CATEGORIES,
    SORT_OPTIONS,
)

logger = logging.getLogger("craigslist_mcp")

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="craigslist-mcp",
    instructions=(
        "An MCP server that searches Craigslist listings across all US and "
        "Canadian cities. Supports searching by keyword, location, category, "
        "price range, and more. Use list_locations to find the right location "
        "code, and list_categories to see available categories. "
        "Locations work just like craigslist.org — each city has its own "
        "subdomain (e.g. 'seattle', 'losangeles', 'sfbay', 'chicago')."
    ),
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def search_craigslist(
    query: str,
    location: str = "newyork",
    category: str = "sss",
    min_price: int | None = None,
    max_price: int | None = None,
    sort_by: str = "relevant",
    has_image: bool = False,
    posted_today: bool = False,
    search_distance: int | None = None,
    postal_code: str | None = None,
    max_results: int = 25,
) -> dict:
    """Search Craigslist listings by keyword, location, and category.

    Parameters
    ----------
    query : str
        Search keywords (e.g. "dirtbike", "mountain bike", "couch").
    location : str, optional
        Craigslist location/city code — the subdomain used on craigslist.org.
        Examples: "newyork", "losangeles", "sfbay", "chicago", "seattle",
        "dallas", "atlanta", "denver", "portland", "phoenix", "miami",
        "boston", "detroit", "minneapolis", "houston", "austin", "sandiego",
        "toronto", "vancouver".
        Use the list_locations tool to find valid codes.
        Default: "newyork".
    category : str, optional
        Craigslist search category code. Common ones:
        - "sss" = All For Sale (default)
        - "mca" = Motorcycles/Scooters
        - "cta" = Cars & Trucks
        - "sga" = Sporting Goods
        - "bia" = Bicycles
        - "sna" = ATV/UTV/Snowmobile
        - "boa" = Boats
        - "rva" = Recreational Vehicles
        - "tla" = Tools
        - "ela" = Electronics
        - "fua" = Furniture
        - "apa" = Apartments / Housing For Rent
        - "rea" = Real Estate For Sale
        - "jjj" = All Jobs
        Use list_categories for the full list.
    min_price : int, optional
        Minimum price filter in dollars.
    max_price : int, optional
        Maximum price filter in dollars.
    sort_by : str, optional
        Sort order — "relevant" (default), "date" (newest first),
        "priceasc" (low to high), "pricedsc" (high to low).
    has_image : bool, optional
        If True, only return listings with images (default: False).
    posted_today : bool, optional
        If True, only return listings posted today (default: False).
    search_distance : int, optional
        Search radius in miles from postal_code. Requires postal_code.
    postal_code : str, optional
        ZIP/postal code to center the distance search on.
    max_results : int, optional
        Maximum number of results to return (default: 25, max: 120).

    Returns
    -------
    dict
        A dict containing:
        - query: the search terms
        - location / location_name: the Craigslist city used
        - category / category_name: the category searched
        - url: direct link to the search on craigslist.org
        - result_count: number of results returned
        - results: list of listings, each with title, url, price,
          neighborhood, date, and thumbnail
    """
    cap = min(max_results, MAX_RESULTS_CAP)
    return search_listings(
        query=query,
        location=location,
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        has_image=has_image,
        posted_today=posted_today,
        search_distance=search_distance,
        postal_code=postal_code,
        max_results=cap,
    )


MAX_RESULTS_CAP = 120


@mcp.tool()
def get_listing(url: str) -> dict:
    """Get full details of a single Craigslist listing.

    Parameters
    ----------
    url : str
        The full URL of a Craigslist listing page.
        Example: "https://newyork.craigslist.org/mnh/mcy/d/new-york-2022-honda-crf250r/1234567890.html"

    Returns
    -------
    dict
        Detailed listing information including:
        - title: listing title
        - price: asking price
        - description: full listing body text
        - attributes: item attributes (condition, make, model, etc.)
        - location: map address if available
        - latitude / longitude: GPS coordinates if available
        - posted: posting date/time
        - images: list of image URLs
        - url: the listing URL
    """
    return get_listing_details(url=url)


@mcp.tool()
def list_locations(filter_text: str | None = None) -> dict:
    """List available Craigslist locations (cities/regions).

    Craigslist uses location subdomains just like the site itself —
    e.g. "seattle" for seattle.craigslist.org, "sfbay" for sfbay.craigslist.org.

    Parameters
    ----------
    filter_text : str, optional
        Filter locations by keyword (case-insensitive).
        Examples: "california", "texas", "new york", "florida".
        If omitted, returns all locations.

    Returns
    -------
    dict
        A dict with:
        - total: number of matching locations
        - locations: list of {code, name} where code is the subdomain
          to use with search_craigslist
    """
    return get_locations(filter_text=filter_text)


@mcp.tool()
def list_categories() -> dict:
    """List all available Craigslist search categories.

    Returns category codes you can pass to search_craigslist's `category`
    parameter. Categories include For Sale subcategories (motorcycles,
    cars, electronics, etc.), Housing, Jobs, Services, and more.

    Returns
    -------
    dict
        A dict with:
        - total: number of categories
        - categories: list of {code, name} pairs
    """
    return get_categories()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(verbose: bool = False) -> None:
    """Start the MCP server."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger.info("Starting craigslist-mcp server v0.1.0")
    mcp.run()
