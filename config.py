#!/usr/bin/env python3

"""
Configuration and secrets management using Pydantic BaseSettings.

This module handles configuration for MongoDB connections and other sensitive settings.
Configuration can be provided via:
1. Environment variables
2. .env file
3. secrets.json file (create this for local development)

Example secrets.json:
{
    "MONGO_HOST": "localhost",
    "MONGO_PORT": 27017,
    "MONGO_DATABASE": "flights_scanner",
    "MONGO_USERNAME": "",
    "MONGO_PASSWORD": ""
}
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

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        json_file='secrets.json',
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
