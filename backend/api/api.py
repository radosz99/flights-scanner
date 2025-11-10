#!/usr/bin/env python3

"""
FastAPI REST API for filtering and sorting Ryanair flight data.

This API provides endpoints to:
1. Query flights with various filters (origin, destination, date range, price range)
2. Sort results by price, date, duration
3. Get statistics about stored flights
4. Track price changes over time

Usage:
    uvicorn api:app --reload --host 0.0.0.0 --port 8000

Example queries:
    GET /flights?origin=WRO&destination=BCN&min_price=10&max_price=100&sort_by=price
    GET /flights?date_from=2025-12-01&date_to=2025-12-31&sort_by=date
    GET /flights/stats
    GET /flights/price-history/{flight_id}
"""

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pymongo import MongoClient, ASCENDING, DESCENDING
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date
from loguru import logger
import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to import config and models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import settings
from constants import POLISH_AIRPORTS
from api_models import (
    PriceHistoryEntry,
    FlightSegment,
    FlightResponse,
    FlightListResponse,
    StatsResponse,
    ScanIterationResponse,
    ScanRequest,
    ScanTriggerResponse,
    UpdateCoordinatesRequest,
    UpdateCoordinatesResponse,
)

# Add scrapper directory to path to import scanner modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapper"))

# ============================================================================
# CONFIGURATION
# ============================================================================

FLIGHTS_COLLECTION = "ryanair_flights"
SCAN_ITERATIONS_COLLECTION = "scan_iterations"

# Thread pool for running CPU/IO-intensive scanner tasks
# This prevents blocking the async event loop
MAX_SCAN_WORKERS = int(os.getenv("MAX_SCAN_WORKERS", "4"))
scan_executor = ThreadPoolExecutor(max_workers=MAX_SCAN_WORKERS, thread_name_prefix="scanner")

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Ryanair Flight Scanner API",
    description="REST API for filtering and sorting Ryanair flight data with price tracking",
    version="1.0.0"
)

# Enable CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient(settings.mongo_uri)
db = client[settings.MONGO_DATABASE]
flights_collection = db[FLIGHTS_COLLECTION]
scan_iterations_collection = db[SCAN_ITERATIONS_COLLECTION]

