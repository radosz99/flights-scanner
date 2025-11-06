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
from datetime import datetime
from config import settings
from flight_connector import (
    build_airport_database,
    fetch_ryanair_routes,
    fetch_wizzair_routes,
    save_to_mongodb,
    load_from_mongodb,
)


def populate_ryanair_database():
    """Populate Ryanair route database."""
    print("\n" + "=" * 80)
    print("POPULATING RYANAIR DATABASE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Build airport database
    print("\n" + "-" * 80)
    print("Step 1: Building airport database...")
    print("-" * 80)
    database = build_airport_database()

    if not database.airports:
        print("\n✗ ERROR: Failed to build airport database")
        print("  The FlightConnections API may be blocking requests.")
        print("  Please try again later or check your network connection.")
        return False

    # Step 2: Fetch Ryanair routes
    print("\n" + "-" * 80)
    print("Step 2: Fetching Ryanair routes...")
    print("-" * 80)
    routes = fetch_ryanair_routes()

    if not routes:
        print("\n✗ ERROR: Failed to fetch Ryanair routes")
        print("  The FlightConnections API may be blocking requests.")
        print("  Airport database was built successfully, but no routes were fetched.")
        return False

    # Step 3: Populate connections
    print("\n" + "-" * 80)
    print("Step 3: Populating Ryanair connections...")
    print("-" * 80)
    connections_added = database.populate_connections_from_routes(routes)
    print(f"✓ Added {connections_added} Ryanair connections")

    # Step 4: Save to MongoDB
    print("\n" + "-" * 80)
    print("Step 4: Saving to MongoDB...")
    print("-" * 80)
    success = save_to_mongodb(database, "ryanair", settings.mongo_uri)

    if success:
        print("\n" + "=" * 80)
        print("✓ RYANAIR DATABASE POPULATED SUCCESSFULLY")
        print(f"  Airports: {len(database.airports)}")
        print(f"  Connections: {connections_added}")
        print(f"  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        return True
    else:
        print("\n✗ RYANAIR DATABASE POPULATION FAILED")
        return False


def populate_wizzair_database():
    """Populate Wizz Air route database."""
    print("\n" + "=" * 80)
    print("POPULATING WIZZ AIR DATABASE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Build airport database
    print("\n" + "-" * 80)
    print("Step 1: Building airport database...")
    print("-" * 80)
    database = build_airport_database()

    if not database.airports:
        print("\n✗ ERROR: Failed to build airport database")
        print("  The FlightConnections API may be blocking requests.")
        print("  Please try again later or check your network connection.")
        return False

    # Step 2: Fetch Wizz Air routes
    print("\n" + "-" * 80)
    print("Step 2: Fetching Wizz Air routes...")
    print("-" * 80)
    routes = fetch_wizzair_routes()

    if not routes:
        print("\n✗ ERROR: Failed to fetch Wizz Air routes")
        print("  The FlightConnections API may be blocking requests.")
        print("  Airport database was built successfully, but no routes were fetched.")
        return False

    # Step 3: Populate connections
    print("\n" + "-" * 80)
    print("Step 3: Populating Wizz Air connections...")
    print("-" * 80)
    connections_added = database.populate_connections_from_routes(routes)
    print(f"✓ Added {connections_added} Wizz Air connections")

    # Step 4: Save to MongoDB
    print("\n" + "-" * 80)
    print("Step 4: Saving to MongoDB...")
    print("-" * 80)
    success = save_to_mongodb(database, "wizzair", settings.mongo_uri)

    if success:
        print("\n" + "=" * 80)
        print("✓ WIZZ AIR DATABASE POPULATED SUCCESSFULLY")
        print(f"  Airports: {len(database.airports)}")
        print(f"  Connections: {connections_added}")
        print(f"  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        return True
    else:
        print("\n✗ WIZZ AIR DATABASE POPULATION FAILED")
        return False


def main():
    """Main entry point for database population."""
    print("\n" + "=" * 80)
    print("FLIGHT SCANNER DATABASE POPULATION")
    print("=" * 80)
    print(f"MongoDB: {settings.MONGO_HOST}:{settings.MONGO_PORT}/{settings.MONGO_DATABASE}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = {
        "ryanair": False,
        "wizzair": False,
    }

    # Populate Ryanair database
    try:
        results["ryanair"] = populate_ryanair_database()
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error during Ryanair population: {e}")
        import traceback
        traceback.print_exc()

    # Populate Wizz Air database
    try:
        results["wizzair"] = populate_wizzair_database()
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error during Wizz Air population: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print("\n" + "=" * 80)
    print("POPULATION SUMMARY")
    print("=" * 80)
    print(f"Ryanair: {'✓ SUCCESS' if results['ryanair'] else '✗ FAILED'}")
    print(f"Wizz Air: {'✓ SUCCESS' if results['wizzair'] else '✗ FAILED'}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Exit with appropriate code
    if all(results.values()):
        print("\n✓ All databases populated successfully!")
        sys.exit(0)
    elif any(results.values()):
        print("\n⚠ Some databases populated successfully, but some failed.")
        sys.exit(1)
    else:
        print("\n✗ All database populations failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
