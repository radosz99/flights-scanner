#!/usr/bin/env python3

import re
import requests
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, Field, field_validator
from concurrent.futures import ThreadPoolExecutor, as_completed


class AirportGeometry(BaseModel):
    """Represents a single airport geometry entry from the tile data."""
    s: int = Field(description="Size/importance indicator")
    p: List[int] = Field(description="Pixel coordinates [x, y] or connection references")
    a: str = Field(description="Airport name and code, e.g., 'Abilene (ABI)'")
    c: int = Field(description="Airport unique identifier")

    @property
    def airport_code(self) -> Optional[str]:
        """Extract the three-letter airport code from the airport string."""
        match = re.search(r'\(([A-Z]{3})\)', self.a)
        return match.group(1) if match else None

    @property
    def airport_name(self) -> str:
        """Extract the airport name without the code."""
        match = re.search(r'^(.+?)\s*\([A-Z]{3}\)', self.a)
        return match.group(1).strip() if match else self.a


class TileData(BaseModel):
    """Represents the data from a single tile JSON."""
    geom: List[AirportGeometry] = Field(default_factory=list)


class Airport(BaseModel):
    """Represents an airport with its details."""
    code: str = Field(description="Three-letter IATA airport code")
    name: str = Field(description="Airport name")
    airport_id: int = Field(description="Unique airport identifier from API")
    size: int = Field(description="Size/importance indicator")
    coordinates: List[int] = Field(description="Pixel coordinates on tile")
    tile: str = Field(description="Tile where this airport was found (e.g., '0-0')")


class AirlineRoutes(BaseModel):
    """Represents airline route data from FlightConnections API."""
    routes: List[Dict[str, List[int]]] = Field(default_factory=list)


class FlightConnectionsDatabase(BaseModel):
    """Database of all airports and their connections."""
    airports: Dict[str, Airport] = Field(default_factory=dict)
    airports_by_id: Dict[int, str] = Field(default_factory=dict)
    connections: Dict[str, Set[str]] = Field(default_factory=dict)  # airport_code -> set of connected airport codes

    def add_airport(self, airport: Airport):
        """Add an airport to the database."""
        self.airports[airport.code] = airport
        self.airports_by_id[airport.airport_id] = airport.code
        # Initialize empty connections set for this airport
        if airport.code not in self.connections:
            self.connections[airport.code] = set()

    def add_connection(self, from_code: str, to_code: str):
        """
        Add a flight connection between two airports.

        Args:
            from_code: Origin airport code
            to_code: Destination airport code
        """
        if from_code not in self.connections:
            self.connections[from_code] = set()
        self.connections[from_code].add(to_code)

    def add_bidirectional_connection(self, code1: str, code2: str):
        """
        Add a bidirectional flight connection between two airports.

        Args:
            code1: First airport code
            code2: Second airport code
        """
        self.add_connection(code1, code2)
        self.add_connection(code2, code1)

    def get_airport_by_code(self, code: str) -> Optional[Airport]:
        """Get airport by its IATA code."""
        return self.airports.get(code)

    def get_airport_by_id(self, airport_id: int) -> Optional[Airport]:
        """Get airport by its unique ID."""
        code = self.airports_by_id.get(airport_id)
        return self.airports.get(code) if code else None

    def get_all_airports(self) -> List[Airport]:
        """Get all airports sorted by code."""
        return sorted(self.airports.values(), key=lambda x: x.code)

    def get_all_airports_dict(self) -> Dict[str, str]:
        """
        Get all airports as a dictionary mapping code to city/airport name.

        Returns:
            Dictionary with airport codes as keys and airport names as values
            Example: {"JFK": "New York", "LAX": "Los Angeles", ...}
        """
        return {code: airport.name for code, airport in self.airports.items()}

    def get_connections_from(self, airport_code: str) -> List[str]:
        """
        Get all destination airports that have flights from the given airport.

        Args:
            airport_code: IATA code of the origin airport

        Returns:
            List of destination airport codes that can be reached from this airport
            Returns empty list if airport not found or has no connections
        """
        return sorted(list(self.connections.get(airport_code, set())))

    def get_connections_from_with_names(self, airport_code: str) -> List[Dict[str, str]]:
        """
        Get all destinations from an airport with full airport information.

        Args:
            airport_code: IATA code of the origin airport

        Returns:
            List of dictionaries with destination info:
            [{"code": "LAX", "name": "Los Angeles"}, ...]
        """
        connections = self.get_connections_from(airport_code)
        result = []
        for dest_code in connections:
            airport = self.get_airport_by_code(dest_code)
            if airport:
                result.append({
                    "code": dest_code,
                    "name": airport.name
                })
        return result

    def get_connection_count(self, airport_code: str) -> int:
        """
        Get the number of destinations from an airport.

        Args:
            airport_code: IATA code of the airport

        Returns:
            Number of destinations reachable from this airport
        """
        return len(self.connections.get(airport_code, set()))

    def get_airports_by_connection_count(self, limit: Optional[int] = None) -> List[Dict[str, any]]:
        """
        Get airports sorted by number of connections (most connected first).

        Args:
            limit: Optional limit on number of results

        Returns:
            List of dictionaries with airport info and connection counts
        """
        results = []
        for code, airport in self.airports.items():
            results.append({
                "code": code,
                "name": airport.name,
                "connections": self.get_connection_count(code)
            })

        # Sort by connection count descending
        results.sort(key=lambda x: x["connections"], reverse=True)

        if limit:
            return results[:limit]
        return results

    def populate_connections_from_routes(self, airline_routes: AirlineRoutes) -> int:
        """
        Populate connections from airline route data.

        Args:
            airline_routes: AirlineRoutes object containing route data

        Returns:
            Number of connections added
        """
        connections_added = 0
        skipped = 0

        for route_data in airline_routes.routes:
            dep_ids = route_data.get("dep", [])
            des_ids = route_data.get("des", [])

            # Both arrays should have the same length
            if len(dep_ids) != len(des_ids):
                print(f"Warning: Mismatched route data lengths (dep: {len(dep_ids)}, des: {len(des_ids)})")
                continue

            # Process each route
            for dep_id, des_id in zip(dep_ids, des_ids):
                # Look up airport codes from IDs
                dep_code = self.airports_by_id.get(dep_id)
                des_code = self.airports_by_id.get(des_id)

                if dep_code and des_code:
                    # Add connection
                    self.add_connection(dep_code, des_code)
                    connections_added += 1
                else:
                    skipped += 1

        if skipped > 0:
            print(f"Skipped {skipped} routes with unknown airport IDs")

        return connections_added