# Initialize API service
from .api_service import APIService
api_service = APIService(client, settings.MONGO_DATABASE)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - redirects to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/flights", response_model=FlightListResponse)
async def get_flights(
    origin: Optional[str] = Query(None, description="Filter by origin airport code (e.g., WRO)"),
    destination: Optional[str] = Query(None, description="Filter by destination airport code (e.g., BCN)"),
    date_from: Optional[date] = Query(None, description="Filter flights departing from this date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter flights departing until this date (YYYY-MM-DD)"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    currency: Optional[str] = Query(None, description="Filter by currency code (e.g., EUR, PLN)"),
    sort_by: Literal["price", "date", "duration", "price_desc"] = Query("price", description="Sort results by field"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Number of results per page")
):
    """
    Query flights with various filters and sorting options.

    Returns paginated list of flights matching the specified criteria.
    """
    result = api_service.get_flights(
        origin=origin,
        destination=destination,
        date_from=date_from,
        date_to=date_to,
        min_price=min_price,
        max_price=max_price,
        currency=currency,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )

    # Convert to response models
    flights = [FlightResponse(**flight) for flight in result["flights"]]

    return FlightListResponse(
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        flights=flights
    )


@app.get("/flights/price-chart")
async def get_price_chart(
    origin: str = Query(..., description="Origin airport code (e.g., WRO)"),
    destination: str = Query(..., description="Destination airport code (e.g., BCN)")
):
    """
    Get price chart data for a specific route over the full date range.

    Returns all flights for the route grouped by date with min, max, and average prices.
    """
    chart_data = api_service.get_price_chart(origin=origin, destination=destination)

    if not chart_data:
        raise HTTPException(
            status_code=404,
            detail=f"No flights found for route {origin.upper()} → {destination.upper()}"
        )

    return chart_data


@app.get("/flights/round-trips")
async def get_round_trips(
    origin: str = Query(..., description="Origin airport code (e.g., WRO)"),
    destination: Optional[str] = Query(None, description="Destination airport code (e.g., BCN). If not provided, shows all destinations."),
    min_days: int = Query(..., ge=1, description="Minimum trip duration in days"),
    max_days: int = Query(..., ge=1, description="Maximum trip duration in days"),
    passengers: int = Query(2, ge=1, le=10, description="Number of passengers"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results")
):
    """
    Find all possible round trips (two-way) within specified trip length range.

    Returns combinations of outbound and return flights that form valid round trips
    with trip duration between min_days and max_days, sorted by total price.

    If destination is not provided, shows round trips to all available destinations.
    """
    if min_days > max_days:
        raise HTTPException(
            status_code=400,
            detail="min_days must be less than or equal to max_days"
        )

    round_trips = api_service.find_round_trips(
        origin=origin,
        destination=destination,
        min_days=min_days,
        max_days=max_days,
        passengers=passengers
    )

    if not round_trips:
        dest_msg = destination.upper() if destination else "any destination"
        raise HTTPException(
            status_code=404,
            detail=f"No round trips found for {origin.upper()} → {dest_msg} with {min_days}-{max_days} days duration"
        )

    # Apply limit
    limited_trips = round_trips[:limit]

    return {
        "origin": origin.upper(),
        "destination": destination.upper() if destination else "ALL",
        "min_days": min_days,
        "max_days": max_days,
        "passengers": passengers,
        "total_combinations": len(round_trips),
        "showing": len(limited_trips),
        "trips": limited_trips
    }


@app.get("/flights/round-trips/preview")
async def get_round_trips_preview(
    origin: str = Query(..., description="Origin airport code (e.g., WRO)"),
    min_days: int = Query(3, ge=1, description="Minimum trip duration in days"),
    max_days: int = Query(7, ge=1, description="Maximum trip duration in days")
):
    """
    Get preview of all available destinations from origin with lowest round-trip prices.

    Returns a list of destinations with minimum round-trip prices for the given duration range.
    """
    if min_days > max_days:
        raise HTTPException(
            status_code=400,
            detail="min_days must be less than or equal to max_days"
        )

    preview_data = api_service.get_round_trips_preview(
        origin=origin,
        min_days=min_days,
        max_days=max_days
    )

    return {
        "origin": origin.upper(),
        "min_days": min_days,
        "max_days": max_days,
        "destinations": preview_data
    }


@app.get("/flights/{flight_id}", response_model=FlightResponse)
async def get_flight(flight_id: str):
    """
    Get detailed information about a specific flight including full price history.
    """
    flight = api_service.get_flight_by_id(flight_id)

    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")

    return FlightResponse(**flight)


@app.get("/flights/stats/summary", response_model=StatsResponse)
async def get_stats():
    """
    Get database statistics including total flights, price changes, and price ranges.
    """
    stats = api_service.get_stats()
    return StatsResponse(**stats)


@app.get("/airports/origins")
async def get_origins():
    """
    Get list of all available origin airports with flight counts.
    """
    origins = api_service.get_origins()
    return {"origins": origins}


@app.get("/airports/polish-origins")
async def get_polish_origins():
    """
    Get list of all available Polish origin airports with flight counts.
    Used for trip search where we only want to show Polish departure airports.
    """
    origins = api_service.get_polish_origins()
    return {"origins": origins}


@app.get("/airports/destinations")
async def get_destinations():
    """
    Get list of all available destination airports with flight counts.
    """
    destinations = api_service.get_destinations()
    return {"destinations": destinations}


@app.get("/airports/routes")
async def get_routes(origin: Optional[str] = Query(None, description="Filter routes by origin")):
    """
    Get list of all available routes with flight counts.
    """
    routes = api_service.get_routes(origin=origin)
    return {"routes": routes}


@app.get("/airports/two-way-routes")
async def get_two_way_routes(
    origin: Optional[str] = Query(None, description="Filter routes by origin airport code"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of routes")
):
    """
    Get all possible two-way routes from Polish airports.

    This returns routes where both outbound and return flights exist,
    useful for displaying on the trip search page.

    Args:
        origin: Optional filter to show only routes from specific origin airport
        limit: Maximum number of routes to return
    """
    routes = api_service.get_all_two_way_routes(origin=origin, limit=limit)
    return {"routes": routes, "total": len(routes)}


@app.get("/airports/one-way-examples")
async def get_one_way_examples(limit: int = Query(50, ge=1, le=200, description="Maximum number of examples")):
    """
    Get example one-way routes from Polish airports.

    Returns one-way routes sorted by price, useful for displaying
    on the price chart page as examples.
    """
    routes = api_service.get_one_way_route_examples(limit=limit)
    return {"routes": routes, "total": len(routes)}


@app.get("/airports/origins/{origin}/destinations")
async def get_destinations_from_origin(origin: str):
    """
    Get list of all available destinations from a specific origin airport.

    This is useful for cascading dropdowns where you first select origin,
    then see only the destinations available from that origin.
    """
    destinations = api_service.get_destinations_from_origin(origin=origin)

    if not destinations:
        raise HTTPException(
            status_code=404,
            detail=f"No destinations found from origin {origin.upper()}"
        )

    return {"destinations": destinations}


@app.get("/airports/coordinates")
async def get_airports_with_coordinates(
    airline: str = Query("ryanair", description="Airline name (ryanair, wizzair)"),
    format: str = Query("simple", description="Output format: simple, geojson, or connections")
):
    """
    Get all airports with their geographic coordinates for map visualization.

    This endpoint returns airport data with latitude/longitude coordinates
    in various formats suitable for different mapping libraries.

    Formats:
    - simple: List of airports with code, name, lat, lon, and connection count
    - geojson: GeoJSON FeatureCollection for Leaflet, Mapbox GL JS
    - connections: GeoJSON LineStrings showing routes between airports

    Args:
        airline: Airline name (default: ryanair)
        format: Output format (default: simple)

    Returns:
        Airport data with coordinates in the requested format
    """
    try:
        from scrapper.database_population import load_from_mongodb

        airline = airline.lower()

        # Validate airline
        if airline not in ["ryanair", "wizzair"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid airline. Must be 'ryanair' or 'wizzair'"
            )

        # Load database
        database = load_from_mongodb(airline, settings.mongo_uri)

        if not database:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load {airline} database from MongoDB"
            )

        # Format output based on requested format
        if format == "simple":
            airports = []
            for airport in database.get_all_airports():
                if airport.latitude is None or airport.longitude is None:
                    continue

                airports.append({
                    "code": airport.code,
                    "name": airport.name,
                    "latitude": airport.latitude,
                    "longitude": airport.longitude,
                    "connections": database.get_connections_from(airport.code),
                    "connection_count": len(database.get_connections_from(airport.code))
                })

            # Sort by connection count (hub airports first)
            airports.sort(key=lambda x: x["connection_count"], reverse=True)
            return {"airports": airports, "total": len(airports), "format": "simple"}

        elif format == "geojson":
            features = []
            for airport in database.get_all_airports():
                if airport.latitude is None or airport.longitude is None:
                    continue

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [airport.longitude, airport.latitude]
                    },
                    "properties": {
                        "code": airport.code,
                        "name": airport.name,
                        "airport_id": airport.airport_id,
                        "size": airport.size,
                        "connections": len(database.get_connections_from(airport.code))
                    }
                }
                features.append(feature)

            return {
                "type": "FeatureCollection",
                "features": features
            }

        elif format == "connections":
            features = []
            for from_code in database.connections:
                from_airport = database.get_airport_by_code(from_code)
                if not from_airport or from_airport.latitude is None:
                    continue

                for to_code in database.get_connections_from(from_code):
                    to_airport = database.get_airport_by_code(to_code)
                    if not to_airport or to_airport.latitude is None:
                        continue

                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [from_airport.longitude, from_airport.latitude],
                                [to_airport.longitude, to_airport.latitude]
                            ]
                        },
                        "properties": {
                            "from": from_code,
                            "to": to_code,
                            "from_name": from_airport.name,
                            "to_name": to_airport.name,
                            "airline": airline
                        }
                    }
                    features.append(feature)

            return {
                "type": "FeatureCollection",
                "features": features
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Must be 'simple', 'geojson', or 'connections'"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get airports with coordinates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve airport coordinates: {str(e)}"
        )


