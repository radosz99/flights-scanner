#!/usr/bin/env python3

"""
Integration tests for the API service layer.

These tests verify the business logic in api_service.py using a real MongoDB instance.
Requires MongoDB to be running (e.g., via Docker Compose).
"""

import pytest
import os
import sys
from datetime import datetime, date
from pymongo import MongoClient

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api_service import APIService
from config import Settings


@pytest.fixture(scope="session")
def test_settings():
    """Create test settings that use a separate test database."""
    settings = Settings()
    # Override database name for testing to avoid interfering with production data
    settings.MONGO_DATABASE = "flights_scanner_test"
    return settings


@pytest.fixture(scope="session")
def mongo_client(test_settings):
    """Create a real MongoDB client for testing."""
    client = MongoClient(test_settings.mongo_uri)
    yield client
    # Close connection after all tests
    client.close()


@pytest.fixture
def api_service(mongo_client, test_settings):
    """
    Create an APIService instance with real database.
    Cleans up test database before each test.
    """
    # Clean up test database before each test
    mongo_client.drop_database(test_settings.MONGO_DATABASE)

    service = APIService(mongo_client, test_settings.MONGO_DATABASE)
    return service


@pytest.fixture
def sample_flights(api_service):
    """Insert sample flight data for testing."""
    flights = [
        {
            "flight_id": "WRO-BCN-2025-12-01-FR123",
            "origin": "WRO",
            "origin_name": "Wroclaw",
            "destination": "BCN",
            "destination_name": "Barcelona",
            "flight_number": "FR123",
            "operator": "RYANAIR",
            "date_out": "2025-12-01",
            "departure_time": "10:00",
            "arrival_time": "12:30",
            "duration": "02:30",
            "current_price": 50.99,
            "currency": "EUR",
            "fares_left": 5,
            "infants_left": 2,
            "segments": [
                {
                    "segment_nr": 0,
                    "origin": "WRO",
                    "destination": "BCN",
                    "flight_number": "FR123",
                    "departure_time": "10:00",
                    "arrival_time": "12:30",
                    "duration": "02:30"
                }
            ],
            "first_seen": datetime(2025, 11, 1, 10, 0, 0),
            "last_seen": datetime(2025, 11, 7, 10, 0, 0),
            "scan_count": 3,
            "price_history": [
                {"price": 60.00, "timestamp": datetime(2025, 11, 1, 10, 0, 0), "change": 0.0},
                {"price": 55.00, "timestamp": datetime(2025, 11, 5, 10, 0, 0), "change": -5.0},
                {"price": 50.99, "timestamp": datetime(2025, 11, 7, 10, 0, 0), "change": -4.01}
            ]
        },
        {
            "flight_id": "WRO-BCN-2025-12-02-FR124",
            "origin": "WRO",
            "origin_name": "Wroclaw",
            "destination": "BCN",
            "destination_name": "Barcelona",
            "flight_number": "FR124",
            "operator": "RYANAIR",
            "date_out": "2025-12-02",
            "departure_time": "14:00",
            "arrival_time": "16:30",
            "duration": "02:30",
            "current_price": 75.50,
            "currency": "EUR",
            "fares_left": 10,
            "infants_left": 3,
            "segments": [
                {
                    "segment_nr": 0,
                    "origin": "WRO",
                    "destination": "BCN",
                    "flight_number": "FR124",
                    "departure_time": "14:00",
                    "arrival_time": "16:30",
                    "duration": "02:30"
                }
            ],
            "first_seen": datetime(2025, 11, 1, 10, 0, 0),
            "last_seen": datetime(2025, 11, 7, 10, 0, 0),
            "scan_count": 2,
            "price_history": [
                {"price": 75.50, "timestamp": datetime(2025, 11, 1, 10, 0, 0), "change": 0.0}
            ]
        },
        {
            "flight_id": "KRK-MAD-2025-12-01-FR200",
            "origin": "KRK",
            "origin_name": "Krakow",
            "destination": "MAD",
            "destination_name": "Madrid",
            "flight_number": "FR200",
            "operator": "RYANAIR",
            "date_out": "2025-12-01",
            "departure_time": "08:00",
            "arrival_time": "11:00",
            "duration": "03:00",
            "current_price": 120.00,
            "currency": "EUR",
            "fares_left": 8,
            "infants_left": 1,
            "segments": [
                {
                    "segment_nr": 0,
                    "origin": "KRK",
                    "destination": "MAD",
                    "flight_number": "FR200",
                    "departure_time": "08:00",
                    "arrival_time": "11:00",
                    "duration": "03:00"
                }
            ],
            "first_seen": datetime(2025, 11, 1, 10, 0, 0),
            "last_seen": datetime(2025, 11, 7, 10, 0, 0),
            "scan_count": 1,
            "price_history": [
                {"price": 120.00, "timestamp": datetime(2025, 11, 1, 10, 0, 0), "change": 0.0}
            ]
        }
    ]

    api_service.flights_collection.insert_many(flights)
    return flights


