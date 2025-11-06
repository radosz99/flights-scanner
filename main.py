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


def main():
    """Main entry point with robust cookie management."""
    print("=" * 80)
    print("RYANAIR FLIGHT SCANNER")
    print("=" * 80)

    # Step 1: Get valid cookie (automatically handles everything)
    print("\n🔑 Getting valid cookie...")
    cookie = get_valid_cookie(auto_refresh=True)

    if not cookie:
        print("\n❌ Failed to get valid cookie")
        print("Please ensure:")
        print("  - MongoDB is running")
        print("  - Chrome/ChromeDriver is installed")
        print("  - Internet connection is available")
        return False

    # Step 2: Use the cookie to fetch flights
    print("\n" + "=" * 80)
    print("FETCHING FLIGHT DATA")
    print("=" * 80)

    try:
        flights = get_ryanair_flights(
            origin="WRO",
            destination="ALC",
            date_out="2026-03-06",
            date_in="2026-03-08",
            adt=1,
            cookies=cookie
        )

        print(f"\n✅ Successfully fetched flight data!")
        print(f"\nCurrency: {flights.currency}")
        print(f"Trips found: {len(flights.trips)}")

        # Display flight details
        for trip in flights.trips:
            print(f"\n{'='*80}")
            print(f"Route: {trip.origin} ({trip.originName}) → {trip.destination} ({trip.destinationName})")
            print(f"{'='*80}")

            for date_info in trip.dates[:3]:  # Show first 3 dates
                if date_info.flights:
                    print(f"\n  📅 Date: {date_info.dateOut}")

                    for flight in date_info.flights[:2]:  # Show first 2 flights per date
                        print(f"\n    ✈️  Flight {flight.flightNumber}")
                        print(f"       Time: {flight.time[0]} → {flight.time[1]}")
                        print(f"       Duration: {flight.duration}")

                        if flight.regularFare and flight.regularFare.fares:
                            price = flight.regularFare.fares[0].amount
                            print(f"       Price: {price} {flights.currency}")

        print("\n" + "=" * 80)
        print("✅ SUCCESS!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Error fetching flights: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