@app.post("/airports/populate")
async def populate_airports(background_tasks: BackgroundTasks):
    """
    Populate the airport database with Ryanair and Wizz Air routes.

    This endpoint triggers a background task that:
    1. Builds airport database from FlightConnections tiles
    2. Fetches routes for Ryanair and Wizz Air
    3. Populates connections for each airline
    4. Saves to MongoDB in separate collections

    The task runs in the background and returns immediately.
    Check the logs to monitor progress.
    """
    try:
        from scrapper.database_population import populate_ryanair_database, populate_wizzair_database

        def run_population():
            """Background task to populate databases."""
            try:
                logger.info("Starting airport database population...")

                ryanair_success = populate_ryanair_database()
                wizzair_success = populate_wizzair_database()

                if ryanair_success and wizzair_success:
                    logger.success("All airport databases populated successfully")
                elif ryanair_success or wizzair_success:
                    logger.warning("Some airport databases populated successfully")
                else:
                    logger.error("Failed to populate airport databases")

            except Exception as e:
                logger.error(f"Error during airport database population: {e}")
                import traceback
                traceback.print_exc()

        # Start background task
        background_tasks.add_task(run_population)

        return {
            "message": "Airport database population started in background",
            "status": "started",
            "info": "Check server logs for progress. This may take several minutes."
        }

    except Exception as e:
        logger.error(f"Failed to trigger airport population: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger population: {str(e)}")


