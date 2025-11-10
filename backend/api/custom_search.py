#!/usr/bin/env python3

"""
Custom Trip Search Module
==========================

This module provides comprehensive functionality for searching and analyzing round trip flights.
It handles complex search scenarios including multi-airport searches, flexible return options,
weekday filtering, and trip duration constraints.

Main Features
-------------
1. **Single Origin/Destination Search**: Find round trips from one airport to another
2. **Multi-Airport Batch Search**: Efficiently search across multiple origins and destinations
3. **Flexible Return Options**: Allow returns from different airports in destination country
4. **Weekday Filtering**: Filter flights by departure days (e.g., only Friday departures)
5. **Trip Duration Control**: Specify minimum and maximum trip lengths
6. **Price Optimization**: Automatic sorting by total trip price
7. **Performance Safeguards**: Prevents searches that would be too expensive to compute

Performance Considerations
--------------------------
The module includes several safeguards to prevent expensive queries:
- Maximum 5,000 flights per direction (outbound/return)
- Maximum 50,000,000 total flight combinations
- Raises TooManyFlightsError when limits are exceeded

Usage Example
-------------
Basic round trip search:

    >>> from pymongo import MongoClient
    >>> from api.custom_search import CustomTripSearch
    >>>
    >>> client = MongoClient("mongodb://localhost:27017/")
    >>> flights_collection = client["flights_scanner"]["ryanair_flights"]
    >>> search = CustomTripSearch(flights_collection)
    >>>
    >>> # Find round trips from Warsaw to Barcelona for 3-7 days
    >>> results = search.find_round_trips(
    ...     origin="WAW",
    ...     destination="BCN",
    ...     min_days=3,
    ...     max_days=7,
    ...     passengers=2
    ... )
    >>>
    >>> # Search multiple origins and destinations
    >>> batch_results = search.find_round_trips_batch(
    ...     origins=["WAW", "WRO", "KRK"],
    ...     destinations=["BCN", "AGP", "VLC"],
    ...     min_days=3,
    ...     max_days=7,
    ...     passengers=2,
    ...     return_from_same_airport=False  # Allow different return airports
    ... )

Data Structures
---------------
Round Trip Result (find_round_trips):
    {
        "outbound_flight": {
            "flight_id": str,
            "flight_number": str,
            "date": str (YYYY-MM-DD),
            "departure_time": str (ISO format),
            "arrival_time": str (ISO format),
            "duration": str,
            "price": float,
            "currency": str
        },
        "return_flight": {
            ... same structure as outbound_flight ...
        },
        "trip_duration_days": int,
        "total_price": float,
        "price_per_person": float,
        "passengers": int,
        "currency": str,
        "destination": str (optional, when searching all destinations),
        "destination_name": str (optional, when searching all destinations)
    }

Batch Search Result (find_round_trips_batch):
    {
        "outbound": {
            "flight_id": str,
            "origin": str,
            "origin_name": str,
            "destination": str,
            "destination_name": str,
            "date_out": str (YYYY-MM-DD),
            "departure_time": str (ISO format),
            "arrival_time": str (ISO format),
            "duration": str,
            "current_price": float
        },
        "return": {
            ... same structure as outbound ...
        },
        "trip_duration_days": int,
        "stay_duration": str (format: "Xd Yh Zm"),
        "total_price": float,
        "price_per_person": float,
        "passengers": int,
        "currency": str
    }

Exceptions
----------
TooManyFlightsError:
    Raised when a search would generate too many flight combinations to process
    efficiently. Includes helpful suggestions for narrowing the search criteria.

Author: Ryanair Flight Scanner API
Version: 1.0.0
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
import sys
import os

# Add parent directory to path to import constants
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from constants import POLISH_AIRPORTS


class TooManyFlightsError(Exception):
    """
    Raised when there are too many flights to process efficiently.

    This exception is raised to prevent expensive queries that would take too long
    to compute or consume too much memory. The error message includes specific
    suggestions for narrowing the search criteria.

    Attributes:
        message (str): Detailed error message with suggestions for fixing the issue

    Example:
        >>> try:
        ...     results = search.find_round_trips_batch(origins=all_airports, ...)
        ... except TooManyFlightsError as e:
        ...     print(f"Search too broad: {e}")
        ...     # Narrow search by adding date filters, weekday filters, etc.
    """
    pass


class CustomTripSearch:
    """
    Service class for custom trip search operations.

    This class provides methods for searching round trip flights with various filtering
    options. It's designed to work with MongoDB collections containing flight data.

    Attributes:
        flights_collection (Collection): MongoDB collection containing flight documents

    Flight Document Schema (Expected):
        {
            "_id": ObjectId,
            "flight_id": str,
            "flight_number": str,
            "origin": str (airport code),
            "origin_name": str,
            "destination": str (airport code),
            "destination_name": str,
            "date_out": str (YYYY-MM-DD),
            "departure_time": str (ISO format),
            "arrival_time": str (ISO format),
            "duration": str,
            "current_price": float,
            "currency": str
        }

    Performance Limits:
        - MAX_FLIGHTS_PER_DIRECTION: 5,000 flights
        - MAX_TOTAL_COMBINATIONS: 50,000,000 combinations

    Example:
        >>> from pymongo import MongoClient
        >>> client = MongoClient("mongodb://localhost:27017/")
        >>> collection = client["db"]["flights"]
        >>> search = CustomTripSearch(collection)
        >>>
        >>> # Search for weekend getaways
        >>> trips = search.find_round_trips(
        ...     origin="WAW",
        ...     destination="BCN",
        ...     min_days=2,
        ...     max_days=4,
        ...     passengers=2,
        ...     outbound_weekdays=[4, 5],  # Friday or Saturday
        ...     return_weekdays=[0, 6]      # Monday or Sunday
        ... )
    """

    # Performance limit constants
    MAX_FLIGHTS_PER_DIRECTION = 5000
    """Maximum number of flights allowed in a single direction (outbound or return)"""

    MAX_TOTAL_COMBINATIONS = 50_000_000
    """Maximum number of flight combinations that can be processed"""

    def __init__(self, flights_collection: Collection):
        """
        Initialize the custom trip search service.

        Args:
            flights_collection (Collection): MongoDB collection containing flight data.
                The collection should contain documents with flight information including
                origin, destination, dates, times, and prices.

        Example:
            >>> from pymongo import MongoClient
            >>> client = MongoClient("mongodb://localhost:27017/")
            >>> flights = client["flights_scanner"]["ryanair_flights"]
            >>> search = CustomTripSearch(flights)
        """
        self.flights_collection = flights_collection

    def find_round_trips(
        self,
        origin: str,
        destination: Optional[str],
        min_days: int,
        max_days: int,
        passengers: int = 2,
        return_from_same_airport: bool = True,
        outbound_weekdays: Optional[List[int]] = None,
        return_weekdays: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all possible round trips within specified trip length range.

        This method searches for valid round trip combinations where the return flight
        departs between min_days and max_days after the outbound flight. Results are
        automatically sorted by total price (cheapest first).

        Args:
            origin (str): Origin airport code (e.g., "WAW" for Warsaw).
                Airport codes are case-insensitive.

            destination (Optional[str]): Destination airport code (e.g., "BCN" for Barcelona).
                If None, searches all possible destinations from the origin.

            min_days (int): Minimum trip duration in days. Must be >= 1.
                Example: min_days=3 means return flight is at least 3 days after departure.

            max_days (int): Maximum trip duration in days. Must be >= min_days.
                Example: max_days=7 means return flight is at most 7 days after departure.

            passengers (int, optional): Number of passengers. Defaults to 2.
                Affects total_price calculation: total_price = (outbound + return) * passengers

            return_from_same_airport (bool, optional): If True, return flight must depart
                from the same airport where outbound flight landed. Defaults to True.
                Example: If False and destination is not specified, a trip could be
                WAW→BCN outbound and VLC→WAW return (different Spanish airports).

            outbound_weekdays (Optional[List[int]], optional): List of allowed weekdays for
                outbound flights. 0=Monday, 6=Sunday. None means any day. Defaults to None.
                Example: [4, 5] means only Friday or Saturday departures.

            return_weekdays (Optional[List[int]], optional): List of allowed weekdays for
                return flights. 0=Monday, 6=Sunday. None means any day. Defaults to None.
                Example: [0, 6] means only Monday or Sunday returns.

        Returns:
            List[Dict[str, Any]]: List of round trip combinations, sorted by total_price.
                Each dictionary contains:
                - outbound_flight: Dict with outbound flight details
                - return_flight: Dict with return flight details
                - trip_duration_days: Number of days between outbound and return
                - total_price: Total cost for all passengers
                - price_per_person: Cost per passenger
                - passengers: Number of passengers
                - currency: Price currency
                - destination: Destination airport code (only when destination param is None)
                - destination_name: Destination airport name (only when destination param is None)

        Raises:
            TooManyFlightsError: If the search would generate more than MAX_FLIGHTS_PER_DIRECTION
                flights in either direction, or more than MAX_TOTAL_COMBINATIONS total combinations.
                The error message includes specific counts and suggestions for narrowing the search.

        Examples:
            >>> # Find 3-7 day trips from Warsaw to Barcelona
            >>> trips = search.find_round_trips(
            ...     origin="WAW",
            ...     destination="BCN",
            ...     min_days=3,
            ...     max_days=7,
            ...     passengers=2
            ... )
            >>>
            >>> # Find weekend getaways (Friday-Monday)
            >>> weekend_trips = search.find_round_trips(
            ...     origin="WRO",
            ...     destination="AGP",
            ...     min_days=2,
            ...     max_days=4,
            ...     passengers=1,
            ...     outbound_weekdays=[4, 5],  # Friday or Saturday
            ...     return_weekdays=[0, 1]      # Monday or Tuesday
            ... )
            >>>
            >>> # Find all possible destinations for 5-day trips
            >>> all_destinations = search.find_round_trips(
            ...     origin="KRK",
            ...     destination=None,  # Search all destinations
            ...     min_days=5,
            ...     max_days=5,
            ...     passengers=2
            ... )

        Notes:
            - Trip duration is calculated as: (return_date - outbound_date).days
            - Flights are matched based on dates, not specific flight times
            - Results are sorted by total_price in ascending order
            - When destination is None, results include destination info for each trip
        """
        # Query construction based on destination parameter
        if destination:
            # Specific destination search: get direct flights
            outbound_flights = list(self.flights_collection.find({
                "origin": origin.upper(),
                "destination": destination.upper()
            }).sort("departure_time", ASCENDING))

            # Return flights logic (currently same for both settings)
            # Note: The return_from_same_airport logic is validated in the loop below
            if return_from_same_airport:
                return_flights = list(self.flights_collection.find({
                    "origin": destination.upper(),
                    "destination": origin.upper()
                }).sort("departure_time", ASCENDING))
            else:
                # When destination is specified, return flights must still be from that destination
                # The flag is more relevant when destination is None
                return_flights = list(self.flights_collection.find({
                    "origin": destination.upper(),
                    "destination": origin.upper()
                }).sort("departure_time", ASCENDING))
        else:
            # Search all destinations: get all outbound flights from origin
            outbound_flights = list(self.flights_collection.find({
                "origin": origin.upper()
            }).sort("departure_time", ASCENDING))

            # Get all return flights back to origin
            return_flights = list(self.flights_collection.find({
                "destination": origin.upper()
            }).sort("departure_time", ASCENDING))

        # Performance validation
        logger.info(f"Found {len(outbound_flights)} outbound flights and {len(return_flights)} return flights")

        if len(outbound_flights) > self.MAX_FLIGHTS_PER_DIRECTION:
            raise TooManyFlightsError(
                f"Too many outbound flights ({len(outbound_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific destination, weekday filters). "
                f"Maximum allowed: {self.MAX_FLIGHTS_PER_DIRECTION}"
            )

        if len(return_flights) > self.MAX_FLIGHTS_PER_DIRECTION:
            raise TooManyFlightsError(
                f"Too many return flights ({len(return_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific destination, weekday filters). "
                f"Maximum allowed: {self.MAX_FLIGHTS_PER_DIRECTION}"
            )

        potential_combinations = len(outbound_flights) * len(return_flights)
        if potential_combinations > self.MAX_TOTAL_COMBINATIONS:
            raise TooManyFlightsError(
                f"Too many potential combinations ({potential_combinations:,} = {len(outbound_flights)} × {len(return_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific destination, weekday filters). "
                f"Maximum allowed: {self.MAX_TOTAL_COMBINATIONS:,}"
            )

        # Main search logic: iterate through all valid combinations
        round_trips = []

        for outbound in outbound_flights:
            # Extract date from departure_time (format: YYYY-MM-DDTHH:MM:SS.mmm)
            outbound_date_str = outbound["departure_time"].split("T")[0]
            outbound_date = datetime.strptime(outbound_date_str, "%Y-%m-%d")

            # Apply outbound weekday filter if specified
            if outbound_weekdays is not None:
                if outbound_date.weekday() not in outbound_weekdays:
                    continue  # Skip this outbound flight

            for return_flight in return_flights:
                # Validate return airport logic
                if return_from_same_airport:
                    if not destination:
                        # When searching all destinations, ensure return is from where we landed
                        if return_flight["origin"] != outbound["destination"]:
                            continue  # Skip this return flight
                # Note: When return_from_same_airport is False and destination is None,
                # we allow returns from any airport (no additional filtering needed)

                # Extract return flight date
                return_date_str = return_flight["departure_time"].split("T")[0]
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d")

                # Apply return weekday filter if specified
                if return_weekdays is not None:
                    if return_date.weekday() not in return_weekdays:
                        continue  # Skip this return flight

                # Calculate trip duration in days
                trip_duration = (return_date - outbound_date).days

                # Check if trip duration is within the specified range
                if min_days <= trip_duration <= max_days:
                    # Calculate total price for all passengers
                    total_price = (outbound["current_price"] + return_flight["current_price"]) * passengers

                    # Build trip data structure
                    trip_data = {
                        "outbound_flight": {
                            "flight_id": outbound["flight_id"],
                            "flight_number": outbound["flight_number"],
                            "date": outbound_date_str,
                            "departure_time": outbound["departure_time"],
                            "arrival_time": outbound["arrival_time"],
                            "duration": outbound["duration"],
                            "price": outbound["current_price"],
                            "currency": outbound["currency"]
                        },
                        "return_flight": {
                            "flight_id": return_flight["flight_id"],
                            "flight_number": return_flight["flight_number"],
                            "date": return_date_str,
                            "departure_time": return_flight["departure_time"],
                            "arrival_time": return_flight["arrival_time"],
                            "duration": return_flight["duration"],
                            "price": return_flight["current_price"],
                            "currency": return_flight["currency"]
                        },
                        "trip_duration_days": trip_duration,
                        "total_price": round(total_price, 2),
                        "price_per_person": round(total_price / passengers, 2),
                        "passengers": passengers,
                        "currency": outbound["currency"]
                    }

                    # Add destination info when searching all destinations
                    if not destination:
                        trip_data["destination"] = outbound["destination"]
                        trip_data["destination_name"] = outbound.get("destination_name", outbound["destination"])

                    round_trips.append(trip_data)

        # Sort results by total price (cheapest first)
        round_trips.sort(key=lambda x: x["total_price"])

        return round_trips

    def get_round_trips_preview(
        self,
        origin: str,
        min_days: int,
        max_days: int,
        return_from_same_airport: bool = True,
        outbound_weekdays: Optional[List[int]] = None,
        return_weekdays: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get preview of all destinations from origin with lowest round-trip prices.

        This method provides a summary view of all possible destinations, showing
        the minimum price for a round trip to each destination. Useful for displaying
        destination options before doing a full search.

        Args:
            origin (str): Origin airport code (e.g., "WAW" for Warsaw)
            min_days (int): Minimum trip duration in days
            max_days (int): Maximum trip duration in days
            return_from_same_airport (bool, optional): If True, return must be from same
                airport as outbound destination. Defaults to True.
            outbound_weekdays (Optional[List[int]], optional): Filter outbound flights by
                weekdays (0=Monday, 6=Sunday). Defaults to None.
            return_weekdays (Optional[List[int]], optional): Filter return flights by
                weekdays (0=Monday, 6=Sunday). Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of destinations with pricing info, sorted by price.
                Each dictionary contains:
                - destination: Destination airport code
                - destination_name: Destination airport name
                - min_total_price: Lowest total round trip price found
                - flight_count: Number of flights to this destination

        Example:
            >>> # Get preview of all destinations for 3-7 day trips
            >>> preview = search.get_round_trips_preview(
            ...     origin="WAW",
            ...     min_days=3,
            ...     max_days=7
            ... )
            >>> for dest in preview[:5]:  # Top 5 cheapest
            ...     print(f"{dest['destination_name']}: {dest['min_total_price']} PLN")
        """
        # Get all possible destinations from this origin using aggregation
        pipeline = [
            {"$match": {"origin": origin.upper()}},
            {"$group": {
                "_id": "$destination",
                "destination_name": {"$first": "$destination_name"},
                "flight_count": {"$sum": 1}
            }},
            {"$sort": {"_id": ASCENDING}}
        ]

        results = list(self.flights_collection.aggregate(pipeline))

        destinations = [
            {
                "code": r["_id"],
                "name": r["destination_name"],
                "flight_count": r["flight_count"]
            }
            for r in results
        ]

        preview_data = []

        # For each destination, find the cheapest valid round trip
        for dest in destinations:
            destination_code = dest["code"]

            # Get all outbound flights to this destination
            outbound_flights = list(self.flights_collection.find({
                "origin": origin.upper(),
                "destination": destination_code
            }))

            # Get return flights based on return_from_same_airport setting
            if return_from_same_airport:
                return_flights = list(self.flights_collection.find({
                    "origin": destination_code,
                    "destination": origin.upper()
                }))
            else:
                # Allow returns from any airport back to origin
                return_flights = list(self.flights_collection.find({
                    "destination": origin.upper()
                }))

            if not outbound_flights or not return_flights:
                continue  # Skip destinations without valid flights

            # Find the minimum price for this destination
            min_price = float('inf')

            for outbound in outbound_flights:
                outbound_date_str = outbound["departure_time"].split("T")[0]
                outbound_date = datetime.strptime(outbound_date_str, "%Y-%m-%d")

                # Apply weekday filter for outbound
                if outbound_weekdays is not None:
                    if outbound_date.weekday() not in outbound_weekdays:
                        continue

                for return_flight in return_flights:
                    return_date_str = return_flight["departure_time"].split("T")[0]
                    return_date = datetime.strptime(return_date_str, "%Y-%m-%d")

                    # Apply weekday filter for return
                    if return_weekdays is not None:
                        if return_date.weekday() not in return_weekdays:
                            continue

                    trip_duration = (return_date - outbound_date).days

                    # Check if this combination meets the duration requirement
                    if min_days <= trip_duration <= max_days:
                        total_price = outbound["current_price"] + return_flight["current_price"]
                        if total_price < min_price:
                            min_price = total_price

            # Add destination to preview if valid trips were found
            if min_price != float('inf'):
                preview_data.append({
                    "destination": destination_code,
                    "destination_name": dest["name"],
                    "min_total_price": round(min_price, 2),
                    "flight_count": dest["flight_count"]
                })

        # Sort by price (cheapest first)
        preview_data.sort(key=lambda x: x["min_total_price"])

        return preview_data

    def find_round_trips_batch(
        self,
        origins: List[str],
        destinations: List[str],
        min_days: int,
        max_days: int,
        passengers: int = 1,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        return_from_same_airport: bool = True,
        return_to_same_airport: bool = True,
        outbound_weekdays: Optional[List[int]] = None,
        return_weekdays: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all possible round trips from multiple origins to multiple destinations.

        This is an efficient batch search that processes all origin-destination combinations
        in a single operation. It's optimized for searching across many airports simultaneously.

        Args:
            origins (List[str]): List of origin airport codes (e.g., ["WAW", "WRO", "KRK"])

            destinations (List[str]): List of destination airport codes (e.g., ["BCN", "AGP", "VLC"])

            min_days (int): Minimum trip duration in days

            max_days (int): Maximum trip duration in days

            passengers (int, optional): Number of passengers. Defaults to 1.

            date_from (Optional[str], optional): Filter flights departing on or after this date.
                Format: YYYY-MM-DD. Defaults to None (no lower bound).

            date_to (Optional[str], optional): Filter flights departing on or before this date.
                Format: YYYY-MM-DD. Defaults to None (no upper bound).

            min_price (Optional[float], optional): Minimum total trip price filter.
                Filters out trips cheaper than this value. Defaults to None.

            max_price (Optional[float], optional): Maximum total trip price filter.
                Filters out trips more expensive than this value. Defaults to None.

            return_from_same_airport (bool, optional): If True, return flight must depart from
                the same airport where outbound landed. If False, can return from any airport
                in the selected destinations list. Defaults to True.

                Example when True: WAW→BCN outbound, BCN→WAW return
                Example when False: WAW→BCN outbound, VLC→WAW return (both in destinations list)

            return_to_same_airport (bool, optional): If True, return flight must land at the
                same airport where outbound departed from. If False, can land at any airport
                in the selected origins list. Defaults to True.

                Example when True: WAW→BCN outbound, BCN→WAW return
                Example when False: WAW→BCN outbound, BCN→KRK return (both in origins list)

                Note: This is useful when you want to fly from one city and return to another
                (e.g., fly from Warsaw, return to Krakow for a road trip).

            outbound_weekdays (Optional[List[int]], optional): Filter outbound flights by weekdays.
                0=Monday, 6=Sunday. Defaults to None (any day).

            return_weekdays (Optional[List[int]], optional): Filter return flights by weekdays.
                0=Monday, 6=Sunday. Defaults to None (any day).

        Returns:
            List[Dict[str, Any]]: List of round trip combinations, sorted by total_price.
                Each dictionary contains:
                - outbound: Dict with outbound flight details (includes origin/destination info)
                - return: Dict with return flight details (includes origin/destination info)
                - trip_duration_days: Number of days between flights
                - stay_duration: Total stay time from arrival to departure (format: "Xd Yh Zm")
                - total_price: Total cost for all passengers
                - price_per_person: Cost per passenger
                - passengers: Number of passengers
                - currency: Price currency

        Raises:
            TooManyFlightsError: If the search would exceed performance limits.

        Examples:
            >>> # Search from multiple Polish airports to Spanish destinations
            >>> trips = search.find_round_trips_batch(
            ...     origins=["WAW", "WRO", "KRK"],
            ...     destinations=["BCN", "AGP", "MAD", "VLC"],
            ...     min_days=3,
            ...     max_days=7,
            ...     passengers=2,
            ...     date_from="2024-06-01",
            ...     date_to="2024-08-31"
            ... )
            >>>
            >>> # Weekend getaway with flexible return airports
            >>> weekend_trips = search.find_round_trips_batch(
            ...     origins=["WAW"],
            ...     destinations=["BCN", "VLC", "AGP"],  # Any Spanish airport
            ...     min_days=2,
            ...     max_days=4,
            ...     passengers=1,
            ...     return_from_same_airport=False,  # Can return from different airport
            ...     outbound_weekdays=[4, 5],  # Friday or Saturday departure
            ...     return_weekdays=[0, 6],     # Monday or Sunday return
            ...     max_price=500
            ... )

        Notes:
            - All airport codes are automatically converted to uppercase
            - Results include full origin/destination info for both outbound and return flights
            - Date filters apply to both outbound and return flights
            - Price filters are applied after calculating total price for all passengers
        """
        # Normalize airport codes to uppercase
        origins_upper = [o.upper() for o in origins]
        destinations_upper = [d.upper() for d in destinations]

        # Build MongoDB query for outbound flights
        outbound_query = {
            "origin": {"$in": origins_upper},
            "destination": {"$in": destinations_upper}
        }

        # Build MongoDB query for return flights
        if return_from_same_airport:
            # Return must be from destination airports to origin airports (strict matching)
            return_query = {
                "origin": {"$in": destinations_upper},
                "destination": {"$in": origins_upper}
            }
        else:
            # Return can be from any destination airport to any origin airport
            # (still limited to selected destination countries)
            return_query = {
                "origin": {"$in": destinations_upper},
                "destination": {"$in": origins_upper}
            }

        # Add optional date filters to both queries
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            outbound_query["date_out"] = date_filter
            return_query["date_out"] = date_filter

        # Fetch all matching flights from database
        outbound_flights = list(self.flights_collection.find(outbound_query).sort("departure_time", ASCENDING))
        return_flights = list(self.flights_collection.find(return_query).sort("departure_time", ASCENDING))

        logger.info(f"Found {len(outbound_flights)} outbound flights and {len(return_flights)} return flights")

        # Validate performance constraints
        if len(outbound_flights) > self.MAX_FLIGHTS_PER_DIRECTION:
            raise TooManyFlightsError(
                f"Too many outbound flights ({len(outbound_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific airports, weekday filters). "
                f"Maximum allowed: {self.MAX_FLIGHTS_PER_DIRECTION}"
            )

        if len(return_flights) > self.MAX_FLIGHTS_PER_DIRECTION:
            raise TooManyFlightsError(
                f"Too many return flights ({len(return_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific airports, weekday filters). "
                f"Maximum allowed: {self.MAX_FLIGHTS_PER_DIRECTION}"
            )

        potential_combinations = len(outbound_flights) * len(return_flights)
        if potential_combinations > self.MAX_TOTAL_COMBINATIONS:
            raise TooManyFlightsError(
                f"Too many potential combinations ({potential_combinations:,} = {len(outbound_flights)} × {len(return_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific destination, weekday filters). "
                f"Maximum allowed: {self.MAX_TOTAL_COMBINATIONS:,}"
            )

        # Main search logic: find all valid combinations
        round_trips = []

        for outbound in outbound_flights:
            # Extract date from date_out field (handle ISO datetime format YYYY-MM-DDTHH:MM:SS.mmm)
            outbound_date_str = outbound["date_out"]
            outbound_date = datetime.strptime(outbound_date_str.split('T')[0], "%Y-%m-%d")

            # Apply outbound weekday filter
            if outbound_weekdays is not None:
                if outbound_date.weekday() not in outbound_weekdays:
                    continue

            for return_flight in return_flights:
                # Validate airport matching when return_from_same_airport is True
                if return_from_same_airport:
                    if return_flight["origin"] != outbound["destination"]:
                        continue  # Return must be from where we landed

                # Validate airport matching when return_to_same_airport is True
                if return_to_same_airport:
                    if return_flight["destination"] != outbound["origin"]:
                        continue  # Return must land where we departed from

                # Extract return date
                return_date_str = return_flight["date_out"]
                return_date = datetime.strptime(return_date_str.split('T')[0], "%Y-%m-%d")

                # Apply return weekday filter
                if return_weekdays is not None:
                    if return_date.weekday() not in return_weekdays:
                        continue

                # Calculate trip duration
                trip_duration = (return_date - outbound_date).days

                # Check if duration is within specified range
                if min_days <= trip_duration <= max_days:
                    # Calculate total price
                    total_price = (outbound["current_price"] + return_flight["current_price"]) * passengers

                    # Apply price filters
                    if min_price is not None and total_price < min_price:
                        continue
                    if max_price is not None and total_price > max_price:
                        continue

                    # Calculate stay duration (from arrival at destination to departure back)
                    # Parse ISO format timestamps: YYYY-MM-DDTHH:MM:SS.mmm or YYYY-MM-DDTHH:MM:SS
                    outbound_arrival = datetime.fromisoformat(outbound["arrival_time"].replace("Z", "+00:00"))
                    return_departure = datetime.fromisoformat(return_flight["departure_time"].replace("Z", "+00:00"))
                    stay_duration_delta = return_departure - outbound_arrival

                    # Format as days, hours, minutes
                    stay_days = stay_duration_delta.days
                    stay_seconds = stay_duration_delta.seconds
                    stay_hours = stay_seconds // 3600
                    stay_minutes = (stay_seconds % 3600) // 60
                    stay_duration_formatted = f"{stay_days}d {stay_hours}h {stay_minutes}m"

                    # Build result structure
                    trip_data = {
                        "outbound": {
                            "flight_id": outbound["flight_id"],
                            "origin": outbound["origin"],
                            "origin_name": outbound.get("origin_name", outbound["origin"]),
                            "destination": outbound["destination"],
                            "destination_name": outbound.get("destination_name", outbound["destination"]),
                            "date_out": outbound_date_str,
                            "departure_time": outbound["departure_time"],
                            "arrival_time": outbound["arrival_time"],
                            "duration": outbound["duration"],
                            "current_price": outbound["current_price"]
                        },
                        "return": {
                            "flight_id": return_flight["flight_id"],
                            "origin": return_flight["origin"],
                            "origin_name": return_flight.get("origin_name", return_flight["origin"]),
                            "destination": return_flight["destination"],
                            "destination_name": return_flight.get("destination_name", return_flight["destination"]),
                            "date_out": return_date_str,
                            "departure_time": return_flight["departure_time"],
                            "arrival_time": return_flight["arrival_time"],
                            "duration": return_flight["duration"],
                            "current_price": return_flight["current_price"]
                        },
                        "trip_duration_days": trip_duration,
                        "stay_duration": stay_duration_formatted,
                        "total_price": round(total_price, 2),
                        "price_per_person": round(total_price / passengers, 2) if passengers > 0 else round(total_price, 2),
                        "passengers": passengers,
                        "currency": outbound["currency"]
                    }

                    round_trips.append(trip_data)

        # Sort results by total price (cheapest first)
        round_trips.sort(key=lambda x: x["total_price"])

        logger.info(f"Found {len(round_trips)} valid round trips")

        return round_trips

    def get_all_two_way_routes(self, origin: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all possible two-way routes from Polish airports with coordinates and prices.

        This method finds routes that have both outbound and return flights available,
        making them suitable for round trips. Useful for map visualizations and route displays.

        Args:
            origin (Optional[str], optional): Filter to show only routes from specific origin
                airport. If None, shows routes from all Polish airports. Defaults to None.

            limit (int, optional): Maximum number of route pairs to return. Defaults to 100.

        Returns:
            List[Dict[str, Any]]: List of two-way routes with pricing and coordinates.
                Each dictionary contains:
                - origin: Origin airport code
                - origin_name: Origin airport name
                - destination: Destination airport code
                - destination_name: Destination airport name
                - outbound_flights: Number of outbound flights available
                - cheapest_price: Minimum round trip price (for 1 person)
                - currency: Price currency
                - origin_coordinates: Dict with latitude/longitude (if available)
                - destination_coordinates: Dict with latitude/longitude (if available)

        Example:
            >>> # Get routes from Warsaw with coordinates for map display
            >>> routes = search.get_all_two_way_routes(origin="WAW", limit=20)
            >>> for route in routes:
            ...     print(f"{route['origin']} → {route['destination']}: "
            ...           f"{route['cheapest_price']} {route['currency']}")
            ...     if 'origin_coordinates' in route:
            ...         print(f"  Origin: {route['origin_coordinates']}")
            ...         print(f"  Dest: {route['destination_coordinates']}")

        Notes:
            - Only returns routes that have both outbound and return flights
            - Coordinates are loaded from the Ryanair database if available
            - If coordinates cannot be loaded, routes are still returned without them
            - Results are sorted by outbound price (cheapest first)
        """
        # Attempt to load airport coordinates for map visualization
        try:
            from scrapper.database_population import load_from_mongodb
            from config import settings

            # Load Ryanair database which contains airport coordinates
            ryanair_db = load_from_mongodb("ryanair", settings.mongo_uri)

            # Create coordinate lookup dictionary
            airport_coords = {}
            if ryanair_db:
                for airport in ryanair_db.get_all_airports():
                    if airport.latitude is not None and airport.longitude is not None:
                        airport_coords[airport.code] = {
                            "latitude": airport.latitude,
                            "longitude": airport.longitude,
                            "name": airport.name
                        }
        except Exception as e:
            logger.warning(f"Failed to load airport coordinates: {e}")
            airport_coords = {}

        # Build match query based on origin parameter
        if origin:
            match_query = {"origin": origin.upper()}
        else:
            # Default to Polish airports
            match_query = {"origin": {"$in": POLISH_AIRPORTS}}

        # Aggregate unique routes with price information
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": {
                    "origin": "$origin",
                    "destination": "$destination"
                },
                "origin_name": {"$first": "$origin_name"},
                "destination_name": {"$first": "$destination_name"},
                "min_outbound_price": {"$min": "$current_price"},
                "flight_count": {"$sum": 1},
                "currency": {"$first": "$currency"}
            }},
            {"$sort": {"min_outbound_price": ASCENDING}}
        ]

        results = list(self.flights_collection.aggregate(pipeline))

        # Filter to only include routes with return flights
        two_way_routes = []

        for route in results:
            origin_code = route["_id"]["origin"]
            destination = route["_id"]["destination"]

            # Check if return flight exists for this route
            return_flight = self.flights_collection.find_one(
                {
                    "origin": destination,
                    "destination": origin_code
                },
                sort=[("current_price", ASCENDING)]
            )

            if return_flight:
                # Calculate cheapest round-trip price (for 1 person)
                cheapest_price = route["min_outbound_price"] + return_flight["current_price"]

                route_data = {
                    "origin": origin_code,
                    "origin_name": route["origin_name"],
                    "destination": destination,
                    "destination_name": route["destination_name"],
                    "outbound_flights": route["flight_count"],
                    "cheapest_price": round(cheapest_price, 2),
                    "currency": route["currency"]
                }

                # Add coordinates if available
                if origin_code in airport_coords:
                    route_data["origin_coordinates"] = airport_coords[origin_code]

                if destination in airport_coords:
                    route_data["destination_coordinates"] = airport_coords[destination]

                two_way_routes.append(route_data)

                # Stop when limit is reached
                if len(two_way_routes) >= limit:
                    break

        return two_way_routes

    def get_one_way_route_examples(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get example one-way routes from Polish airports for price displays.

        This method provides sample routes useful for displaying price ranges and
        available destinations. Returns the cheapest one-way routes.

        Args:
            limit (int, optional): Maximum number of routes to return. Defaults to 50.

        Returns:
            List[Dict[str, Any]]: List of one-way routes sorted by price.
                Each dictionary contains:
                - origin: Origin airport code
                - origin_name: Origin airport name
                - destination: Destination airport code
                - destination_name: Destination airport name
                - min_price: Lowest one-way price
                - avg_price: Average one-way price
                - flight_count: Number of flights on this route
                - currency: Price currency

        Example:
            >>> # Get cheapest routes for homepage display
            >>> routes = search.get_one_way_route_examples(limit=10)
            >>> for route in routes:
            ...     print(f"{route['origin_name']} → {route['destination_name']}")
            ...     print(f"  From: {route['min_price']} {route['currency']}")
            ...     print(f"  Avg: {route['avg_price']} {route['currency']}")

        Notes:
            - Only includes routes from Polish airports
            - Results are sorted by minimum price (cheapest first)
            - Includes both min and average prices for each route
        """
        # Aggregate routes with price statistics
        pipeline = [
            {"$match": {"origin": {"$in": POLISH_AIRPORTS}}},
            {"$group": {
                "_id": {
                    "origin": "$origin",
                    "destination": "$destination"
                },
                "origin_name": {"$first": "$origin_name"},
                "destination_name": {"$first": "$destination_name"},
                "min_price": {"$min": "$current_price"},
                "avg_price": {"$avg": "$current_price"},
                "flight_count": {"$sum": 1},
                "currency": {"$first": "$currency"}
            }},
            {"$sort": {"min_price": ASCENDING}},
            {"$limit": limit}
        ]

        results = list(self.flights_collection.aggregate(pipeline))

        routes = [
            {
                "origin": r["_id"]["origin"],
                "origin_name": r["origin_name"],
                "destination": r["_id"]["destination"],
                "destination_name": r["destination_name"],
                "min_price": round(r["min_price"], 2),
                "avg_price": round(r["avg_price"], 2),
                "flight_count": r["flight_count"],
                "currency": r["currency"]
            }
            for r in results
        ]

        return routes
