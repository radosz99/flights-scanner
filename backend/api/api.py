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
from pymongo import MongoClient, ASCENDING, DESCENDING
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date
from config import settings
from loguru import logger
import sys
import os

# Add scrapper directory to path to import scanner modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapper"))

# ============================================================================
# CONFIGURATION
# ============================================================================

FLIGHTS_COLLECTION = "ryanair_flights"
SCAN_ITERATIONS_COLLECTION = "scan_iterations"

# ============================================================================
# PYDANTIC MODELS FOR API RESPONSES
# ============================================================================

class PriceHistoryEntry(BaseModel):
    """Price history entry model."""
    price: float
    timestamp: datetime
    change: float


class FlightSegment(BaseModel):
    """Flight segment model for multi-leg flights."""
    segment_nr: int
    origin: str
    destination: str
    flight_number: str
    departure_time: str
    arrival_time: str
    duration: str


class FlightResponse(BaseModel):
    """Flight response model."""
    flight_id: str
    origin: str
    origin_name: str
    destination: str
    destination_name: str
    flight_number: str
    operator: str
    date_out: str
    departure_time: str
    arrival_time: str
    duration: str
    current_price: float
    currency: str
    fares_left: int
    infants_left: int
    segments: List[FlightSegment]
    first_seen: datetime
    last_seen: datetime
    scan_count: int
    price_history: List[PriceHistoryEntry]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FlightListResponse(BaseModel):
    """Response model for flight list queries."""
    total: int
    page: int
    page_size: int
    flights: List[FlightResponse]


class StatsResponse(BaseModel):
    """Statistics response model."""
    total_flights: int
    flights_with_price_changes: int
    unique_origins: int
    unique_destinations: int
    cheapest_flight: Optional[Dict[str, Any]]
    most_expensive_flight: Optional[Dict[str, Any]]
    average_price: float


class ScanIterationResponse(BaseModel):
    """Scan iteration response model."""
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    stats: Dict[str, Any]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScanRequest(BaseModel):
    """Request model for triggering a scan."""
    departure_airports: Optional[List[str]] = Field(
        default=None,
        description="List of departure airport codes (e.g., ['WRO', 'KRK']). If not provided, scans all Polish airports."
    )
    trip_duration_days: Optional[int] = Field(
        default=4,
        ge=1,
        le=30,
        description="Number of days between outbound and return flight"
    )
    scan_until_date: Optional[str] = Field(
        default="2025-12-31",
        description="Scan all date ranges until this date (YYYY-MM-DD)"
    )


class ScanTriggerResponse(BaseModel):
    """Response model for scan trigger."""
    message: str
    status: str
    scan_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


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


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Ryanair Flight Scanner API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Health check endpoint",
            "GET /flights": "Query flights with filters and sorting",
            "GET /flights/{flight_id}": "Get specific flight details",
            "GET /flights/stats/summary": "Get database statistics",
            "GET /airports/origins": "Get list of available origin airports",
            "GET /airports/destinations": "Get list of available destination airports",
            "GET /airports/routes": "Get list of available routes",
            "GET /scans": "Get scan iteration history",
            "GET /scans/latest": "Get latest scan iteration details",
            "POST /scans/run": "Trigger a new flight scan (background task)"
        }
    }


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
    # Build MongoDB query
    query = {}

    if origin:
        query["origin"] = origin.upper()

    if destination:
        query["destination"] = destination.upper()

    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = date_from.strftime("%Y-%m-%d")
        if date_to:
            date_query["$lte"] = date_to.strftime("%Y-%m-%d")
        query["date_out"] = date_query

    if min_price is not None or max_price is not None:
        price_query = {}
        if min_price is not None:
            price_query["$gte"] = min_price
        if max_price is not None:
            price_query["$lte"] = max_price
        query["current_price"] = price_query

    if currency:
        query["currency"] = currency.upper()

    # Determine sort order
    sort_field = "current_price"
    sort_direction = ASCENDING

    if sort_by == "price":
        sort_field = "current_price"
        sort_direction = ASCENDING
    elif sort_by == "price_desc":
        sort_field = "current_price"
        sort_direction = DESCENDING
    elif sort_by == "date":
        sort_field = "date_out"
        sort_direction = ASCENDING
    elif sort_by == "duration":
        sort_field = "duration"
        sort_direction = ASCENDING

    # Count total results
    total = flights_collection.count_documents(query)

    # Calculate pagination
    skip = (page - 1) * page_size

    # Execute query
    cursor = flights_collection.find(query).sort(sort_field, sort_direction).skip(skip).limit(page_size)

    # Convert to response models
    flights = []
    for doc in cursor:
        # Convert MongoDB document to FlightResponse
        doc.pop("_id", None)  # Remove MongoDB _id field
        flights.append(FlightResponse(**doc))

    return FlightListResponse(
        total=total,
        page=page,
        page_size=page_size,
        flights=flights
    )


