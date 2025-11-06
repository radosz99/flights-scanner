#!/usr/bin/env python3

import requests
from models import RyanairResponse


def get_ryanair_flights(
    origin: str = "WRO",
    destination: str = "ALC",
    date_out: str = "2025-12-11",
    date_in: str = "2025-12-15",
    adt: int = 1,
    teen: int = 0,
    chd: int = 0,
    inf: int = 0,
    flex_days_before_out: int = 2,
    flex_days_out: int = 2,
    flex_days_before_in: int = 2,
    flex_days_in: int = 2,
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

    Returns:
        RyanairResponse: Parsed Pydantic model with flight data
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

    # Add browser-like headers to avoid bot detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:144.0) Gecko/20100101 Firefox/144.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.ryanair.com/gb/en/',
        'Origin': 'https://www.ryanair.com',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()

    # Parse response into Pydantic model
    data = response.json()
    ryanair_data = RyanairResponse(**data)

    return ryanair_data


def main():
    print("Fetching Ryanair flights...")

    try:
        flights_data = get_ryanair_flights()

        print(f"\nCurrency: {flights_data.currency}")
        print(f"Number of trips: {len(flights_data.trips)}")

        for trip in flights_data.trips:
            print(f"\n{trip.origin} ({trip.originName}) -> {trip.destination} ({trip.destinationName})")

            for date_info in trip.dates:
                if date_info.flights:
                    print(f"\n  Date: {date_info.dateOut}")
                    for flight in date_info.flights:
                        price = flight.regularFare.fares[0].amount if flight.regularFare.fares else "N/A"
                        print(f"    Flight {flight.flightNumber}: {flight.time[0]} -> {flight.time[1]}")
                        print(f"    Duration: {flight.duration}, Price: {price} {flights_data.currency}")

        print(f"\nSuccessfully parsed {len(flights_data.trips)} trips!")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except Exception as e:
        print(f"Error parsing data: {e}")


if __name__ == "__main__":
    main()
