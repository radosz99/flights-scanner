#!/usr/bin/env python3

"""
Test script for flight_connector with sample data.

Note: The actual FlightConnections CDN blocks automated requests (403 Forbidden).
This test demonstrates the parsing logic works correctly with sample data.
"""

from flight_connector import (
    AirportGeometry,
    TileData,
    Airport,
    FlightConnectionsDatabase,
)


def test_with_sample_data():
    """Test the parsing logic with sample data from the user's example."""

    # Sample data from the user's example
    sample_geom_data = [
        {"s": 4, "p": [228, 158], "a": "Abilene (ABI)", "c": 555},
        {"s": 4, "p": [232, 111], "a": "Aberdeen (ABR)", "c": 564},
        {"s": 4, "p": [235, 161], "a": "Waco (ACT)", "c": 584},
        {"s": 4, "p": [10, 83], "a": "Adak Island (ADK)", "c": 596},
        {"s": 4, "p": [220, 124], "a": "Alliance (AIA)", "c": 669},
        {"s": 4, "p": [16, 81], "a": "Atka (AKB)", "c": 702},
        {"s": 4, "p": [53, 36], "a": "Akiak (AKI)", "c": 708},
        {"s": 4, "p": [73, 58], "a": "Akhiok (AKK)", "c": 710},
        {"s": 4, "p": [249, 122], "a": "Waterloo (ALO)", "c": 734},
        {"s": 4, "p": [211, 141], "a": "Alamosa (ALS)", "c": 738},
        {"s": 4, "p": [176, 108], "a": "Walla Walla (ALW)", "c": 742},
        {"s": 4, "p": [56, 26], "a": "Anvik (ANV)", "c": 787},
    ]

    print("Testing FlightConnections Parser")
    print("=" * 60)

    # Parse the data
    tile_data = TileData(geom=[AirportGeometry(**geom) for geom in sample_geom_data])

    print(f"\nParsed {len(tile_data.geom)} airports from sample data\n")

    # Build database
    database = FlightConnectionsDatabase()

    for airport_geom in tile_data.geom:
        airport_code = airport_geom.airport_code
        if not airport_code:
            continue

        airport = Airport(
            code=airport_code,
            name=airport_geom.airport_name,
            airport_id=airport_geom.c,
            size=airport_geom.s,
            coordinates=airport_geom.p,
            tile="sample",
        )

        database.add_airport(airport)

    # Display results
    print("Parsed Airports:")
    print("-" * 60)
    for airport in database.get_all_airports():
        print(f"  {airport.code:4s} | {airport.name:20s} | ID: {airport.airport_id:4d} | Coords: {airport.coordinates}")

    print("\n" + "=" * 60)
    print(f"Total airports in database: {len(database.airports)}")
    print("=" * 60)

    # Test lookup functions
    print("\nTesting lookup functions:")
    test_code = "ABI"
    airport = database.get_airport_by_code(test_code)
    if airport:
        print(f"  Lookup by code '{test_code}': {airport.name}")

    test_id = 564
    airport = database.get_airport_by_id(test_id)
    if airport:
        print(f"  Lookup by ID {test_id}: {airport.code} - {airport.name}")

    return database


if __name__ == "__main__":
    test_with_sample_data()
