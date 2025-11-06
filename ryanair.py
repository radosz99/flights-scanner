#!/usr/bin/env python3

"""
Ryanair API integration module with Selenium automation support.

Note: Ryanair uses bot protection that blocks automated requests.
You can either:
1. Extract cookies manually from browser (see module docstring)
2. Use Selenium automation to get cookies automatically (recommended)

Required cookies from browser:
- sid: Session ID
- rid: Request ID
- rid.sig: Request signature
- xid: Transaction ID
- PIM-SESSION-ID: PIM session
- RY_COOKIE_CONSENT: Cookie consent
- _cc: Cookie consent confirmation

How to extract cookies manually:
1. Open https://www.ryanair.com in Firefox/Chrome
2. Open Developer Tools (F12) → Network tab
3. Search for a flight
4. Find the GET request to "/api/booking/v4/.../availability"
5. Copy the Cookie header value

Or use Selenium automation (recommended):
- Use extract_cookies_from_ryanair() to get cookies automatically
- Then pass cookies to get_ryanair_flights()
- Requires selenium and chromedriver
"""

import requests
import time
import json
from typing import Optional
from datetime import datetime
from ryanair_models import RyanairResponse

# Selenium imports (optional - only needed for automation)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# MongoDB imports (optional - only needed for cookie storage)
try:
    from pymongo import MongoClient, DESCENDING
    from pymongo.errors import PyMongoError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# Config import
try:
    from config import settings
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    class MockSettings:
        RYANAIR_COOKIE_URL = "https://www.ryanair.com/hr/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-03-06&dateIn=2026-03-08&isConnectedFlight=false&discount=0&promoCode=&isReturn=true&originIata=WRO&destinationIata=ALC&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-03-06&tpEndDate=2026-03-08&tpDiscount=0&tpPromoCode=&tpOriginIata=WRO&tpDestinationIata=ALC"
        MONGO_HOST = "localhost"
        MONGO_PORT = 27017
        MONGO_DATABASE = "flights_scanner"
        @property
        def mongo_uri(self):
            return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DATABASE}"
    settings = MockSettings()


