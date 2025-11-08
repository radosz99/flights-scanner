"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PriceHistoryEntry(BaseModel):
    """Price history entry model."""
    price: float
    timestamp: datetime
    change: float


class FlightSegment(BaseModel):
    """Flight segment model for multi-leg flights."""
    segment_nr: int
    origin: str
    destination: str
    flight_number: str
    departure_time: str
    arrival_time: str
    duration: str


class FlightResponse(BaseModel):
    """Flight response model."""
    flight_id: str
    origin: str
    origin_name: str
    destination: str
    destination_name: str
    flight_number: str
    operator: str
    date_out: str
    departure_time: str
    arrival_time: str
    duration: str
    current_price: float
    currency: str
    fares_left: int
    infants_left: int
    segments: List[FlightSegment]
    first_seen: datetime
    last_seen: datetime
    scan_count: int
    price_history: List[PriceHistoryEntry]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FlightListResponse(BaseModel):
    """Response model for flight list queries."""
    total: int
    page: int
    page_size: int
    flights: List[FlightResponse]


class StatsResponse(BaseModel):
    """Statistics response model."""
    total_flights: int
    flights_with_price_changes: int
    unique_origins: int
    unique_destinations: int
    cheapest_flight: Optional[Dict[str, Any]]
    most_expensive_flight: Optional[Dict[str, Any]]
    average_price: float


class ScanIterationResponse(BaseModel):
    """Scan iteration response model."""
    start_time: datetime
    end_time: Optional[datetime] = Field(default=None)
    status: str
    stats: Dict[str, Any]
    progress: Optional[Dict[str, Any]] = Field(default=None)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScanRequest(BaseModel):
    """Request model for triggering a scan."""
    trip_duration_days: Optional[int] = Field(
        default=7,
        ge=1,
        le=30,
        description="Number of days between outbound and return flight"
    )
    scan_until_date: Optional[str] = Field(
        default="2026-03-31",
        description="Scan all date ranges until this date (YYYY-MM-DD)"
    )


class ScanTriggerResponse(BaseModel):
    """Response model for scan trigger."""
    message: str
    status: str
    scan_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
