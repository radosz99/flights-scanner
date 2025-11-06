#!/usr/bin/env python3

"""
Main entry point for Ryanair flight scanner.

This demonstrates the robust cookie management system that:
1. Checks for active cookies in MongoDB
2. Tests them automatically
3. Refreshes if needed
4. Returns validated cookie ready for use

Usage:
    python3 main.py
"""

from ryanair import get_valid_cookie, get_ryanair_flights
from flight_connector import load_from_mongodb
from config import settings
from datetime import datetime, timedelta
from loguru import logger


def main():
    """Main entry point with robust cookie management and WRO airport route scanning."""
    logger.info("=" * 80)
    logger.info("RYANAIR FLIGHT SCANNER - WRO AIRPORT DEPARTURES")
    logger.info("=" * 80)

    # Step 1: Get valid cookie (automatically handles everything)
    logger.info("Getting valid cookie...")
    cookie = get_valid_cookie(auto_refresh=True)

    if not cookie:
        logger.error("Failed to get valid cookie")
        logger.warning("Please ensure:")
        logger.warning("  - MongoDB is running")
        logger.warning("  - Chrome/ChromeDriver is installed")
        logger.warning("  - Internet connection is available")
        return False

    # Step 2: Load Ryanair database to get all WRO departures
    logger.info("=" * 80)
    logger.info("LOADING RYANAIR ROUTES FROM DATABASE")
    logger.info("=" * 80)

    database = load_from_mongodb("ryanair", settings.mongo_uri)

    if not database:
        logger.error("Failed to load Ryanair database from MongoDB")
        logger.warning("Make sure MongoDB is running and database has been populated.")
        logger.warning("Run: python3 populate_databases.py")
        return False

    # Get all destinations from WRO
    airport_code = "WRO"
    airport = database.get_airport_by_code(airport_code)

    if not airport:
        logger.error(f"Airport {airport_code} not found in database")
        return False

    destinations = database.get_connections_from(airport_code)

    logger.success(f"Found airport: {airport.name} ({airport_code})")
    logger.info(f"Number of destinations: {len(destinations)}")

    # Step 3: Set date range
    date_out = datetime.now() + timedelta(days=30)  # 30 days from now
    date_in = date_out + timedelta(days=2)  # 2-day trip

    date_out_str = date_out.strftime("%Y-%m-%d")
    date_in_str = date_in.strftime("%Y-%m-%d")

    logger.info(f"Date range: {date_out_str} to {date_in_str}")

    # Step 4: Fetch flights for each destination
    logger.info("=" * 80)
    logger.info("FETCHING FLIGHTS FOR ALL WRO DEPARTURES")
    logger.info("=" * 80)

    successful_queries = 0
    failed_queries = 0

    for i, dest_code in enumerate(destinations, 1):
        dest_airport = database.get_airport_by_code(dest_code)
        dest_name = dest_airport.name if dest_airport else dest_code

        logger.info(f"\n[{i}/{len(destinations)}] Querying: {airport_code} → {dest_code} ({dest_name})")

        try:
            flights = get_ryanair_flights(
                origin=airport_code,
                destination=dest_code,
                date_out=date_out_str,
                date_in=date_in_str,
                adt=1,
                cookies=cookie
            )

            logger.success(f"Successfully fetched flight data for {airport_code} → {dest_code}")
            logger.info(f"  Currency: {flights.currency}")
            logger.info(f"  Trips found: {len(flights.trips)}")

            # Display some flight details
            for trip in flights.trips[:1]:  # Show first trip only
                for date_info in trip.dates[:1]:  # Show first date only
                    if date_info.flights:
                        logger.info(f"  Date: {date_info.dateOut}")

                        for flight in date_info.flights[:1]:  # Show first flight only
                            logger.info(f"    Flight {flight.flightNumber}: {flight.time[0]} → {flight.time[1]}")
                            logger.info(f"    Duration: {flight.duration}")

                            if flight.regularFare and flight.regularFare.fares:
                                price = flight.regularFare.fares[0].amount
                                logger.info(f"    Price: {price} {flights.currency}")

            successful_queries += 1

        except Exception as e:
            logger.error(f"Error fetching flights for {airport_code} → {dest_code}: {str(e)[:100]}")
            failed_queries += 1

    # Summary
    logger.info("=" * 80)
    logger.success("SCAN COMPLETED!")
    logger.info("=" * 80)
    logger.info(f"Total destinations: {len(destinations)}")
    logger.success(f"Successful queries: {successful_queries}")
    if failed_queries > 0:
        logger.warning(f"Failed queries: {failed_queries}")

    return True


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