def fetch_tile(n: int, m: int) -> Optional[TileData]:
    """
    Fetch a single tile from the flight connections API.

    Args:
        n: First tile coordinate (0-3)
        m: Second tile coordinate (0-3)

    Returns:
        TileData object or None if fetch fails
    """
    url = f"https://cdn.flightconnections.com/tiles/251103/en/2/{n}-{m}.json"

    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.flightconnections.com/',
        'Origin': 'https://www.flightconnections.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return TileData(**data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tile {n}-{m}: {e}")
        return None
    except Exception as e:
        print(f"Error parsing tile {n}-{m}: {e}")
        return None


def fetch_all_tiles(max_workers: int = 4) -> List[tuple[str, TileData]]:
    """
    Fetch all tile combinations (0-0 through 3-3) in parallel.

    Args:
        max_workers: Number of parallel workers for fetching

    Returns:
        List of tuples (tile_name, TileData)
    """
    tiles = []
    tile_coords = [(n, m) for n in range(4) for m in range(4)]

    print(f"Fetching {len(tile_coords)} tiles...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_coords = {
            executor.submit(fetch_tile, n, m): (n, m)
            for n, m in tile_coords
        }

        # Collect results as they complete
        for future in as_completed(future_to_coords):
            n, m = future_to_coords[future]
            tile_name = f"{n}-{m}"
            try:
                tile_data = future.result()
                if tile_data:
                    tiles.append((tile_name, tile_data))
                    print(f"✓ Fetched tile {tile_name}: {len(tile_data.geom)} airports")
                else:
                    print(f"✗ Failed to fetch tile {tile_name}")
            except Exception as e:
                print(f"✗ Exception fetching tile {tile_name}: {e}")

    return tiles


