# Flights Scanner

A Python application for fetching and analyzing flight data from Ryanair, Wizz Air, and FlightConnections.

## Features

### 1. Ryanair API Integration (`ryanair.py`)
- Fetch flight availability from Ryanair API
- Parse responses using Pydantic models
- Display flight information with prices, times, and durations
- Configurable search parameters (origin, destination, dates, passengers)
- **Note**: Ryanair also uses bot protection that blocks automated requests

### 2. Wizz Air API Integration (`wizz_air.py`)
- Fetch available flight dates between airports
- Search for detailed flight information with pricing
- Support for one-way and round-trip searches
- Multiple fare bundles (basic, smart, middleTwo, plus)
- Parallel scanning of multiple dates
- Comprehensive pricing breakdown with fees

### 3. FlightConnections Data Scraper (`flight_connector.py`)
- Scrape airport data from FlightConnections CDN
- Parse airport information including:
  - Airport codes (IATA 3-letter codes)
  - Airport names
  - Unique identifiers
  - Tile coordinates
  - Size/importance indicators
- Build a comprehensive airport database
- Lookup airports by code or ID
- **NEW**: Manage flight connections/routes between airports:
  - Get all airports as {code: city} dictionary
  - Get all destinations from a specific airport
  - Track and query flight routes/connections
  - Find major airport hubs by connection count

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Ryanair Flight Search

**Note:** Ryanair API also uses bot protection that blocks automated requests (403 Forbidden). The code includes browser-like headers but may still be blocked. Similar to Wizz Air, you may need to:
- Extract headers/cookies from a browser session
- Use browser automation (Selenium/Playwright)
- Access from environments that aren't flagged as bots

Test the API:

```bash
python3 ryanair.py  # Will show instructions for extracting cookies
```

Example usage with browser-extracted cookies:

```python
from ryanair import get_ryanair_flights

# Extract cookies from browser DevTools (see module docstring for instructions)
cookies = "sid=xxx; rid=yyy; xid=zzz; PIM-SESSION-ID=abc; ..."

# Search for flights
flights_data = get_ryanair_flights(
    origin="WRO",
    destination="ALC",
    date_out="2025-12-11",
    date_in="2025-12-15",
    adt=1,
    cookies=cookies  # Required for bot protection bypass
)

# Access flight information
for trip in flights_data.trips:
    print(f"{trip.origin} -> {trip.destination}")
    for date_info in trip.dates:
        for flight in date_info.flights:
            price = flight.regularFare.fares[0].amount
            print(f"  Flight {flight.flightNumber}: {price} {flights_data.currency}")
```

### Wizz Air Flight Search

**Note:** Wizz Air uses bot protection (Kasada SDK + Akamai Bot Manager) that blocks automated requests.

Extract headers and cookies from browser and use with the API:

```python
from wizz_air import WizzAirAPI

# Headers extracted from browser DevTools (see wizz_air.py docstring for instructions)
bot_protection_headers = {
    'X-RequestVerificationToken': 'YOUR_TOKEN',
    'x-kpsdk-ct': 'YOUR_KASADA_TOKEN',
    'x-kpsdk-cd': 'YOUR_KASADA_DATA',
    'x-kpsdk-v': 'j-1.1.29259',
    'x-kpsdk-h': 'YOUR_KASADA_HASH',
}

cookies = {
    'RequestVerificationToken': 'YOUR_TOKEN',
    'ak_bm_vw_1.1': 'YOUR_AKAMAI_SESSION',
    'ASP.NET_SessionId': 'YOUR_SESSION_ID',
}

# Initialize with extracted headers
api = WizzAirAPI(
    custom_headers=bot_protection_headers,
    cookies=cookies
)

# Use the API
flight_dates = api.get_flight_dates("WRO", "NCE", "2025-12-13", "2026-01-13")
```

⚠️ **Warning**: Headers expire quickly (minutes to hours) and this may violate Terms of Service.

Test with sample data (no API access needed):

```bash
python3 test_wizz_air.py
```

Example usage:

