# Flights Scanner

A Python application for fetching and analyzing flight data from Ryanair, Wizz Air, and FlightConnections.

## Features

### 1. Ryanair API Integration (`main.py`)
- Fetch flight availability from Ryanair API
- Parse responses using Pydantic models
- Display flight information with prices, times, and durations
- Configurable search parameters (origin, destination, dates, passengers)

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

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Ryanair Flight Search

```python
python3 main.py
```

Or use the API programmatically:

```python
from main import get_ryanair_flights

# Search for flights
flights_data = get_ryanair_flights(
    origin="WRO",
    destination="ALC",
    date_out="2025-12-11",
    date_in="2025-12-15",
    adt=1  # Number of adults
)

# Access flight information
for trip in flights_data.trips:
    print(f"{trip.origin} -> {trip.destination}")
    for date_info in trip.dates:
        for flight in date_info.flights:
            print(f"  Flight {flight.flightNumber}: {flight.time[0]} -> {flight.time[1]}")
```

### Wizz Air Flight Search

**Note:** The Wizz Air API currently blocks automated requests (403 Forbidden). The code structure is complete and tested with sample data.

To test the parsing logic with sample data:

```bash
python3 test_wizz_air.py
```

Example usage (when API access is available):

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

# Get all airports
airports = database.get_all_airports()

# Lookup specific airport
airport = database.get_airport_by_code("LAX")
print(f"{airport.code}: {airport.name} (ID: {airport.airport_id})")
```

## Data Models

### Ryanair Models (`models.py`)
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
- `FlightConnectionsDatabase`: Airport database with lookup functions
- `TileData`: Tile JSON structure

## Files

- `main.py` - Ryanair API integration and main entry point
- `models.py` - Pydantic models for Ryanair API responses
- `wizz_air.py` - Wizz Air API integration module
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
```

## Known Limitations

1. **Wizz Air API Access**: The API currently blocks automated requests (403 Forbidden). For production use, consider:
   - Browser automation tools (Selenium/Playwright)
   - Proxy services
   - Official API access if available

2. **FlightConnections CDN Access**: The CDN currently blocks automated requests. Alternative solutions are needed for live data access.

3. **Rate Limiting**: Be mindful of API rate limits when making multiple requests to Ryanair.

4. **Date Formats**:
   - Ryanair API requires dates in YYYY-MM-DD format
   - Wizz Air API requires dates in YYYY-MM-DDTHH:MM:SS format

## License

This project is for educational purposes.
