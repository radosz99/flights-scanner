#!/usr/bin/env python3

"""
Wizz Air API integration module.

Provides functions to:
1. Fetch available flight dates between two airports
2. Search for detailed flight information for specific dates
3. Scan all available flights within a date range
"""

import requests
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from api_models.wizz_air_models import FlightDatesResponse, SearchResponse, Flight


class WizzAirAPI:
    """
    Wizz Air API client.

    Note: Wizz Air uses bot protection (Kasada SDK + Akamai Bot Manager).
    To successfully make requests, you need to extract headers and cookies
    from a real browser session.

    Required bot protection headers:
    - X-RequestVerificationToken: Anti-CSRF token
    - x-kpsdk-ct: Kasada SDK challenge token
    - x-kpsdk-cd: Kasada SDK challenge data
    - x-kpsdk-v: Kasada SDK version
    - x-kpsdk-h: Kasada SDK hash

    Required cookies:
    - RequestVerificationToken: Must match X-RequestVerificationToken header
    - ak_bm_vw_1.1: Akamai Bot Manager session
    - ASP.NET_SessionId: ASP.NET session ID
    - OptanonConsent: Cookie consent data
    """

    BASE_URL = "https://be.wizzair.com/27.35.0/Api"

    # Default headers for API requests
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:144.0) Gecko/20100101 Firefox/144.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Content-Type': 'application/json',
        'Origin': 'https://www.wizzair.com',
        'Referer': 'https://www.wizzair.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }

    def __init__(self, custom_headers: Optional[Dict[str, str]] = None,
                 cookies: Optional[Dict[str, str]] = None):
        """
        Initialize Wizz Air API client.

        Args:
            custom_headers: Additional headers to include (e.g., bot protection headers)
            cookies: Cookies to include in requests (e.g., session cookies)
        """
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

        # Add custom headers if provided (e.g., bot protection headers)
        if custom_headers:
            self.session.headers.update(custom_headers)

        # Add cookies if provided
        if cookies:
            self.session.cookies.update(cookies)

    def get_flight_dates(
        self,
        departure_station: str,
        arrival_station: str,
        from_date: str,
        to_date: str,
    ) -> FlightDatesResponse:
        """
        Fetch available flight dates between two airports.

        Args:
            departure_station: Departure airport code (e.g., 'WRO')
            arrival_station: Arrival airport code (e.g., 'NCE')
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format

        Returns:
            FlightDatesResponse with list of available flight dates
        """
        url = f"{self.BASE_URL}/search/flightDates"

        params = {
            'departureStation': departure_station,
            'arrivalStation': arrival_station,
            'from': from_date,
            'to': to_date,
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return FlightDatesResponse(**data)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching flight dates: {e}")
            raise
        except Exception as e:
            print(f"Error parsing flight dates response: {e}")
            raise

    def search_flights(
        self,
        departure_station: str,
        arrival_station: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adult_count: int = 1,
        child_count: int = 0,
        infant_count: int = 0,
        wdc: bool = True,
    ) -> SearchResponse:
        """
        Search for flights between two airports on specific dates.

        Args:
            departure_station: Departure airport code (e.g., 'WRO')
            arrival_station: Arrival airport code (e.g., 'NCE')
            departure_date: Departure date in YYYY-MM-DDTHH:MM:SS format
            return_date: Return date in YYYY-MM-DDTHH:MM:SS format (optional, for round trip)
            adult_count: Number of adults
            child_count: Number of children
            infant_count: Number of infants
            wdc: Include Wizz Discount Club prices

        Returns:
            SearchResponse with flight details and fares
        """
        url = f"{self.BASE_URL}/search/search"

        # Build flight list
        flight_list = [
            {
                "departureStation": departure_station,
                "arrivalStation": arrival_station,
                "departureDate": departure_date,
            }
        ]

        # Add return flight if specified
        if return_date:
            flight_list.append({
                "departureStation": arrival_station,
                "arrivalStation": departure_station,
                "departureDate": return_date,
            })

        body = {
            "isFlightChange": False,
            "flightList": flight_list,
            "adultCount": adult_count,
            "childCount": child_count,
            "infantCount": infant_count,
            "wdc": wdc,
        }

        try:
            response = self.session.post(url, json=body, timeout=15)
            response.raise_for_status()
            data = response.json()
            return SearchResponse(**data)
        except requests.exceptions.RequestException as e:
            print(f"Error searching flights: {e}")
            raise
        except Exception as e:
            print(f"Error parsing search response: {e}")
            raise

    def scan_all_flights(
        self,
        departure_station: str,
        arrival_station: str,
        from_date: str,
        to_date: str,
        return_date_offset_days: Optional[int] = None,
        adult_count: int = 1,
        max_workers: int = 3,
    ) -> List[SearchResponse]:
        """
        Scan all available flights within a date range.

        First fetches available flight dates, then searches for detailed
        flight information for each date.

        Args:
            departure_station: Departure airport code
            arrival_station: Arrival airport code
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
            return_date_offset_days: If set, search for round trips with return
                                     this many days after departure
            adult_count: Number of adults
            max_workers: Number of parallel workers for searching

        Returns:
            List of SearchResponse objects for each date
        """
        print(f"Fetching available flight dates from {departure_station} to {arrival_station}...")

        # Get available flight dates
        flight_dates_response = self.get_flight_dates(
            departure_station,
            arrival_station,
            from_date,
            to_date,
        )

        flight_dates = flight_dates_response.flightDates
        print(f"Found {len(flight_dates)} available flight dates")

        if not flight_dates:
            print("No flights available for the specified date range")
            return []

        # Search for flights on each date
        results = []

        def search_for_date(departure_date: str) -> Optional[SearchResponse]:
            """Search flights for a specific date."""
            try:
                # Calculate return date if round trip
                return_date = None
                if return_date_offset_days is not None:
                    dep_dt = datetime.fromisoformat(departure_date)
                    ret_dt = dep_dt + timedelta(days=return_date_offset_days)
                    return_date = ret_dt.strftime("%Y-%m-%dT00:00:00")

                search_result = self.search_flights(
                    departure_station=departure_station,
                    arrival_station=arrival_station,
                    departure_date=departure_date,
                    return_date=return_date,
                    adult_count=adult_count,
                )

                date_str = departure_date.split("T")[0]
                print(f"✓ Searched flights for {date_str}: "
                      f"{len(search_result.outboundFlights)} outbound, "
                      f"{len(search_result.returnFlights)} return")

                return search_result
            except Exception as e:
                date_str = departure_date.split("T")[0]
                print(f"✗ Error searching flights for {date_str}: {e}")
                return None

        # Search in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_date = {
                executor.submit(search_for_date, date): date
                for date in flight_dates
            }

            for future in as_completed(future_to_date):
                result = future.result()
                if result:
                    results.append(result)
                # Small delay to avoid rate limiting
                time.sleep(0.2)

        print(f"\nSuccessfully retrieved {len(results)} flight search results")
        return results


