"""
Ryanair scraping package.
"""

from .ryanair import (
    get_valid_cookie,
    get_ryanair_flights,
    extract_cookies_from_ryanair,
)
from .ryanair_scanner import (
    scan_flights,
    generate_date_ranges,
    ScanIterationManager,
    FlightStorage,
    SCAN_ITERATIONS_COLLECTION,
    FLIGHTS_COLLECTION,
)

__all__ = [
    # Ryanair API
    "get_valid_cookie",
    "get_ryanair_flights",
    "extract_cookies_from_ryanair",
    # Scanner
    "scan_flights",
    "generate_date_ranges",
    "ScanIterationManager",
    "FlightStorage",
    "SCAN_ITERATIONS_COLLECTION",
    "FLIGHTS_COLLECTION",
]
