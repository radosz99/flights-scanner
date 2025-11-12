#!/usr/bin/env python3

"""
API Request Logging Middleware for FastAPI.

This middleware logs all incoming API requests to MongoDB, including:
- Request method, path, query parameters, headers
- Real user IP (extracted from nginx headers)
- Response status code and processing time
- Any errors that occurred during request handling

Collection: api_request_logs
"""

import time
import json
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from pymongo import MongoClient


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests to MongoDB."""

    def __init__(self, app, mongo_client: MongoClient, database_name: str):
        """
        Initialize the request logging middleware.

        Args:
            app: FastAPI application instance
            mongo_client: MongoDB client instance
            database_name: Name of the MongoDB database
        """
        super().__init__(app)
        self.db = mongo_client[database_name]
        self.logs_collection = self.db["api_request_logs"]

        # Create indexes for efficient querying
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes on the api_request_logs collection."""
        try:
            # Index on timestamp for time-based queries
            self.logs_collection.create_index([("timestamp", -1)])

            # Index on path for filtering by endpoint
            self.logs_collection.create_index("path")

            # Index on status_code for filtering by response status
            self.logs_collection.create_index("status_code")

            # Index on user_ip for filtering by IP
            self.logs_collection.create_index("user_ip")

            # Compound index for common queries
            self.logs_collection.create_index([
                ("path", 1),
                ("timestamp", -1)
            ])

            logger.success("Created indexes for api_request_logs collection")
        except Exception as e:
            logger.warning(f"Failed to create indexes for api_request_logs: {e}")

    def _get_real_ip(self, request: Request) -> str:
        """
        Extract the real user IP address from request headers.

        Checks for common nginx proxy headers in order of preference:
        1. X-Real-IP (nginx proxy)
        2. X-Forwarded-For (may contain multiple IPs)
        3. Forwarded (RFC 7239 standard)
        4. Client host (fallback)

        Args:
            request: FastAPI request object

        Returns:
            User's real IP address
        """
        # Check X-Real-IP header (set by nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Check X-Forwarded-For header (may contain multiple IPs: client, proxy1, proxy2)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP (original client)
            return forwarded_for.split(",")[0].strip()

        # Check Forwarded header (RFC 7239)
        forwarded = request.headers.get("Forwarded")
        if forwarded:
            # Parse "for=xxx" from Forwarded header
            for part in forwarded.split(";"):
                if part.strip().startswith("for="):
                    return part.split("=")[1].strip()

        # Fallback to direct client host
        if request.client:
            return request.client.host

        return "unknown"

    def _extract_query_params(self, request: Request) -> dict:
        """
        Extract query parameters from the request.

        Args:
            request: FastAPI request object

        Returns:
            Dictionary of query parameters
        """
        return dict(request.query_params)

    def _extract_headers(self, request: Request) -> dict:
        """
        Extract all headers from the request.

        Args:
            request: FastAPI request object

        Returns:
            Dictionary of request headers
        """
        # Convert headers to dict (excluding sensitive data like API keys if needed)
        headers = dict(request.headers)

        # Optional: Mask sensitive headers for security
        # if "x-api-key" in headers:
        #     headers["x-api-key"] = "***MASKED***"

        return headers

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log it to MongoDB.

        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler

        Returns:
            Response from the route handler
        """
        # Skip logging for health check endpoints
        path = request.url.path
        if path in ["/health", "/api/health", "/api/", "/"]:
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Extract request information
        user_ip = self._get_real_ip(request)
        method = request.method
        query_params = self._extract_query_params(request)
        headers = self._extract_headers(request)

        # Initialize response variables
        status_code = 500  # Default to error if something goes wrong
        error_message = None

        try:
            # Process the request
            response = await call_next(request)
            status_code = response.status_code

        except Exception as e:
            # Log the error
            error_message = str(e)
            logger.error(f"Request failed: {method} {path} - {error_message}")
            raise  # Re-raise to let FastAPI handle the error response

        finally:
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Prepare log document
            log_document = {
                "timestamp": datetime.utcnow(),
                "method": method,
                "path": path,
                "query_params": query_params,
                "headers": headers,
                "user_ip": user_ip,
                "status_code": status_code,
                "processing_time_ms": round(processing_time_ms, 2),
                "error": error_message
            }

            # Add API key usage flag (if X-API-Key header exists)
            log_document["api_key_used"] = "x-api-key" in headers

            # Log to MongoDB (non-blocking)
            try:
                self.logs_collection.insert_one(log_document)
            except Exception as e:
                # Don't fail the request if logging fails
                logger.error(f"Failed to log request to MongoDB: {e}")

            # Also log to console for debugging
            logger.info(
                f"{method} {path} | "
                f"IP: {user_ip} | "
                f"Status: {status_code} | "
                f"Time: {processing_time_ms:.2f}ms | "
                f"Params: {json.dumps(query_params)}"
            )

        return response


def setup_request_logging(app, mongo_client: MongoClient, database_name: str):
    """
    Setup request logging middleware for the FastAPI app.

    Args:
        app: FastAPI application instance
        mongo_client: MongoDB client instance
        database_name: Name of the MongoDB database
    """
    app.add_middleware(RequestLoggingMiddleware, mongo_client=mongo_client, database_name=database_name)
    logger.success("Request logging middleware enabled - logging to api_request_logs collection")