```python
from wizz_air import WizzAirAPI

api = WizzAirAPI()

# 1. Get available flight dates
flight_dates = api.get_flight_dates(
    departure_station="WRO",
    arrival_station="NCE",
    from_date="2025-12-13",
    to_date="2026-01-13"
)

print(f"Found {len(flight_dates.flightDates)} available dates")

# 2. Search for specific flight (round trip)
search_result = api.search_flights(
    departure_station="WRO",
    arrival_station="NCE",
    departure_date="2025-12-13T00:00:00",
    return_date="2025-12-20T00:00:00",
    adult_count=1
)

# Get cheapest prices
for flight in search_result.outboundFlights:
    cheapest_fare = flight.get_cheapest_fare()
    print(f"Flight {flight.flightNumber}: {cheapest_fare.basePrice.amount} PLN")

# Get total cheapest round trip price
total_price = search_result.get_total_cheapest_price()
print(f"Total: {total_price} {search_result.currencyCode}")

# 3. Scan all available flights in date range
all_results = api.scan_all_flights(
    departure_station="WRO",
    arrival_station="NCE",
    from_date="2025-12-13",
    to_date="2025-12-20",
    return_date_offset_days=7,  # 7-day round trip
    adult_count=1
)

# Find best deal
best_deal = min(
    all_results,
    key=lambda r: r.get_total_cheapest_price() or float('inf')
)
```

### FlightConnections Airport Database

**Note:** The FlightConnections CDN currently blocks automated requests (403 Forbidden). The code structure is complete and tested with sample data.

To test the parsing logic with sample data:

```bash
python3 test_flight_connector.py
```

For production use with live data, you may need to:
- Use browser automation (Selenium/Playwright)
- Access the API through a proxy
- Contact FlightConnections for API access
- Update the tile version/date in the URL if the format has changed

Example usage (when CDN access is available):

```python
from flight_connector import build_airport_database

# Build the airport database
database = build_airport_database()

# 1. Get all airports as a dictionary {code: name}
all_airports = database.get_all_airports_dict()
print(f"Total airports: {len(all_airports)}")
# Output: {"JFK": "New York", "LAX": "Los Angeles", ...}

# 2. Get all airports as Airport objects
airports = database.get_all_airports()
for airport in airports[:5]:
    print(f"{airport.code}: {airport.name}")

# 3. Lookup specific airport
airport = database.get_airport_by_code("LAX")
print(f"{airport.code}: {airport.name} (ID: {airport.airport_id})")

# 4. Add connections between airports
database.add_connection("JFK", "LAX")  # One-way
database.add_bidirectional_connection("LAX", "ORD")  # Both ways

# 5. Get all flights/connections from an airport
connections = database.get_connections_from("JFK")
print(f"Destinations from JFK: {connections}")
# Output: ['LAX', 'ORD', ...]

# 6. Get connections with full airport names
connections_detailed = database.get_connections_from_with_names("JFK")
for conn in connections_detailed:
    print(f"  → {conn['code']}: {conn['name']}")

# 7. Get connection statistics
count = database.get_connection_count("JFK")
print(f"JFK has {count} destinations")

# 8. Find most connected airports
top_hubs = database.get_airports_by_connection_count(limit=10)
for hub in top_hubs:
    print(f"{hub['code']} ({hub['name']}): {hub['connections']} destinations")
```

## Data Models

### Ryanair Models (`ryanair_models.py`)
- `RyanairResponse`: Complete API response
- `Trip`: Trip details (origin, destination, dates)
- `Flight`: Individual flight information
- `Fare`: Pricing information
- `Segment`: Flight segment details

### Wizz Air Models (`wizz_air_models.py`)
- `FlightDatesResponse`: Available flight dates
- `SearchResponse`: Complete search response with flights and bundles
- `Flight`: Flight details with fares, times, and aircraft info
- `Fare`: Detailed fare information for different bundles
- `Price`: Price with currency and exchange info
- `FlightPriceDetail`: Detailed pricing breakdown
- `Bundle`: Bundle information (basic, smart, middleTwo, plus)
- `WDC`: Wizz Discount Club information

### FlightConnections Models (`flight_connector.py`)
- `AirportGeometry`: Raw airport data from tiles
- `Airport`: Parsed airport information
- `FlightConnectionsDatabase`: Airport database with:
  - Airport storage and lookup by code/ID
  - Connection/route management
  - Functions to query destinations from airports
  - Statistics on most connected airports
- `TileData`: Tile JSON structure

**Key FlightConnectionsDatabase Methods**:
- `get_all_airports_dict()`: Get {code: name} dictionary
- `get_connections_from(code)`: Get all destinations from an airport
- `get_connections_from_with_names(code)`: Get destinations with full info
- `add_connection(from, to)`: Add one-way flight route
- `add_bidirectional_connection(a, b)`: Add round-trip route
- `get_connection_count(code)`: Count destinations from airport
- `get_airports_by_connection_count(limit)`: Find major hubs

