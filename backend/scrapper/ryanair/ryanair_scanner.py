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

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from .ryanair import get_valid_cookie, get_ryanair_flights
from config import settings
from constants import POLISH_AIRPORTS
from database_population import load_from_mongodb
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
TRIP_DURATION_DAYS = 4  # How many days between date_out and date_in
SCAN_UNTIL_DATE = "2025-12-31"  # Scan all date ranges until this date

# Departure airports to scan (all Polish airports)
DEPARTURE_AIRPORTS = POLISH_AIRPORTS

# MongoDB collection names
FLIGHTS_COLLECTION = "ryanair_flights"
SCAN_ITERATIONS_COLLECTION = "scan_iterations"

# ============================================================================
# MONGODB FLIGHT STORAGE
# ============================================================================

class FlightStorage:
    """Handles MongoDB storage and price tracking for individual flights."""

    def __init__(self, mongo_uri: str, database_name: str, collection_name: str, create_indexes: bool = False):
        """Initialize MongoDB connection."""
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        if create_indexes:
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

        logger.success(f"✓ Created indexes on collection: {self.collection.name}")

    def create_indexes(self):
        """Public method to create indexes (called once before scanning)."""
        self._create_indexes()

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


class ScanIterationManager:
    """Manages scan iterations and enforces scan interval rules."""

    def __init__(self, mongo_uri: str, database_name: str, collection_name: str, create_indexes: bool = False):
        """Initialize MongoDB connection for scan iterations."""
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        if create_indexes:
            self._create_indexes()

    def _create_indexes(self):
        """Create indexes for efficient querying."""
        self.collection.create_index("start_time", unique=False)
        self.collection.create_index("status", unique=False)
        logger.success(f"✓ Created indexes on collection: {self.collection.name}")

    def can_start_scan(self, scan_interval_hours: int) -> tuple[bool, Optional[str]]:
        """
        Check if enough time has passed since last scan to start a new one.

        Args:
            scan_interval_hours: Minimum hours between scans

        Returns:
            Tuple of (can_start, reason_if_cannot)
        """
        # Find the most recent completed scan
        last_scan = self.collection.find_one(
            {"status": "completed"},
            sort=[("start_time", -1)]
        )

        if not last_scan:
            # No previous scans, can start
            return True, None

        last_scan_time = last_scan.get("start_time")
        if not last_scan_time:
            return True, None

        time_since_last = datetime.now() - last_scan_time
        hours_since_last = time_since_last.total_seconds() / 3600

        if hours_since_last < scan_interval_hours:
            time_remaining = scan_interval_hours - hours_since_last
            return False, f"Last scan was {hours_since_last:.1f} hours ago. Wait {time_remaining:.1f} more hours."

        return True, None

    def start_scan(self, config: Dict[str, Any]) -> str:
        """
        Record the start of a new scan iteration.

        Args:
            config: Configuration used for this scan

        Returns:
            Scan iteration ID
        """
        total_date_ranges = config.get("total_date_ranges", 0)
        scan_doc = {
            "start_time": datetime.now(),
            "status": "running",
            "config": config,
            "date_ranges": [],
            "stats": {
                "total_routes": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "flights_saved": 0
            },
            "progress": {
                "total_date_ranges": total_date_ranges,
                "completed_date_ranges": 0,
                "current_date_range": None,
                "percentage": 0
            }
        }
        result = self.collection.insert_one(scan_doc)
        logger.success(f"Started scan iteration: {result.inserted_id}")
        return str(result.inserted_id)

    def add_date_range_result(self, scan_id: str, date_out: str, date_in: str, stats: Dict[str, Any]):
        """
        Add results from scanning a specific date range.

        Args:
            scan_id: Scan iteration ID
            date_out: Outbound date
            date_in: Return date
            stats: Statistics from this date range scan
        """
        from bson import ObjectId

        # Get current scan to calculate progress
        scan = self.collection.find_one({"_id": ObjectId(scan_id)})
        if scan:
            completed = scan.get("progress", {}).get("completed_date_ranges", 0) + 1
            total = scan.get("progress", {}).get("total_date_ranges", 1)
            percentage = round((completed / total) * 100, 1) if total > 0 else 0
        else:
            completed = 1
            percentage = 0

        self.collection.update_one(
            {"_id": ObjectId(scan_id)},
            {
                "$push": {
                    "date_ranges": {
                        "date_out": date_out,
                        "date_in": date_in,
                        "timestamp": datetime.now(),
                        "stats": stats
                    }
                },
                "$inc": {
                    "stats.total_routes": stats.get("total_routes", 0),
                    "stats.successful_queries": stats.get("successful_queries", 0),
                    "stats.failed_queries": stats.get("failed_queries", 0),
                    "stats.flights_saved": stats.get("flights_saved", 0),
                    "progress.completed_date_ranges": 1
                },
                "$set": {
                    "progress.percentage": percentage,
                    "progress.current_date_range": f"{date_out} to {date_in}"
                }
            }
        )

    def complete_scan(self, scan_id: str, success: bool = True):
        """
        Mark a scan iteration as completed.

        Args:
            scan_id: Scan iteration ID
            success: Whether the scan completed successfully
        """
        from bson import ObjectId
        self.collection.update_one(
            {"_id": ObjectId(scan_id)},
            {
                "$set": {
                    "end_time": datetime.now(),
                    "status": "completed" if success else "failed",
                    "progress.percentage": 100 if success else None
                }
            }
        )
        logger.success(f"Scan iteration completed: {scan_id}")

    def get_scan_stats(self) -> Dict[str, Any]:
        """Get statistics about all scan iterations."""
        total_scans = self.collection.count_documents({})
        completed_scans = self.collection.count_documents({"status": "completed"})
        failed_scans = self.collection.count_documents({"status": "failed"})
        running_scans = self.collection.count_documents({"status": "running"})

        return {
            "total_scans": total_scans,
            "completed_scans": completed_scans,
            "failed_scans": failed_scans,
            "running_scans": running_scans
        }