@pytest.fixture
def sample_scans(api_service):
    """Insert sample scan iteration data for testing."""
    scans = [
        {
            "start_time": datetime(2025, 11, 7, 10, 0, 0),
            "end_time": datetime(2025, 11, 7, 11, 0, 0),
            "status": "completed",
            "stats": {
                "total_routes": 100,
                "successful_queries": 95,
                "failed_queries": 5,
                "flights_saved": 500
            },
            "progress": {
                "current": 10,
                "total": 10
            }
        },
        {
            "start_time": datetime(2025, 11, 6, 10, 0, 0),
            "end_time": datetime(2025, 11, 6, 11, 30, 0),
            "status": "completed",
            "stats": {
                "total_routes": 100,
                "successful_queries": 98,
                "failed_queries": 2,
                "flights_saved": 520
            },
            "progress": {
                "current": 10,
                "total": 10
            }
        }
    ]

    api_service.scan_iterations_collection.insert_many(scans)
    return scans


class TestGetFlights:
    """Test get_flights service method."""

    def test_get_flights_no_filters(self, api_service, sample_flights):
        """Test getting all flights without filters."""
        result = api_service.get_flights()

        assert result["total"] == 3
        assert result["page"] == 1
        assert result["page_size"] == 50
        assert len(result["flights"]) == 3

    def test_get_flights_filter_by_origin(self, api_service, sample_flights):
        """Test filtering flights by origin airport."""
        result = api_service.get_flights(origin="WRO")

        assert result["total"] == 2
        assert len(result["flights"]) == 2
        assert all(f["origin"] == "WRO" for f in result["flights"])

    def test_get_flights_filter_by_destination(self, api_service, sample_flights):
        """Test filtering flights by destination airport."""
        result = api_service.get_flights(destination="BCN")

        assert result["total"] == 2
        assert len(result["flights"]) == 2
        assert all(f["destination"] == "BCN" for f in result["flights"])

    def test_get_flights_filter_by_date_range(self, api_service, sample_flights):
        """Test filtering flights by date range."""
        result = api_service.get_flights(
            date_from=date(2025, 12, 1),
            date_to=date(2025, 12, 1)
        )

        assert result["total"] == 2
        assert all(f["date_out"] == "2025-12-01" for f in result["flights"])

    def test_get_flights_filter_by_price_range(self, api_service, sample_flights):
        """Test filtering flights by price range."""
        result = api_service.get_flights(min_price=60.0, max_price=100.0)

        assert result["total"] == 1
        assert result["flights"][0]["current_price"] == 75.50

    def test_get_flights_sort_by_price(self, api_service, sample_flights):
        """Test sorting flights by price (ascending)."""
        result = api_service.get_flights(sort_by="price")

        assert result["flights"][0]["current_price"] == 50.99
        assert result["flights"][1]["current_price"] == 75.50
        assert result["flights"][2]["current_price"] == 120.00

    def test_get_flights_sort_by_price_desc(self, api_service, sample_flights):
        """Test sorting flights by price (descending)."""
        result = api_service.get_flights(sort_by="price_desc")

        assert result["flights"][0]["current_price"] == 120.00
        assert result["flights"][1]["current_price"] == 75.50
        assert result["flights"][2]["current_price"] == 50.99

    def test_get_flights_pagination(self, api_service, sample_flights):
        """Test flight pagination."""
        result = api_service.get_flights(page=1, page_size=2)

        assert result["total"] == 3
        assert result["page"] == 1
        assert result["page_size"] == 2
        assert len(result["flights"]) == 2