@app.get("/flights/{flight_id}", response_model=FlightResponse)
async def get_flight(flight_id: str):
    """
    Get detailed information about a specific flight including full price history.
    """
    flight = flights_collection.find_one({"flight_id": flight_id})

    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")

    flight.pop("_id", None)
    return FlightResponse(**flight)


@app.get("/flights/stats/summary", response_model=StatsResponse)
async def get_stats():
    """
    Get database statistics including total flights, price changes, and price ranges.
    """
    # Total flights
    total_flights = flights_collection.count_documents({})

    # Flights with price changes
    flights_with_changes = flights_collection.count_documents({
        "price_history.1": {"$exists": True}
    })

    # Unique origins and destinations
    unique_origins = len(flights_collection.distinct("origin"))
    unique_destinations = len(flights_collection.distinct("destination"))

    # Cheapest flight
    cheapest = flights_collection.find_one(sort=[("current_price", ASCENDING)])
    cheapest_flight = None
    if cheapest:
        cheapest_flight = {
            "flight_id": cheapest.get("flight_id"),
            "route": f"{cheapest.get('origin')} → {cheapest.get('destination')}",
            "price": cheapest.get("current_price"),
            "currency": cheapest.get("currency"),
            "date": cheapest.get("date_out")
        }

    # Most expensive flight
    most_expensive = flights_collection.find_one(sort=[("current_price", DESCENDING)])
    most_expensive_flight = None
    if most_expensive:
        most_expensive_flight = {
            "flight_id": most_expensive.get("flight_id"),
            "route": f"{most_expensive.get('origin')} → {most_expensive.get('destination')}",
            "price": most_expensive.get("current_price"),
            "currency": most_expensive.get("currency"),
            "date": most_expensive.get("date_out")
        }

    # Average price
    pipeline = [
        {"$group": {"_id": None, "avg_price": {"$avg": "$current_price"}}}
    ]
    avg_result = list(flights_collection.aggregate(pipeline))
    average_price = avg_result[0]["avg_price"] if avg_result else 0.0

    return StatsResponse(
        total_flights=total_flights,
        flights_with_price_changes=flights_with_changes,
        unique_origins=unique_origins,
        unique_destinations=unique_destinations,
        cheapest_flight=cheapest_flight,
        most_expensive_flight=most_expensive_flight,
        average_price=round(average_price, 2)
    )


@app.get("/airports/origins")
async def get_origins():
    """
    Get list of all available origin airports with flight counts.
    """
    pipeline = [
        {"$group": {
            "_id": "$origin",
            "origin_name": {"$first": "$origin_name"},
            "flight_count": {"$sum": 1}
        }},
        {"$sort": {"_id": ASCENDING}}
    ]

    results = list(flights_collection.aggregate(pipeline))

    origins = [
        {
            "code": r["_id"],
            "name": r["origin_name"],
            "flight_count": r["flight_count"]
        }
        for r in results
    ]

    return {"origins": origins}


@app.get("/airports/destinations")
async def get_destinations():
    """
    Get list of all available destination airports with flight counts.
    """
    pipeline = [
        {"$group": {
            "_id": "$destination",
            "destination_name": {"$first": "$destination_name"},
            "flight_count": {"$sum": 1}
        }},
        {"$sort": {"_id": ASCENDING}}
    ]

    results = list(flights_collection.aggregate(pipeline))

    destinations = [
        {
            "code": r["_id"],
            "name": r["destination_name"],
            "flight_count": r["flight_count"]
        }
        for r in results
    ]

    return {"destinations": destinations}


