#!/usr/bin/env python3

"""
Script to iterate through all cookies in MongoDB and find a valid one.

This will try each cookie (starting from most recent) until finding one that works.
"""

from pymongo import MongoClient, DESCENDING
from ryanair import get_ryanair_flights, mark_cookie_valid, mark_cookie_invalid
from config import settings


def find_valid_cookie_from_db():
    """
    Iterate through all cookies in MongoDB and test each one until finding a valid one.

    Returns:
        str: Valid cookie string if found, None otherwise
    """
    print("=" * 80)
    print("SEARCHING FOR VALID COOKIE IN MONGODB")
    print("=" * 80)

    # Connect to MongoDB
    print(f"\nConnecting to MongoDB: {settings.mongo_uri}")
    client = MongoClient(settings.mongo_uri)
    db = client.get_default_database()
    cookies_col = db["ryanair_cookies"]

    # Get all cookies, sorted by most recent first
    all_cookies = list(cookies_col.find().sort("fetched", DESCENDING))

    print(f"\n✓ Found {len(all_cookies)} cookies in database")

    if not all_cookies:
        print("\n✗ No cookies found in MongoDB")
        print("   Run: python3 test_ryanair_cookies.py extract")
        client.close()
        return None

    # Try each cookie
    for idx, cookie_doc in enumerate(all_cookies, 1):
        cookie_string = cookie_doc["cookie"]
        fetched = cookie_doc.get("fetched", "unknown")
        active = cookie_doc.get("active", "unknown")

        print(f"\n{'='*80}")
        print(f"TESTING COOKIE {idx}/{len(all_cookies)}")
        print(f"{'='*80}")
        print(f"Fetched: {fetched}")
        print(f"Active: {active}")
        print(f"Cookie preview: {cookie_string[:80]}...")
        print(f"Cookie length: {len(cookie_string)} characters")

        # Test the cookie
        print("\n🧪 Testing cookie with real API request...")
        try:
            flights = get_ryanair_flights(
                origin="WRO",
                destination="ALC",
                date_out="2026-03-06",
                date_in="2026-03-08",
                adt=1,
                cookies=cookie_string
            )

            # Success!
            print("\n" + "🎉" * 40)
            print("✓ FOUND VALID COOKIE!")
            print("🎉" * 40)
            print(f"\nCookie #{idx} is VALID!")
            print(f"Currency: {flights.currency}")
            print(f"Trips found: {len(flights.trips)}")
            print(f"\nThis cookie has been marked as valid in MongoDB")

            client.close()
            return cookie_string

        except Exception as e:
            print(f"\n✗ Cookie #{idx} is INVALID")
            print(f"   Error: {str(e)[:100]}")
            print(f"   Marked as invalid in MongoDB")
            print(f"   Continuing to next cookie...")
            continue

    # No valid cookie found
    print("\n" + "=" * 80)
    print("✗ NO VALID COOKIES FOUND")
    print("=" * 80)
    print(f"\nTested all {len(all_cookies)} cookies - none are valid")
    print("You need to extract a new cookie:")
    print("   python3 test_ryanair_cookies.py extract")

    client.close()
    return None


def main():
    """Main entry point."""
    cookie = find_valid_cookie_from_db()

    if cookie:
        print("\n" + "=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print(f"\nValid cookie found and ready to use")
        print(f"Cookie preview: {cookie[:100]}...")
        return True
    else:
        print("\n" + "=" * 80)
        print("FAILED")
        print("=" * 80)
        print("\nNo valid cookies found in database")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