class TestGetFlightById:
    """Test get_flight_by_id service method."""

    def test_get_flight_by_id_exists(self, api_service, sample_flights):
        """Test getting a flight by ID when it exists."""
        flight = api_service.get_flight_by_id("WRO-BCN-2025-12-01-FR123")

        assert flight is not None
        assert flight["flight_id"] == "WRO-BCN-2025-12-01-FR123"
        assert flight["origin"] == "WRO"
        assert flight["destination"] == "BCN"
        assert "_id" not in flight

    def test_get_flight_by_id_not_exists(self, api_service, sample_flights):
        """Test getting a flight by ID when it doesn't exist."""
        flight = api_service.get_flight_by_id("NONEXISTENT")

        assert flight is None


class TestGetStats:
    """Test get_stats service method."""

    def test_get_stats(self, api_service, sample_flights):
        """Test getting database statistics."""
        stats = api_service.get_stats()

        assert stats["total_flights"] == 3
        assert stats["flights_with_price_changes"] == 1  # Only first flight has multiple price history entries
        assert stats["unique_origins"] == 2  # WRO and KRK
        assert stats["unique_destinations"] == 2  # BCN and MAD
        assert stats["cheapest_flight"]["price"] == 50.99
        assert stats["most_expensive_flight"]["price"] == 120.00
        assert stats["average_price"] > 0

    def test_get_stats_empty_database(self, api_service):
        """Test getting statistics from empty database."""
        stats = api_service.get_stats()

        assert stats["total_flights"] == 0
        assert stats["flights_with_price_changes"] == 0
        assert stats["unique_origins"] == 0
        assert stats["unique_destinations"] == 0
        assert stats["cheapest_flight"] is None
        assert stats["most_expensive_flight"] is None
        assert stats["average_price"] == 0.0


class TestGetOrigins:
    """Test get_origins service method."""

    def test_get_origins(self, api_service, sample_flights):
        """Test getting list of origin airports."""
        origins = api_service.get_origins()

        assert len(origins) == 2
        assert origins[0]["code"] == "KRK"
        assert origins[0]["name"] == "Krakow"
        assert origins[0]["flight_count"] == 1
        assert origins[1]["code"] == "WRO"
        assert origins[1]["name"] == "Wroclaw"
        assert origins[1]["flight_count"] == 2

    def test_get_origins_empty_database(self, api_service):
        """Test getting origins from empty database."""
        origins = api_service.get_origins()

        assert len(origins) == 0


class TestGetDestinations:
    """Test get_destinations service method."""

    def test_get_destinations(self, api_service, sample_flights):
        """Test getting list of destination airports."""
        destinations = api_service.get_destinations()

        assert len(destinations) == 2
        assert destinations[0]["code"] == "BCN"
        assert destinations[0]["name"] == "Barcelona"
        assert destinations[0]["flight_count"] == 2
        assert destinations[1]["code"] == "MAD"
        assert destinations[1]["name"] == "Madrid"
        assert destinations[1]["flight_count"] == 1

    def test_get_destinations_empty_database(self, api_service):
        """Test getting destinations from empty database."""
        destinations = api_service.get_destinations()

        assert len(destinations) == 0


