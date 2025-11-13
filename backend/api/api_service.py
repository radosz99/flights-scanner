#!/usr/bin/env python3

"""
API Service Layer - Contains business logic for API endpoints.

This service layer separates business logic from API endpoint handlers,
making the code more testable and maintainable.
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from typing import Optional, List, Dict, Any, Tuple
from datetime import date
from loguru import logger
import sys
import os

# Add parent directory to path to import constants
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from constants import POLISH_AIRPORTS

# Import custom search functionality
from api.custom_search import CustomTripSearch, TooManyFlightsError


class APIService:
    """Service class containing business logic for API operations."""

    def __init__(self, mongo_client: MongoClient, database_name: str):
        """
        Initialize the API service.

        Args:
            mongo_client: MongoDB client instance
            database_name: Name of the MongoDB database
        """
        self.client = mongo_client
        self.db = self.client[database_name]
        self.flights_collection = self.db["ryanair_flights"]
        self.scan_iterations_collection = self.db["scan_iterations"]

        # Initialize custom trip search service
        self.custom_search = CustomTripSearch(self.flights_collection)

    def get_flights(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        currency: Optional[str] = None,
        sort_by: str = "price",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Query flights with various filters and sorting options.

        Args:
            origin: Filter by origin airport code
            destination: Filter by destination airport code
            date_from: Filter flights departing from this date
            date_to: Filter flights departing until this date
            min_price: Minimum price filter
            max_price: Maximum price filter
            currency: Filter by currency code
            sort_by: Sort results by field (price, date, duration, price_desc)
            page: Page number
            page_size: Number of results per page

        Returns:
            Dict containing total count, page info, and list of flights
        """
        # Build MongoDB query
        query = {}

        if origin:
            query["origin"] = origin.upper()

        if destination:
            query["destination"] = destination.upper()

        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from.strftime("%Y-%m-%d")
            if date_to:
                date_query["$lte"] = date_to.strftime("%Y-%m-%d")
            query["date_out"] = date_query

        if min_price is not None or max_price is not None:
            price_query = {}
            if min_price is not None:
                price_query["$gte"] = min_price
            if max_price is not None:
                price_query["$lte"] = max_price
            query["current_price"] = price_query

        if currency:
            query["currency"] = currency.upper()

        # Determine sort order
        sort_field = "current_price"
        sort_direction = ASCENDING

        if sort_by == "price":
            sort_field = "current_price"
            sort_direction = ASCENDING
        elif sort_by == "price_desc":
            sort_field = "current_price"
            sort_direction = DESCENDING
        elif sort_by == "date":
            sort_field = "date_out"
            sort_direction = ASCENDING
        elif sort_by == "duration":
            sort_field = "duration"
            sort_direction = ASCENDING

        # Count total results
        total = self.flights_collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * page_size

        # Execute query
        cursor = self.flights_collection.find(query).sort(sort_field, sort_direction).skip(skip).limit(page_size)

        # Convert to list and remove MongoDB _id
        flights = []
        for doc in cursor:
            doc.pop("_id", None)
            flights.append(doc)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "flights": flights
        }

    def get_flight_by_id(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific flight.

        Args:
            flight_id: The flight ID to retrieve

        Returns:
            Flight data dict or None if not found
        """
        flight = self.flights_collection.find_one({"flight_id": flight_id})

        if not flight:
            return None

        flight.pop("_id", None)
        return flight

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics including total flights, price changes, and price ranges.

        Returns:
            Dict containing statistics data
        """
        # Total flights
        total_flights = self.flights_collection.count_documents({})

        # Flights with price changes
        flights_with_changes = self.flights_collection.count_documents({
            "price_history.1": {"$exists": True}
        })

        # Unique origins and destinations
        unique_origins = len(self.flights_collection.distinct("origin"))
        unique_destinations = len(self.flights_collection.distinct("destination"))

        # Cheapest flight
        cheapest = self.flights_collection.find_one(sort=[("current_price", ASCENDING)])
        cheapest_flight = None
        if cheapest:
            cheapest_flight = {
                "flight_id": cheapest.get("flight_id"),
                "route": f"{cheapest.get('origin')} → {cheapest.get('destination')}",
                "price": cheapest.get("current_price"),
                "currency": cheapest.get("currency"),
                "date": cheapest.get("date_out")
            }

        # Most expensive flight
        most_expensive = self.flights_collection.find_one(sort=[("current_price", DESCENDING)])
        most_expensive_flight = None
        if most_expensive:
            most_expensive_flight = {
                "flight_id": most_expensive.get("flight_id"),
                "route": f"{most_expensive.get('origin')} → {most_expensive.get('destination')}",
                "price": most_expensive.get("current_price"),
                "currency": most_expensive.get("currency"),
                "date": most_expensive.get("date_out")
            }

        # Average price
        pipeline = [
            {"$group": {"_id": None, "avg_price": {"$avg": "$current_price"}}}
        ]
        avg_result = list(self.flights_collection.aggregate(pipeline))
        average_price = avg_result[0]["avg_price"] if avg_result and avg_result[0].get("avg_price") is not None else 0.0

        return {
            "total_flights": total_flights,
            "flights_with_price_changes": flights_with_changes,
            "unique_origins": unique_origins,
            "unique_destinations": unique_destinations,
            "cheapest_flight": cheapest_flight,
            "most_expensive_flight": most_expensive_flight,
            "average_price": round(average_price, 2)
        }

    def get_origins(self) -> List[Dict[str, Any]]:
        """
        Get list of all available origin airports with flight counts.

        Returns:
            List of origin airports with codes, names, and flight counts
        """
        pipeline = [
            {"$group": {
                "_id": "$origin",
                "origin_name": {"$first": "$origin_name"},
                "flight_count": {"$sum": 1}
            }},
            {"$sort": {"_id": ASCENDING}}
        ]

        results = list(self.flights_collection.aggregate(pipeline))

        origins = [
            {
                "code": r["_id"],
                "name": r["origin_name"],
                "flight_count": r["flight_count"]
            }
            for r in results
        ]

        return origins

    def get_polish_origins(self) -> List[Dict[str, Any]]:
        """
        Get list of all available Polish origin airports with flight counts.

        Returns:
            List of Polish origin airports with codes, names, and flight counts
        """
        pipeline = [
            {"$match": {"origin": {"$in": POLISH_AIRPORTS}}},
            {"$group": {
                "_id": "$origin",
                "origin_name": {"$first": "$origin_name"},
                "flight_count": {"$sum": 1}
            }},
            {"$sort": {"_id": ASCENDING}}
        ]

        results = list(self.flights_collection.aggregate(pipeline))

        origins = [
            {
                "code": r["_id"],
                "name": r["origin_name"],
                "flight_count": r["flight_count"]
            }
            for r in results
        ]

        return origins

    def get_destinations(self) -> List[Dict[str, Any]]:
        """
        Get list of all available destination airports with flight counts.

        Returns:
            List of destination airports with codes, names, and flight counts
        """
        pipeline = [
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

        return destinations

    def get_routes(self, origin: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of all available routes with flight counts and price info.

        Args:
            origin: Optional filter to show only routes from specific origin

        Returns:
            List of routes with origin, destination, counts, and price statistics
        """
        match_stage = {}
        if origin:
            match_stage = {"$match": {"origin": origin.upper()}}

        pipeline = [
            match_stage,
            {"$group": {
                "_id": {
                    "origin": "$origin",
                    "destination": "$destination"
                },
                "origin_name": {"$first": "$origin_name"},
                "destination_name": {"$first": "$destination_name"},
                "flight_count": {"$sum": 1},
                "min_price": {"$min": "$current_price"},
                "max_price": {"$max": "$current_price"},
                "avg_price": {"$avg": "$current_price"},
                "currency": {"$first": "$currency"}
            }},
            {"$sort": {"_id.origin": ASCENDING, "_id.destination": ASCENDING}}
        ]

        # Remove empty match stage
        if not match_stage:
            pipeline = pipeline[1:]

        results = list(self.flights_collection.aggregate(pipeline))

        routes = [
            {
                "origin": r["_id"]["origin"],
                "origin_name": r["origin_name"],
                "destination": r["_id"]["destination"],
                "destination_name": r["destination_name"],
                "flight_count": r["flight_count"],
                "min_price": round(r["min_price"], 2),
                "max_price": round(r["max_price"], 2),
                "avg_price": round(r["avg_price"], 2),
                "currency": r["currency"]
            }
            for r in results
        ]

        return routes

    def get_scans(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get scan iteration history.

        Args:
            limit: Number of scans to return

        Returns:
            List of scan iterations
        """
        cursor = self.scan_iterations_collection.find().sort("start_time", DESCENDING).limit(limit)

        scans = []
        for doc in cursor:
            doc.pop("_id", None)
            doc.pop("date_ranges", None)  # Remove detailed date ranges
            doc.pop("config", None)  # Remove config details
            scans.append(doc)

        return scans

    def get_latest_scan(self) -> Optional[Dict[str, Any]]:
        """
        Get details of the most recent scan iteration.

        Returns:
            Latest scan data or None if no scans found
        """
        scan = self.scan_iterations_collection.find_one(sort=[("start_time", DESCENDING)])

        if not scan:
            return None

        scan.pop("_id", None)
        scan.pop("date_ranges", None)
        scan.pop("config", None)

        return scan

    def get_price_chart(self, origin: str, destination: str) -> Optional[Dict[str, Any]]:
        """
        Get price chart data for a specific route over the full date range.

        Args:
            origin: Origin airport code
            destination: Destination airport code

        Returns:
            Dict containing price chart data or None if no flights found
        """
        query = {
            "origin": origin.upper(),
            "destination": destination.upper()
        }

        # Aggregate flights by date to get price statistics
        # Extract date from departure_time (format: YYYY-MM-DDTHH:MM:SS.mmm)
        pipeline = [
            {"$match": query},
            {"$addFields": {
                "departure_date": {"$substr": ["$departure_time", 0, 10]}
            }},
            {"$group": {
                "_id": "$departure_date",
                "min_price": {"$min": "$current_price"},
                "max_price": {"$max": "$current_price"},
                "avg_price": {"$avg": "$current_price"},
                "current_price": {"$first": "$current_price"},  # Sample current price
                "flight_count": {"$sum": 1},
                "currency": {"$first": "$currency"}
            }},
            {"$sort": {"_id": ASCENDING}}
        ]

        results = list(self.flights_collection.aggregate(pipeline))

        if not results:
            return None

        chart_data = [
            {
                "date": r["_id"],
                "min_price": round(r["min_price"], 2),
                "max_price": round(r["max_price"], 2),
                "avg_price": round(r["avg_price"], 2),
                "current_price": round(r["current_price"], 2),
                "flight_count": r["flight_count"],
                "currency": r["currency"]
            }
            for r in results
        ]

        return {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "data": chart_data,
            "total_dates": len(chart_data)
        }

    def get_destinations_from_origin(self, origin: str) -> List[Dict[str, Any]]:
        """
        Get list of all available destinations from a specific origin.

        Args:
            origin: Origin airport code

        Returns:
            List of destination airports with codes, names, and flight counts
        """
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

        return destinations

    def get_flight_price_history(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """
        Get price history for a specific flight across multiple scans.

        Args:
            flight_id: Unique flight identifier

        Returns:
            Dict containing flight info and price history, or None if not found
        """
        flight = self.flights_collection.find_one({"flight_id": flight_id})

        if not flight:
            return None

        # Extract relevant flight info
        price_history = flight.get("price_history", [])

        # Format timestamps for frontend
        formatted_history = []
        for entry in price_history:
            formatted_history.append({
                "price": round(entry["price"], 2),
                "timestamp": entry["timestamp"].isoformat() if hasattr(entry["timestamp"], "isoformat") else str(entry["timestamp"]),
                "change": round(entry.get("change", 0), 2)
            })

        return {
            "flight_id": flight["flight_id"],
            "flight_number": flight.get("flight_number"),
            "origin": flight["origin"],
            "origin_name": flight.get("origin_name"),
            "destination": flight["destination"],
            "destination_name": flight.get("destination_name"),
            "date_out": flight.get("date_out"),
            "departure_time": flight.get("departure_time"),
            "arrival_time": flight.get("arrival_time"),
            "duration": flight.get("duration"),
            "current_price": round(flight["current_price"], 2),
            "currency": flight.get("currency"),
            "first_seen": flight.get("first_seen").isoformat() if flight.get("first_seen") and hasattr(flight.get("first_seen"), "isoformat") else None,
            "last_seen": flight.get("last_seen").isoformat() if flight.get("last_seen") and hasattr(flight.get("last_seen"), "isoformat") else None,
            "scan_count": flight.get("scan_count", 0),
            "price_history": formatted_history
        }

    def get_flights_for_date(self, origin: str, destination: str, date: str) -> List[Dict[str, Any]]:
        """
        Get all flights for a specific route on a specific date.

        Args:
            origin: Origin airport code
            destination: Destination airport code
            date: Date in YYYY-MM-DD format

        Returns:
            List of flights with basic info
        """
        # Use aggregation pipeline to match on date extracted from departure_time
        # This ensures consistency with the price chart which uses the same approach
        pipeline = [
            {"$match": {
                "origin": origin.upper(),
                "destination": destination.upper()
            }},
            {"$addFields": {
                "departure_date": {"$substr": ["$departure_time", 0, 10]}
            }},
            {"$match": {
                "departure_date": date
            }},
            {"$sort": {"current_price": ASCENDING}}
        ]

        flights = list(self.flights_collection.aggregate(pipeline))

        return [
            {
                "flight_id": f["flight_id"],
                "flight_number": f.get("flight_number"),
                "departure_time": f.get("departure_time"),
                "arrival_time": f.get("arrival_time"),
                "duration": f.get("duration"),
                "current_price": round(f["current_price"], 2),
                "currency": f.get("currency"),
                "scan_count": f.get("scan_count", 0)
            }
            for f in flights
        ]

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
        return self.custom_search.find_round_trips(
            origin=origin,
            destination=destination,
            min_days=min_days,
            max_days=max_days,
            passengers=passengers,
            return_from_same_airport=return_from_same_airport,
            outbound_weekdays=outbound_weekdays,
            return_weekdays=return_weekdays
        )

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
        return self.custom_search.get_round_trips_preview(
            origin=origin,
            min_days=min_days,
            max_days=max_days,
            return_from_same_airport=return_from_same_airport,
            outbound_weekdays=outbound_weekdays,
            return_weekdays=return_weekdays
        )

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
        return self.custom_search.get_all_two_way_routes(origin=origin, limit=limit)

    def get_one_way_route_examples(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get example one-way routes from Polish airports for price chart display.

        Args:
            limit: Maximum number of routes to return

        Returns:
            List of one-way routes with sample flights
        """
        return self.custom_search.get_one_way_route_examples(limit=limit)

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
            return_to_same_airport: If True, return must land at same airport as outbound origin (default True)
            outbound_weekdays: Optional list of weekdays for outbound flights (0=Monday, 6=Sunday)
            return_weekdays: Optional list of weekdays for return flights (0=Monday, 6=Sunday)

        Returns:
            List of round trip combinations with pricing
        """
        return self.custom_search.find_round_trips_batch(
            origins=origins,
            destinations=destinations,
            min_days=min_days,
            max_days=max_days,
            passengers=passengers,
            date_from=date_from,
            date_to=date_to,
            min_price=min_price,
            max_price=max_price,
            return_from_same_airport=return_from_same_airport,
            return_to_same_airport=return_to_same_airport,
            outbound_weekdays=outbound_weekdays,
            return_weekdays=return_weekdays
        )

    def get_health(self) -> Tuple[Dict[str, Any], bool]:
        """
        Check API and database health.

        Returns:
            Tuple of (health_data dict, is_healthy bool)
        """
        try:
            # Test MongoDB connection
            self.db.command("ping")

            # Get basic stats
            flight_count = self.flights_collection.count_documents({})

            from datetime import datetime
            return {
                "status": "healthy",
                "database": "connected",
                "flights_in_database": flight_count,
                "timestamp": datetime.now().isoformat()
            }, True

        except Exception as e:
            from datetime import datetime
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, False
