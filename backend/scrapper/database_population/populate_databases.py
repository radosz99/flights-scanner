#!/usr/bin/env python3

"""
Script to populate MongoDB with Ryanair and Wizz Air flight route data.

This script:
1. Builds airport database from FlightConnections tiles
2. Fetches routes for Ryanair and Wizz Air separately
3. Populates connections for each airline
4. Saves to MongoDB in separate collections

Can be run daily via cron job or scheduled task to keep data updated.

Usage:
    python3 populate_databases.py

Environment:
    Configure MongoDB connection in secrets.json or environment variables
"""

import sys
import os
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from config import settings
from .flight_connector import (
    build_airport_database,
    fetch_ryanair_routes,
    fetch_wizzair_routes,
    save_to_mongodb,
    load_from_mongodb,
)


def populate_ryanair_database():
    """Populate Ryanair route database."""
    logger.info("=" * 80)
    logger.info("POPULATING RYANAIR DATABASE")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Build airport database
    logger.info("-" * 80)
    logger.info("Step 1: Building airport database...")
    logger.info("-" * 80)
    database = build_airport_database()

    if not database.airports:
        logger.error("Failed to build airport database")
        logger.warning("The FlightConnections API may be blocking requests.")
        logger.warning("Please try again later or check your network connection.")
        return False

    # Step 2: Fetch Ryanair routes
    logger.info("-" * 80)
    logger.info("Step 2: Fetching Ryanair routes...")
    logger.info("-" * 80)
    routes = fetch_ryanair_routes()

    if not routes:
        logger.error("Failed to fetch Ryanair routes")
        logger.warning("The FlightConnections API may be blocking requests.")
        logger.warning("Airport database was built successfully, but no routes were fetched.")
        return False

    # Step 3: Populate connections
    logger.info("-" * 80)
    logger.info("Step 3: Populating Ryanair connections...")
    logger.info("-" * 80)
    connections_added = database.populate_connections_from_routes(routes)
    logger.success(f"Added {connections_added} Ryanair connections")

    # Step 4: Save to MongoDB
    logger.info("-" * 80)
    logger.info("Step 4: Saving to MongoDB...")
    logger.info("-" * 80)
    success = save_to_mongodb(database, "ryanair", settings.mongo_uri)

    if success:
        logger.info("=" * 80)
        logger.success("RYANAIR DATABASE POPULATED SUCCESSFULLY")
        logger.info(f"  Airports: {len(database.airports)}")
        logger.info(f"  Connections: {connections_added}")
        logger.info(f"  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        return True
    else:
        logger.error("RYANAIR DATABASE POPULATION FAILED")
        return False


def populate_wizzair_database():
    """Populate Wizz Air route database."""
    logger.info("=" * 80)
    logger.info("POPULATING WIZZ AIR DATABASE")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Build airport database
    logger.info("-" * 80)
    logger.info("Step 1: Building airport database...")
    logger.info("-" * 80)
    database = build_airport_database()

    if not database.airports:
        logger.error("Failed to build airport database")
        logger.warning("The FlightConnections API may be blocking requests.")
        logger.warning("Please try again later or check your network connection.")
        return False

    # Step 2: Fetch Wizz Air routes
    logger.info("-" * 80)
    logger.info("Step 2: Fetching Wizz Air routes...")
    logger.info("-" * 80)
    routes = fetch_wizzair_routes()

    if not routes:
        logger.error("Failed to fetch Wizz Air routes")
        logger.warning("The FlightConnections API may be blocking requests.")
        logger.warning("Airport database was built successfully, but no routes were fetched.")
        return False

    # Step 3: Populate connections
    logger.info("-" * 80)
    logger.info("Step 3: Populating Wizz Air connections...")
    logger.info("-" * 80)
    connections_added = database.populate_connections_from_routes(routes)
    logger.success(f"Added {connections_added} Wizz Air connections")

    # Step 4: Save to MongoDB
    logger.info("-" * 80)
    logger.info("Step 4: Saving to MongoDB...")
    logger.info("-" * 80)
    success = save_to_mongodb(database, "wizzair", settings.mongo_uri)

    if success:
        logger.info("=" * 80)
        logger.success("WIZZ AIR DATABASE POPULATED SUCCESSFULLY")
        logger.info(f"  Airports: {len(database.airports)}")
        logger.info(f"  Connections: {connections_added}")
        logger.info(f"  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        return True
    else:
        logger.error("WIZZ AIR DATABASE POPULATION FAILED")
        return False


def main():
    """Main entry point for database population."""
    logger.info("=" * 80)
    logger.info("FLIGHT SCANNER DATABASE POPULATION")
    logger.info("=" * 80)
    logger.info(f"MongoDB: {settings.MONGO_HOST}:{settings.MONGO_PORT}/{settings.MONGO_DATABASE}")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    results = {
        "ryanair": False,
        "wizzair": False,
    }

    # Populate Ryanair database
    try:
        results["ryanair"] = populate_ryanair_database()
    except KeyboardInterrupt:
        logger.error("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during Ryanair population: {e}")
        import traceback
        traceback.print_exc()

    # Populate Wizz Air database
    try:
        results["wizzair"] = populate_wizzair_database()
    except KeyboardInterrupt:
        logger.error("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during Wizz Air population: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    logger.info("=" * 80)
    logger.info("POPULATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Ryanair: {'✓ SUCCESS' if results['ryanair'] else '✗ FAILED'}")
    logger.info(f"Wizz Air: {'✓ SUCCESS' if results['wizzair'] else '✗ FAILED'}")
    logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    # Exit with appropriate code
    if all(results.values()):
        logger.success("All databases populated successfully!")
        sys.exit(0)
    elif any(results.values()):
        logger.warning("Some databases populated successfully, but some failed.")
        sys.exit(1)
    else:
        logger.error("All database populations failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
