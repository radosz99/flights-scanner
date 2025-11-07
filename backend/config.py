#!/usr/bin/env python3

"""
Configuration and secrets management using Pydantic BaseSettings.

This module handles configuration for MongoDB connections and other sensitive settings.
Configuration can be provided via:
1. Environment variables
2. .env file in the project root

Example .env file:
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=flights_scanner
MONGO_USERNAME=
MONGO_PASSWORD=

# Ryanair scraping configuration
RYANAIR_REQUEST_DELAY=2
RYANAIR_COOKIE_WAIT_TIME=30
RYANAIR_COOKIE_CHECK_INTERVAL=0.5
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with MongoDB configuration."""

    # MongoDB settings
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DATABASE: str = "flights_scanner"
    MONGO_USERNAME: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None

    # Airline IDs for route fetching
    RYANAIR_AIRLINE_ID: int = 39
    WIZZAIR_AIRLINE_IDS: str = "52,6002,6092"  # Wizz Air, Wizz Air UK, Wizz Air Abu Dhabi

    # Ryanair cookie extraction URL
    # This page triggers the availability API request which contains valid cookies
    RYANAIR_COOKIE_URL: str = "https://www.ryanair.com/hr/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-03-06&dateIn=2026-03-08&isConnectedFlight=false&discount=0&promoCode=&isReturn=true&originIata=WRO&destinationIata=ALC&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-03-06&tpEndDate=2026-03-08&tpDiscount=0&tpPromoCode=&tpOriginIata=WRO&tpDestinationIata=ALC"

    # Ryanair scraping configuration
    RYANAIR_REQUEST_DELAY: float = 2.0  # Delay between Ryanair API requests (seconds)
    RYANAIR_COOKIE_WAIT_TIME: int = 30  # Max time to wait for cookie extraction (seconds)
    RYANAIR_COOKIE_CHECK_INTERVAL: float = 0.5  # Interval for checking cookie extraction progress (seconds)

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=True
    )

    @property
    def mongo_uri(self) -> str:
        """
        Generate MongoDB connection URI.

        Returns:
            MongoDB connection string
        """
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DATABASE}"
        else:
            return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DATABASE}"

    def get_wizzair_ids_list(self) -> list[str]:
        """Get Wizz Air airline IDs as a list."""
        return [id.strip() for id in self.WIZZAIR_AIRLINE_IDS.split(',')]


# Global settings instance
settings = Settings()


if __name__ == "__main__":
    """Test configuration loading."""
    print("=" * 60)
    print("Configuration Settings")
    print("=" * 60)
    print(f"MongoDB Host: {settings.MONGO_HOST}")
    print(f"MongoDB Port: {settings.MONGO_PORT}")
    print(f"MongoDB Database: {settings.MONGO_DATABASE}")
    print(f"MongoDB URI: {settings.mongo_uri}")
    print(f"\nRyanair Airline ID: {settings.RYANAIR_AIRLINE_ID}")
    print(f"Wizz Air Airline IDs: {settings.WIZZAIR_AIRLINE_IDS}")
    print(f"Wizz Air IDs (list): {settings.get_wizzair_ids_list()}")
    print("=" * 60)
