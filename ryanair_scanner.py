#!/usr/bin/env python3

"""
Ryanair Flight Scanner with MongoDB storage and price tracking.

This scanner:
1. Fetches flights from specified departure airports
2. Saves individual flight records to MongoDB
3. Tracks price changes over time
4. Runs periodically to monitor price fluctuations

Configuration is set via variables at the top of this file.
"""

from ryanair import get_valid_cookie, get_ryanair_flights
from flight_connector import load_from_mongodb
from config import settings
from datetime import datetime, timedelta
from loguru import logger
from pymongo import MongoClient, ASCENDING
from typing import Optional, List, Dict, Any
import time
import sys

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Scan interval in hours (how often to run the scanner)
SCAN_INTERVAL_HOURS = 1

# Date range configuration
DATE_RANGE_DAYS_FROM_NOW = 30  # Outbound flight X days from now
TRIP_DURATION_DAYS = 2  # How many days for the trip

# Departure airports to scan
DEPARTURE_AIRPORTS = ["WRO"]

# MongoDB collection name for flight records
FLIGHTS_COLLECTION = "ryanair_flights"

# ============================================================================
# MONGODB FLIGHT STORAGE
# ============================================================================

class FlightStorage:
    """Handles MongoDB storage and price tracking for individual flights."""

    def __init__(self, mongo_uri: str, database_name: str, collection_name: str):
        """Initialize MongoDB connection."""
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes for efficient querying and unique constraints."""
        # Unique index on flight_id
        self.collection.create_index("flight_id", unique=True)

        # Compound index for common queries
        self.collection.create_index([
            ("origin", ASCENDING),
            ("destination", ASCENDING),
            ("date_out", ASCENDING)
        ])

        # Index for price tracking queries
        self.collection.create_index("last_seen")
        self.collection.create_index("current_price")

        logger.info(f"Created indexes on collection: {self.collection.name}")

    def _generate_flight_id(self, origin: str, destination: str, flight_number: str,
                           date_out: str, departure_time: str) -> str:
        """
        Generate unique flight identifier.

        Format: {origin}_{destination}_{flight_number}_{date_out}_{departure_time}
        Example: WRO_ALC_FR1234_2025-12-06_10:30
        """
        return f"{origin}_{destination}_{flight_number}_{date_out}_{departure_time}"

    def save_flight(self, flight_data: Dict[str, Any], scan_timestamp: datetime) -> bool:
        """
        Save or update a flight record with price tracking.

        Args:
            flight_data: Dictionary containing all flight information
            scan_timestamp: Timestamp of when this scan occurred

        Returns:
            True if successful, False otherwise
        """
        try:
            flight_id = flight_data["flight_id"]
            current_price = flight_data["current_price"]

            # Check if flight already exists
            existing_flight = self.collection.find_one({"flight_id": flight_id})

            if existing_flight:
                # Update existing flight
                price_changed = existing_flight.get("current_price") != current_price

                update_data = {
                    "$set": {
                        "current_price": current_price,
                        "last_seen": scan_timestamp,
                        "scan_count": existing_flight.get("scan_count", 0) + 1
                    }
                }

                # Add to price history if price changed
                if price_changed:
                    update_data["$push"] = {
                        "price_history": {
                            "price": current_price,
                            "timestamp": scan_timestamp,
                            "change": current_price - existing_flight.get("current_price", current_price)
                        }
                    }
                    logger.info(
                        f"Price change detected for {flight_id}: "
                        f"{existing_flight.get('current_price')} → {current_price}"
                    )

                self.collection.update_one({"flight_id": flight_id}, update_data)

            else:
                # Insert new flight
                flight_data["first_seen"] = scan_timestamp
                flight_data["last_seen"] = scan_timestamp
                flight_data["scan_count"] = 1
                flight_data["price_history"] = [{
                    "price": current_price,
                    "timestamp": scan_timestamp,
                    "change": 0
                }]

                self.collection.insert_one(flight_data)
                logger.success(f"New flight saved: {flight_id} at {current_price} {flight_data['currency']}")

            return True

        except Exception as e:
            logger.error(f"Error saving flight: {e}")
            return False

    def get_flight_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked flights."""
        total_flights = self.collection.count_documents({})

        # Count flights with price changes
        flights_with_changes = self.collection.count_documents({
            "price_history.1": {"$exists": True}  # Has more than 1 price entry
        })

        return {
            "total_flights": total_flights,
            "flights_with_price_changes": flights_with_changes,
            "collection": self.collection.name
        }


