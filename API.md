# Backend API Documentation

## Architecture

**Framework**: FastAPI
**Location**: `/backend/api/`
**Entry Point**: `api.py`
**Service Layer**: `api_service.py`

## Structure

```
backend/api/
├── api.py              # FastAPI endpoints
├── api_service.py      # Business logic
├── __init__.py
└── test_api_service.py
```

## Key Endpoints

### Flights

- `GET /flights` - Query flights with filters (origin, destination, date range, price)
- `GET /flights/{flight_id}` - Get specific flight details
- `GET /flights/price-chart` - Price trends for a route
- `GET /flights/round-trips` - Find round trip combinations

### Airports

- `GET /airports/origins` - List all origin airports
- `GET /airports/destinations` - List all destination airports
- `GET /airports/routes` - List all available routes
- `GET /airports/two-way-routes` - Two-way routes from Polish airports
- `GET /airports/one-way-examples` - One-way route examples
- `GET /airports/origins/{origin}/destinations` - Destinations from specific origin

### Scanning

- `POST /scans/run` - Trigger new flight scan
- `GET /scans` - Get scan history
- `GET /scans/latest` - Get latest scan status

### System

- `GET /health` - Health check

## Response Models

### FlightResponse
```python
{
  "flight_id": str,
  "flight_number": str,
  "origin": str,
  "destination": str,
  "departure_time": str,        # ISO format
  "arrival_time": str,          # ISO format
  "duration": str,
  "current_price": float,
  "currency": str,
  "price_history": [
    {
      "price": float,
      "timestamp": str,
      "scan_id": str
    }
  ]
}
```

### RoundTripResponse
```python
{
  "origin": str,
  "destination": str,
  "trips": [
    {
      "outbound_flight": FlightSegment,
      "return_flight": FlightSegment,
      "trip_duration_days": int,
      "total_price": float,
      "price_per_person": float,
      "passengers": int,
      "currency": str
    }
  ]
}
```

### PriceChartResponse
```python
{
  "origin": str,
  "destination": str,
  "total_dates": int,
  "data": [
    {
      "date": str,              # YYYY-MM-DD
      "min_price": float,
      "avg_price": float,
      "max_price": float,
      "flight_count": int,
      "currency": str
    }
  ]
}
```

## Service Layer

**APIService** class encapsulates all business logic:
- Database queries
- Data aggregation
- Price calculations
- Round trip matching

Endpoints in `api.py` should be thin wrappers calling `api_service` methods.

## Constants

Import from `constants.py`:
```python
from constants import POLISH_AIRPORTS
```

## CORS

Configured to allow all origins in development. Restrict in production.

## Security

### API Documentation Access Control

**By default, API documentation (Swagger/ReDoc) is DISABLED in production for security.**

To enable documentation access, set the environment variable:

```bash
ENABLE_API_DOCS=true
```

When enabled:
- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI Schema: `/api/openapi.json`

When disabled (default):
- All documentation endpoints return 404
- The root endpoint (`/api/`) will not include docs links

**Recommendation**: Keep docs disabled in production and only enable temporarily when needed.

### API Key Authentication

Protected endpoints (POST, DELETE operations) require an API key:

```bash
X-API-Key: your-secret-key-here
```

Configure the API key via the `API_KEY` environment variable.

**Protected endpoints:**
- `POST /scans/run` - Trigger flight scan
- `DELETE /flights/{flight_id}` - Delete flight data
- `POST /airports/populate` - Populate airport database
- Other write operations

**Public endpoints:**
- All GET endpoints (flights, airports, stats, etc.)

## Error Handling

- `404` - Resource not found
- `400` - Invalid parameters
- `403` - Missing or invalid API key
- `500` - Internal server error

All errors return JSON with `detail` field.
