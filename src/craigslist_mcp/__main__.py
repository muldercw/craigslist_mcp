"""CLI entry point for craigslist-mcp server."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="craigslist-mcp",
        description="MCP server that searches Craigslist listings by location, category, and keyword.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging.",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Print server info (locations, categories), then exit.",
    )
    args = parser.parse_args()

    if args.info:
        from craigslist_mcp.scraper import LOCATIONS, CATEGORIES
        import json

        info = {
            "name": "craigslist-mcp",
            "version": "0.1.0",
            "description": "MCP server — search Craigslist listings by location, category, and keyword.",
            "total_locations": len(LOCATIONS),
            "sample_locations": dict(list(LOCATIONS.items())[:20]),
            "categories": CATEGORIES,
        }
        print(json.dumps(info, indent=2))
        sys.exit(0)

    from craigslist_mcp.server import run
    run(verbose=args.verbose)


if __name__ == "__main__":
    main()
