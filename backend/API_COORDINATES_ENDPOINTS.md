# Airport Coordinates API Endpoints

This document describes the new API endpoints for managing and retrieving airport coordinates.

## Endpoints

### 1. Update Airport Coordinates

**POST** `/airports/update-coordinates`

Updates the geographic coordinates (latitude/longitude) for all airports in the database.

#### Request Body

```json
{
  "airline": "ryanair"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| airline | string | No | "ryanair" | Airline name (ryanair or wizzair) |

#### Response

```json
{
  "message": "Coordinate update started for ryanair airports",
  "status": "started",
  "airline": "ryanair",
  "background_task_started": true
}
```

#### Example Usage

```bash
# Update Ryanair airport coordinates
curl -X POST "http://localhost:8000/airports/update-coordinates" \
  -H "Content-Type: application/json" \
  -d '{"airline": "ryanair"}'

# Update Wizz Air airport coordinates
curl -X POST "http://localhost:8000/airports/update-coordinates" \
  -H "Content-Type: application/json" \
  -d '{"airline": "wizzair"}'
```

#### Notes

- This endpoint runs as a background task and returns immediately
- Check server logs to monitor progress
- The process fetches coordinates from the airportsdata package
- Updates are saved to MongoDB

---

### 2. Get Airports with Coordinates

**GET** `/airports/coordinates`

Retrieves all airports with their geographic coordinates in various formats.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| airline | string | No | "ryanair" | Airline name (ryanair or wizzair) |
| format | string | No | "simple" | Output format (simple, geojson, or connections) |

#### Formats

##### 1. Simple Format (`format=simple`)

Returns a list of airports with basic information and coordinates.

**Response:**
```json
{
  "airports": [
    {
      "code": "DUB",
      "name": "Dublin",
      "latitude": 53.4213,
      "longitude": -6.2701,
      "connections": ["WRO", "BCN", "STN", ...],
      "connection_count": 142
    },
    ...
  ],
  "total": 267,
  "format": "simple"
}
```

##### 2. GeoJSON Format (`format=geojson`)

Returns airports as GeoJSON FeatureCollection for mapping libraries like Leaflet, Mapbox GL JS.

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-6.2701, 53.4213]
      },
      "properties": {
        "code": "DUB",
        "name": "Dublin",
        "airport_id": 1234,
        "size": 8,
        "connections": 142
      }
    },
    ...
  ]
}
```

##### 3. Connections Format (`format=connections`)

Returns flight routes as GeoJSON LineStrings showing connections between airports.

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [-6.2701, 53.4213],
          [16.8858, 51.1027]
        ]
      },
      "properties": {
        "from": "DUB",
        "to": "WRO",
        "from_name": "Dublin",
        "to_name": "Wrocław",
        "airline": "ryanair"
      }
    },
    ...
  ]
}
```

#### Example Usage

```bash
# Get simple list of airports with coordinates
curl "http://localhost:8000/airports/coordinates?airline=ryanair&format=simple"

# Get GeoJSON for map visualization
curl "http://localhost:8000/airports/coordinates?airline=ryanair&format=geojson"

# Get flight route connections
curl "http://localhost:8000/airports/coordinates?airline=ryanair&format=connections"

# Get Wizz Air airports
curl "http://localhost:8000/airports/coordinates?airline=wizzair&format=simple"
```

#### Frontend Integration Example

##### Leaflet.js

```javascript
// Fetch airports and display on map
const response = await fetch('/airports/coordinates?format=geojson&airline=ryanair');
const geojson = await response.json();

// Add to Leaflet map
L.geoJSON(geojson, {
  pointToLayer: (feature, latlng) => {
    return L.marker(latlng);
  },
  onEachFeature: (feature, layer) => {
    const props = feature.properties;
    layer.bindPopup(`
      <b>${props.code}</b><br>
      ${props.name}<br>
      ${props.connections} connections
    `);
  }
}).addTo(map);
```

##### Simple List Display

```javascript
// Fetch airports as simple list
const response = await fetch('/airports/coordinates?format=simple&airline=ryanair');
const data = await response.json();

// Display in table or list
data.airports.forEach(airport => {
  console.log(`${airport.code}: ${airport.name} (${airport.connection_count} connections)`);
});
```

##### Route Visualization

```javascript
// Fetch route connections
const response = await fetch('/airports/coordinates?format=connections&airline=ryanair');
const routes = await response.json();

// Add routes to map as lines
L.geoJSON(routes, {
  style: {
    color: '#0066cc',
    weight: 2,
    opacity: 0.6
  }
}).addTo(map);
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid airline. Must be 'ryanair' or 'wizzair'"
}
```

### 404 Not Found

```json
{
  "detail": "No airports found with coordinates"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Failed to load ryanair database from MongoDB"
}
```

## Complete Workflow

### 1. Populate Airports

```bash
# First, populate the airport database
curl -X POST "http://localhost:8000/airports/populate"
```

### 2. Update Coordinates

```bash
# Add geographic coordinates
curl -X POST "http://localhost:8000/airports/update-coordinates" \
  -H "Content-Type: application/json" \
  -d '{"airline": "ryanair"}'
```

### 3. Retrieve and Display

```bash
# Get airports for map visualization
curl "http://localhost:8000/airports/coordinates?format=geojson" > airports.geojson
```

## Requirements

- MongoDB must be running with populated airport data
- `airportsdata` Python package must be installed
- Airports must be populated before updating coordinates

## Notes

- Only airports with IATA codes in the airportsdata database will have coordinates
- Airports without coordinates are excluded from the response
- Coordinates are stored in MongoDB and persist across restarts
- The simple format sorts airports by connection count (hubs first)
- GeoJSON follows the RFC 7946 standard
- Coordinates are in WGS84 decimal degrees (latitude, longitude)
