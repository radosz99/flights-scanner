#!/usr/bin/env python3

"""
Ryanair API integration module.

Note: Ryanair uses bot protection that blocks automated requests.
You need to extract cookies from a browser session to successfully make requests.

Required cookies from browser:
- sid: Session ID
- rid: Request ID
- rid.sig: Request signature
- xid: Transaction ID
- PIM-SESSION-ID: PIM session
- RY_COOKIE_CONSENT: Cookie consent
- _cc: Cookie consent confirmation

How to extract cookies:
1. Open https://www.ryanair.com in Firefox/Chrome
2. Open Developer Tools (F12) → Network tab
3. Search for a flight
4. Find the GET request to "/api/booking/v4/.../availability"
5. Copy the Cookie header value
"""

import requests
from typing import Optional
from ryanair_models import RyanairResponse


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

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()

    # Parse response into Pydantic model
    data = response.json()
    ryanair_data = RyanairResponse(**data)

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
