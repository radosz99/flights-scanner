#!/usr/bin/env python3

"""
Query flight route databases from MongoDB.

This script demonstrates how to query the populated MongoDB databases
for Ryanair and Wizz Air flight routes.

Usage:
    python3 query_databases.py
"""

from config import settings
from flight_connector import load_from_mongodb
from loguru import logger


def query_airline_routes(airline_name: str, sample_airports: list[str]):
    """
    Query and display routes for an airline.

    Args:
        airline_name: Name of airline ("ryanair" or "wizzair")
        sample_airports: List of airport codes to show connections for
    """
    logger.info("=" * 80)
    logger.info(f"QUERYING {airline_name.upper()} ROUTES")
    logger.info("=" * 80)

    # Load database from MongoDB
    database = load_from_mongodb(airline_name, settings.mongo_uri)

    if not database:
        logger.error(f"Failed to load {airline_name} database from MongoDB")
        logger.warning("Make sure MongoDB is running and the database has been populated.")
        logger.warning(f"Run: python3 populate_databases.py")
        return

    # Show database statistics
    logger.info(f"Database Statistics:")
    logger.info(f"  Total airports: {len(database.airports)}")

    airports_with_connections = sum(1 for conns in database.connections.values() if conns)
    total_connections = sum(len(conns) for conns in database.connections.values())

    logger.info(f"  Airports with routes: {airports_with_connections}")
    logger.info(f"  Total route connections: {total_connections}")

    # Show sample airport connections
    logger.info(f"{'-' * 80}")
    logger.info("Sample Airport Connections:")
    logger.info("-" * 80)

    for code in sample_airports:
        airport = database.get_airport_by_code(code)
        if not airport:
            logger.warning(f"{code}: Airport not found in database")
            continue

        connections = database.get_connections_from(code)
        logger.info(f"{code} - {airport.name}:")
        logger.info(f"  Number of destinations: {len(connections)}")

        if connections:
            # Show first 20 destinations
            sample_dests = connections[:20]
            dest_names = []
            for dest_code in sample_dests:
                dest_airport = database.get_airport_by_code(dest_code)
                if dest_airport:
                    dest_names.append(f"{dest_code} ({dest_airport.name})")
                else:
                    dest_names.append(dest_code)

            logger.info(f"  Destinations:")
            for dest in dest_names:
                logger.info(f"    → {dest}")

            if len(connections) > 20:
                logger.info(f"    ... and {len(connections) - 20} more")

    # Show top hub airports
    logger.info(f"{'-' * 80}")
    logger.info(f"Top 15 {airline_name.upper()} Hub Airports:")
    logger.info("-" * 80)

    top_hubs = database.get_airports_by_connection_count(limit=15)
    for i, hub in enumerate(top_hubs, 1):
        if hub['connections'] > 0:
            logger.info(f"{i:2d}. {hub['code']:4s} - {hub['name']:35s}: {hub['connections']:3d} destinations")


def main():
    """Main query demonstration."""
    logger.info("=" * 80)
    logger.info("FLIGHT ROUTE DATABASE QUERY TOOL")
    logger.info("=" * 80)
    logger.info(f"MongoDB: {settings.MONGO_HOST}:{settings.MONGO_PORT}/{settings.MONGO_DATABASE}")
    logger.info("=" * 80)

    # Sample airports to query
    ryanair_samples = ['DUB', 'STN', 'BCN', 'MAD', 'WRO', 'KRK', 'WAW']
    wizzair_samples = ['BUD', 'WAW', 'KTW', 'WRO', 'VIE', 'SOF', 'OTP']

    # Query Ryanair routes
    try:
        query_airline_routes("ryanair", ryanair_samples)
    except Exception as e:
        logger.error(f"Error querying Ryanair: {e}")
        import traceback
        traceback.print_exc()

    # Query Wizz Air routes
    try:
        query_airline_routes("wizzair", wizzair_samples)
    except Exception as e:
        logger.error(f"Error querying Wizz Air: {e}")
        import traceback
        traceback.print_exc()

    logger.info("=" * 80)
    logger.success("QUERY COMPLETED")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