class TestGetRoutes:
    """Test get_routes service method."""

    def test_get_routes_all(self, api_service, sample_flights):
        """Test getting all routes."""
        routes = api_service.get_routes()

        assert len(routes) == 2
        # First route: KRK -> MAD
        assert routes[0]["origin"] == "KRK"
        assert routes[0]["destination"] == "MAD"
        assert routes[0]["flight_count"] == 1
        # Second route: WRO -> BCN
        assert routes[1]["origin"] == "WRO"
        assert routes[1]["destination"] == "BCN"
        assert routes[1]["flight_count"] == 2
        assert routes[1]["min_price"] == 50.99
        assert routes[1]["max_price"] == 75.50

    def test_get_routes_filtered_by_origin(self, api_service, sample_flights):
        """Test getting routes filtered by origin."""
        routes = api_service.get_routes(origin="WRO")

        assert len(routes) == 1
        assert routes[0]["origin"] == "WRO"
        assert routes[0]["destination"] == "BCN"

    def test_get_routes_empty_database(self, api_service):
        """Test getting routes from empty database."""
        routes = api_service.get_routes()

        assert len(routes) == 0


class TestGetScans:
    """Test get_scans service method."""

    def test_get_scans(self, api_service, sample_scans):
        """Test getting scan iteration history."""
        scans = api_service.get_scans(limit=10)

        assert len(scans) == 2
        # Should be ordered by start_time descending (most recent first)
        assert scans[0]["start_time"] > scans[1]["start_time"]
        assert scans[0]["status"] == "completed"
        assert "stats" in scans[0]
        assert "_id" not in scans[0]

    def test_get_scans_with_limit(self, api_service, sample_scans):
        """Test getting scans with limit."""
        scans = api_service.get_scans(limit=1)

        assert len(scans) == 1

    def test_get_scans_empty_database(self, api_service):
        """Test getting scans from empty database."""
        scans = api_service.get_scans()

        assert len(scans) == 0


class TestGetLatestScan:
    """Test get_latest_scan service method."""

    def test_get_latest_scan(self, api_service, sample_scans):
        """Test getting the latest scan."""
        scan = api_service.get_latest_scan()

        assert scan is not None
        assert scan["start_time"] == datetime(2025, 11, 7, 10, 0, 0)
        assert scan["status"] == "completed"
        assert "_id" not in scan

    def test_get_latest_scan_empty_database(self, api_service):
        """Test getting latest scan from empty database."""
        scan = api_service.get_latest_scan()

        assert scan is None


class TestGetPriceChart:
    """Test get_price_chart service method."""

    def test_get_price_chart_exists(self, api_service, sample_flights):
        """Test getting price chart for existing route."""
        chart = api_service.get_price_chart(origin="WRO", destination="BCN")

        assert chart is not None
        assert chart["origin"] == "WRO"
        assert chart["destination"] == "BCN"
        assert chart["total_dates"] == 2
        assert len(chart["data"]) == 2
        # Check first date entry
        assert chart["data"][0]["date"] == "2025-12-01"
        assert chart["data"][0]["min_price"] == 50.99
        assert chart["data"][0]["flight_count"] == 1

    def test_get_price_chart_not_exists(self, api_service, sample_flights):
        """Test getting price chart for non-existent route."""
        chart = api_service.get_price_chart(origin="XXX", destination="YYY")

        assert chart is None

    def test_get_price_chart_case_insensitive(self, api_service, sample_flights):
        """Test that price chart lookup is case-insensitive."""
        chart = api_service.get_price_chart(origin="wro", destination="bcn")

        assert chart is not None
        assert chart["origin"] == "WRO"
        assert chart["destination"] == "BCN"


class TestGetHealth:
    """Test get_health service method."""

    def test_get_health_healthy(self, api_service, sample_flights):
        """Test health check when database is healthy."""
        health_data, is_healthy = api_service.get_health()

        assert is_healthy is True
        assert health_data["status"] == "healthy"
        assert health_data["database"] == "connected"
        assert health_data["flights_in_database"] == 3
        assert "timestamp" in health_data

    def test_get_health_empty_database(self, api_service):
        """Test health check with empty database."""
        health_data, is_healthy = api_service.get_health()

        assert is_healthy is True
        assert health_data["status"] == "healthy"
        assert health_data["flights_in_database"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