def save_cookie_to_mongodb(
    cookie_string: str,
    mongo_uri: Optional[str] = None
) -> bool:
    """
    Save Ryanair cookie to MongoDB with tracking information.

    Args:
        cookie_string: Cookie string to save
        mongo_uri: MongoDB connection URI (uses settings if not provided)

    Returns:
        True if successful, False otherwise
    """
    if not MONGODB_AVAILABLE:
        print("⚠ MongoDB not available. Cookie not saved.")
        return False

    try:
        uri = mongo_uri or settings.mongo_uri
        client = MongoClient(uri)
        db = client.get_default_database()
        cookies_col = db["ryanair_cookies"]

        # Create index
        cookies_col.create_index([("fetched", DESCENDING)])
        cookies_col.create_index([("active", DESCENDING)])

        cookie_doc = {
            "cookie": cookie_string,
            "active": True,
            "fetched": datetime.utcnow(),
            "last_valid_use": None,
            "last_invalid_use": None,
        }

        result = cookies_col.insert_one(cookie_doc)
        client.close()

        print(f"✓ Cookie saved to MongoDB (ID: {result.inserted_id})")
        return True

    except PyMongoError as e:
        print(f"✗ MongoDB error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def get_latest_valid_cookie(mongo_uri: Optional[str] = None) -> Optional[str]:
    """
    Get the most recently fetched active cookie from MongoDB.

    Args:
        mongo_uri: MongoDB connection URI (uses settings if not provided)

    Returns:
        Cookie string or None if not found
    """
    if not MONGODB_AVAILABLE:
        print("⚠ MongoDB not available.")
        return None

    try:
        uri = mongo_uri or settings.mongo_uri
        client = MongoClient(uri)
        db = client.get_default_database()
        cookies_col = db["ryanair_cookies"]

        # Find most recent active cookie
        cookie_doc = cookies_col.find_one(
            {"active": True},
            sort=[("fetched", DESCENDING)]
        )

        client.close()

        if cookie_doc:
            print(f"✓ Found active cookie (fetched: {cookie_doc['fetched']})")
            return cookie_doc["cookie"]
        else:
            print("⚠ No active cookies found in MongoDB")
            return None

    except PyMongoError as e:
        print(f"✗ MongoDB error: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


def mark_cookie_valid(
    cookie_string: str,
    mongo_uri: Optional[str] = None
) -> bool:
    """
    Mark a cookie as having been successfully used.

    Args:
        cookie_string: Cookie string to mark as valid
        mongo_uri: MongoDB connection URI (uses settings if not provided)

    Returns:
        True if successful, False otherwise
    """
    if not MONGODB_AVAILABLE:
        return False

    try:
        uri = mongo_uri or settings.mongo_uri
        client = MongoClient(uri)
        db = client.get_default_database()
        cookies_col = db["ryanair_cookies"]

        result = cookies_col.update_one(
            {"cookie": cookie_string},
            {"$set": {"last_valid_use": datetime.utcnow()}}
        )

        client.close()
        return result.modified_count > 0

    except Exception:
        return False


def mark_cookie_invalid(
    cookie_string: str,
    mongo_uri: Optional[str] = None
) -> bool:
    """
    Mark a cookie as invalid and deactivate it.

    Args:
        cookie_string: Cookie string to mark as invalid
        mongo_uri: MongoDB connection URI (uses settings if not provided)

    Returns:
        True if successful, False otherwise
    """
    if not MONGODB_AVAILABLE:
        return False

    try:
        uri = mongo_uri or settings.mongo_uri
        client = MongoClient(uri)
        db = client.get_default_database()
        cookies_col = db["ryanair_cookies"]

        result = cookies_col.update_one(
            {"cookie": cookie_string},
            {
                "$set": {
                    "last_invalid_use": datetime.utcnow(),
                    "active": False
                }
            }
        )

        client.close()
        return result.modified_count > 0

    except Exception:
        return False


def setup_driver(enable_network_capture: bool = False):
    """
    Setup Chrome WebDriver for Selenium automation.

    Args:
        enable_network_capture: Enable network logging to capture requests

    Returns:
        webdriver.Chrome: Configured Chrome driver

    Raises:
        ImportError: If selenium is not installed
        Exception: If chromedriver is not found or other setup issues
    """
    if not SELENIUM_AVAILABLE:
        raise ImportError(
            "Selenium is not installed. Install with: pip install selenium"
        )

    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Enable performance logging to capture network requests
    if enable_network_capture:
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def extract_cookies_from_ryanair(wait_time: int = 30, save_to_db: bool = True) -> Optional[str]:
    """
    Use Selenium to navigate to Ryanair flight selection page and extract cookies
    from the availability API request.

    This function:
    1. Opens Chrome browser with network logging enabled
    2. Navigates to Ryanair flight selection page
    3. Monitors network requests for availability API call
    4. Extracts cookies from the availability request header
    5. Optionally saves to MongoDB for tracking

    Args:
        wait_time: Seconds to wait for availability request (default: 30)
        save_to_db: Save cookies to MongoDB for tracking (default: True)

    Returns:
        Cookie string from availability request or None if not found

    Raises:
        ImportError: If selenium is not installed
        Exception: If browser fails to start or navigate

    Example:
        cookies = extract_cookies_from_ryanair(wait_time=30, save_to_db=True)
        if cookies:
            flights = get_ryanair_flights("WRO", "ALC", "2025-12-11", "2025-12-15", cookies=cookies)
    """
    print("🌐 Starting Chrome browser with network logging...")
    driver = setup_driver(enable_network_capture=True)

    try:
        url = settings.RYANAIR_COOKIE_URL
        print(f"🔍 Navigating to Ryanair flight selection page...")
        print(f"   URL: {url[:80]}...")
        driver.get(url)

        print(f"⏳ Waiting up to {wait_time} seconds for availability request...")
        print("   Monitoring network traffic for 'availability' API call...")

        cookie_string = None
        start_time = time.time()

        while time.time() - start_time < wait_time:
            # Get performance logs
            logs = driver.get_log('performance')

            for log in logs:
                try:
                    log_entry = json.loads(log['message'])
                    message = log_entry.get('message', {})

                    # Look for Network.requestWillBeSent events
                    if message.get('method') == 'Network.requestWillBeSent':
                        params = message.get('params', {})
                        request = params.get('request', {})
                        request_url = request.get('url', '')

                        # Check if this is the availability request
                        if 'availability' in request_url.lower():
                            headers = request.get('headers', {})
                            cookie_header = headers.get('Cookie') or headers.get('cookie')

                            if cookie_header:
                                cookie_string = cookie_header
                                print(f"\n✓ Found availability request!")
                                print(f"   URL: {request_url[:100]}...")
                                print(f"   Extracted {len(cookie_header)} characters of cookies")
                                break

                except Exception as e:
                    # Skip malformed log entries
                    continue

            if cookie_string:
                break

            # Small delay to avoid busy waiting
            time.sleep(0.5)

        if not cookie_string:
            print(f"\n✗ No availability request found after {wait_time} seconds")
            print("   The page may not have loaded the flight data.")
            print("   Try increasing wait_time or check if the URL is correct.")
            return None

        # Save to MongoDB if requested
        if save_to_db and MONGODB_AVAILABLE:
            print("\n💾 Saving cookie to MongoDB...")
            save_cookie_to_mongodb(cookie_string)

        print("\n✓ Cookie extraction completed successfully")
        return cookie_string

    finally:
        print("\n🔒 Closing browser...")
        driver.quit()


def get_ryanair_flights(
    origin: str,
    destination: str,
    date_out: str,
    date_in: str,
    adt: int = 1,
    teen: int = 0,
    chd: int = 0,
    inf: int = 0,
    flex_days_before_out: int = 2,
    flex_days_out: int = 2,
    flex_days_before_in: int = 2,
    flex_days_in: int = 2,
    cookies: Optional[str] = None,
) -> RyanairResponse:
    """
    Fetch flight availability from Ryanair API.

    Args:
        origin: Origin airport code (e.g., 'WRO')
        destination: Destination airport code (e.g., 'ALC')
        date_out: Outbound date (YYYY-MM-DD format)
        date_in: Return date (YYYY-MM-DD format)
        adt: Number of adults
        teen: Number of teens
        chd: Number of children
        inf: Number of infants
        flex_days_before_out: Flex days before outbound
        flex_days_out: Flex days after outbound
        flex_days_before_in: Flex days before return
        flex_days_in: Flex days after return
        cookies: Cookie header string from browser (required for bot protection bypass)
                 Example: "sid=xxx; rid=yyy; xid=zzz; ..."

    Returns:
        RyanairResponse: Parsed Pydantic model with flight data

    Raises:
        requests.exceptions.HTTPError: If request fails (403 if cookies missing/expired)

    Example:
        # Extract cookies from browser DevTools
        cookies = "sid=8b4d93ba-...; rid=614a7f95-...; xid=7e28c79b-..."

        flights = get_ryanair_flights(
            origin="WRO",
            destination="ALC",
            date_out="2025-12-11",
            date_in="2025-12-15",
            cookies=cookies
        )
    """
    url = "https://www.ryanair.com/api/booking/v4/pl-pl/availability"

    params = {
        "ADT": adt,
        "TEEN": teen,
        "CHD": chd,
        "INF": inf,
        "Origin": origin,
        "Destination": destination,
        "promoCode": "",
        "IncludeConnectingFlights": "false",
        "DateOut": date_out,
        "DateIn": date_in,
        "FlexDaysBeforeOut": flex_days_before_out,
        "FlexDaysOut": flex_days_out,
        "FlexDaysBeforeIn": flex_days_before_in,
        "FlexDaysIn": flex_days_in,
        "RoundTrip": "true",
        "IncludePrimeFares": "false",
        "ToUs": "AGREED",
    }

    # Browser-like headers matching actual browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:144.0) Gecko/20100101 Firefox/144.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Connection': 'keep-alive',
        'TE': 'trailers',
    }

    # Add cookies if provided
    if cookies:
        headers['Cookie'] = cookies

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        # Parse response into Pydantic model
        data = response.json()
        ryanair_data = RyanairResponse(**data)

        # Mark cookie as valid if request succeeded
        if cookies:
            mark_cookie_valid(cookies)

    except requests.exceptions.HTTPError as e:
        # If 403, mark cookie as invalid
        if e.response.status_code == 403 and cookies:
            print(f"⚠ Cookie returned 403 Forbidden - marking as invalid")
            mark_cookie_invalid(cookies)
        raise

    return ryanair_data


def main():
    """
    Example usage - requires cookies from browser.

    To use:
    1. Extract cookies from browser (see module docstring)
    2. Set the cookies variable below
    3. Run: python3 ryanair.py
    """
    print("Ryanair Flight Scanner")
    print("=" * 60)
    print()

    # IMPORTANT: Replace with actual cookies from your browser
    cookies = None  # Set to your cookie string: "sid=...; rid=...; ..."

    if not cookies:
        print("⚠️  Cookies required!")
        print()
        print("To extract cookies from browser:")
        print("1. Open https://www.ryanair.com in Firefox/Chrome")
        print("2. Open Developer Tools (F12) → Network tab")
        print("3. Search for a flight")
        print("4. Find GET request to '/api/booking/v4/.../availability'")
        print("5. Copy the Cookie header value")
        print("6. Set cookies variable in this script")
        print()
        print("Example cookies string:")
        print('cookies = "sid=xxx; rid=yyy; xid=zzz; PIM-SESSION-ID=abc; ..."')
        return

    try:
        print("Fetching Ryanair flights...")
        flights_data = get_ryanair_flights(
            origin="WRO",
            destination="ALC",
            date_out="2025-12-11",
            date_in="2025-12-15",
            cookies=cookies
        )

        print(f"\n✓ Successfully fetched flights!")
        print(f"Currency: {flights_data.currency}")
        print(f"Number of trips: {len(flights_data.trips)}")

        for trip in flights_data.trips:
            print(f"\n{trip.origin} ({trip.originName}) → {trip.destination} ({trip.destinationName})")

            for date_info in trip.dates:
                if date_info.flights:
                    print(f"\n  Date: {date_info.dateOut}")
                    for flight in date_info.flights[:2]:  # Show first 2 per date
                        price = flight.regularFare.fares[0].amount if flight.regularFare.fares else "N/A"
                        print(f"    Flight {flight.flightNumber}: {flight.time[0]} → {flight.time[1]}")
                        print(f"    Duration: {flight.duration}, Price: {price} {flights_data.currency}")

        print(f"\n✓ Successfully parsed {len(flights_data.trips)} trips!")

    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
        if e.response.status_code == 403:
            print("\nPossible reasons:")
            print("- Cookies are missing or expired")
            print("- Extract fresh cookies from browser")
            print("- Bot protection detected the request")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