def extract_flight_data(trip, flight_date, flight, currency: str) -> Optional[Dict[str, Any]]:
    """
    Extract and flatten flight data from Trip/FlightDate/Flight structure.

    Args:
        trip: Trip object containing origin/destination info
        flight_date: FlightDate object containing date info
        flight: Individual Flight object
        currency: Currency code

    Returns:
        Dictionary with flattened flight data ready for MongoDB storage
    """
    try:
        # Get price information
        price = None
        if flight.regularFare and flight.regularFare.fares and len(flight.regularFare.fares) > 0:
            price = flight.regularFare.fares[0].amount

        if price is None:
            logger.warning(f"No price found for flight {flight.flightNumber}, skipping")
            return None

        # Extract times
        departure_time = flight.time[0] if len(flight.time) > 0 else ""
        arrival_time = flight.time[1] if len(flight.time) > 1 else ""

        # Generate unique flight ID
        storage = FlightStorage(settings.mongo_uri, settings.MONGO_DATABASE, FLIGHTS_COLLECTION)
        flight_id = storage._generate_flight_id(
            trip.origin,
            trip.destination,
            flight.flightNumber,
            flight_date.dateOut,
            departure_time
        )

        # Build flight data structure
        flight_data = {
            "flight_id": flight_id,

            # Route information
            "origin": trip.origin,
            "origin_name": trip.originName,
            "destination": trip.destination,
            "destination_name": trip.destinationName,

            # Flight details
            "flight_number": flight.flightNumber,
            "flight_key": flight.flightKey,
            "operator": flight.operatedBy,

            # Date and time
            "date_out": flight_date.dateOut,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "departure_time_utc": flight.timeUTC[0] if len(flight.timeUTC) > 0 else "",
            "arrival_time_utc": flight.timeUTC[1] if len(flight.timeUTC) > 1 else "",
            "duration": flight.duration,

            # Price information
            "current_price": price,
            "currency": currency,
            "fare_key": flight.regularFare.fareKey,

            # Availability
            "fares_left": flight.faresLeft,
            "infants_left": flight.infantsLeft,

            # Segments (for multi-leg flights)
            "segments": [
                {
                    "segment_nr": seg.segmentNr,
                    "origin": seg.origin,
                    "destination": seg.destination,
                    "flight_number": seg.flightNumber,
                    "departure_time": seg.time[0] if len(seg.time) > 0 else "",
                    "arrival_time": seg.time[1] if len(seg.time) > 1 else "",
                    "duration": seg.duration
                }
                for seg in flight.segments
            ],

            # Trip metadata
            "trip_type": trip.tripType,
            "route_group": trip.routeGroup,
        }

        return flight_data

    except Exception as e:
        logger.error(f"Error extracting flight data: {e}")
        return None


# ============================================================================
# MAIN SCANNER LOGIC
# ============================================================================

