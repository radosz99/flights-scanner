# MongoDB Documentation

## Database Overview

The application uses MongoDB to store flight data, scan iterations, and airport information.

**Database Name**: `flights_db` (configurable via `MONGO_DATABASE` in settings)

## Collections

### 1. `ryanair_flights`

Stores individual flight records with price history tracking.

**Key Fields**:
```javascript
{
  flight_id: String,              // Unique identifier
  flight_number: String,          // e.g., "FR1234"
  origin: String,                 // IATA code (e.g., "WRO")
  origin_name: String,            // Full airport name
  destination: String,            // IATA code (e.g., "BCN")
  destination_name: String,       // Full airport name
  departure_time: ISODate,        // Format: "YYYY-MM-DDTHH:MM:SS.mmm"
  arrival_time: ISODate,          // Format: "YYYY-MM-DDTHH:MM:SS.mmm"
  duration: String,               // e.g., "02h 30m"
  current_price: Number,          // Current price
  currency: String,               // e.g., "EUR", "PLN"
  price_history: [                // Price change tracking
    {
      price: Number,
      timestamp: ISODate,
      scan_id: String
    }
  ]
}
```

**Indexes**:
- `flight_id` (unique)
- `origin`, `destination`
- `departure_time`

### 2. `scan_iterations`

Tracks scanning sessions for monitoring and debugging.

**Key Fields**:
```javascript
{
  scan_id: String,                // Unique scan identifier
  start_time: ISODate,
  end_time: ISODate,
  status: String,                 // "running", "completed", "failed"
  config: {
    trip_duration_days: Number,
    scan_until_date: String,
    departure_airports: [String]
  },
  stats: {
    total_routes: Number,
    successful_queries: Number,
    failed_queries: Number,
    flights_saved: Number
  }
}
```

### 3. `ryanair_airports` & `ryanair_connections`

Airport and route information from Ryanair.

**airports**:
```javascript
{
  iata_code: String,
  name: String,
  country: String,
  coordinates: {
    lat: Number,
    lon: Number
  }
}
```

**connections**:
```javascript
{
  origin: String,                 // IATA code
  destinations: [String]          // Array of IATA codes
}
```

## Data Flow

1. **Scrapper** writes to `ryanair_flights` and `scan_iterations`
2. **API** reads from all collections
3. **Price History** is appended, not overwritten

## Important Date Fields

**DO NOT USE `date_out`** - This field is deprecated.

**Always use**:
- `departure_time` - Full datetime of departure
- `arrival_time` - Full datetime of arrival

Extract date from these fields when needed: `departure_time.split('T')[0]`
