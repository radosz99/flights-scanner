#!/usr/bin/env python3

"""
Helper script for using Ryanair API with browser-extracted cookies.

Ryanair uses bot protection that blocks automated requests. This script shows
how to extract cookies from a real browser session and use them with the API.

IMPORTANT NOTES:
1. Cookies expire quickly (usually within hours)
2. Using extracted cookies may violate Ryanair's Terms of Service
3. This is for educational purposes only
4. For production use, consider browser automation

How to extract cookies:
======================

1. Open https://www.ryanair.com in Firefox/Chrome
2. Open Developer Tools (F12)
3. Go to Network tab
4. Search for a flight (to trigger API calls)
5. Find the GET request to "/api/booking/v4/.../availability"
6. Right-click → Copy → Copy as cURL
7. Extract the Cookie header value

Example Cookie header from browser:
mkt=/hr/en/; sid=8b4d93ba-1cff-43a5-8b37-02e91bbb9cd8; rid=614a7f95-aad8-45e7-8c85-6c81bc32702c; ...

Key cookies for Ryanair:
- sid: Session ID
- rid: Request ID
- rid.sig: Request signature
- xid: Transaction ID
- PIM-SESSION-ID: PIM session
- _cc: Cookie consent
- RY_COOKIE_CONSENT: Ryanair cookie consent
"""

import requests
from ryanair_models import RyanairResponse


def get_ryanair_flights_with_cookies(
    origin: str = "WRO",
    destination: str = "ALC",
    date_out: str = "2025-12-11",
    date_in: str = "2025-12-15",
    adt: int = 1,
    cookies_str: str = None,
):
    """
    Fetch Ryanair flights using browser-extracted cookies.

    Args:
        origin: Origin airport code
        destination: Destination airport code
        date_out: Departure date (YYYY-MM-DD)
        date_in: Return date (YYYY-MM-DD)
        adt: Number of adults
        cookies_str: Full Cookie header string from browser

    Returns:
        RyanairResponse object with flight data
    """
    url = "https://www.ryanair.com/api/booking/v4/pl-pl/availability"

    params = {
        "ADT": adt,
        "TEEN": 0,
        "CHD": 0,
        "INF": 0,
        "Origin": origin,
        "Destination": destination,
        "promoCode": "",
        "IncludeConnectingFlights": "false",
        "DateOut": date_out,
        "DateIn": date_in,
        "FlexDaysBeforeOut": 2,
        "FlexDaysOut": 2,
        "FlexDaysBeforeIn": 2,
        "FlexDaysIn": 2,
        "RoundTrip": "true",
        "IncludePrimeFares": "false",
        "ToUs": "AGREED",
    }

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
    if cookies_str:
        headers['Cookie'] = cookies_str

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        return RyanairResponse(**data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        raise
    except Exception as e:
        print(f"Error parsing data: {e}")
        raise


def example_usage():
    """
    Example of using Ryanair API with extracted cookies.

    Replace the YOUR_COOKIES_HERE placeholder with actual cookies
    from your browser session.
    """

    # Example: Extract this from browser DevTools Network tab
    # Copy the entire Cookie header value
    cookies_from_browser = "YOUR_COOKIES_HERE"

    # Example actual cookie string (these are expired/fake):
    # cookies_from_browser = (
    #     "mkt=/hr/en/; "
    #     "sid=8b4d93ba-1cff-43a5-8b37-02e91bbb9cd8; "
    #     "rid=614a7f95-aad8-45e7-8c85-6c81bc32702c; "
    #     "rid.sig=jyna6R42wntYgoTpqvxHMK7H+KyM6xLed+9I3KsvYZa...; "
    #     "xid=7e28c79b-7552-4e36-b8fa-f594ec7014e1; "
    #     "PIM-SESSION-ID=bYjlTeWPKOgp3gBK; "
    #     "_cc=AYxzu0UhE%2FZFWf62wL%2F%2BQ%2FY4; "
    #     "RY_COOKIE_CONSENT=true"
    # )

    print("To use this script:")
    print("1. Open Ryanair website in your browser")
    print("2. Search for a flight")
    print("3. Open DevTools (F12) → Network tab")
    print("4. Find the 'availability' request")
    print("5. Copy the Cookie header value")
    print("6. Paste it in the cookies_from_browser variable")
    print()

    if cookies_from_browser == "YOUR_COOKIES_HERE":
        print("⚠️  Please extract cookies from browser first!")
        return

    try:
        flights = get_ryanair_flights_with_cookies(
            origin="WRO",
            destination="ALC",
            date_out="2025-12-11",
            date_in="2025-12-15",
            cookies_str=cookies_from_browser
        )

        print(f"✓ Successfully fetched flights!")
        print(f"Currency: {flights.currency}")
        print(f"Trips: {len(flights.trips)}")

        for trip in flights.trips:
            print(f"\n{trip.origin} → {trip.destination}")
            for date_info in trip.dates:
                if date_info.flights:
                    print(f"  Date: {date_info.dateOut}")
                    for flight in date_info.flights[:2]:  # Show first 2
                        price = flight.regularFare.fares[0].amount
                        print(f"    {flight.flightNumber}: {price} {flights.currency}")

    except Exception as e:
        print(f"✗ Request failed: {e}")
        print("\nPossible reasons:")
        print("1. Cookies have expired (extract fresh ones)")
        print("2. Bot protection detected the request")
        print("3. Network/connectivity issues")


def alternative_browser_automation():
    """
    Alternative approach using browser automation.

    This is more reliable but slower than direct API calls.
    """
    print("\nAlternative: Browser Automation (Recommended)")
    print("=" * 60)
    print("""
For a more reliable solution, use browser automation:

```python
from selenium import webdriver
import undetected_chromedriver as uc
import time

# Use undetected chromedriver
driver = uc.Chrome()

# Navigate to Ryanair
driver.get('https://www.ryanair.com')
time.sleep(5)  # Let page load

# Use Selenium to search for flights
# Or extract cookies and use with requests:
cookies = {c['name']: c['value'] for c in driver.get_cookies()}
cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])

# Now use cookie_str with requests
```

This approach:
- ✓ Bypasses bot protection naturally
- ✓ More reliable long-term
- ✗ Slower (full browser overhead)
- ✗ Requires browser drivers
""")


if __name__ == "__main__":
    print("Ryanair API with Browser Cookies")
    print("=" * 60)
    print()
    print("⚠️  WARNING: This is for educational purposes only!")
    print("⚠️  Using extracted cookies may violate Terms of Service")
    print()
    print("=" * 60)
    print()

    example_usage()
    alternative_browser_automation()
