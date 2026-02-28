# craigslist-mcp

An MCP (Model Context Protocol) server that **searches Craigslist listings** across all US and Canadian cities — like browsing craigslist.org, but for AI agents.

Give it a search query, location, and category and it will fetch matching listings, parse them, and return structured results. Supports price filters, distance search, sorting, and full listing details.

## ✨ Features

- **400+ locations** — every US and Canadian Craigslist city/region
- **50+ categories** — motorcycles, cars, electronics, furniture, housing, jobs, and more
- **Location-based** — uses the same city subdomains as craigslist.org
- **Price filters** — min/max price range
- **Distance search** — search within X miles of a ZIP code
- **Sort options** — relevant, newest, price low/high
- **Listing details** — fetch full description, attributes, images, map location
- **Four MCP tools** — `search_craigslist`, `get_listing`, `list_locations`, `list_categories`
- **Cross-platform** — Windows, macOS, Linux
- **Zero config** — works out of the box

## 🚀 Quick Start

### Run directly from GitHub

```bash
uvx --from git+https://github.com/muldercw/craigslist_mcp.git craigslist-mcp
```

### Local development

```bash
git clone https://github.com/muldercw/craigslist_mcp.git
cd craigslist_mcp
uv pip install -e .
craigslist-mcp              # start the MCP server
craigslist-mcp --info       # print locations & categories
craigslist-mcp --verbose    # debug logging
```

## 🔌 Integration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "craigslist-mcp": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/muldercw/craigslist_mcp.git",
        "craigslist-mcp"
      ]
    }
  }
}
```

### VS Code / Copilot

Add to your `.vscode/mcp.json`:

```json
{
  "servers": {
    "craigslist-mcp": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/muldercw/craigslist_mcp.git",
        "craigslist-mcp"
      ]
    }
  }
}
```

## 🛠 Tool Reference

### `search_craigslist`

Search Craigslist listings by keyword, location, and category.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | string | (required) | Search keywords (e.g. "dirtbike", "honda crf") |
| location | string | "newyork" | City code — e.g. "seattle", "losangeles", "sfbay" |
| category | string | "sss" | Category code — e.g. "mca" (motorcycles), "cta" (cars) |
| min_price | int | null | Minimum price in dollars |
| max_price | int | null | Maximum price in dollars |
| sort_by | string | "relevant" | "relevant", "date", "priceasc", "pricedsc" |
| has_image | bool | false | Only show listings with images |
| posted_today | bool | false | Only show listings posted today |
| search_distance | int | null | Radius in miles (requires postal_code) |
| postal_code | string | null | ZIP code for distance search |
| max_results | int | 25 | Max results to return (up to 120) |

Returns a list of listings with title, URL, price, neighborhood, date, and thumbnail.

### `get_listing`

Get full details of a single Craigslist listing.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | string | (required) | Full URL of a Craigslist listing |

Returns title, price, full description, attributes (condition, make, model...), location, GPS coordinates, images, and posting date.

### `list_locations`

List available Craigslist locations (cities/regions).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| filter_text | string | null | Filter by keyword (e.g. "california", "texas") |

### `list_categories`

List all available Craigslist search categories.

No parameters. Returns all category codes and names.

## 📋 Example Queries

Search for dirtbikes in Seattle:
```
search_craigslist(query="dirtbike", location="seattle", category="mca")
```

Find cheap furniture in Los Angeles:
```
search_craigslist(query="couch", location="losangeles", category="fua", max_price=200)
```

Search for cars near a ZIP code:
```
search_craigslist(query="honda civic", location="sfbay", category="cta", search_distance=25, postal_code="94102")
```

Find apartments in Chicago posted today:
```
search_craigslist(query="studio", location="chicago", category="apa", posted_today=True)
```

## 📋 Requirements

- Python ≥ 3.10
- [FastMCP](https://github.com/jlowin/fastmcp) ≥ 2.0 — serves the MCP protocol
- [httpx](https://www.python-httpx.org/) — HTTP client
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

Built for the MCP ecosystem. Contributions welcome!
