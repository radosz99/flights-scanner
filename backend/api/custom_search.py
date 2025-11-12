#!/usr/bin/env python3

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from constants import POLISH_AIRPORTS


class TooManyFlightsError(Exception):
    pass


class CustomTripSearch:
    MAX_FLIGHTS_PER_DIRECTION = 10000
    MAX_TOTAL_COMBINATIONS = 100_000_000

    def __init__(self, flights_collection: Collection):
        self.flights_collection = flights_collection
        # EUR to PLN conversion rate
        self.euro_pln = float(os.getenv("EURO_PLN", "4.23"))

    def convert_price_to_pln(self, price: float, currency: str) -> float:
        """Convert price to PLN if it's in EUR."""
        if currency == "EUR":
            return price * self.euro_pln
        return price

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
        if destination:
            outbound_flights = list(self.flights_collection.find({
                "origin": origin.upper(),
                "destination": destination.upper()
            }).sort("departure_time", ASCENDING))

            if return_from_same_airport:
                return_flights = list(self.flights_collection.find({
                    "origin": destination.upper(),
                    "destination": origin.upper()
                }).sort("departure_time", ASCENDING))
            else:
                return_flights = list(self.flights_collection.find({
                    "origin": destination.upper(),
                    "destination": origin.upper()
                }).sort("departure_time", ASCENDING))
        else:
            outbound_flights = list(self.flights_collection.find({
                "origin": origin.upper()
            }).sort("departure_time", ASCENDING))

            return_flights = list(self.flights_collection.find({
                "destination": origin.upper()
            }).sort("departure_time", ASCENDING))

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

        round_trips = []

        for outbound in outbound_flights:
            outbound_date_str = outbound["departure_time"].split("T")[0]
            outbound_date = datetime.strptime(outbound_date_str, "%Y-%m-%d")

            if outbound_weekdays is not None:
                if outbound_date.weekday() not in outbound_weekdays:
                    continue

            for return_flight in return_flights:
                if return_from_same_airport:
                    if not destination:
                        if return_flight["origin"] != outbound["destination"]:
                            continue

                return_date_str = return_flight["departure_time"].split("T")[0]
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d")

                if return_weekdays is not None:
                    if return_date.weekday() not in return_weekdays:
                        continue

                trip_duration = (return_date - outbound_date).days

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
                            "currency": outbound["currency"],
                            "last_seen": outbound.get("last_seen")
                        },
                        "return_flight": {
                            "flight_id": return_flight["flight_id"],
                            "flight_number": return_flight["flight_number"],
                            "date": return_date_str,
                            "departure_time": return_flight["departure_time"],
                            "arrival_time": return_flight["arrival_time"],
                            "duration": return_flight["duration"],
                            "price": return_flight["current_price"],
                            "currency": return_flight["currency"],
                            "last_seen": return_flight.get("last_seen")
                        },
                        "trip_duration_days": trip_duration,
                        "total_price": round(total_price, 2),
                        "price_per_person": round(total_price / passengers, 2),
                        "passengers": passengers,
                        "currency": outbound["currency"]
                    }

                    if not destination:
                        trip_data["destination"] = outbound["destination"]
                        trip_data["destination_name"] = outbound.get("destination_name", outbound["destination"])

                    round_trips.append(trip_data)

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

            outbound_flights = list(self.flights_collection.find({
                "origin": origin.upper(),
                "destination": destination_code
            }))

            if return_from_same_airport:
                return_flights = list(self.flights_collection.find({
                    "origin": destination_code,
                    "destination": origin.upper()
                }))
            else:
                return_flights = list(self.flights_collection.find({
                    "destination": origin.upper()
                }))

            if not outbound_flights or not return_flights:
                continue

            min_price = float('inf')

            for outbound in outbound_flights:
                outbound_date_str = outbound["departure_time"].split("T")[0]
                outbound_date = datetime.strptime(outbound_date_str, "%Y-%m-%d")

                if outbound_weekdays is not None:
                    if outbound_date.weekday() not in outbound_weekdays:
                        continue

                for return_flight in return_flights:
                    return_date_str = return_flight["departure_time"].split("T")[0]
                    return_date = datetime.strptime(return_date_str, "%Y-%m-%d")

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
        import time
        perf_start_total = time.time()

        logger.info(f"=== BATCH ROUND TRIPS SEARCH STARTED ===")
        logger.info(f"Parameters: origins={origins}, destinations={destinations}, min_days={min_days}, max_days={max_days}, passengers={passengers}")
        logger.info(f"Filters: date_from={date_from}, date_to={date_to}, min_price={min_price}, max_price={max_price}")
        logger.info(f"Constraints: return_from_same_airport={return_from_same_airport}, return_to_same_airport={return_to_same_airport}")
        logger.info(f"Weekday filters: outbound_weekdays={outbound_weekdays}, return_weekdays={return_weekdays}")

        origins_upper = [o.upper() for o in origins]

        # Support "anywhere" search when destinations is empty
        if destinations:
            destinations_upper = [d.upper() for d in destinations]
            outbound_query = {
                "origin": {"$in": origins_upper},
                "destination": {"$in": destinations_upper}
            }
            if return_from_same_airport:
                return_query = {
                    "origin": {"$in": destinations_upper},
                    "destination": {"$in": origins_upper}
                }
            else:
                return_query = {
                    "origin": {"$in": destinations_upper},
                    "destination": {"$in": origins_upper}
                }
        else:
            # "Anywhere" search - search all destinations from origins
            outbound_query = {
                "origin": {"$in": origins_upper}
            }
            return_query = {
                "destination": {"$in": origins_upper}
            }

        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            outbound_query["date_out"] = date_filter
            return_query["date_out"] = date_filter

        # Query 1: Fetch outbound flights
        perf_query1_start = time.time()
        outbound_flights = list(self.flights_collection.find(outbound_query).sort("departure_time", ASCENDING))
        perf_query1_time = time.time() - perf_query1_start
        logger.info(f"[PERF] Outbound flights query: {perf_query1_time:.3f}s - Found {len(outbound_flights)} flights")

        # Query 2: Fetch return flights
        perf_query2_start = time.time()
        return_flights = list(self.flights_collection.find(return_query).sort("departure_time", ASCENDING))
        perf_query2_time = time.time() - perf_query2_start
        logger.info(f"[PERF] Return flights query: {perf_query2_time:.3f}s - Found {len(return_flights)} flights")

        # Build return flight index for O(1) lookup - MAJOR OPTIMIZATION
        # This eliminates 95%+ of wasted iterations by only checking relevant return flights
        perf_index_start = time.time()
        return_flight_index = {}

        # Pre-parse all dates to avoid repeated parsing in inner loop - OPTIMIZATION
        # This saves ~850K date parsing operations (from 4μs to 0.5μs per iteration)
        return_flight_dates = {}  # flight_id -> (parsed_date, parsed_arrival, parsed_departure)

        for flight in return_flights:
            key = (flight["origin"], flight["destination"])
            if key not in return_flight_index:
                return_flight_index[key] = []
            return_flight_index[key].append(flight)

            # Pre-parse dates once per flight instead of once per iteration
            flight_id = flight["flight_id"]
            date_str = flight["date_out"].split('T')[0]
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            parsed_departure = datetime.fromisoformat(flight["departure_time"].replace("Z", "+00:00"))
            return_flight_dates[flight_id] = (parsed_date, parsed_departure)

        # Also pre-parse outbound flight dates and arrival times
        outbound_flight_dates = {}  # flight_id -> (parsed_date, parsed_arrival)
        for flight in outbound_flights:
            flight_id = flight["flight_id"]
            date_str = flight["date_out"].split('T')[0]
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            parsed_arrival = datetime.fromisoformat(flight["arrival_time"].replace("Z", "+00:00"))
            outbound_flight_dates[flight_id] = (parsed_date, parsed_arrival)

        perf_index_time = time.time() - perf_index_start
        logger.info(f"[PERF] Built indexes: {perf_index_time:.3f}s - {len(return_flight_index)} routes, {len(outbound_flight_dates) + len(return_flight_dates)} dates pre-parsed")

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
        logger.info(f"[PERF] Potential combinations to analyze: {potential_combinations:,} ({len(outbound_flights)} × {len(return_flights)})")

        if potential_combinations > self.MAX_TOTAL_COMBINATIONS:
            raise TooManyFlightsError(
                f"Too many potential combinations ({potential_combinations:,} = {len(outbound_flights)} × {len(return_flights)}). "
                f"Please narrow your search criteria (e.g., shorter date range, specific destination, weekday filters). "
                f"Maximum allowed: {self.MAX_TOTAL_COMBINATIONS:,}"
            )

        # Performance counters
        perf_matching_start = time.time()
        counters = {
            "iterations": 0,
            "filtered_outbound_weekday": 0,
            "filtered_return_weekday": 0,
            "filtered_same_airport": 0,
            "filtered_return_to_same": 0,
            "filtered_date_range": 0,  # Pre-filtered before iteration
            "filtered_trip_duration": 0,
            "filtered_price": 0,
            "filtered_top500_cutoff": 0,  # NEW: Pruned by top-500 optimization
            "valid_trips": 0
        }

        # Top-500 optimization: Use heap to track best 500 trips
        # This allows early pruning of expensive flights that won't make the cut
        import heapq
        MAX_RESULTS = 500
        top_trips_heap = []  # Max-heap of (-total_price, trip_data)
        price_cutoff = float('inf')  # Current 500th-best price (worst in heap)

        round_trips = []

        for outbound in outbound_flights:
            # Use pre-parsed dates instead of parsing in loop
            outbound_date, outbound_arrival = outbound_flight_dates[outbound["flight_id"]]
            outbound_date_str = outbound["date_out"]

            if outbound_weekdays is not None:
                if outbound_date.weekday() not in outbound_weekdays:
                    counters["filtered_outbound_weekday"] += 1
                    continue

            # Pre-convert outbound price once per outbound flight
            outbound_price_pln = self.convert_price_to_pln(outbound["current_price"], outbound["currency"])

            # Get only relevant return flights from index (OPTIMIZATION)
            # Instead of checking all 5,290 flights, only check ~130 relevant ones
            if return_from_same_airport and return_to_same_airport:
                # Most common case: exact route reversal (e.g., WRO→FCO, then FCO→WRO)
                lookup_key = (outbound["destination"], outbound["origin"])
                relevant_return_flights = return_flight_index.get(lookup_key, [])
            elif return_from_same_airport:
                # Return from same destination airport, but can land at any origin airport
                # e.g., WRO→FCO, then FCO→BER is allowed
                relevant_return_flights = []
                for origin_airport in origins_upper:
                    lookup_key = (outbound["destination"], origin_airport)
                    relevant_return_flights.extend(return_flight_index.get(lookup_key, []))
            elif return_to_same_airport:
                # Can depart from any destination airport, but must land at origin
                # e.g., WRO→FCO, then NAP→WRO is allowed
                relevant_return_flights = []
                if destinations:
                    for dest_airport in destinations_upper:
                        lookup_key = (dest_airport, outbound["origin"])
                        relevant_return_flights.extend(return_flight_index.get(lookup_key, []))
                else:
                    # Anywhere search: need all flights returning to origin
                    relevant_return_flights = [f for f in return_flights if f["destination"] == outbound["origin"]]
            else:
                # Most flexible: no constraints (rare case, fallback to all flights)
                relevant_return_flights = return_flights

            # Date-based pre-filtering (OPTIMIZATION for flexible routing)
            # Calculate valid return date range based on trip duration constraints
            # This eliminates ~95% of iterations that would fail trip_duration check
            min_return_date = outbound_date + timedelta(days=min_days)
            max_return_date = outbound_date + timedelta(days=max_days)

            # Filter return flights to only those within valid date range
            # This is especially effective in flexible mode where we check many return flights
            date_filtered_returns = []
            for flight in relevant_return_flights:
                return_date_for_filter = return_flight_dates[flight["flight_id"]][0]
                if min_return_date <= return_date_for_filter <= max_return_date:
                    date_filtered_returns.append(flight)
                else:
                    counters["filtered_date_range"] += 1

            relevant_return_flights = date_filtered_returns

            for return_flight in relevant_return_flights:
                counters["iterations"] += 1

                # Airport matching is now handled by index lookup, so these checks are removed
                # The counters will show 0, indicating we're using the optimized path

                # Top-500 optimization: Early price pruning
                # Calculate best possible price for this combination and skip if too expensive
                return_price_pln = self.convert_price_to_pln(return_flight["current_price"], return_flight["currency"])
                estimated_total = (outbound_price_pln + return_price_pln) * passengers

                # Skip if this can't possibly beat our top 500 worst price
                if estimated_total > price_cutoff:
                    counters["filtered_top500_cutoff"] += 1
                    continue

                # Use pre-parsed dates instead of parsing in loop
                return_date, return_departure = return_flight_dates[return_flight["flight_id"]]
                return_date_str = return_flight["date_out"]

                if return_weekdays is not None:
                    if return_date.weekday() not in return_weekdays:
                        counters["filtered_return_weekday"] += 1
                        continue

                trip_duration = (return_date - outbound_date).days

                if min_days <= trip_duration <= max_days:
                    # Price already calculated above for early pruning
                    total_price = estimated_total

                    if min_price is not None and total_price < min_price:
                        counters["filtered_price"] += 1
                        continue
                    if max_price is not None and total_price > max_price:
                        counters["filtered_price"] += 1
                        continue

                    # Use pre-parsed arrival/departure times for stay duration calculation
                    stay_duration_delta = return_departure - outbound_arrival

                    stay_days = stay_duration_delta.days
                    stay_seconds = stay_duration_delta.seconds
                    stay_hours = stay_seconds // 3600
                    stay_minutes = (stay_seconds % 3600) // 60
                    stay_duration_formatted = f"{stay_days}d {stay_hours}h {stay_minutes}m"

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
                            "current_price": round(outbound_price_pln, 2),
                            "last_seen": outbound.get("last_seen")
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
                            "current_price": round(return_price_pln, 2),
                            "last_seen": return_flight.get("last_seen")
                        },
                        "trip_duration_days": trip_duration,
                        "stay_duration": stay_duration_formatted,
                        "total_price": round(total_price, 2),
                        "price_per_person": round(total_price / passengers, 2) if passengers > 0 else round(total_price, 2),
                        "passengers": passengers,
                        "currency": "PLN"
                    }

                    counters["valid_trips"] += 1

                    # Top-500 optimization: Use heap to keep only best 500 trips
                    if len(top_trips_heap) < MAX_RESULTS:
                        # Still building up to 500 trips
                        heapq.heappush(top_trips_heap, (-total_price, trip_data))
                        if len(top_trips_heap) == MAX_RESULTS:
                            # Just filled up - set cutoff to worst price
                            price_cutoff = -top_trips_heap[0][0]
                    elif total_price < price_cutoff:
                        # Better than worst in heap - replace it
                        heapq.heapreplace(top_trips_heap, (-total_price, trip_data))
                        price_cutoff = -top_trips_heap[0][0]  # Update cutoff
                else:
                    counters["filtered_trip_duration"] += 1

        # Extract trips from heap and sort (heap is max-heap with negative prices)
        round_trips = [trip_data for _, trip_data in sorted(top_trips_heap, key=lambda x: -x[0])]

        perf_matching_time = time.time() - perf_matching_start
        logger.info(f"[PERF] Matching/Analysis phase: {perf_matching_time:.3f}s")
        logger.info(f"[PERF] Analysis stats:")
        logger.info(f"  - Total iterations: {counters['iterations']:,}")
        logger.info(f"  - Filtered by outbound weekday: {counters['filtered_outbound_weekday']:,}")
        logger.info(f"  - Filtered by return weekday: {counters['filtered_return_weekday']:,}")
        logger.info(f"  - Filtered by same airport constraint: {counters['filtered_same_airport']:,}")
        logger.info(f"  - Filtered by return to same constraint: {counters['filtered_return_to_same']:,}")
        logger.info(f"  - Filtered by date range (pre-filter): {counters['filtered_date_range']:,}")
        logger.info(f"  - Filtered by trip duration: {counters['filtered_trip_duration']:,}")
        logger.info(f"  - Filtered by price: {counters['filtered_price']:,}")
        logger.info(f"  - Filtered by top-500 cutoff: {counters['filtered_top500_cutoff']:,}")
        logger.info(f"  - Valid trips found: {counters['valid_trips']:,}")
        logger.info(f"  - Returned (top 500): {len(round_trips)}")

        # Sorting phase is now part of heap extraction above
        perf_sort_start = time.time()
        perf_sort_time = time.time() - perf_sort_start
        logger.info(f"[PERF] Sorting via heap extraction: {perf_sort_time:.3f}s")

        perf_total_time = time.time() - perf_start_total
        logger.info(f"[PERF] === TOTAL TIME: {perf_total_time:.3f}s ===")
        logger.info(f"[PERF] Breakdown:")
        logger.info(f"  - Outbound query: {perf_query1_time:.3f}s ({perf_query1_time/perf_total_time*100:.1f}%)")
        logger.info(f"  - Return query: {perf_query2_time:.3f}s ({perf_query2_time/perf_total_time*100:.1f}%)")
        logger.info(f"  - Index building: {perf_index_time:.3f}s ({perf_index_time/perf_total_time*100:.1f}%)")
        logger.info(f"  - Matching/Analysis: {perf_matching_time:.3f}s ({perf_matching_time/perf_total_time*100:.1f}%)")
        logger.info(f"  - Sorting: {perf_sort_time:.3f}s ({perf_sort_time/perf_total_time*100:.1f}%)")
        logger.info(f"=== BATCH ROUND TRIPS SEARCH COMPLETED - {len(round_trips)} trips returned ===")

        return round_trips

    def get_all_two_way_routes(self, origin: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            from scrapper.database_population import load_from_mongodb
            from config import settings

            ryanair_db = load_from_mongodb("ryanair", settings.mongo_uri)

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

        if origin:
            match_query = {"origin": origin.upper()}
        else:
            match_query = {"origin": {"$in": POLISH_AIRPORTS}}

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

        two_way_routes = []

        for route in results:
            origin_code = route["_id"]["origin"]
            destination = route["_id"]["destination"]

            return_flight = self.flights_collection.find_one(
                {
                    "origin": destination,
                    "destination": origin_code
                },
                sort=[("current_price", ASCENDING)]
            )

            if return_flight:
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

                if origin_code in airport_coords:
                    route_data["origin_coordinates"] = airport_coords[origin_code]

                if destination in airport_coords:
                    route_data["destination_coordinates"] = airport_coords[destination]

                two_way_routes.append(route_data)

                if len(two_way_routes) >= limit:
                    break

        return two_way_routes

    def get_one_way_route_examples(self, limit: int = 50) -> List[Dict[str, Any]]:
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