@app.post("/airports/update-coordinates", response_model=UpdateCoordinatesResponse)
async def update_airport_coordinates(
    request: UpdateCoordinatesRequest,
    background_tasks: BackgroundTasks
):
    """
    Update airport coordinates (latitude/longitude) for all airports.

    This endpoint triggers a background task that:
    1. Loads airport data from MongoDB for the specified airline
    2. Fetches real geographic coordinates using the airportsdata package
    3. Updates each airport with latitude and longitude
    4. Saves the updated data back to MongoDB

    The coordinates enable map visualizations and geographic queries.

    Args:
        request: UpdateCoordinatesRequest with airline name
        background_tasks: FastAPI background tasks handler

    Returns:
        UpdateCoordinatesResponse with status information

    The task runs in the background and returns immediately.
    Check the logs to monitor progress.
    """
    try:
        from scrapper.database_population.update_airport_coordinates import main as update_coords_main

        airline = request.airline.lower()

        # Validate airline
        if airline not in ["ryanair", "wizzair"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid airline. Must be 'ryanair' or 'wizzair'"
            )

        def run_coordinate_update():
            """Background task to update coordinates."""
            try:
                logger.info(f"Starting coordinate update for {airline}...")

                success = update_coords_main(
                    airline_name=airline,
                    mongo_uri=settings.mongo_uri,
                    verbose=True
                )

                if success:
                    logger.success(f"Coordinates updated successfully for {airline}")
                else:
                    logger.error(f"Failed to update coordinates for {airline}")

            except Exception as e:
                logger.error(f"Error during coordinate update: {e}")
                import traceback
                traceback.print_exc()

        # Start background task
        background_tasks.add_task(run_coordinate_update)

        return UpdateCoordinatesResponse(
            message=f"Coordinate update started for {airline} airports",
            status="started",
            airline=airline,
            background_task_started=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger coordinate update: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger coordinate update: {str(e)}"
        )


