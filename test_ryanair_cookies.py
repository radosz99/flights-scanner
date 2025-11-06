#!/usr/bin/env python3

"""
Ryanair cookie management tool.

This script demonstrates the full cookie workflow:
1. Extract cookies from Ryanair website using Selenium
2. Save cookies to MongoDB with tracking
3. Use cookies to fetch flight data
4. Track cookie validity over time

Usage:
    # Extract and save new cookie
    python3 test_ryanair_cookies.py extract

    # Test existing cookie from MongoDB
    python3 test_ryanair_cookies.py test

    # Extract and immediately test
    python3 test_ryanair_cookies.py full
"""

import sys
from ryanair import (
    extract_cookies_from_ryanair,
    get_latest_valid_cookie,
    get_ryanair_flights,
)


def extract_cookie():
    """Extract cookie from Ryanair and save to MongoDB."""
    print("=" * 80)
    print("EXTRACTING RYANAIR COOKIE")
    print("=" * 80)

    print("\nThis will:")
    print("1. Open Chrome browser")
    print("2. Navigate to Ryanair flight selection page")
    print("3. Monitor for availability API request")
    print("4. Extract cookies from that request")
    print("5. Save to MongoDB")

    input("\nPress Enter to continue or Ctrl+C to cancel...")

    cookie = extract_cookies_from_ryanair(wait_time=30, save_to_db=True)

    if cookie:
        print("\n" + "=" * 80)
        print("✓ COOKIE EXTRACTED AND SAVED SUCCESSFULLY")
        print("=" * 80)
        print(f"\nCookie preview: {cookie[:100]}...")
        print(f"Cookie length: {len(cookie)} characters")
        return True
    else:
        print("\n" + "=" * 80)
        print("✗ COOKIE EXTRACTION FAILED")
        print("=" * 80)
        return False


def test_cookie():
    """Test the latest cookie from MongoDB."""
    print("=" * 80)
    print("TESTING LATEST COOKIE FROM MONGODB")
    print("=" * 80)

    print("\nFetching latest active cookie from MongoDB...")
    cookie = get_latest_valid_cookie()

    if not cookie:
        print("\n✗ No active cookie found in MongoDB")
        print("   Run: python3 test_ryanair_cookies.py extract")
        return False

    print("\n" + "-" * 80)
    print("Testing cookie with a real flight search...")
    print("-" * 80)

    try:
        flights = get_ryanair_flights(
            origin="WRO",
            destination="ALC",
            date_out="2026-03-06",
            date_in="2026-03-08",
            adt=1,
            cookies=cookie
        )

        print("\n" + "=" * 80)
        print("✓ COOKIE IS VALID!")
        print("=" * 80)
        print(f"\nCurrency: {flights.currency}")
        print(f"Trips found: {len(flights.trips)}")

        if flights.trips:
            trip = flights.trips[0]
            print(f"\nSample trip: {trip.origin} → {trip.destination}")
            print(f"Dates available: {len(trip.dates)}")

            if trip.dates and trip.dates[0].flights:
                flight = trip.dates[0].flights[0]
                print(f"\nSample flight:")
                print(f"  Flight number: {flight.flightNumber}")
                print(f"  Time: {flight.time}")
                if flight.regularFare and flight.regularFare.fares:
                    price = flight.regularFare.fares[0].amount
                    print(f"  Price: {price} {flights.currency}")

        print("\n✓ Cookie has been marked as valid in MongoDB")
        return True

    except Exception as e:
        print("\n" + "=" * 80)
        print("✗ COOKIE IS INVALID")
        print("=" * 80)
        print(f"Error: {e}")
        print("\n✗ Cookie has been marked as invalid in MongoDB")
        print("   You may need to extract a new cookie.")
        return False


def full_workflow():
    """Extract cookie and immediately test it."""
    print("=" * 80)
    print("FULL COOKIE WORKFLOW")
    print("=" * 80)

    # Step 1: Extract
    if not extract_cookie():
        return False

    print("\n" + "=" * 80)
    print("Waiting 2 seconds before testing...")
    print("=" * 80)
    import time
    time.sleep(2)

    # Step 2: Test
    return test_cookie()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 test_ryanair_cookies.py extract  - Extract and save new cookie")
        print("  python3 test_ryanair_cookies.py test     - Test existing cookie from MongoDB")
        print("  python3 test_ryanair_cookies.py full     - Extract and immediately test")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "extract":
        success = extract_cookie()
    elif command == "test":
        success = test_cookie()
    elif command == "full":
        success = full_workflow()
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: extract, test, full")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
