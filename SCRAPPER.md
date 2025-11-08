# Scrapper Documentation

## Architecture

**Language**: Python 3.11+
**Location**: `/backend/scrapper/`
**Main Module**: `ryanair/ryanair_scanner.py`

## Structure

```
backend/scrapper/
├── ryanair/
│   ├── ryanair.py              # Ryanair API client
│   ├── ryanair_scanner.py      # Scanner orchestration
│   └── find_valid_cookie.py    # Cookie management
├── wizzair/
│   └── wizz_air.py             # WizzAir client (future)
└── database_population/
    ├── flight_connector.py     # Airport data fetcher
    └── populate_databases.py   # Database initialization
```

## How It Works

### 1. Cookie Management

Ryanair requires valid session cookies for API access.

- `get_valid_cookie()` - Retrieves valid cookie
- Cookies are cached and refreshed when needed
- Auto-refresh on expiration

### 2. Flight Scanning

**Scan Process**:
1. Generate date ranges (departure + return dates)
2. For each Polish airport, query available routes
3. Fetch flight data for each route and date combination
4. Store flights in MongoDB with price tracking

**Key Components**:
- `scan_flights()` - Main scanning function
- `FlightStorage` - MongoDB persistence
- `ScanIterationManager` - Tracks scan progress

### 3. Price Tracking

When a flight is found:
- If flight exists: append price to `price_history`
- If new flight: create record with initial price
- Track: price, timestamp, scan_id

## Configuration

Edit `ryanair_scanner.py`:

```python
SCAN_INTERVAL_HOURS = 1         # How often to scan
TRIP_DURATION_DAYS = 4          # Days between outbound/return
SCAN_UNTIL_DATE = "2025-12-31"  # Scan until this date
DEPARTURE_AIRPORTS = POLISH_AIRPORTS  # From constants.py
```

## Scanning Modes

### 1. Manual Scan
```bash
python -m scrapper.ryanair.ryanair_scanner
```

### 2. API Triggered
```bash
POST /scans/run
```

### 3. Periodic (Docker)
Configured in `docker-compose.yml` with cron or scheduler.

## Data Flow

1. **Fetch** flights from Ryanair API
2. **Transform** to internal format
3. **Store** in MongoDB with deduplication
4. **Track** price changes over time

## Date Range Generation

```python
generate_date_ranges(today, scan_until, trip_duration_days)
```

Creates all combinations of:
- Outbound dates: today → scan_until
- Return dates: outbound + trip_duration_days

## Error Handling

- Failed queries are logged and tracked
- Scan continues even if individual routes fail
- Stats include: successful/failed queries, flights saved

## Airport Database Population

Initialize airport and route data:
```bash
POST /airports/populate
```

Fetches from FlightConnections and stores in MongoDB.
