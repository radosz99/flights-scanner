"""
Database population package for building airport and route databases.
"""

from .flight_connector import (
    build_airport_database,
    fetch_ryanair_routes,
    fetch_wizzair_routes,
    save_to_mongodb,
    load_from_mongodb,
    Airport,
    FlightConnectionsDatabase,
)
from .populate_databases import (
    populate_ryanair_database,
    populate_wizzair_database,
)

__all__ = [
    # Flight connector
    "build_airport_database",
    "fetch_ryanair_routes",
    "fetch_wizzair_routes",
    "save_to_mongodb",
    "load_from_mongodb",
    "Airport",
    "FlightConnectionsDatabase",
    # Database population
    "populate_ryanair_database",
    "populate_wizzair_database",
]
