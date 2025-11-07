#!/usr/bin/env python3

"""
Pytest configuration for API integration tests.

This file contains shared fixtures and configuration for all tests.
"""

import pytest
import os
import sys
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Settings


def pytest_configure(config):
    """
    Pytest hook that runs before test collection.
    Check if MongoDB is available before running tests.
    """
    # Get test settings
    settings = Settings()
    settings.MONGO_DATABASE = "flights_scanner_test"

    # Try to connect to MongoDB
    try:
        client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=2000)
        client.server_info()
        client.close()
        print(f"\n✓ Connected to MongoDB at {settings.mongo_uri}")
        print(f"✓ Using test database: {settings.MONGO_DATABASE}")
    except ServerSelectionTimeoutError:
        pytest.exit(
            f"\n\n"
            f"ERROR: Cannot connect to MongoDB!\n"
            f"Connection URI: {settings.mongo_uri}\n\n"
            f"These are integration tests that require a running MongoDB instance.\n\n"
            f"To run the tests:\n"
            f"  1. Start MongoDB using Docker Compose:\n"
            f"     make docker-up\n\n"
            f"  2. Or start just MongoDB:\n"
            f"     docker-compose up -d mongodb\n\n"
            f"  3. Then run the tests:\n"
            f"     make test-api\n\n"
        )
    except Exception as e:
        pytest.exit(f"\n\nERROR: Unexpected error connecting to MongoDB: {e}\n\n")
