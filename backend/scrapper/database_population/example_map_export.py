#!/usr/bin/env python3
"""
Example script showing how to export airport coordinates for map visualization.

This demonstrates various export formats useful for different mapping libraries.
"""

import json
import sys
from typing import Dict, List, Any

from flight_connector import load_from_mongodb


def export_geojson(airline_name: str = "ryanair", mongo_uri: str = "mongodb://localhost:27017/flights_scanner") -> Dict:
    """
    Export airports as GeoJSON format for map libraries like Leaflet, Mapbox GL JS.

    Returns:
        GeoJSON FeatureCollection
    """
    database = load_from_mongodb(airline_name, mongo_uri)

    if not database:
        return {"type": "FeatureCollection", "features": []}

    features = []

    for airport in database.get_all_airports():
        if airport.latitude is None or airport.longitude is None:
            continue

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [airport.longitude, airport.latitude]  # GeoJSON uses [lon, lat]
            },
            "properties": {
                "code": airport.code,
                "name": airport.name,
                "airport_id": airport.airport_id,
                "size": airport.size,
                "connections": len(database.get_connections_from(airport.code))
            }
        }

        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }


def export_simple_list(airline_name: str = "ryanair", mongo_uri: str = "mongodb://localhost:27017/flights_scanner") -> List[Dict]:
    """
    Export airports as a simple list of dictionaries.

    Returns:
        List of airport dictionaries with coordinates
    """
    database = load_from_mongodb(airline_name, mongo_uri)

    if not database:
        return []

    airports = []

    for airport in database.get_all_airports():
        if airport.latitude is None or airport.longitude is None:
            continue

        airports.append({
            "code": airport.code,
            "name": airport.name,
            "latitude": airport.latitude,
            "longitude": airport.longitude,
            "connections": database.get_connections_from(airport.code),
            "connection_count": len(database.get_connections_from(airport.code))
        })

    # Sort by connection count (hub airports first)
    airports.sort(key=lambda x: x["connection_count"], reverse=True)

    return airports


def export_connections_geojson(airline_name: str = "ryanair", mongo_uri: str = "mongodb://localhost:27017/flights_scanner") -> Dict:
    """
    Export airport connections as GeoJSON LineStrings for route visualization.

    Returns:
        GeoJSON FeatureCollection with LineString features for each route
    """
    database = load_from_mongodb(airline_name, mongo_uri)

    if not database:
        return {"type": "FeatureCollection", "features": []}

    features = []

    for from_code in database.connections:
        from_airport = database.get_airport_by_code(from_code)

        if not from_airport or from_airport.latitude is None:
            continue

        for to_code in database.get_connections_from(from_code):
            to_airport = database.get_airport_by_code(to_code)

            if not to_airport or to_airport.latitude is None:
                continue

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [from_airport.longitude, from_airport.latitude],
                        [to_airport.longitude, to_airport.latitude]
                    ]
                },
                "properties": {
                    "from": from_code,
                    "to": to_code,
                    "from_name": from_airport.name,
                    "to_name": to_airport.name,
                    "airline": airline_name
                }
            }

            features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }


def main():
    """Export airport data in various formats."""
    import argparse

    parser = argparse.ArgumentParser(description="Export airport coordinates for map visualization")
    parser.add_argument("--airline", default="ryanair", help="Airline name (default: ryanair)")
    parser.add_argument("--format", choices=["geojson", "simple", "connections"], default="geojson",
                        help="Export format (default: geojson)")
    parser.add_argument("--output", help="Output file path (prints to stdout if not specified)")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017/flights_scanner",
                        help="MongoDB connection URI")

    args = parser.parse_args()

    print(f"Exporting {args.airline} airports in {args.format} format...", file=sys.stderr)

    # Export data
    if args.format == "geojson":
        data = export_geojson(args.airline, args.mongo_uri)
    elif args.format == "simple":
        data = export_simple_list(args.airline, args.mongo_uri)
    elif args.format == "connections":
        data = export_connections_geojson(args.airline, args.mongo_uri)
    else:
        print(f"Unknown format: {args.format}", file=sys.stderr)
        sys.exit(1)

    # Output data
    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"✓ Exported to {args.output}", file=sys.stderr)

        # Print statistics
        if args.format == "geojson":
            print(f"  Airports: {len(data['features'])}", file=sys.stderr)
        elif args.format == "simple":
            print(f"  Airports: {len(data)}", file=sys.stderr)
        elif args.format == "connections":
            print(f"  Connections: {len(data['features'])}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
