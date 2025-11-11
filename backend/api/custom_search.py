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
    MAX_TOTAL_COMBINATIONS = 50_000_000

    def __init__(self, flights_collection: Collection):
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
        origins_upper = [o.upper() for o in origins]
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

        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            outbound_query["date_out"] = date_filter
            return_query["date_out"] = date_filter

        outbound_flights = list(self.flights_collection.find(outbound_query).sort("departure_time", ASCENDING))
        return_flights = list(self.flights_collection.find(return_query).sort("departure_time", ASCENDING))

        logger.info(f"Found {len(outbound_flights)} outbound flights and {len(return_flights)} return flights")

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

        round_trips = []

        for outbound in outbound_flights:
            outbound_date_str = outbound["date_out"]
            outbound_date = datetime.strptime(outbound_date_str.split('T')[0], "%Y-%m-%d")

            if outbound_weekdays is not None:
                if outbound_date.weekday() not in outbound_weekdays:
                    continue

            for return_flight in return_flights:
                if return_from_same_airport:
                    if return_flight["origin"] != outbound["destination"]:
                        continue

                if return_to_same_airport:
                    if return_flight["destination"] != outbound["origin"]:
                        continue

                return_date_str = return_flight["date_out"]
                return_date = datetime.strptime(return_date_str.split('T')[0], "%Y-%m-%d")

                if return_weekdays is not None:
                    if return_date.weekday() not in return_weekdays:
                        continue

                trip_duration = (return_date - outbound_date).days

                if min_days <= trip_duration <= max_days:
                    total_price = (outbound["current_price"] + return_flight["current_price"]) * passengers

                    if min_price is not None and total_price < min_price:
                        continue
                    if max_price is not None and total_price > max_price:
                        continue

                    outbound_arrival = datetime.fromisoformat(outbound["arrival_time"].replace("Z", "+00:00"))
                    return_departure = datetime.fromisoformat(return_flight["departure_time"].replace("Z", "+00:00"))
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

        round_trips.sort(key=lambda x: x["total_price"])

        logger.info(f"Found {len(round_trips)} valid round trips")

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