def fetch_airline_routes(airline_id: int) -> Optional[AirlineRoutes]:
    """
    Fetch airline route data from FlightConnections API.

    Args:
        airline_id: The ID of the airline to fetch routes for

    Returns:
        AirlineRoutes object or None if fetch fails

    Example:
        routes = fetch_airline_routes(39)  # Ryanair
    """
    url = "https://www.flightconnections.com/airline_routes.php"

    params = {
        'v': '1097',
        'lang': 'en',
        'type': 'ar',
        'ids': str(airline_id),
        'cl': '',
        'flight_direction': 'from',
        'flight_type': 'round',
        'airlines': str(airline_id),
        'alliance': '',
        'classes': '',
        'dates': '',
        'dates_type': '',
        'days_in_destination': '',
        'aircrafts': '',
        'dep_country': '',
        'des_country': '',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.flightconnections.com/',
        'Origin': 'https://www.flightconnections.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        return AirlineRoutes(**data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching airline routes: {e}")
        return None
    except Exception as e:
        print(f"Error parsing airline routes: {e}")
        return None


def build_airport_database() -> FlightConnectionsDatabase:
    """
    Fetch all tiles and build a comprehensive airport database.

    Returns:
        FlightConnectionsDatabase with all airports
    """
    database = FlightConnectionsDatabase()
    tiles = fetch_all_tiles()

    total_airports = 0
    duplicates = 0

    for tile_name, tile_data in tiles:
        for airport_geom in tile_data.geom:
            airport_code = airport_geom.airport_code
            if not airport_code:
                continue

            # Check if airport already exists
            if airport_code in database.airports:
                duplicates += 1
                continue

            airport = Airport(
                code=airport_code,
                name=airport_geom.airport_name,
                airport_id=airport_geom.c,
                size=airport_geom.s,
                coordinates=airport_geom.p,
                tile=tile_name,
            )

            database.add_airport(airport)
            total_airports += 1

    print(f"\n{'='*60}")
    print(f"Database built successfully!")
    print(f"Total unique airports: {total_airports}")
    print(f"Duplicate entries skipped: {duplicates}")
    print(f"{'='*60}")

    return database


def main():
    """Main function to demonstrate the flight connections scraper."""
    print("Flight Connections Data Scraper")
    print("=" * 60)

    # Build the airport database
    database = build_airport_database()

    # Display some statistics
    airports = database.get_all_airports()

    print(f"\nSample airports:")
    for airport in airports[:10]:
        print(f"  {airport.code}: {airport.name} (ID: {airport.airport_id}, Tile: {airport.tile})")

    # Show airports by size
    print(f"\nAirports by size/importance:")
    size_counts = {}
    for airport in airports:
        size_counts[airport.size] = size_counts.get(airport.size, 0) + 1

    for size in sorted(size_counts.keys(), reverse=True):
        print(f"  Size {size}: {size_counts[size]} airports")

    # Fetch airline routes (example: Ryanair with ID 39)
    print(f"\n{'='*60}")
    print("Fetching airline routes (Ryanair - ID 39)...")
    print(f"{'='*60}")

    routes = fetch_airline_routes(39)
    if routes:
        connections_added = database.populate_connections_from_routes(routes)
        print(f"✓ Added {connections_added} route connections to database")

        # Show some example connections
        print(f"\n{'='*60}")
        print("Example connections:")
        print(f"{'='*60}")

        # Find some major airports and show their connections
        major_airports = ['DUB', 'STN', 'BCN', 'MAD', 'FCO']
        for code in major_airports:
            airport = database.get_airport_by_code(code)
            if airport:
                connections = database.get_connections_from(code)
                print(f"\n{code} - {airport.name}:")
                print(f"  Total destinations: {len(connections)}")
                if connections:
                    print(f"  Sample destinations: {', '.join(connections[:10])}")

        # Show top hubs by connection count
        print(f"\n{'='*60}")
        print("Top 10 hub airports by connections:")
        print(f"{'='*60}")
        top_hubs = database.get_airports_by_connection_count(limit=10)
        for i, hub in enumerate(top_hubs, 1):
            print(f"{i:2d}. {hub['code']} - {hub['name']}: {hub['connections']} destinations")
    else:
        print("✗ Failed to fetch airline routes")

    return database


if __name__ == "__main__":
    main()
