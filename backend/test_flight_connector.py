#!/usr/bin/env python3

"""
Test script for flight_connector with real API requests.

This script attempts to fetch real data from FlightConnections.
Note: The API may block automated requests (403 Forbidden).
"""

from flight_connector import (
    AirportGeometry,
    TileData,
    Airport,
    FlightConnectionsDatabase,
    AirlineRoutes,
    build_airport_database,
    fetch_airline_routes,
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


def test_airport_connections():
    """Test the connections functionality."""
    print("\n\nTesting Airport Connections")
    print("=" * 60)

    # Create a database with sample airports
    database = FlightConnectionsDatabase()

    # Add sample airports
    airports_data = [
        {"code": "JFK", "name": "New York", "id": 1001, "coords": [100, 200]},
        {"code": "LAX", "name": "Los Angeles", "id": 1002, "coords": [50, 250]},
        {"code": "ORD", "name": "Chicago", "id": 1003, "coords": [120, 180]},
        {"code": "DFW", "name": "Dallas", "id": 1004, "coords": [110, 220]},
        {"code": "ATL", "name": "Atlanta", "id": 1005, "coords": [130, 210]},
    ]

    for apt_data in airports_data:
        airport = Airport(
            code=apt_data["code"],
            name=apt_data["name"],
            airport_id=apt_data["id"],
            size=4,
            coordinates=apt_data["coords"],
            tile="test",
        )
        database.add_airport(airport)

    # Add sample connections
    # JFK connects to: LAX, ORD, ATL
    database.add_connection("JFK", "LAX")
    database.add_connection("JFK", "ORD")
    database.add_connection("JFK", "ATL")

    # LAX connects to: JFK, ORD, DFW
    database.add_connection("LAX", "JFK")
    database.add_connection("LAX", "ORD")
    database.add_connection("LAX", "DFW")

    # ORD connects to: JFK, LAX, ATL
    database.add_connection("ORD", "JFK")
    database.add_connection("ORD", "LAX")
    database.add_connection("ORD", "ATL")

    print("\n1. Get all airports as dictionary:")
    print("-" * 60)
    all_airports = database.get_all_airports_dict()
    for code, name in sorted(all_airports.items()):
        print(f"  {code}: {name}")

    print("\n2. Get connections from JFK:")
    print("-" * 60)
    jfk_connections = database.get_connections_from("JFK")
    print(f"  Airport codes: {jfk_connections}")

    print("\n3. Get connections from JFK with names:")
    print("-" * 60)
    jfk_connections_detailed = database.get_connections_from_with_names("JFK")
    for conn in jfk_connections_detailed:
        print(f"  {conn['code']}: {conn['name']}")

    print("\n4. Get connection counts:")
    print("-" * 60)
    for code in ["JFK", "LAX", "ORD", "DFW", "ATL"]:
        count = database.get_connection_count(code)
        print(f"  {code}: {count} connections")

    print("\n5. Get airports by connection count (top 3):")
    print("-" * 60)
    top_airports = database.get_airports_by_connection_count(limit=3)
    for airport in top_airports:
        print(f"  {airport['code']} ({airport['name']}): {airport['connections']} connections")

    return database


def test_airline_routes():
    """Test populating connections from airline routes data."""
    print("\n\nTesting Airline Routes Population")
    print("=" * 60)

    # Create a database with sample airports
    database = FlightConnectionsDatabase()

    # Add sample airports with their IDs (matching FlightConnections structure)
    airports_data = [
        {"code": "WRO", "name": "Wrocław", "id": 2, "coords": [100, 200]},
        {"code": "LTN", "name": "London Luton", "id": 76, "coords": [120, 150]},
        {"code": "STN", "name": "London Stansted", "id": 107, "coords": [121, 150]},
        {"code": "DUB", "name": "Dublin", "id": 175, "coords": [115, 140]},
        {"code": "BCN", "name": "Barcelona", "id": 188, "coords": [105, 180]},
        {"code": "ALC", "name": "Alicante", "id": 232, "coords": [103, 185]},
        {"code": "MAD", "name": "Madrid", "id": 256, "coords": [100, 180]},
        {"code": "LPA", "name": "Gran Canaria", "id": 333, "coords": [95, 205]},
    ]

    for apt_data in airports_data:
        airport = Airport(
            code=apt_data["code"],
            name=apt_data["name"],
            airport_id=apt_data["id"],
            size=4,
            coordinates=apt_data["coords"],
            tile="test",
        )
        database.add_airport(airport)

    print(f"Created database with {len(database.airports)} airports\n")

    # Sample airline routes data (simulating FlightConnections API response)
    # Format: dep[i] -> des[i] represents a route
    sample_routes_data = {
        "routes": [
            {
                "dep": [2, 2, 2, 76, 76, 107, 175, 175, 188, 188],
                "des": [76, 107, 175, 188, 232, 256, 333, 9, 98, 150]
                # WRO -> LTN, WRO -> STN, WRO -> DUB, LTN -> BCN, LTN -> ALC, STN -> MAD, DUB -> LPA, ...
                # Some destinations (9, 98, 150) don't exist in our database to test skipping
            }
        ]
    }

    # Parse routes data
    airline_routes = AirlineRoutes(**sample_routes_data)

    print("Populating connections from airline routes...")
    connections_added = database.populate_connections_from_routes(airline_routes)
    print(f"✓ Added {connections_added} connections\n")

    # Show connections for each airport
    print("Connections by airport:")
    print("-" * 60)
    for code in sorted(database.airports.keys()):
        connections = database.get_connections_from(code)
        conn_with_names = database.get_connections_from_with_names(code)
        if connections:
            print(f"\n{code} - {database.get_airport_by_code(code).name}:")
            for conn in conn_with_names:
                print(f"  → {conn['code']} ({conn['name']})")
        else:
            print(f"\n{code} - {database.get_airport_by_code(code).name}: No outbound connections")

    # Show statistics
    print("\n" + "=" * 60)
    print("Statistics:")
    print("-" * 60)
    print(f"Total airports: {len(database.airports)}")
    print(f"Total connections: {connections_added}")
    print(f"Airports with connections: {sum(1 for c in database.connections.values() if c)}")

    # Show top hubs
    print("\nTop hub airports:")
    print("-" * 60)
    top_hubs = database.get_airports_by_connection_count(limit=5)
    for i, hub in enumerate(top_hubs, 1):
        if hub['connections'] > 0:
            print(f"{i}. {hub['code']} - {hub['name']}: {hub['connections']} destinations")

    return database


def test_real_api():
    """Test with real API requests."""
    print("=" * 80)
    print("TESTING WITH REAL API REQUESTS")
    print("=" * 80)

    # Step 1: Build airport database from tiles
    print("\n" + "=" * 80)
    print("Step 1: Building airport database from tiles...")
    print("=" * 80)

    database = build_airport_database()

    if not database.airports:
        print("\n⚠ WARNING: No airports fetched (API may be blocking requests)")
        print("Falling back to sample data tests...\n")
        return None

    print(f"\n✓ Database built with {len(database.airports)} airports")

    # Show sample airports
    print("\nSample airports:")
    sample_airports = list(database.airports.values())[:10]
    for airport in sample_airports:
        print(f"  {airport.code}: {airport.name} (ID: {airport.airport_id})")

    # Step 2: Fetch airline routes
    print("\n" + "=" * 80)
    print("Step 2: Fetching airline routes (Ryanair - ID 39)...")
    print("=" * 80)

    routes = fetch_airline_routes(39)

    if not routes:
        print("\n⚠ WARNING: Failed to fetch airline routes (API may be blocking requests)")
        print("Database structure is ready but no connections populated.\n")
        return database

    # Step 3: Populate connections
    print("\n" + "=" * 80)
    print("Step 3: Populating connections from airline routes...")
    print("=" * 80)

    connections_added = database.populate_connections_from_routes(routes)
    print(f"\n✓ Added {connections_added} route connections")

    # Step 4: Show connection statistics
    print("\n" + "=" * 80)
    print("Step 4: Connection Statistics")
    print("=" * 80)

    # Count airports with connections
    airports_with_connections = sum(1 for conns in database.connections.values() if conns)
    print(f"\nTotal airports: {len(database.airports)}")
    print(f"Airports with outbound connections: {airports_with_connections}")
    print(f"Total route connections: {connections_added}")

    # Step 5: Show example connections from major airports
    print("\n" + "=" * 80)
    print("Step 5: Example Connections from Major Airports")
    print("=" * 80)

    major_airports = ['DUB', 'STN', 'BCN', 'MAD', 'FCO', 'WRO', 'AMS', 'CDG']
    for code in major_airports:
        airport = database.get_airport_by_code(code)
        if airport:
            connections = database.get_connections_from(code)
            print(f"\n{code} - {airport.name}:")
            print(f"  Destinations: {len(connections)}")
            if connections:
                # Show first 15 destinations
                sample_dests = connections[:15]
                print(f"  Sample: {', '.join(sample_dests)}")
                if len(connections) > 15:
                    print(f"  ... and {len(connections) - 15} more")

    # Step 6: Show top hub airports
    print("\n" + "=" * 80)
    print("Step 6: Top 20 Hub Airports by Connection Count")
    print("=" * 80)

    top_hubs = database.get_airports_by_connection_count(limit=20)
    for i, hub in enumerate(top_hubs, 1):
        if hub['connections'] > 0:
            print(f"{i:2d}. {hub['code']:4s} - {hub['name']:30s}: {hub['connections']:3d} destinations")

    print("\n" + "=" * 80)
    print("✓ REAL API TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)

    return database


if __name__ == "__main__":
    # Try real API first
    database = test_real_api()

    # If real API failed, run sample data tests
    if database is None or not database.airports:
        print("\n" + "=" * 80)
        print("Running sample data tests (API unavailable)...")
        print("=" * 80)
        test_with_sample_data()
        test_airport_connections()
        test_airline_routes()
