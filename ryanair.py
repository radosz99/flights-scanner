#!/usr/bin/env python3

"""
Ryanair API integration module with Selenium automation support.

Note: Ryanair uses bot protection that blocks automated requests.
You can either:
1. Extract cookies manually from browser (see module docstring)
2. Use Selenium automation to get cookies automatically (recommended)

Required cookie from browser:
- fr-correlation-id: Correlation ID for Ryanair requests

How to extract cookies manually:
1. Open https://www.ryanair.com in Firefox/Chrome
2. Open Developer Tools (F12) → Network tab
3. Search for a flight
4. Look through network requests for the "fr-correlation-id" cookie
5. Copy the cookie value

Or use Selenium automation (recommended):
- Use extract_cookies_from_ryanair() to get fr-correlation-id cookie automatically
- Then pass cookies to get_ryanair_flights()
- Requires selenium and chromedriver
"""

import requests
import time
import json
from typing import Optional
from datetime import datetime
from ryanair_models import RyanairResponse
from loguru import logger

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
        logger.warning("MongoDB not available. Cookie not saved.")
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

        logger.success(f"Cookie saved to MongoDB (ID: {result.inserted_id})")
        return True

    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
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
        logger.warning("MongoDB not available.")
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
            logger.success(f"Found active cookie (fetched: {cookie_doc['fetched']})")
            return cookie_doc["cookie"]
        else:
            logger.warning("No active cookies found in MongoDB")
            return None

    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
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
    Use Selenium to navigate to Ryanair flight selection page and extract fr-correlation-id cookie
    from network requests.

    This function:
    1. Opens Chrome browser with network logging enabled
    2. Navigates to Ryanair flight selection page
    3. Monitors ALL network requests for fr-correlation-id cookie
    4. Extracts the fr-correlation-id cookie value
    5. Tests it against the availability endpoint
    6. Returns the validated cookie
    7. Optionally saves to MongoDB for tracking

    Args:
        wait_time: Seconds to wait for requests with cookies (default: 30)
        save_to_db: Save cookies to MongoDB for tracking (default: True)

    Returns:
        Valid fr-correlation-id cookie string or None if not found

    Raises:
        ImportError: If selenium is not installed
        Exception: If browser fails to start or navigate

    Example:
        cookies = extract_cookies_from_ryanair(wait_time=30, save_to_db=True)
        if cookies:
            flights = get_ryanair_flights("WRO", "ALC", "2025-12-11", "2025-12-15", cookies=cookies)
    """
    logger.info("Starting Chrome browser with network logging...")
    driver = setup_driver(enable_network_capture=True)

    try:
        url = settings.RYANAIR_COOKIE_URL
        logger.info(f"Navigating to Ryanair flight selection page...")
        logger.info(f"URL: {url[:80]}...")
        driver.get(url)

        logger.info(f"Waiting up to {wait_time} seconds to find fr-correlation-id cookie...")
        logger.info("Monitoring ALL network requests for fr-correlation-id cookie...")

        fr_correlation_id = None
        start_time = time.time()
        checked_requests = 0

        while time.time() - start_time < wait_time:
            # Get performance logs
            logs = driver.get_log('performance')

            for log in logs:
                try:
                    log_entry = json.loads(log['message'])
                    message = log_entry.get('message', {})

                    # Look for Network.requestWillBeSentExtraInfo events
                    if message.get('method') == 'Network.requestWillBeSentExtraInfo':
                        params = message.get('params', {})
                        associated_cookies = params.get('associatedCookies', [])
                        request_url = params.get('headers', {}).get('Referer', 'unknown')

                        # Check if this request has the fr-correlation-id cookie
                        if associated_cookies:
                            checked_requests += 1
                            for cookie_data in associated_cookies:
                                cookie = cookie_data.get('cookie', {})
                                cookie_name = cookie.get('name')
                                cookie_value = cookie.get('value')

                                if cookie_name == 'fr-correlation-id' and cookie_value:
                                    fr_correlation_id = cookie_value
                                    logger.success(f"Found fr-correlation-id cookie!")
                                    logger.info(f"Value: {fr_correlation_id}")
                                    logger.info(f"Found in request after checking {checked_requests} requests")
                                    break

                            if fr_correlation_id:
                                break

                except Exception as e:
                    # Skip malformed log entries
                    continue

            if fr_correlation_id:
                break

            # Small delay to avoid busy waiting
            time.sleep(0.5)

        if not fr_correlation_id:
            logger.error(f"fr-correlation-id cookie not found after {wait_time} seconds")
            logger.info(f"Checked {checked_requests} network requests")
            logger.warning("The page may not have loaded properly or the cookie name might be different.")
            logger.warning("Try increasing wait_time or verify the cookie name.")
            return None

        logger.info(f"{'='*80}")
        logger.success(f"Found fr-correlation-id cookie: {fr_correlation_id}")
        logger.info(f"{'='*80}")
        logger.info("Testing cookie validity with API request...")

        # Build cookie string with fr-correlation-id
        cookie_string = f"fr-correlation-id={fr_correlation_id}"

        try:
            test_flights = get_ryanair_flights(
                origin="WRO",
                destination="ALC",
                date_out="2026-03-06",
                date_in="2026-03-08",
                adt=1,
                cookies=cookie_string
            )
            logger.info(f"{'='*80}")
            logger.success(f"FR-CORRELATION-ID COOKIE IS VALID!")
            logger.info(f"{'='*80}")
            logger.success(f"Successfully fetched {len(test_flights.trips)} trips")
            logger.info(f"Currency: {test_flights.currency}")

            # Save to MongoDB if requested
            if save_to_db and MONGODB_AVAILABLE:
                logger.info("Saving validated cookie to MongoDB...")
                save_cookie_to_mongodb(cookie_string)

            logger.success("Cookie extraction and validation completed successfully")
            return cookie_string

        except Exception as e:
            logger.info(f"{'='*80}")
            logger.error(f"FR-CORRELATION-ID COOKIE IS INVALID")
            logger.info(f"{'='*80}")
            logger.error(f"Error: {str(e)[:200]}")
            logger.warning("The cookie may have expired or might not be sufficient alone.")
            return None

    finally:
        logger.info("Closing browser...")
        driver.quit()


def get_valid_cookie(auto_refresh: bool = True) -> Optional[str]:
    """
    Get a valid Ryanair cookie with automatic testing and refresh.

    This is the main method users should call to get a working cookie.

    Workflow:
    1. Check MongoDB for the most recent active cookie
    2. Test the cookie with a real API request
    3. If valid, return it
    4. If invalid and auto_refresh=True, extract a new cookie from browser
    5. Return the validated cookie or None if all attempts fail

    Args:
        auto_refresh: Automatically extract new cookie if existing ones are invalid (default: True)

    Returns:
        Valid cookie string or None if unable to get a valid cookie

    Example:
        # Simple usage - automatically handles everything
        cookie = get_valid_cookie()
        if cookie:
            flights = get_ryanair_flights("WRO", "ALC", "2026-03-06", "2026-03-08", cookies=cookie)
    """
    logger.info("=" * 80)
    logger.info("GETTING VALID RYANAIR COOKIE")
    logger.info("=" * 80)

    # Step 1: Try to get latest cookie from MongoDB
    logger.info("1️⃣  Checking MongoDB for active cookies...")
    cookie = get_latest_valid_cookie()

    if cookie:
        logger.success(f"Found active cookie in database")
        logger.info(f"Cookie preview: {cookie[:60]}...")

        # Step 2: Test the cookie
        logger.info("2️⃣  Testing cookie validity...")
        try:
            test_flights = get_ryanair_flights(
                origin="WRO",
                destination="ALC",
                date_out="2026-03-06",
                date_in="2026-03-08",
                adt=1,
                cookies=cookie
            )

            logger.info(f"{'='*80}")
            logger.success("COOKIE IS VALID AND READY TO USE!")
            logger.info(f"{'='*80}")
            logger.success(f"Fetched {len(test_flights.trips)} trips")
            return cookie

        except Exception as e:
            logger.error(f"Cookie test failed: {str(e)[:100]}")
            logger.warning(f"Cookie marked as invalid in database")

            if not auto_refresh:
                logger.warning("Auto-refresh disabled. Returning None.")
                return None

            logger.info(f"Will attempt to extract fresh cookie...")
    else:
        logger.warning(f"No active cookies found in database")

        if not auto_refresh:
            logger.warning("Auto-refresh disabled. Returning None.")
            return None

        logger.info(f"Will attempt to extract fresh cookie...")

    # Step 3: Extract new cookie if needed
    if auto_refresh:
        logger.info("3️⃣  Extracting fresh cookie from browser...")
        logger.info("(This will open a Chrome window)")

        try:
            new_cookie = extract_cookies_from_ryanair(wait_time=30, save_to_db=True)

            if new_cookie:
                logger.info(f"{'='*80}")
                logger.success("NEW COOKIE EXTRACTED AND VALIDATED!")
                logger.info(f"{'='*80}")
                return new_cookie
            else:
                logger.error("Failed to extract new cookie")
                return None

        except Exception as e:
            logger.error(f"Error extracting cookie: {str(e)[:100]}")
            return None

    return None


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

    # Minimal headers - only cookie is required for bot protection bypass
    headers = {}

    # Add cookies if provided (required for bypassing bot protection)
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
            logger.warning(f"Cookie returned 403 Forbidden - marking as invalid")
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
    logger.info("Ryanair Flight Scanner")
    logger.info("=" * 60)

    # IMPORTANT: Replace with actual cookies from your browser
    cookies = None  # Set to your cookie string: "sid=...; rid=...; ..."

    if not cookies:
        logger.warning("Cookies required!")
        logger.info("To extract cookies from browser:")
        logger.info("1. Open https://www.ryanair.com in Firefox/Chrome")
        logger.info("2. Open Developer Tools (F12) → Network tab")
        logger.info("3. Search for a flight")
        logger.info("4. Find GET request to '/api/booking/v4/.../availability'")
        logger.info("5. Copy the Cookie header value")
        logger.info("6. Set cookies variable in this script")
        logger.info("")
        logger.info("Example cookies string:")
        logger.info('cookies = "sid=xxx; rid=yyy; xid=zzz; PIM-SESSION-ID=abc; ..."')
        return

    try:
        logger.info("Fetching Ryanair flights...")
        flights_data = get_ryanair_flights(
            origin="WRO",
            destination="ALC",
            date_out="2025-12-11",
            date_in="2025-12-15",
            cookies=cookies
        )

        logger.success("Successfully fetched flights!")
        logger.info(f"Currency: {flights_data.currency}")
        logger.info(f"Number of trips: {len(flights_data.trips)}")

        for trip in flights_data.trips:
            logger.info(f"{trip.origin} ({trip.originName}) → {trip.destination} ({trip.destinationName})")

            for date_info in trip.dates:
                if date_info.flights:
                    logger.info(f"  Date: {date_info.dateOut}")
                    for flight in date_info.flights[:2]:  # Show first 2 per date
                        price = flight.regularFare.fares[0].amount if flight.regularFare.fares else "N/A"
                        logger.info(f"    Flight {flight.flightNumber}: {flight.time[0]} → {flight.time[1]}")
                        logger.info(f"    Duration: {flight.duration}, Price: {price} {flights_data.currency}")

        logger.success(f"Successfully parsed {len(flights_data.trips)} trips!")

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        if e.response.status_code == 403:
            logger.error("Possible reasons:")
            logger.error("- Cookies are missing or expired")
            logger.error("- Extract fresh cookies from browser")
            logger.error("- Bot protection detected the request")
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
