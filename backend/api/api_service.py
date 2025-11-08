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

    def find_round_trips(
        self,
        origin: str,
        destination: str,
        min_days: int,
        max_days: int,
        passengers: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find all possible round trips (two-way) within specified trip length range.

        Args:
            origin: Origin airport code
            destination: Destination airport code
            min_days: Minimum trip duration in days
            max_days: Maximum trip duration in days
            passengers: Number of passengers (default 2)

        Returns:
            List of round trip combinations with pricing
        """
        from datetime import datetime, timedelta

        # Get all outbound flights from origin to destination
        outbound_flights = list(self.flights_collection.find({
            "origin": origin.upper(),
            "destination": destination.upper()
        }).sort("departure_time", ASCENDING))

        # Get all return flights from destination to origin
        return_flights = list(self.flights_collection.find({
            "origin": destination.upper(),
            "destination": origin.upper()
        }).sort("departure_time", ASCENDING))

        # Find valid round trip combinations
        round_trips = []

        for outbound in outbound_flights:
            # Extract date from departure_time (format: YYYY-MM-DDTHH:MM:SS.mmm)
            outbound_date_str = outbound["departure_time"].split("T")[0]
            outbound_date = datetime.strptime(outbound_date_str, "%Y-%m-%d")

            for return_flight in return_flights:
                # Extract date from departure_time (format: YYYY-MM-DDTHH:MM:SS.mmm)
                return_date_str = return_flight["departure_time"].split("T")[0]
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d")

                # Calculate trip duration
                trip_duration = (return_date - outbound_date).days

                # Check if trip duration is within range
                if min_days <= trip_duration <= max_days:
                    total_price = (outbound["current_price"] + return_flight["current_price"]) * passengers

                    round_trips.append({
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
                    })

        # Sort by total price
        round_trips.sort(key=lambda x: x["total_price"])

        return round_trips

    def get_all_two_way_routes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all possible two-way routes from Polish airports.

        This returns example routes that can form round trips, useful for
        displaying on the trip search page.

        Args:
            limit: Maximum number of route pairs to return

        Returns:
            List of route pairs (origin-destination combinations)
        """
        # Polish airport codes
        polish_airports = ["WRO", "KRK", "GDN", "POZ", "WAW", "KTW", "WMI", "SZN", "LCJ", "LUZ", "RZE", "SZY", "BZG"]

        # Get unique routes from Polish airports
        pipeline = [
            {"$match": {"origin": {"$in": polish_airports}}},
            {"$group": {
                "_id": {
                    "origin": "$origin",
                    "destination": "$destination"
                },
                "origin_name": {"$first": "$origin_name"},
                "destination_name": {"$first": "$destination_name"},
                "flight_count": {"$sum": 1}
            }},
            {"$sort": {"_id.origin": ASCENDING, "_id.destination": ASCENDING}},
            {"$limit": limit}
        ]

        results = list(self.flights_collection.aggregate(pipeline))

        # Now check which routes have return flights
        two_way_routes = []

        for route in results:
            origin = route["_id"]["origin"]
            destination = route["_id"]["destination"]

            # Check if return route exists
            return_route_exists = self.flights_collection.count_documents({
                "origin": destination,
                "destination": origin
            }) > 0

            if return_route_exists:
                two_way_routes.append({
                    "origin": origin,
                    "origin_name": route["origin_name"],
                    "destination": destination,
                    "destination_name": route["destination_name"],
                    "outbound_flights": route["flight_count"]
                })

        return two_way_routes

    def get_one_way_route_examples(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get example one-way routes from Polish airports for price chart display.

        Args:
            limit: Maximum number of routes to return

        Returns:
            List of one-way routes with sample flights
        """
        # Polish airport codes
        polish_airports = ["WRO", "KRK", "GDN", "POZ", "WAW", "KTW", "WMI", "SZN", "LCJ", "LUZ", "RZE", "SZY", "BZG"]

        # Get unique routes from Polish airports with min prices
        pipeline = [
            {"$match": {"origin": {"$in": polish_airports}}},
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
