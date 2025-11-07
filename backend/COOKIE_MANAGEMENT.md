# Ryanair Cookie Management System

## Overview

This system provides robust, automatic cookie management for Ryanair API access, including:
- Automatic cookie validation
- Database tracking (MongoDB)
- Auto-refresh on expiration
- Simple, one-line usage

## Quick Start

### Simple Usage (Recommended)

```python
from ryanair import get_valid_cookie, get_ryanair_flights

# Get a valid cookie (automatically handles everything)
cookie = get_valid_cookie()

if cookie:
    # Use it to fetch flights
    flights = get_ryanair_flights(
        origin="WRO",
        destination="ALC",
        date_out="2026-03-06",
        date_in="2026-03-08",
        cookies=cookie
    )
    print(f"Found {len(flights.trips)} trips")
```

### Run the Demo

```bash
python3 main.py
```

## How It Works

### `get_valid_cookie()` - The Robust Method

This is the main method you should use. It automatically:

1. **Checks MongoDB** for the most recent active cookie
2. **Tests the cookie** with a real API request
3. **Returns it** if valid
4. **Auto-refreshes** if invalid (extracts new cookie from browser)
5. **Saves to MongoDB** for future use

```python
cookie = get_valid_cookie(auto_refresh=True)
```

#### Parameters:
- `auto_refresh` (bool, default=True): Automatically extract new cookie if existing ones are invalid

#### Returns:
- Valid cookie string or `None` if unable to get a valid cookie

#### Workflow:

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: Check MongoDB for active cookie                │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │ Cookie found? │
         └───┬───────┬───┘
             │       │
         Yes │       │ No
             │       │
             ▼       ▼
┌────────────────────────────────────────┐
│ Step 2: Test cookie with API request  │
└────────────────┬───────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │ Cookie valid? │
         └───┬───────┬───┘
             │       │
         Yes │       │ No
             │       │
             ▼       ▼
┌─────────────────────────────────────────┐
│ Step 3: Extract new cookie from browser│
│ (Opens Chrome, monitors network)        │
└────────────────┬────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │ Save to DB    │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │ Return cookie │
         └───────────────┘
```

## API Reference

### Main Functions

#### `get_valid_cookie(auto_refresh=True)`
The robust, recommended method for getting cookies.

#### `get_ryanair_flights(..., cookies=None)`
Fetch flight data from Ryanair API. Requires cookies parameter.

**Note on Headers**: Only the `Cookie` header is used. All other headers have been removed as they're not necessary for the API to work.

### Helper Functions

#### `extract_cookies_from_ryanair(wait_time=30, save_to_db=True)`
Extract fresh cookies using Selenium browser automation.

#### `get_latest_valid_cookie()`
Get the most recent active cookie from MongoDB (without testing).

#### `mark_cookie_valid(cookie_string)`
Mark a cookie as valid in MongoDB.

#### `mark_cookie_invalid(cookie_string)`
Mark a cookie as invalid and deactivate it in MongoDB.

## MongoDB Schema

Cookies are stored in the `ryanair_cookies` collection:

```python
{
    "cookie": "fr-correlation-id=...",
    "active": true,                  # Is this cookie still valid?
    "fetched": datetime,             # When was it extracted?
    "last_valid_use": datetime,      # Last successful use
    "last_invalid_use": datetime     # Last failed use
}
```

## Error Handling

The system automatically handles:
- Missing cookies (extracts new ones)
- Expired cookies (marks as invalid, extracts new ones)
- 403 Forbidden errors (marks cookie as invalid)
- MongoDB connection issues (graceful fallback)

## Requirements

- Python 3.7+
- MongoDB (running locally or remote)
- Chrome/ChromeDriver (for cookie extraction)
- Dependencies: `requests`, `pymongo`, `selenium`, `pydantic`

## Configuration

Edit `config.py` to customize:

```python
MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_DATABASE = "flights_scanner"

RYANAIR_COOKIE_URL = "https://www.ryanair.com/..."
```

## Troubleshooting

### "No active cookies found in MongoDB"
- Run: `python3 test_ryanair_cookies.py extract`
- Or use `get_valid_cookie(auto_refresh=True)` to extract automatically

### "Cookie test failed"
- Cookie may have expired (will auto-refresh if `auto_refresh=True`)
- Check internet connection
- Verify MongoDB is running

### "Failed to extract new cookie"
- Ensure Chrome/ChromeDriver is installed
- Check that ChromeDriver version matches Chrome version
- Increase `wait_time` parameter: `extract_cookies_from_ryanair(wait_time=60)`

## Advanced Usage

### Manual Cookie Management

```python
# Get cookie without auto-refresh
cookie = get_valid_cookie(auto_refresh=False)
if not cookie:
    print("No valid cookies - manual extraction needed")

# Extract new cookie manually
cookie = extract_cookies_from_ryanair(wait_time=30, save_to_db=True)

# Test a specific cookie
try:
    flights = get_ryanair_flights("WRO", "ALC", "2026-03-06", "2026-03-08", cookies=cookie)
    mark_cookie_valid(cookie)
except:
    mark_cookie_invalid(cookie)
```

### Iterate Through All Cookies

```python
# Find first valid cookie from database
from find_valid_cookie import find_valid_cookie_from_db

cookie = find_valid_cookie_from_db()
```

## Examples

See:
- `main.py` - Complete demo with robust cookie management
- `test_ryanair_cookies.py` - Cookie extraction and testing tools
- `find_valid_cookie.py` - Iterate through all cookies to find valid one
