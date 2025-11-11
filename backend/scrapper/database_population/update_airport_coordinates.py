#!/usr/bin/env python3
"""
Script to fetch and update geographic coordinates (latitude/longitude) for all airports.

This script:
1. Loads airport data from MongoDB
2. Uses the airportsdata package to fetch real coordinates
3. Updates airports with latitude/longitude
4. Saves the updated data back to MongoDB
"""

import sys
from typing import Optional

try:
    import airportsdata
except ImportError:
    print("✗ airportsdata package not installed")
    print("Install with: pip install airportsdata")
    sys.exit(1)

try:
    import pycountry
except ImportError:
    print("✗ pycountry package not installed")
    print("Install with: pip install pycountry")
    sys.exit(1)

from .flight_connector import (
    load_from_mongodb,
    save_to_mongodb,
    FlightConnectionsDatabase,
)


def update_airport_coordinates(
    database: FlightConnectionsDatabase,
    verbose: bool = True
) -> tuple[int, int, int]:
    """
    Update all airports in the database with geographic coordinates and country information.

    Args:
        database: FlightConnectionsDatabase to update
        verbose: Print detailed progress information

    Returns:
        Tuple of (updated_count, not_found_count, already_had_coords)
    """
    # Load airports data by IATA code
    if verbose:
        print("\n" + "="*60)
        print("Loading airportsdata database...")
        print("="*60)

    airports_data = airportsdata.load('IATA')

    if verbose:
        print(f"✓ Loaded data for {len(airports_data)} airports with IATA codes")
        print(f"\nUpdating coordinates and country for {len(database.airports)} airports...")
        print("="*60)

    updated_count = 0
    not_found_count = 0
    already_had_coords = 0

    for code, airport in database.airports.items():
        # Check if airport already has coordinates
        if airport.latitude is not None and airport.longitude is not None and airport.country is not None:
            already_had_coords += 1
            if verbose:
                print(f"  ⊙ {code}: Already has coordinates and country ({airport.latitude:.4f}, {airport.longitude:.4f}, {airport.country})")
            continue

        # Look up airport in airportsdata
        airport_data = airports_data.get(code)

        if airport_data:
            # Update coordinates and country
            airport.latitude = airport_data['lat']
            airport.longitude = airport_data['lon']

            # Convert full country name to ISO2 code using pycountry
            country_name = airport_data.get('country', 'Unknown')
            try:
                if country_name and country_name != 'Unknown':
                    # Try to find country by name
                    country = pycountry.countries.search_fuzzy(country_name)
                    if country:
                        airport.country = country[0].alpha_2
                    else:
                        airport.country = 'XX'  # Unknown country code
                else:
                    airport.country = 'XX'
            except (LookupError, AttributeError):
                airport.country = 'XX'  # Fallback for lookup errors

            updated_count += 1

            if verbose:
                print(f"  ✓ {code}: {airport.name} → ({airport.latitude:.4f}, {airport.longitude:.4f}, {airport.country})")
        else:
            not_found_count += 1
            if verbose:
                print(f"  ✗ {code}: {airport.name} - not found in airportsdata")

    if verbose:
        print("\n" + "="*60)
        print("Summary:")
        print(f"  Updated: {updated_count}")
        print(f"  Already had coordinates and country: {already_had_coords}")
        print(f"  Not found: {not_found_count}")
        print(f"  Total: {len(database.airports)}")
        print("="*60)

    return updated_count, not_found_count, already_had_coords


def main(
    airline_name: str = "ryanair",
    mongo_uri: str = "mongodb://localhost:27017/flights_scanner",
    verbose: bool = True
):
    """
    Main function to update coordinates for all airports.

    Args:
        airline_name: Name of airline (e.g., "ryanair", "wizzair")
        mongo_uri: MongoDB connection URI
        verbose: Print detailed progress information
    """
    print(f"\n{'='*60}")
    print(f"Airport Coordinates Updater - {airline_name.upper()}")
    print(f"{'='*60}")

    # Load database from MongoDB
    database = load_from_mongodb(airline_name, mongo_uri)

    if not database:
        print("✗ Failed to load database from MongoDB")
        return False

    # Update coordinates
    updated, not_found, already_had = update_airport_coordinates(database, verbose)

    if updated > 0 or already_had > 0:
        # Save back to MongoDB
        print(f"\n{'='*60}")
        print(f"Saving updated data to MongoDB...")
        print(f"{'='*60}")

        success = save_to_mongodb(database, airline_name, mongo_uri)

        if success:
            print("\n" + "="*60)
            print("✓ Successfully updated airport coordinates!")
            print("="*60)
            return True
        else:
            print("\n✗ Failed to save to MongoDB")
            return False
    else:
        print("\n⚠ No airports were updated (all not found or already had coordinates)")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Update geographic coordinates for airports in the database"
    )
    parser.add_argument(
        "--airline",
        default="ryanair",
        help="Airline name (default: ryanair)"
    )
    parser.add_argument(
        "--mongo-uri",
        default="mongodb://localhost:27017/flights_scanner",
        help="MongoDB connection URI"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output"
    )

    args = parser.parse_args()

    success = main(
        airline_name=args.airline,
        mongo_uri=args.mongo_uri,
        verbose=not args.quiet
    )

    sys.exit(0 if success else 1)