@app.delete("/airports/clear")
async def clear_airports(
    airline: Optional[str] = Query(None, description="Clear specific airline (ryanair/wizzair) or all if not specified")
):
    """
    Clear airport database collections.

    This will remove all airport and connection data for the specified airline,
    or for all airlines if no airline is specified.

    WARNING: This action cannot be undone. Use /airports/populate to repopulate the data.
    """
    try:
        collections_to_clear = []

        if airline:
            airline = airline.lower()
            if airline not in ["ryanair", "wizzair"]:
                raise HTTPException(status_code=400, detail="Invalid airline. Must be 'ryanair' or 'wizzair'")
            collections_to_clear = [
                f"{airline}_airports",
                f"{airline}_connections"
            ]
        else:
            # Clear all airlines
            collections_to_clear = [
                "ryanair_airports",
                "ryanair_connections",
                "wizzair_airports",
                "wizzair_connections"
            ]

        results = {}
        total_deleted = 0

        for collection_name in collections_to_clear:
            collection = db[collection_name]
            result = collection.delete_many({})
            results[collection_name] = result.deleted_count
            total_deleted += result.deleted_count
            logger.info(f"Cleared {result.deleted_count} documents from {collection_name}")

        return {
            "message": f"Successfully cleared {len(collections_to_clear)} collections",
            "total_documents_deleted": total_deleted,
            "collections_cleared": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear airport collections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear collections: {str(e)}")


@app.get("/scans", response_model=List[ScanIterationResponse])
async def get_scans(limit: int = Query(10, ge=1, le=100, description="Number of scans to return")):
    """
    Get scan iteration history.
    """
    scans_data = api_service.get_scans(limit=limit)
    return [ScanIterationResponse(**scan) for scan in scans_data]


@app.get("/scans/latest", response_model=ScanIterationResponse)
async def get_latest_scan():
    """
    Get details of the most recent scan iteration.
    """
    scan = api_service.get_latest_scan()

    if not scan:
        raise HTTPException(status_code=404, detail="No scan iterations found")

    return ScanIterationResponse(**scan)


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API and database connectivity.
    """
    health_data, _ = api_service.get_health()
    return health_data


def run_scanner_background(
    departure_airports: List[str],
    trip_duration_days: int,
    scan_until_date: str,
    scan_id: str
):
    """
    Background task to run the flight scanner.

    This imports and runs the scanner logic in a background thread.
    """
    try:
        from scrapper.ryanair import (
            scan_flights,
            generate_date_ranges,
            ScanIterationManager,
            FlightStorage,
            SCAN_ITERATIONS_COLLECTION,
            FLIGHTS_COLLECTION,
            get_valid_cookie,
        )
        from datetime import datetime, timedelta

        logger.info(f"Starting background scan {scan_id}")

        # Get valid cookie
        logger.info("Getting valid cookie...")
        cookie = get_valid_cookie(auto_refresh=True)

        if not cookie:
            logger.error("Failed to get valid cookie")
            # Mark scan as failed
            scan_manager = ScanIterationManager(
                settings.mongo_uri,
                settings.MONGO_DATABASE,
                SCAN_ITERATIONS_COLLECTION
            )
            scan_manager.complete_scan(scan_id, success=False)
            return

        # Generate date ranges
        today = datetime.now()
        scan_until = datetime.strptime(scan_until_date, "%Y-%m-%d")
        date_ranges = generate_date_ranges(today, scan_until, trip_duration_days)

        logger.info(f"Generated {len(date_ranges)} date ranges to scan")

        # Get scan manager
        scan_manager = ScanIterationManager(
            settings.mongo_uri,
            settings.MONGO_DATABASE,
            SCAN_ITERATIONS_COLLECTION
        )

        # Run scan for each date range
        total_stats = {
            "total_routes": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "flights_saved": 0
        }

        for idx, (date_out_str, date_in_str) in enumerate(date_ranges, 1):
            logger.info(f"Scanning date range {idx}/{len(date_ranges)}: {date_out_str} to {date_in_str}")

            stats = scan_flights(departure_airports, date_out_str, date_in_str, cookie)

            # Update totals
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)

            # Record this date range result
            scan_manager.add_date_range_result(scan_id, date_out_str, date_in_str, stats)

        # Mark scan as completed
        scan_manager.complete_scan(scan_id, success=True)
        logger.success(f"Scan {scan_id} completed successfully")

    except Exception as e:
        logger.error(f"Background scan failed: {e}")
        try:
            from scrapper.ryanair import ScanIterationManager, SCAN_ITERATIONS_COLLECTION
            scan_manager = ScanIterationManager(
                settings.mongo_uri,
                settings.MONGO_DATABASE,
                SCAN_ITERATIONS_COLLECTION
            )
            scan_manager.complete_scan(scan_id, success=False)
        except:
            pass


@app.post("/scans/run", response_model=ScanTriggerResponse)
async def trigger_scan(scan_request: ScanRequest):
    """
    Trigger a new flight scan.

    This endpoint starts a background scan job in a separate thread pool and returns immediately.
    Use GET /scans/latest or GET /scans to check the scan progress.

    Note: Scans all default Polish airports (GDN, SZN, KRK, KTW, WRO, POZ, WMI, WAW, LCJ, LUZ, RZE, SZY, BZG).
    """
    try:
        from scrapper.ryanair import ScanIterationManager, SCAN_ITERATIONS_COLLECTION, generate_date_ranges
        from datetime import datetime

        # Always use all default departure airports (all Polish airports)
        departure_airports = POLISH_AIRPORTS

        trip_duration_days = scan_request.trip_duration_days or 7
        scan_until_date = scan_request.scan_until_date or "2026-03-31"

        # Calculate total date ranges for progress tracking
        today = datetime.now()
        scan_until = datetime.strptime(scan_until_date, "%Y-%m-%d")
        date_ranges = generate_date_ranges(today, scan_until, trip_duration_days)
        total_date_ranges = len(date_ranges)

        # Create scan iteration record
        scan_manager = ScanIterationManager(
            settings.mongo_uri,
            settings.MONGO_DATABASE,
            SCAN_ITERATIONS_COLLECTION
        )

        config = {
            "trip_duration_days": trip_duration_days,
            "scan_until_date": scan_until_date,
            "departure_airports": departure_airports,
            "total_date_ranges": total_date_ranges,
        }

        scan_id = scan_manager.start_scan(config)

        # Run scanner in thread pool to avoid blocking API workers
        # This uses asyncio.get_event_loop().run_in_executor which runs the function in a separate thread
        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            scan_executor,
            run_scanner_background,
            departure_airports,
            trip_duration_days,
            scan_until_date,
            scan_id
        )

        logger.info(f"Scan triggered in thread pool: {scan_id}")

        return ScanTriggerResponse(
            message="Scan started successfully in background thread pool. Use GET /scans/latest to check progress.",
            status="started",
            scan_id=scan_id,
            config=config
        )

    except Exception as e:
        logger.error(f"Failed to trigger scan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger scan: {str(e)}")


# ============================================================================
# STARTUP AND SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 60)
    logger.info("RYANAIR FLIGHT SCANNER API STARTING")
    logger.info("=" * 60)
    logger.info(f"MongoDB URI: {settings.mongo_uri}")
    logger.info(f"Database: {settings.MONGO_DATABASE}")
    logger.info(f"Flights Collection: {FLIGHTS_COLLECTION}")
    logger.info(f"Scan Thread Pool Workers: {MAX_SCAN_WORKERS}")
    logger.info("=" * 60)

    try:
        db.command("ping")
        flight_count = flights_collection.count_documents({})
        logger.success(f"✓ MongoDB connected - {flight_count} flights in database")
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down API...")
    logger.info("Shutting down scan thread pool...")
    scan_executor.shutdown(wait=False)  # Don't wait for running scans to complete
    logger.info("API shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
