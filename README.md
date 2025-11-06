# Flights Scanner

A Python application for fetching and analyzing flight data from Ryanair and FlightConnections.

## Features

### 1. Ryanair API Integration (`main.py`)
- Fetch flight availability from Ryanair API
- Parse responses using Pydantic models
- Display flight information with prices, times, and durations
- Configurable search parameters (origin, destination, dates, passengers)

### 2. FlightConnections Data Scraper (`flight_connector.py`)
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

### Ryanair Models
- `RyanairResponse`: Complete API response
- `Trip`: Trip details (origin, destination, dates)
- `Flight`: Individual flight information
- `Fare`: Pricing information
- `Segment`: Flight segment details

### FlightConnections Models
- `AirportGeometry`: Raw airport data from tiles
- `Airport`: Parsed airport information
- `FlightConnectionsDatabase`: Airport database with lookup functions
- `TileData`: Tile JSON structure

## Files

- `main.py` - Ryanair API integration and main entry point
- `models.py` - Pydantic models for Ryanair API responses
- `flight_connector.py` - FlightConnections data scraper
- `test_flight_connector.py` - Test script with sample data
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

1. **FlightConnections CDN Access**: The CDN currently blocks automated requests. Alternative solutions are needed for live data access.
2. **Rate Limiting**: Be mindful of API rate limits when making multiple requests to Ryanair.
3. **Date Format**: Ryanair API requires dates in YYYY-MM-DD format.

## License

This project is for educational purposes.
