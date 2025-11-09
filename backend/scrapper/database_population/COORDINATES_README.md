# Airport Coordinates Feature

This feature adds real geographic coordinates (latitude/longitude) to all airports in the database, enabling map visualizations and geographic queries.

## Overview

The airport database now includes:
- **Latitude**: Geographic latitude in decimal degrees
- **Longitude**: Geographic longitude in decimal degrees

These coordinates are fetched from the [airportsdata](https://pypi.org/project/airportsdata/) Python package, which contains location data for ~7,859 airports with IATA codes.

## Installation

The `airportsdata` package is included in `requirements.txt`. Install it with:

```bash
pip install airportsdata
# or
pip install -r backend/requirements.txt
```

## Usage

### Option 1: Update Coordinates for Existing Database

If you already have a populated airport database, run the coordinate updater script:

```bash
# Update Ryanair airports
python backend/scrapper/database_population/update_airport_coordinates.py

# Update Wizz Air airports
python backend/scrapper/database_population/update_airport_coordinates.py --airline wizzair

# Custom MongoDB URI
python backend/scrapper/database_population/update_airport_coordinates.py \
  --mongo-uri "mongodb://localhost:27017/flights_scanner"

# Quiet mode (less verbose output)
python backend/scrapper/database_population/update_airport_coordinates.py --quiet
```

### Option 2: Programmatic Usage

```python
from scrapper.database_population import load_from_mongodb, save_to_mongodb
from scrapper.database_population.update_airport_coordinates import update_airport_coordinates

# Load database
database = load_from_mongodb("ryanair")

# Update coordinates
updated, not_found, already_had = update_airport_coordinates(database, verbose=True)

# Save back to MongoDB
save_to_mongodb(database, "ryanair")

print(f"Updated {updated} airports with coordinates")
```

### Option 3: During Population

The coordinates can also be updated right after populating the database:

```python
from scrapper.database_population import (
    build_airport_database,
    fetch_ryanair_routes,
    save_to_mongodb,
)
from scrapper.database_population.update_airport_coordinates import update_airport_coordinates

# Build and populate database
database = build_airport_database()
routes = fetch_ryanair_routes()
database.populate_connections_from_routes(routes)

# Add coordinates before saving
update_airport_coordinates(database)

# Save to MongoDB
save_to_mongodb(database, "ryanair")
```

## Data Structure

### Airport Model

```python
class Airport(BaseModel):
    code: str                    # IATA code (e.g., "WRO")
    name: str                    # Airport name (e.g., "Wrocław")
    airport_id: int              # Unique ID from API
    size: int                    # Size/importance indicator
    coordinates: List[int]       # Pixel coordinates on tile
    tile: str                    # Tile reference (e.g., "0-0")
    latitude: Optional[float]    # Geographic latitude (NEW)
    longitude: Optional[float]   # Geographic longitude (NEW)
```

### MongoDB Document

```json
{
  "code": "WRO",
  "name": "Wrocław",
  "airport_id": 1234,
  "size": 5,
  "coordinates": [228, 158],
  "tile": "1-2",
  "latitude": 51.1027,
  "longitude": 16.8858,
  "updated_at": "2025-11-09T12:00:00Z"
}
```

## Querying Airports with Coordinates

### Get All Airports with Coordinates

```python
from scrapper.database_population import load_from_mongodb

database = load_from_mongodb("ryanair")

# Get airports that have coordinates
airports_with_coords = [
    {
        "code": airport.code,
        "name": airport.name,
        "lat": airport.latitude,
        "lon": airport.longitude
    }
    for airport in database.get_all_airports()
    if airport.latitude is not None and airport.longitude is not None
]

print(f"Found {len(airports_with_coords)} airports with coordinates")
```

### API Endpoint Example

```python
from fastapi import APIRouter
from scrapper.database_population import load_from_mongodb

router = APIRouter()

@router.get("/airports/map")
async def get_airports_map(airline: str = "ryanair"):
    """Get all airports with coordinates for map visualization."""
    database = load_from_mongodb(airline)

    airports = [
        {
            "code": airport.code,
            "name": airport.name,
            "latitude": airport.latitude,
            "longitude": airport.longitude,
            "connections": len(database.get_connections_from(airport.code))
        }
        for airport in database.get_all_airports()
        if airport.latitude is not None and airport.longitude is not None
    ]

    return {"airports": airports, "total": len(airports)}
```

## Expected Results

When you run the coordinate updater, you should see output like:

```
============================================================
Airport Coordinates Updater - RYANAIR
============================================================

============================================================
Loading RYANAIR data from MongoDB...
============================================================
✓ Loaded 267 airports
✓ Loaded 3542 connections

============================================================
✓ RYANAIR data loaded successfully!
============================================================

============================================================
Loading airportsdata database...
============================================================
✓ Loaded data for 7859 airports with IATA codes

Updating coordinates for 267 airports...
============================================================
  ✓ AAL: Aalborg → (57.0928, 9.8492)
  ✓ AAR: Aarhus → (56.3000, 10.6190)
  ✓ ACE: Lanzarote → (28.9455, -13.6052)
  ...
  ✗ XYZ: Unknown Airport - not found in airportsdata

============================================================
Summary:
  Updated: 265
  Already had coordinates: 0
  Not found: 2
  Total: 267
============================================================
```

## Map Visualization Example

Once coordinates are populated, you can create map visualizations using libraries like:

- **Leaflet.js** (JavaScript)
- **Folium** (Python)
- **Mapbox GL JS** (JavaScript)
- **Google Maps API** (JavaScript)

Example with Leaflet:

```javascript
// Fetch airports with coordinates
const response = await fetch('/api/airports/map?airline=ryanair');
const { airports } = await response.json();

// Initialize map
const map = L.map('map').setView([50, 10], 5);

// Add markers for each airport
airports.forEach(airport => {
  const marker = L.marker([airport.latitude, airport.longitude])
    .bindPopup(`<b>${airport.code}</b><br>${airport.name}<br>${airport.connections} connections`)
    .addTo(map);
});
```

## Troubleshooting

### "Airport not found in airportsdata"

Some airports may not have IATA codes in the airportsdata database. This is normal for smaller airports or those without IATA codes. These airports will have `null` latitude/longitude values.

### Missing `airportsdata` Package

If you get an import error:

```bash
pip install airportsdata
```

### MongoDB Connection Issues

Ensure MongoDB is running:

```bash
# Using Docker Compose
docker-compose up -d mongodb

# Or start MongoDB locally
mongod --dbpath /path/to/data
```

## Future Enhancements

Potential improvements:

1. **Fallback coordinate sources** - Use alternative APIs for airports not in airportsdata
2. **Timezone information** - Add timezone data (already available in airportsdata)
3. **Country/region data** - Add country codes and regions
4. **Automatic updates** - Fetch coordinates automatically during database population
5. **Distance calculations** - Add functions to calculate distances between airports

## References

- [airportsdata PyPI](https://pypi.org/project/airportsdata/)
- [airportsdata GitHub](https://github.com/mborsetti/airportsdata)
- Airport data includes IATA codes, coordinates, timezones, and more
- Data is sourced from OurAirports and other open databases
