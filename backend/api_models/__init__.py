"""
API models package containing all Pydantic models for the application.

This package includes:
- API request/response models
- Ryanair API models
- Wizz Air API models
"""

from .api_models import (
    PriceHistoryEntry,
    FlightSegment,
    FlightResponse,
    FlightListResponse,
    StatsResponse,
    ScanIterationResponse,
    ScanRequest,
    ScanTriggerResponse,
    UpdateCoordinatesRequest,
    UpdateCoordinatesResponse,
)
from .ryanair_models import (
    Fare as RyanairFare,
    RegularFare,
    Segment as RyanairSegment,
    Flight as RyanairFlight,
    FlightDate,
    Trip,
    RyanairResponse,
)
from .wizz_air_models import (
    Price,
    WDC,
    Fee,
    FlightPriceDetail,
    Promotion,
    Fare as WizzAirFare,
    LimitExceeded,
    Flight as WizzAirFlight,
    AncillaryService,
    BundleCardTopBlock,
    Bundle,
    FlightDatesResponse,
    SearchResponse,
)

__all__ = [
    # API models
    "PriceHistoryEntry",
    "FlightSegment",
    "FlightResponse",
    "FlightListResponse",
    "StatsResponse",
    "ScanIterationResponse",
    "ScanRequest",
    "ScanTriggerResponse",
    "UpdateCoordinatesRequest",
    "UpdateCoordinatesResponse",
    # Ryanair models
    "RyanairFare",
    "RegularFare",
    "RyanairSegment",
    "RyanairFlight",
    "FlightDate",
    "Trip",
    "RyanairResponse",
    # Wizz Air models
    "Price",
    "WDC",
    "Fee",
    "FlightPriceDetail",
    "Promotion",
    "WizzAirFare",
    "LimitExceeded",
    "WizzAirFlight",
    "AncillaryService",
    "BundleCardTopBlock",
    "Bundle",
    "FlightDatesResponse",
    "SearchResponse",
]