def extract_flight_data(trip, flight_date, flight, currency: str, storage: FlightStorage) -> Optional[Dict[str, Any]]:
    """
    Extract and flatten flight data from Trip/FlightDate/Flight structure.

    Args:
        trip: Trip object containing origin/destination info
        flight_date: FlightDate object containing date info
        flight: Individual Flight object
        currency: Currency code
        storage: FlightStorage instance for generating flight IDs

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

        # Generate unique flight ID using passed storage instance
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
    cookie: str,
    storage: FlightStorage
) -> Dict[str, int]:
    """
    Scan flights from specified airports and save to MongoDB.

    Args:
        departure_airports: List of airport codes to scan from
        date_out_str: Outbound date (YYYY-MM-DD)
        date_in_str: Return date (YYYY-MM-DD)
        cookie: Valid Ryanair cookie
        storage: FlightStorage instance for saving flights

    Returns:
        Dictionary with scan statistics
    """
    scan_timestamp = datetime.now()

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
    for airport_idx, airport_code in enumerate(departure_airports, 1):
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
                            # Extract flight data - pass storage instance
                            flight_data = extract_flight_data(
                                trip, flight_date, flight, flights.currency, storage
                            )

                            if flight_data:
                                # Save to MongoDB
                                if storage.save_flight(flight_data, scan_timestamp):
                                    stats["flights_saved"] += 1

                logger.success(f"✓ {airport_code} → {dest_code}: {len(flights.trips)} trips processed")

            except Exception as e:
                logger.error(f"✗ {airport_code} → {dest_code}: {str(e)[:100]}")
                stats["failed_queries"] += 1

        # Log progress after each airport
        remaining_airports = len(departure_airports) - airport_idx
        logger.info(f"✈️  Completed {airport.name} ({airport_code}). Airports remaining: {remaining_airports}/{len(departure_airports)}")

    return stats


def generate_date_ranges(start_date: datetime, end_date: datetime, trip_duration_days: int) -> List[tuple[str, str]]:
    """
    Generate date ranges from start_date to end_date.

    Args:
        start_date: Starting date (typically today)
        end_date: Maximum date to scan until
        trip_duration_days: Number of days between date_out and date_in

    Returns:
        List of tuples [(date_out, date_in), ...]
    """
    date_ranges = []
    current_date_out = start_date

    while current_date_out.date() <= end_date.date():
        date_out_str = current_date_out.strftime("%Y-%m-%d")
        current_date_in = current_date_out + timedelta(days=trip_duration_days)
        date_in_str = current_date_in.strftime("%Y-%m-%d")

        date_ranges.append((date_out_str, date_in_str))

        # Move to next date range: date_out becomes current date_in
        current_date_out = current_date_in

    return date_ranges


def main():
    """Main entry point for the Ryanair scanner."""
    logger.info("=" * 80)
    logger.info("RYANAIR FLIGHT SCANNER - MONGODB PRICE TRACKING")
    logger.info("=" * 80)
    logger.info(f"Scan interval: {SCAN_INTERVAL_HOURS} hour(s)")
    logger.info(f"Departure airports: {', '.join(DEPARTURE_AIRPORTS)}")
    logger.info(f"Trip duration: {TRIP_DURATION_DAYS} days")
    logger.info(f"Scan until date: {SCAN_UNTIL_DATE}")
    logger.info("=" * 80)

    # Create indexes once before starting scan
    logger.info("Creating database indexes...")
    storage = FlightStorage(settings.mongo_uri, settings.MONGO_DATABASE, FLIGHTS_COLLECTION, create_indexes=True)

    # Check if enough time has passed since last scan
    scan_manager = ScanIterationManager(
        settings.mongo_uri,
        settings.MONGO_DATABASE,
        SCAN_ITERATIONS_COLLECTION,
        create_indexes=True
    )

    can_start, reason = scan_manager.can_start_scan(SCAN_INTERVAL_HOURS)
    if not can_start:
        logger.warning(f"Cannot start scan: {reason}")
        logger.info("Scan skipped due to interval restriction.")
        return True  # Not an error, just skipped

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

    # Generate all date ranges
    today = datetime.now()
    scan_until = datetime.strptime(SCAN_UNTIL_DATE, "%Y-%m-%d")
    date_ranges = generate_date_ranges(today, scan_until, TRIP_DURATION_DAYS)

    logger.info(f"Generated {len(date_ranges)} date ranges to scan")
    logger.info(f"First range: {date_ranges[0][0]} to {date_ranges[0][1]}")
    logger.info(f"Last range: {date_ranges[-1][0]} to {date_ranges[-1][1]}")
    logger.info("=" * 80)

    # Start scan iteration
    config = {
        "scan_interval_hours": SCAN_INTERVAL_HOURS,
        "trip_duration_days": TRIP_DURATION_DAYS,
        "scan_until_date": SCAN_UNTIL_DATE,
        "departure_airports": DEPARTURE_AIRPORTS,
        "total_date_ranges": len(date_ranges)
    }
    scan_id = scan_manager.start_scan(config)

    # Run scan for each date range
    overall_start = datetime.now()
    total_stats = {
        "total_routes": 0,
        "successful_queries": 0,
        "failed_queries": 0,
        "flights_saved": 0
    }

    try:
        for idx, (date_out_str, date_in_str) in enumerate(date_ranges, 1):
            logger.info("=" * 80)
            logger.info(f"DATE RANGE {idx}/{len(date_ranges)}: {date_out_str} to {date_in_str}")
            logger.info("=" * 80)

            range_start = datetime.now()
            stats = scan_flights(DEPARTURE_AIRPORTS, date_out_str, date_in_str, cookie, storage)
            range_duration = (datetime.now() - range_start).total_seconds()

            # Update totals
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)

            # Record this date range result
            scan_manager.add_date_range_result(scan_id, date_out_str, date_in_str, stats)

            logger.info(f"Range completed in {range_duration:.1f}s: {stats.get('successful_queries', 0)} successful, {stats.get('failed_queries', 0)} failed")

        # Mark scan as completed
        scan_manager.complete_scan(scan_id, success=True)
        overall_duration = (datetime.now() - overall_start).total_seconds()

        # Display final results
        logger.info("=" * 80)
        logger.success("FULL SCAN COMPLETED!")
        logger.info("=" * 80)
        logger.info(f"Total duration: {overall_duration:.1f} seconds ({overall_duration/60:.1f} minutes)")
        logger.info(f"Date ranges scanned: {len(date_ranges)}")
        logger.info(f"Total routes scanned: {total_stats['total_routes']}")
        logger.success(f"Successful queries: {total_stats['successful_queries']}")
        logger.info(f"Flights saved/updated: {total_stats['flights_saved']}")

        if total_stats['failed_queries'] > 0:
            logger.warning(f"Failed queries: {total_stats['failed_queries']}")

        # Get storage statistics (reuse existing storage instance)
        db_stats = storage.get_flight_stats()

        logger.info("=" * 80)
        logger.info("DATABASE STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Total flights in database: {db_stats['total_flights']}")
        logger.info(f"Flights with price changes: {db_stats['flights_with_price_changes']}")

        # Get scan iteration statistics
        iteration_stats = scan_manager.get_scan_stats()
        logger.info("=" * 80)
        logger.info("SCAN ITERATION STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Total scans: {iteration_stats['total_scans']}")
        logger.info(f"Completed scans: {iteration_stats['completed_scans']}")
        logger.info(f"Failed scans: {iteration_stats['failed_scans']}")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Scan failed with error: {e}")
        scan_manager.complete_scan(scan_id, success=False)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