def main():
    """Example usage of the Wizz Air API."""
    print("Wizz Air Flight Scanner")
    print("=" * 60)

    api = WizzAirAPI()

    # Example 1: Get flight dates
    print("\n1. Fetching available flight dates...")
    try:
        flight_dates = api.get_flight_dates(
            departure_station="WRO",
            arrival_station="NCE",
            from_date="2025-12-13",
            to_date="2026-01-13",
        )
        print(f"Found {len(flight_dates.flightDates)} available dates:")
        for date in flight_dates.flightDates[:5]:
            print(f"  - {date}")
        if len(flight_dates.flightDates) > 5:
            print(f"  ... and {len(flight_dates.flightDates) - 5} more")
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Search for specific flight
    print("\n2. Searching for specific flight on 2025-12-13...")
    try:
        search_result = api.search_flights(
            departure_station="WRO",
            arrival_station="NCE",
            departure_date="2025-12-13T00:00:00",
            return_date="2025-12-20T00:00:00",  # Round trip
            adult_count=1,
        )

        print(f"\nOutbound flights: {len(search_result.outboundFlights)}")
        for flight in search_result.outboundFlights:
            cheapest = flight.get_cheapest_fare()
            if cheapest:
                print(f"  Flight {flight.flightNumber}: "
                      f"{flight.departureDateTime} -> {flight.arrivalDateTime}")
                print(f"    Duration: {flight.duration}, "
                      f"Cheapest fare: {cheapest.basePrice.amount} {cheapest.basePrice.currencyCode} "
                      f"({cheapest.bundle} bundle)")

        print(f"\nReturn flights: {len(search_result.returnFlights)}")
        for flight in search_result.returnFlights:
            cheapest = flight.get_cheapest_fare()
            if cheapest:
                print(f"  Flight {flight.flightNumber}: "
                      f"{flight.departureDateTime} -> {flight.arrivalDateTime}")
                print(f"    Duration: {flight.duration}, "
                      f"Cheapest fare: {cheapest.basePrice.amount} {cheapest.basePrice.currencyCode} "
                      f"({cheapest.bundle} bundle)")

        total_price = search_result.get_total_cheapest_price()
        if total_price:
            print(f"\nTotal cheapest round trip price: {total_price} {search_result.currencyCode}")

    except Exception as e:
        print(f"Error: {e}")

    # Example 3: Scan all flights in date range
    print("\n3. Scanning all flights in date range (limiting to 3 dates for demo)...")
    try:
        all_results = api.scan_all_flights(
            departure_station="WRO",
            arrival_station="NCE",
            from_date="2025-12-13",
            to_date="2025-12-20",
            return_date_offset_days=7,  # Round trip with 7 days stay
            adult_count=1,
            max_workers=2,
        )

        print(f"\nSummary of all scanned flights:")
        for i, result in enumerate(all_results[:3], 1):
            total = result.get_total_cheapest_price()
            if total:
                print(f"  {i}. Total cheapest: {total} {result.currencyCode}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