## Files

- `ryanair.py` - Ryanair API integration module (includes cookie instructions)
- `ryanair_models.py` - Pydantic models for Ryanair API responses
- `wizz_air.py` - Wizz Air API integration module (includes header/cookie support)
- `wizz_air_models.py` - Pydantic models for Wizz Air API responses
- `test_wizz_air.py` - Test script for Wizz Air with sample data
- `flight_connector.py` - FlightConnections data scraper
- `test_flight_connector.py` - Test script for FlightConnections with sample data
- `requirements.txt` - Python dependencies

## Dependencies

- `requests` - HTTP requests
- `pydantic` - Data validation and parsing

## Example Output

### Ryanair Flight Search
```
Fetching Ryanair flights...

Currency: PLN
Number of trips: 2

WRO (Wroclaw) -> ALC (Alicante)

  Date: 2025-12-11T00:00:00.000
    Flight FR 9876: 2025-12-11T15:40:00.000 -> 2025-12-11T18:50:00.000
    Duration: 03:10, Price: 298.73 PLN
```

### Wizz Air Flight Search (Sample Data)
```
Testing Flight Dates Response Parsing
✓ Parsed 5 flight dates
✓ Converted to datetime objects: 2025-12-13

Testing Search Response Parsing
✓ Parsed flight: 1829
  Route: WRO -> NCE
  Departure: 2025-12-13T18:35:00
  Arrival: 2025-12-13T20:35:00
  Duration: 02:00:00 (120 minutes)
  Aircraft: Airbus A321neo
  Number of fare options: 2

✓ Cheapest fare:
  Bundle: basic
  Price: 90.0 PLN
  Administration fee: 38.0 PLN

✓ Available bundles:
  - basic: 90.0 PLN
  - smart: 219.0 PLN
```

### FlightConnections Parser (Sample Data)
```
Parsed Airports:
  ABI  | Abilene              | ID:  555 | Coords: [228, 158]
  ABR  | Aberdeen             | ID:  564 | Coords: [232, 111]
  ACT  | Waco                 | ID:  584 | Coords: [235, 161]
  ...

Total airports in database: 12

Testing Airport Connections:
1. Get all airports as dictionary:
  ATL: Atlanta
  DFW: Dallas
  JFK: New York
  LAX: Los Angeles
  ORD: Chicago

2. Get connections from JFK:
  Airport codes: ['ATL', 'LAX', 'ORD']

3. Get connections from JFK with names:
  ATL: Atlanta
  LAX: Los Angeles
  ORD: Chicago

4. Get airports by connection count (top 3):
  JFK (New York): 3 connections
  LAX (Los Angeles): 3 connections
  ORD (Chicago): 3 connections
```

## Known Limitations

1. **Bot Protection (Ryanair & Wizz Air)**:

   **Ryanair**:
   - Uses bot protection that blocks automated requests (403 Forbidden / "Access denied")
   - Code includes browser-like headers but still gets blocked
   - May require browser automation or running from non-flagged environments

   **Wizz Air**:
   - Uses Kasada SDK + Akamai Bot Manager for advanced bot detection
   - Blocks automated requests with 403 Forbidden
   - Headers include: `x-kpsdk-*` (Kasada), `X-RequestVerificationToken` (CSRF)

   **Solutions for both**:
   - Extract headers/cookies from browser session (temporary, expires in minutes/hours)
   - Use browser automation (Selenium with undetected-chromedriver recommended)
   - Consider official API access if available
   - Run from environments not flagged as datacenter/VPS IPs
   - **Warning**: Bypassing bot protection may violate Terms of Service

2. **FlightConnections CDN Access**:
   - CDN blocks automated requests with 403 Forbidden
   - Alternative solutions needed for live data access
   - Code structure complete and tested with sample data

3. **Rate Limiting**:
   - Be mindful of API rate limits when making multiple requests
   - Implement delays between requests to avoid triggering bot detection
   - Wizz Air: Use `max_workers` parameter to control parallel request count

4. **Date Formats**:
   - Ryanair API: YYYY-MM-DD format (e.g., "2025-12-11")
   - Wizz Air API: YYYY-MM-DDTHH:MM:SS format (e.g., "2025-12-11T00:00:00")

5. **Header/Cookie Expiration**:
   - Browser-extracted headers expire quickly (typically minutes to hours)
   - Need to refresh headers periodically for continued access
   - Browser automation provides more stable long-term solution

## License

This project is for educational purposes.
