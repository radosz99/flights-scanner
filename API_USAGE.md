# Ryanair Flight Scanner API Documentation

A REST API for filtering and sorting Ryanair flight data with price tracking capabilities.

## Starting the API

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server
python api.py

# Or use uvicorn directly
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

Interactive API documentation (Swagger UI): http://localhost:8000/docs

## API Endpoints

### 1. Root Endpoint
**GET /** - API information and available endpoints

```bash
curl http://localhost:8000/
```

### 2. Query Flights
**GET /flights** - Search and filter flights with pagination

**Query Parameters:**
- `origin` (string): Filter by origin airport code (e.g., WRO, KRK, WAW)
- `destination` (string): Filter by destination airport code (e.g., BCN, LHR, CDG)
- `date_from` (date): Filter flights departing from this date (YYYY-MM-DD)
- `date_to` (date): Filter flights departing until this date (YYYY-MM-DD)
- `min_price` (float): Minimum price filter
- `max_price` (float): Maximum price filter
- `currency` (string): Filter by currency code (e.g., EUR, PLN)
- `sort_by` (string): Sort results by field - options: `price`, `price_desc`, `date`, `duration`
- `page` (int): Page number (default: 1)
- `page_size` (int): Number of results per page (default: 50, max: 500)

**Examples:**

```bash
# Find cheap flights from Warsaw to Barcelona
curl "http://localhost:8000/flights?origin=WAW&destination=BCN&max_price=100&sort_by=price"

# Find all flights from Wroclaw in December 2025
curl "http://localhost:8000/flights?origin=WRO&date_from=2025-12-01&date_to=2025-12-31"

# Find flights under 50 EUR sorted by date
curl "http://localhost:8000/flights?max_price=50&currency=EUR&sort_by=date"

# Get expensive flights sorted by price (descending)
curl "http://localhost:8000/flights?min_price=200&sort_by=price_desc"

# Get second page of results
curl "http://localhost:8000/flights?origin=KRK&page=2&page_size=100"
```

**Response:**
```json
{
  "total": 150,
  "page": 1,
  "page_size": 50,
  "flights": [
    {
      "flight_id": "WRO_BCN_FR1234_2025-12-06_10:30",
      "origin": "WRO",
      "origin_name": "Wroclaw",
      "destination": "BCN",
      "destination_name": "Barcelona",
      "flight_number": "FR1234",
      "operator": "RYANAIR",
      "date_out": "2025-12-06",
      "departure_time": "10:30",
      "arrival_time": "13:15",
      "duration": "02h 45m",
      "current_price": 49.99,
      "currency": "EUR",
      "fares_left": 5,
      "infants_left": 2,
      "segments": [...],
      "first_seen": "2025-11-07T10:00:00",
      "last_seen": "2025-11-07T14:00:00",
      "scan_count": 3,
      "price_history": [
        {
          "price": 59.99,
          "timestamp": "2025-11-07T10:00:00",
          "change": 0
        },
        {
          "price": 49.99,
          "timestamp": "2025-11-07T14:00:00",
          "change": -10.00
        }
      ]
    }
  ]
}
```

### 3. Get Specific Flight
**GET /flights/{flight_id}** - Get detailed information about a specific flight

```bash
curl "http://localhost:8000/flights/WRO_BCN_FR1234_2025-12-06_10:30"
```

### 4. Get Statistics
**GET /flights/stats/summary** - Get database statistics

```bash
curl http://localhost:8000/flights/stats/summary
```

**Response:**
```json
{
  "total_flights": 15234,
  "flights_with_price_changes": 3421,
  "unique_origins": 13,
  "unique_destinations": 245,
  "cheapest_flight": {
    "flight_id": "WRO_BUD_FR5678_2025-12-15_06:00",
    "route": "WRO → BUD",
    "price": 9.99,
    "currency": "EUR",
    "date": "2025-12-15"
  },
  "most_expensive_flight": {
    "flight_id": "WAW_LHR_FR9999_2025-12-25_18:00",
    "route": "WAW → LHR",
    "price": 299.99,
    "currency": "EUR",
    "date": "2025-12-25"
  },
  "average_price": 67.45
}
```

### 5. Get Origin Airports
**GET /airports/origins** - Get list of all available origin airports

```bash
curl http://localhost:8000/airports/origins
```

**Response:**
```json
{
  "origins": [
    {
      "code": "GDN",
      "name": "Gdansk",
      "flight_count": 1234
    },
    {
      "code": "KRK",
      "name": "Krakow",
      "flight_count": 2345
    }
  ]
}
```

### 6. Get Destination Airports
**GET /airports/destinations** - Get list of all available destination airports

```bash
curl http://localhost:8000/airports/destinations
```

### 7. Get Routes
**GET /airports/routes** - Get list of all available routes with statistics

**Query Parameters:**
- `origin` (string, optional): Filter routes by origin airport

```bash
# Get all routes
curl http://localhost:8000/airports/routes

# Get routes from Warsaw
curl "http://localhost:8000/airports/routes?origin=WAW"
```

**Response:**
```json
{
  "routes": [
    {
      "origin": "WRO",
      "origin_name": "Wroclaw",
      "destination": "BCN",
      "destination_name": "Barcelona",
      "flight_count": 156,
      "min_price": 29.99,
      "max_price": 199.99,
      "avg_price": 67.45,
      "currency": "EUR"
    }
  ]
}
```

### 8. Get Scan Iterations
**GET /scans** - Get scan iteration history

**Query Parameters:**
- `limit` (int): Number of scans to return (default: 10, max: 100)

```bash
curl "http://localhost:8000/scans?limit=5"
```

### 9. Get Latest Scan
**GET /scans/latest** - Get details of the most recent scan

```bash
curl http://localhost:8000/scans/latest
```

**Response:**
```json
{
  "start_time": "2025-11-07T10:00:00",
  "end_time": "2025-11-07T12:30:00",
  "status": "completed",
  "stats": {
    "total_routes": 3250,
    "successful_queries": 3180,
    "failed_queries": 70,
    "flights_saved": 15234
  }
}
```

### 10. Health Check
**GET /health** - Check API and database health

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "flights_in_database": 15234,
  "timestamp": "2025-11-07T15:30:00"
}
```

## Common Use Cases

### Find Cheapest Flights from All Polish Airports to Barcelona

```bash
curl "http://localhost:8000/flights?destination=BCN&max_price=100&sort_by=price&page_size=20"
```

### Find Weekend Trips in December

```bash
curl "http://localhost:8000/flights?date_from=2025-12-01&date_to=2025-12-31&sort_by=price"
```

### Monitor Price Changes for Specific Route

```bash
# First, get all flights for the route
curl "http://localhost:8000/flights?origin=WRO&destination=BCN"

# Then, get detailed price history for a specific flight
curl "http://localhost:8000/flights/WRO_BCN_FR1234_2025-12-06_10:30"
```

### Find All Available Destinations from Your City

```bash
curl "http://localhost:8000/airports/routes?origin=WRO"
```

### Get Budget Travel Options

```bash
curl "http://localhost:8000/flights?max_price=50&sort_by=price&page_size=100"
```

## Polish Airports Covered

The scanner monitors all major Polish airports:

- **GDN** - Gdansk (Gdańsk Lech Wałęsa Airport)
- **SZN** - Szczecin (Solidarity Szczecin-Goleniów Airport)
- **KRK** - Krakow (John Paul II International Airport Kraków-Balice)
- **KTW** - Katowice (Katowice Airport)
- **WRO** - Wroclaw (Copernicus Airport Wrocław)
- **POZ** - Poznan (Poznań-Ławica Airport)
- **WMI** - Warsaw Modlin (Warsaw Modlin Airport)
- **WAW** - Warsaw (Warsaw Chopin Airport)
- **LCJ** - Lodz (Łódź Władysław Reymont Airport)
- **LUZ** - Lublin (Lublin Airport)
- **RZE** - Rzeszow (Rzeszów-Jasionka Airport)
- **SZY** - Olsztyn-Mazury (Olsztyn-Mazury Airport)
- **BZG** - Bydgoszcz (Bydgoszcz Ignacy Jan Paderewski Airport)

## Integration with Frontend

The API includes CORS support for web frontend integration. Example JavaScript fetch:

```javascript
// Fetch cheap flights from Warsaw
fetch('http://localhost:8000/flights?origin=WAW&max_price=100&sort_by=price')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.total} flights`);
    data.flights.forEach(flight => {
      console.log(`${flight.origin} → ${flight.destination}: ${flight.current_price} ${flight.currency}`);
    });
  });
```

## Rate Limiting

Currently, the API does not implement rate limiting. In production, consider adding rate limiting middleware to prevent abuse.

## Database

The API reads from MongoDB collections:
- `ryanair_flights` - Individual flight records with price tracking
- `scan_iterations` - Scan history and statistics

Make sure MongoDB is running and the scanner has populated the database before using the API.