@app.get("/airports/routes")
async def get_routes(origin: Optional[str] = Query(None, description="Filter routes by origin")):
    """
    Get list of all available routes with flight counts.
    """
    match_stage = {}
    if origin:
        match_stage = {"$match": {"origin": origin.upper()}}

    pipeline = [
        match_stage,
        {"$group": {
            "_id": {
                "origin": "$origin",
                "destination": "$destination"
            },
            "origin_name": {"$first": "$origin_name"},
            "destination_name": {"$first": "$destination_name"},
            "flight_count": {"$sum": 1},
            "min_price": {"$min": "$current_price"},
            "max_price": {"$max": "$current_price"},
            "avg_price": {"$avg": "$current_price"},
            "currency": {"$first": "$currency"}
        }},
        {"$sort": {"_id.origin": ASCENDING, "_id.destination": ASCENDING}}
    ]

    # Remove empty match stage
    if not match_stage:
        pipeline = pipeline[1:]

    results = list(flights_collection.aggregate(pipeline))

    routes = [
        {
            "origin": r["_id"]["origin"],
            "origin_name": r["origin_name"],
            "destination": r["_id"]["destination"],
            "destination_name": r["destination_name"],
            "flight_count": r["flight_count"],
            "min_price": round(r["min_price"], 2),
            "max_price": round(r["max_price"], 2),
            "avg_price": round(r["avg_price"], 2),
            "currency": r["currency"]
        }
        for r in results
    ]

    return {"routes": routes}


@app.get("/scans", response_model=List[ScanIterationResponse])
async def get_scans(limit: int = Query(10, ge=1, le=100, description="Number of scans to return")):
    """
    Get scan iteration history.
    """
    cursor = scan_iterations_collection.find().sort("start_time", DESCENDING).limit(limit)

    scans = []
    for doc in cursor:
        doc.pop("_id", None)
        doc.pop("date_ranges", None)  # Remove detailed date ranges to keep response small
        doc.pop("config", None)  # Remove config details
        scans.append(ScanIterationResponse(**doc))

    return scans


@app.get("/scans/latest", response_model=ScanIterationResponse)
async def get_latest_scan():
    """
    Get details of the most recent scan iteration.
    """
    scan = scan_iterations_collection.find_one(sort=[("start_time", DESCENDING)])

    if not scan:
        raise HTTPException(status_code=404, detail="No scan iterations found")

    scan.pop("_id", None)
    scan.pop("date_ranges", None)  # Remove detailed date ranges to keep response small
    scan.pop("config", None)  # Remove config details

    return ScanIterationResponse(**scan)


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API and database connectivity.
    """
    try:
        # Test MongoDB connection
        db.command("ping")

        # Get basic stats
        flight_count = flights_collection.count_documents({})

        return {
            "status": "healthy",
            "database": "connected",
            "flights_in_database": flight_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


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
        from ryanair_scanner import (
            scan_flights,
            generate_date_ranges,
            ScanIterationManager,
            FlightStorage,
            SCAN_ITERATIONS_COLLECTION,
            FLIGHTS_COLLECTION
        )
        from ryanair import get_valid_cookie
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
            from ryanair_scanner import ScanIterationManager, SCAN_ITERATIONS_COLLECTION
            scan_manager = ScanIterationManager(
                settings.mongo_uri,
                settings.MONGO_DATABASE,
                SCAN_ITERATIONS_COLLECTION
            )
            scan_manager.complete_scan(scan_id, success=False)
        except:
            pass


@app.post("/scans/run", response_model=ScanTriggerResponse)
async def trigger_scan(scan_request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Trigger a new flight scan.

    This endpoint starts a background scan job and returns immediately.
    Use GET /scans/latest or GET /scans to check the scan progress.
    """
    try:
        from ryanair_scanner import ScanIterationManager, SCAN_ITERATIONS_COLLECTION

        # Default departure airports (all Polish airports)
        default_airports = ["GDN", "SZN", "KRK", "KTW", "WRO", "POZ", "WMI", "WAW", "LCJ", "LUZ", "RZE", "SZY", "BZG"]

        departure_airports = scan_request.departure_airports or default_airports
        trip_duration_days = scan_request.trip_duration_days or 4
        scan_until_date = scan_request.scan_until_date or "2025-12-31"

        # Validate departure airports
        departure_airports = [airport.upper() for airport in departure_airports]

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
        }

        scan_id = scan_manager.start_scan(config)

        # Start background scan
        background_tasks.add_task(
            run_scanner_background,
            departure_airports,
            trip_duration_days,
            scan_until_date,
            scan_id
        )

        logger.info(f"Scan triggered: {scan_id}")

        return ScanTriggerResponse(
            message="Scan started successfully. Use GET /scans/latest to check progress.",
            status="started",
            scan_id=scan_id,
            config=config
        )

    except Exception as e:
        logger.error(f"Failed to trigger scan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger scan: {str(e)}")


# ============================================================================
# STARTUP EVENT
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
    logger.info("=" * 60)

    try:
        db.command("ping")
        flight_count = flights_collection.count_documents({})
        logger.success(f"✓ MongoDB connected - {flight_count} flights in database")
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
