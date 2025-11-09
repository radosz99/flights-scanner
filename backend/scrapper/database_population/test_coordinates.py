#!/usr/bin/env python3
"""
Quick test script to verify airport coordinate fetching works correctly.

This script tests the airportsdata integration without requiring MongoDB.
"""

import sys

try:
    import airportsdata
except ImportError:
    print("✗ airportsdata package not installed")
    print("Install with: pip install airportsdata")
    sys.exit(1)

from flight_connector import Airport


def test_airportsdata():
    """Test basic airportsdata functionality."""
    print("="*60)
    print("Testing airportsdata Package")
    print("="*60)

    # Load airports by IATA code
    airports_data = airportsdata.load('IATA')
    print(f"✓ Loaded data for {len(airports_data)} airports with IATA codes")

    # Test some common airport codes
    test_codes = [
        'WRO',  # Wrocław, Poland
        'WAW',  # Warsaw, Poland
        'KRK',  # Krakow, Poland
        'GDN',  # Gdansk, Poland
        'DUB',  # Dublin, Ireland (Ryanair hub)
        'STN',  # London Stansted (Ryanair hub)
        'BCN',  # Barcelona, Spain
        'FCO',  # Rome, Italy
        'JFK',  # New York JFK
        'LAX',  # Los Angeles
    ]

    print("\n" + "="*60)
    print("Testing Common Airport Codes")
    print("="*60)

    found = 0
    not_found = 0

    for code in test_codes:
        airport_data = airports_data.get(code)

        if airport_data:
            print(f"\n✓ {code}:")
            print(f"  Name: {airport_data['name']}")
            print(f"  City: {airport_data['city']}")
            print(f"  Country: {airport_data['country']}")
            print(f"  Latitude: {airport_data['lat']:.4f}")
            print(f"  Longitude: {airport_data['lon']:.4f}")
            print(f"  Timezone: {airport_data['tz']}")
            found += 1
        else:
            print(f"\n✗ {code}: Not found")
            not_found += 1

    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"Found: {found}/{len(test_codes)}")
    print(f"Not found: {not_found}/{len(test_codes)}")


def test_airport_model():
    """Test Airport model with coordinates."""
    print("\n" + "="*60)
    print("Testing Airport Model with Coordinates")
    print("="*60)

    # Load airportsdata
    airports_data = airportsdata.load('IATA')

    # Create test airport
    wro_data = airports_data.get('WRO')

    if wro_data:
        airport = Airport(
            code='WRO',
            name='Wrocław',
            airport_id=12345,
            size=5,
            coordinates=[228, 158],
            tile='1-2',
            latitude=wro_data['lat'],
            longitude=wro_data['lon'],
        )

        print(f"✓ Created Airport object:")
        print(f"  Code: {airport.code}")
        print(f"  Name: {airport.name}")
        print(f"  Pixel coords: {airport.coordinates}")
        print(f"  Latitude: {airport.latitude}")
        print(f"  Longitude: {airport.longitude}")
        print(f"\n✓ Airport model works correctly with lat/lon fields!")
    else:
        print("✗ Could not find WRO airport in data")


def test_polish_airports():
    """Test all Polish airports that Ryanair typically uses."""
    print("\n" + "="*60)
    print("Testing Polish Airports (Ryanair Scanner)")
    print("="*60)

    polish_airports = [
        'WRO',  # Wrocław
        'WAW',  # Warsaw Chopin
        'WMI',  # Warsaw Modlin
        'KRK',  # Krakow
        'GDN',  # Gdansk
        'KTW',  # Katowice
        'POZ',  # Poznan
        'RZE',  # Rzeszow
        'SZZ',  # Szczecin
        'BZG',  # Bydgoszcz
        'LCJ',  # Lodz
        'LUZ',  # Lublin
        'IEG',  # Zielona Gora
    ]

    airports_data = airportsdata.load('IATA')
    found_count = 0

    for code in polish_airports:
        airport_data = airports_data.get(code)

        if airport_data:
            print(f"  ✓ {code}: {airport_data['name']:30s} → ({airport_data['lat']:8.4f}, {airport_data['lon']:8.4f})")
            found_count += 1
        else:
            print(f"  ✗ {code}: Not found in database")

    print(f"\nFound coordinates for {found_count}/{len(polish_airports)} Polish airports")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Airport Coordinates Test Suite")
    print("="*60)
    print()

    try:
        test_airportsdata()
        test_airport_model()
        test_polish_airports()

        print("\n" + "="*60)
        print("✓ All tests completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Make sure MongoDB is running (docker-compose up -d)")
        print("2. Populate the database: python backend/scrapper/database_population/populate_databases.py")
        print("3. Update coordinates: python backend/scrapper/database_population/update_airport_coordinates.py")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
