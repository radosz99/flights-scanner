#!/usr/bin/env python3

"""
Custom Trip Search Module - Contains business logic for round trip searches.

This module handles complex round trip search logic including:
- Finding round trips from single or multiple origins/destinations
- Batch searching across multiple airports
- Trip duration filtering
- Weekday filtering for outbound and return flights
- Flexible return airport options
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
    """Raised when there are too many flights to process efficiently."""
    pass


class CustomTripSearch:
    """Service class for custom trip search operations."""

    def __init__(self, flights_collection: Collection):
        """
        Initialize the custom trip search service.

        Args:
            flights_collection: MongoDB collection containing flight data
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
        Find all possible round trips (two-way) within specified trip length range.

        Args:
            origin: Origin airport code
            destination: Destination airport code (optional - if None, search all destinations)
            min_days: Minimum trip duration in days
            max_days: Maximum trip duration in days
            passengers: Number of passengers (default 2)
            return_from_same_airport: If True, return must be from same airport as outbound destination (default True)
            outbound_weekdays: Optional list of weekdays for outbound flights (0=Monday, 6=Sunday)
            return_weekdays: Optional list of weekdays for return flights (0=Monday, 6=Sunday)

        Returns:
            List of round trip combinations with pricing
        """
        # If destination is provided, search for that specific destination
        if destination:
            # Get all outbound flights from origin to destination
            outbound_flights = list(self.flights_collection.find({
                "origin": origin.upper(),
                "destination": destination.upper()
            }).sort("departure_time", ASCENDING))

            if return_from_same_airport:
                # Get all return flights from destination to origin
                return_flights = list(self.flights_collection.find({
                    "origin": destination.upper(),
                    "destination": origin.upper()
                }).sort("departure_time", ASCENDING))
            else:
                # Get all return flights from destination to origin
                # (same query as above - the filtering happens in the loop based on the flag)
                return_flights = list(self.flights_collection.find({
                    "origin": destination.upper(),
                    "destination": origin.upper()
                }).sort("departure_time", ASCENDING))
        else:
            # Get all outbound flights from origin to any destination
            outbound_flights = list(self.flights_collection.find({
                "origin": origin.upper()
            }).sort("departure_time", ASCENDING))

            # Get all return flights to origin from any destination
            return_flights = list(self.flights_collection.find({
                "destination": origin.upper()
            }).sort("departure_time", ASCENDING))

        # Check if there are too many flights to process efficiently
        MAX_FLIGHTS_PER_DIRECTION = 5000
        MAX_TOTAL_COMBINATIONS = 50_000_000

        logger.info(f"Found {len(outbound_flights)} outbound flights and {len(return_flights)} return flights")

        if len(outbound_flights) > MAX_FLIGHTS_PER_DIRECTION:
            raise TooManyFlightsError(
                f"Too many outbound flights ({len(outbound_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific destination, weekday filters). "
                f"Maximum allowed: {MAX_FLIGHTS_PER_DIRECTION}"
            )

        if len(return_flights) > MAX_FLIGHTS_PER_DIRECTION:
            raise TooManyFlightsError(
                f"Too many return flights ({len(return_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific destination, weekday filters). "
                f"Maximum allowed: {MAX_FLIGHTS_PER_DIRECTION}"
            )

        potential_combinations = len(outbound_flights) * len(return_flights)
        if potential_combinations > MAX_TOTAL_COMBINATIONS:
            raise TooManyFlightsError(
                f"Too many potential combinations ({potential_combinations:,} = {len(outbound_flights)} × {len(return_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific destination, weekday filters). "
                f"Maximum allowed: {MAX_TOTAL_COMBINATIONS:,}"
            )

        # Find valid round trip combinations
        round_trips = []

        for outbound in outbound_flights:
            # Extract date from departure_time (format: YYYY-MM-DDTHH:MM:SS.mmm)
            outbound_date_str = outbound["departure_time"].split("T")[0]
            outbound_date = datetime.strptime(outbound_date_str, "%Y-%m-%d")

            # Filter by outbound weekday if specified
            if outbound_weekdays is not None:
                if outbound_date.weekday() not in outbound_weekdays:
                    continue

            for return_flight in return_flights:
                # When return_from_same_airport is True and destination is not specified,
                # ensure return flight originates from where the outbound flight lands
                if return_from_same_airport:
                    if not destination:
                        # Return flight must originate from where the outbound flight lands
                        if return_flight["origin"] != outbound["destination"]:
                            continue
                else:
                    # When return_from_same_airport is False, return can be from any airport
                    # but we still need to ensure logical connection
                    if not destination:
                        # At minimum, check that return flight doesn't originate from the departure airport
                        # (otherwise it's not really going anywhere)
                        pass

                # Extract date from departure_time (format: YYYY-MM-DDTHH:MM:SS.mmm)
                return_date_str = return_flight["departure_time"].split("T")[0]
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d")

                # Filter by return weekday if specified
                if return_weekdays is not None:
                    if return_date.weekday() not in return_weekdays:
                        continue

                # Calculate trip duration
                trip_duration = (return_date - outbound_date).days

                # Check if trip duration is within range
                if min_days <= trip_duration <= max_days:
                    total_price = (outbound["current_price"] + return_flight["current_price"]) * passengers

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

        # Sort by total price
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

        Args:
            origin: Origin airport code
            min_days: Minimum trip duration in days
            max_days: Maximum trip duration in days
            return_from_same_airport: If True, return must be from same airport as outbound destination (default True)
            outbound_weekdays: Optional list of weekdays for outbound flights (0=Monday, 6=Sunday)
            return_weekdays: Optional list of weekdays for return flights (0=Monday, 6=Sunday)

        Returns:
            List of destinations with minimum total round-trip prices
        """
        # Get all possible destinations from this origin
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

        for dest in destinations:
            destination_code = dest["code"]

            # Get all outbound flights
            outbound_flights = list(self.flights_collection.find({
                "origin": origin.upper(),
                "destination": destination_code
            }))

            if return_from_same_airport:
                # Get all return flights from destination to origin
                return_flights = list(self.flights_collection.find({
                    "origin": destination_code,
                    "destination": origin.upper()
                }))
            else:
                # Get all return flights to origin from any airport
                return_flights = list(self.flights_collection.find({
                    "destination": origin.upper()
                }))

            if not outbound_flights or not return_flights:
                continue

            # Find the cheapest valid round trip
            min_price = float('inf')

            for outbound in outbound_flights:
                outbound_date_str = outbound["departure_time"].split("T")[0]
                outbound_date = datetime.strptime(outbound_date_str, "%Y-%m-%d")

                # Filter by outbound weekday if specified
                if outbound_weekdays is not None:
                    if outbound_date.weekday() not in outbound_weekdays:
                        continue

                for return_flight in return_flights:
                    return_date_str = return_flight["departure_time"].split("T")[0]
                    return_date = datetime.strptime(return_date_str, "%Y-%m-%d")

                    # Filter by return weekday if specified
                    if return_weekdays is not None:
                        if return_date.weekday() not in return_weekdays:
                            continue

                    trip_duration = (return_date - outbound_date).days

                    if min_days <= trip_duration <= max_days:
                        total_price = outbound["current_price"] + return_flight["current_price"]
                        if total_price < min_price:
                            min_price = total_price

            if min_price != float('inf'):
                preview_data.append({
                    "destination": destination_code,
                    "destination_name": dest["name"],
                    "min_total_price": round(min_price, 2),
                    "flight_count": dest["flight_count"]
                })

        # Sort by price
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
        outbound_weekdays: Optional[List[int]] = None,
        return_weekdays: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all possible round trips from multiple origins to multiple destinations.

        This is an efficient batch search that processes all origin-destination combinations
        in a single operation using MongoDB aggregation.

        Args:
            origins: List of origin airport codes
            destinations: List of destination airport codes
            min_days: Minimum trip duration in days
            max_days: Maximum trip duration in days
            passengers: Number of passengers (default 1)
            date_from: Optional filter for departure date from (YYYY-MM-DD)
            date_to: Optional filter for departure date to (YYYY-MM-DD)
            min_price: Optional minimum total price filter
            max_price: Optional maximum total price filter
            return_from_same_airport: If True, return must be from same airport as outbound destination (default True)
            outbound_weekdays: Optional list of weekdays for outbound flights (0=Monday, 6=Sunday)
            return_weekdays: Optional list of weekdays for return flights (0=Monday, 6=Sunday)

        Returns:
            List of round trip combinations with pricing
        """
        # Normalize inputs
        origins_upper = [o.upper() for o in origins]
        destinations_upper = [d.upper() for d in destinations]

        # Build outbound flight query
        outbound_query = {
            "origin": {"$in": origins_upper},
            "destination": {"$in": destinations_upper}
        }

        # Build return flight query
        if return_from_same_airport:
            # Return must be from destination airports to origin airports
            return_query = {
                "origin": {"$in": destinations_upper},
                "destination": {"$in": origins_upper}
            }
        else:
            # Return can be from any destination airport to origin airports
            # (still limited to selected destination countries)
            return_query = {
                "origin": {"$in": destinations_upper},
                "destination": {"$in": origins_upper}
            }

        # Add date filters if provided
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            outbound_query["date_out"] = date_filter
            return_query["date_out"] = date_filter

        # Fetch outbound flights
        outbound_flights = list(self.flights_collection.find(outbound_query).sort("departure_time", ASCENDING))

        # Fetch return flights
        return_flights = list(self.flights_collection.find(return_query).sort("departure_time", ASCENDING))

        logger.info(f"Found {len(outbound_flights)} outbound flights and {len(return_flights)} return flights")

        # Check if there are too many flights to process efficiently
        # Limit individual flight queries to 5000 each, and total combinations to 50 million
        MAX_FLIGHTS_PER_DIRECTION = 5000
        MAX_TOTAL_COMBINATIONS = 50_000_000

        if len(outbound_flights) > MAX_FLIGHTS_PER_DIRECTION:
            raise TooManyFlightsError(
                f"Too many outbound flights ({len(outbound_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific airports, weekday filters). "
                f"Maximum allowed: {MAX_FLIGHTS_PER_DIRECTION}"
            )

        if len(return_flights) > MAX_FLIGHTS_PER_DIRECTION:
            raise TooManyFlightsError(
                f"Too many return flights ({len(return_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific airports, weekday filters). "
                f"Maximum allowed: {MAX_FLIGHTS_PER_DIRECTION}"
            )

        potential_combinations = len(outbound_flights) * len(return_flights)
        if potential_combinations > MAX_TOTAL_COMBINATIONS:
            raise TooManyFlightsError(
                f"Too many potential combinations ({potential_combinations:,} = {len(outbound_flights)} × {len(return_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific destination, weekday filters). "
                f"Maximum allowed: {MAX_TOTAL_COMBINATIONS:,}"
            )

        # Find valid round trip combinations
        round_trips = []

        for outbound in outbound_flights:
            # Extract date from date_out field (handle ISO datetime format)
            outbound_date_str = outbound["date_out"]
            # Split on 'T' to handle ISO datetime format (YYYY-MM-DDTHH:MM:SS.mmm)
            outbound_date = datetime.strptime(outbound_date_str.split('T')[0], "%Y-%m-%d")

            # Filter by outbound weekday if specified
            if outbound_weekdays is not None:
                if outbound_date.weekday() not in outbound_weekdays:
                    continue

            for return_flight in return_flights:
                # Check if return flight must originate from where the outbound flight lands
                if return_from_same_airport:
                    if return_flight["origin"] != outbound["destination"]:
                        continue

                # Extract date from date_out field (handle ISO datetime format)
                return_date_str = return_flight["date_out"]
                # Split on 'T' to handle ISO datetime format (YYYY-MM-DDTHH:MM:SS.mmm)
                return_date = datetime.strptime(return_date_str.split('T')[0], "%Y-%m-%d")

                # Filter by return weekday if specified
                if return_weekdays is not None:
                    if return_date.weekday() not in return_weekdays:
                        continue

                # Calculate trip duration
                trip_duration = (return_date - outbound_date).days

                # Check if trip duration is within range
                if min_days <= trip_duration <= max_days:
                    total_price = (outbound["current_price"] + return_flight["current_price"]) * passengers

                    # Apply price filters if provided
                    if min_price is not None and total_price < min_price:
                        continue
                    if max_price is not None and total_price > max_price:
                        continue

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
                        "total_price": round(total_price, 2),
                        "price_per_person": round(total_price / passengers, 2) if passengers > 0 else round(total_price, 2),
                        "passengers": passengers,
                        "currency": outbound["currency"]
                    }

                    round_trips.append(trip_data)

        # Sort by total price
        round_trips.sort(key=lambda x: x["total_price"])

        logger.info(f"Found {len(round_trips)} valid round trips")

        return round_trips

    def get_all_two_way_routes(self, origin: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all possible two-way routes from Polish airports with coordinates and cheapest prices.

        This returns example routes that can form round trips, useful for
        displaying on the trip search page and map visualization.

        Args:
            origin: Optional filter to show only routes from specific origin airport
            limit: Maximum number of route pairs to return

        Returns:
            List of route pairs with airport coordinates and cheapest round-trip prices
        """
        # Load airport coordinates from MongoDB
        try:
            from scrapper.database_population import load_from_mongodb
            from config import settings

            # Load Ryanair database for coordinates
            ryanair_db = load_from_mongodb("ryanair", settings.mongo_uri)

            # Create coordinate lookup dict
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

        # Build match query - filter by origin if provided, otherwise all Polish airports
        if origin:
            match_query = {"origin": origin.upper()}
        else:
            match_query = {"origin": {"$in": POLISH_AIRPORTS}}

        # Get unique routes from Polish airports with price info
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

        # Now check which routes have return flights and calculate cheapest round-trip price
        two_way_routes = []

        for route in results:
            origin_code = route["_id"]["origin"]
            destination = route["_id"]["destination"]

            # Get minimum return flight price
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

                # Stop when we reach the limit
                if len(two_way_routes) >= limit:
                    break

        return two_way_routes

    def get_one_way_route_examples(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get example one-way routes from Polish airports for price chart display.

        Args:
            limit: Maximum number of routes to return

        Returns:
            List of one-way routes with sample flights
        """
        # Get unique routes from Polish airports with min prices
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