def scan_flights(
    departure_airports: List[str],
    date_out_str: str,
    date_in_str: str,
    cookie: str
) -> Dict[str, int]:
    """
    Scan flights from specified airports and save to MongoDB.

    Args:
        departure_airports: List of airport codes to scan from
        date_out_str: Outbound date (YYYY-MM-DD)
        date_in_str: Return date (YYYY-MM-DD)
        cookie: Valid Ryanair cookie

    Returns:
        Dictionary with scan statistics
    """
    scan_timestamp = datetime.now()
    storage = FlightStorage(settings.mongo_uri, settings.MONGO_DATABASE, FLIGHTS_COLLECTION)

    # Load Ryanair database for route information
    database = load_from_mongodb("ryanair", settings.mongo_uri)
    if not database:
        logger.error("Failed to load Ryanair database from MongoDB")
        return {"error": "database_load_failed"}

    stats = {
        "total_routes": 0,
        "successful_queries": 0,
        "failed_queries": 0,
        "flights_saved": 0,
        "flights_updated": 0
    }

    # Scan each departure airport
    for airport_code in departure_airports:
        airport = database.get_airport_by_code(airport_code)
        if not airport:
            logger.error(f"Airport {airport_code} not found in database")
            continue

        destinations = database.get_connections_from(airport_code)
        logger.success(f"Scanning {airport.name} ({airport_code}) - {len(destinations)} destinations")

        stats["total_routes"] += len(destinations)

        # Query each destination
        for i, dest_code in enumerate(destinations, 1):
            dest_airport = database.get_airport_by_code(dest_code)
            dest_name = dest_airport.name if dest_airport else dest_code

            logger.info(f"[{i}/{len(destinations)}] {airport_code} → {dest_code} ({dest_name})")

            try:
                # Fetch flights
                flights = get_ryanair_flights(
                    origin=airport_code,
                    destination=dest_code,
                    date_out=date_out_str,
                    date_in=date_in_str,
                    adt=1,
                    cookies=cookie
                )

                stats["successful_queries"] += 1

                # Process each trip -> date -> flight
                for trip in flights.trips:
                    for flight_date in trip.dates:
                        for flight in flight_date.flights:
                            # Extract flight data
                            flight_data = extract_flight_data(
                                trip, flight_date, flight, flights.currency
                            )

                            if flight_data:
                                # Save to MongoDB
                                if storage.save_flight(flight_data, scan_timestamp):
                                    stats["flights_saved"] += 1

                logger.success(f"✓ {airport_code} → {dest_code}: {len(flights.trips)} trips processed")

            except Exception as e:
                logger.error(f"✗ {airport_code} → {dest_code}: {str(e)[:100]}")
                stats["failed_queries"] += 1

    return stats


def main():
    """Main entry point for the Ryanair scanner."""
    logger.info("=" * 80)
    logger.info("RYANAIR FLIGHT SCANNER - MONGODB PRICE TRACKING")
    logger.info("=" * 80)
    logger.info(f"Scan interval: {SCAN_INTERVAL_HOURS} hour(s)")
    logger.info(f"Departure airports: {', '.join(DEPARTURE_AIRPORTS)}")
    logger.info(f"Date range: {DATE_RANGE_DAYS_FROM_NOW} days from now, {TRIP_DURATION_DAYS} day trip")
    logger.info("=" * 80)

    # Get valid cookie
    logger.info("Getting valid cookie...")
    cookie = get_valid_cookie(auto_refresh=True)

    if not cookie:
        logger.error("Failed to get valid cookie")
        logger.warning("Please ensure:")
        logger.warning("  - MongoDB is running")
        logger.warning("  - Chrome/ChromeDriver is installed")
        logger.warning("  - Internet connection is available")
        return False

    # Calculate date range
    date_out = datetime.now() + timedelta(days=DATE_RANGE_DAYS_FROM_NOW)
    date_in = date_out + timedelta(days=TRIP_DURATION_DAYS)

    date_out_str = date_out.strftime("%Y-%m-%d")
    date_in_str = date_in.strftime("%Y-%m-%d")

    logger.info(f"Scanning flights: {date_out_str} to {date_in_str}")
    logger.info("=" * 80)

    # Run scan
    scan_start = datetime.now()
    stats = scan_flights(DEPARTURE_AIRPORTS, date_out_str, date_in_str, cookie)
    scan_duration = (datetime.now() - scan_start).total_seconds()

    # Display results
    logger.info("=" * 80)
    logger.success("SCAN COMPLETED!")
    logger.info("=" * 80)
    logger.info(f"Duration: {scan_duration:.1f} seconds")
    logger.info(f"Total routes scanned: {stats.get('total_routes', 0)}")
    logger.success(f"Successful queries: {stats.get('successful_queries', 0)}")
    logger.info(f"Flights saved/updated: {stats.get('flights_saved', 0)}")

    if stats.get("failed_queries", 0) > 0:
        logger.warning(f"Failed queries: {stats['failed_queries']}")

    # Get storage statistics
    storage = FlightStorage(settings.mongo_uri, settings.MONGO_DATABASE, FLIGHTS_COLLECTION)
    db_stats = storage.get_flight_stats()

    logger.info("=" * 80)
    logger.info("DATABASE STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Total flights in database: {db_stats['total_flights']}")
    logger.info(f"Flights with price changes: {db_stats['flights_with_price_changes']}")
    logger.info("=" * 80)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
