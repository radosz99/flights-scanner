#!/usr/bin/env python3
"""
Trigger a flight scan via the API.

This script calls the /scans/run endpoint to trigger a new scan.
Can be scheduled via cron or systemd timer to run automatically.
"""

import requests
import sys
import os
from datetime import datetime, timedelta
from loguru import logger

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
TRIP_DURATION_DAYS = int(os.getenv("TRIP_DURATION_DAYS", "7"))
SCAN_UNTIL_DAYS = int(os.getenv("SCAN_UNTIL_DAYS", "365"))  # Days from now


def trigger_scan():
    """Trigger a new scan via the API."""
    # Calculate scan_until_date
    scan_until_date = (datetime.now() + timedelta(days=SCAN_UNTIL_DAYS)).strftime("%Y-%m-%d")

    payload = {
        "trip_duration_days": TRIP_DURATION_DAYS,
        "scan_until_date": scan_until_date
    }

    logger.info("=" * 60)
    logger.info("TRIGGERING FLIGHT SCAN")
    logger.info("=" * 60)
    logger.info(f"API URL: {API_URL}")
    logger.info(f"Trip Duration: {TRIP_DURATION_DAYS} days")
    logger.info(f"Scan Until: {scan_until_date}")
    logger.info("=" * 60)

    try:
        response = requests.post(
            f"{API_URL}/scans/run",
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        logger.success("✓ Scan triggered successfully!")
        logger.info(f"Scan ID: {result.get('scan_id')}")
        logger.info(f"Status: {result.get('status')}")
        logger.info(f"Message: {result.get('message')}")

        config = result.get('config', {})
        if config:
            logger.info(f"Total date ranges: {config.get('total_date_ranges')}")
            logger.info(f"Departure airports: {', '.join(config.get('departure_airports', []))}")

        return 0

    except requests.exceptions.ConnectionError:
        logger.error(f"✗ Failed to connect to API at {API_URL}")
        logger.error("Make sure the backend is running!")
        return 1

    except requests.exceptions.Timeout:
        logger.error("✗ Request timed out after 30 seconds")
        return 1

    except requests.exceptions.HTTPError as e:
        logger.error(f"✗ HTTP error: {e}")
        if e.response:
            logger.error(f"Response: {e.response.text}")
        return 1

    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(trigger_scan())
