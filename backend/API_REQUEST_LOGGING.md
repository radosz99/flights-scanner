# API Request Logging

## Overview

All API requests are automatically logged to MongoDB for monitoring, analytics, and debugging purposes. The logging middleware captures comprehensive information about each request including headers, query parameters, real user IP, and response details.

## MongoDB Collection

**Collection Name:** `api_request_logs`

### Document Schema

```javascript
{
  // Request timestamp (UTC)
  "timestamp": ISODate("2025-11-12T10:30:45.123Z"),

  // HTTP method (GET, POST, DELETE, etc.)
  "method": "GET",

  // Request path (e.g., "/flights", "/scans/run")
  "path": "/flights",

  // All query parameters as key-value pairs
  "query_params": {
    "origin": "WRO",
    "destination": "BCN",
    "min_price": 10,
    "max_price": 100,
    "sort_by": "price",
    "page": 1,
    "page_size": 50
  },

  // All request headers
  "headers": {
    "host": "example.com",
    "user-agent": "Mozilla/5.0...",
    "x-real-ip": "192.168.1.100",
    "x-forwarded-for": "192.168.1.100, 10.0.0.1",
    "x-api-key": "secret_key_here",
    "content-type": "application/json",
    // ... all other headers
  },

  // Real user IP address (extracted from nginx headers)
  "user_ip": "192.168.1.100",

  // HTTP response status code
  "status_code": 200,

  // Request processing time in milliseconds
  "processing_time_ms": 45.67,

  // Flag indicating if API key was used
  "api_key_used": false,

  // Error message (if request failed)
  "error": null
}
```

### Indexes

The following indexes are automatically created for efficient querying:

1. **timestamp** (descending) - For time-based queries
2. **path** - For filtering by endpoint
3. **status_code** - For filtering by response status
4. **user_ip** - For filtering by IP address
5. **Compound: (path, timestamp)** - For common queries

## Real IP Detection

The middleware automatically extracts the real user IP address from nginx proxy headers in the following order of preference:

1. **X-Real-IP** - Set by nginx `proxy_set_header X-Real-IP $remote_addr;`
2. **X-Forwarded-For** - May contain multiple IPs (client, proxy1, proxy2). Uses the first IP.
3. **Forwarded** - RFC 7239 standard header
4. **Client host** - Fallback to direct client connection

### Nginx Configuration

To ensure real IP logging works correctly, add these headers to your nginx configuration:

```nginx
location /api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Query Examples

### Get all requests from a specific IP

```javascript
db.api_request_logs.find({ user_ip: "192.168.1.100" })
```

### Get all requests to /flights endpoint

```javascript
db.api_request_logs.find({ path: "/flights" })
```

### Get all failed requests (4xx, 5xx)

```javascript
db.api_request_logs.find({ status_code: { $gte: 400 } })
```

### Get slow requests (> 1 second)

```javascript
db.api_request_logs.find({ processing_time_ms: { $gt: 1000 } })
```

### Get requests with specific filter parameters

```javascript
db.api_request_logs.find({
  path: "/flights",
  "query_params.origin": "WRO",
  "query_params.destination": "BCN"
})
```

### Get requests from the last 24 hours

```javascript
db.api_request_logs.find({
  timestamp: {
    $gte: new Date(Date.now() - 24 * 60 * 60 * 1000)
  }
})
```

### Aggregate requests by endpoint

```javascript
db.api_request_logs.aggregate([
  {
    $group: {
      _id: "$path",
      count: { $sum: 1 },
      avg_time_ms: { $avg: "$processing_time_ms" }
    }
  },
  { $sort: { count: -1 } }
])
```

### Aggregate requests by IP address

```javascript
db.api_request_logs.aggregate([
  {
    $group: {
      _id: "$user_ip",
      count: { $sum: 1 },
      endpoints: { $addToSet: "$path" }
    }
  },
  { $sort: { count: -1 } }
])
```

### Get most common filter combinations

```javascript
db.api_request_logs.aggregate([
  { $match: { path: "/flights" } },
  {
    $group: {
      _id: {
        origin: "$query_params.origin",
        destination: "$query_params.destination"
      },
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 10 }
])
```

## Performance Considerations

- Logging is **non-blocking** - if MongoDB logging fails, the request still succeeds
- Each request log is inserted asynchronously to avoid impacting API performance
- Indexes are created automatically on first startup to ensure fast queries
- Consider setting up TTL (Time-To-Live) index to auto-delete old logs:

```javascript
db.api_request_logs.createIndex(
  { "timestamp": 1 },
  { expireAfterSeconds: 2592000 }  // 30 days
)
```

## Privacy & Security

### Sensitive Data

By default, ALL headers are logged including:
- API keys (`X-API-Key`)
- User agents
- Cookies
- Authorization tokens

**To mask sensitive headers**, uncomment the masking code in `request_logging_middleware.py`:

```python
def _extract_headers(self, request: Request) -> dict:
    headers = dict(request.headers)

    # Mask sensitive headers for security
    if "x-api-key" in headers:
        headers["x-api-key"] = "***MASKED***"
    if "authorization" in headers:
        headers["authorization"] = "***MASKED***"

    return headers
```

### GDPR Compliance

If storing user IP addresses and request data, ensure compliance with:
- Data retention policies
- User consent (if required)
- Right to deletion
- Data access requests

Consider implementing:
1. TTL indexes for automatic data deletion
2. IP anonymization (hash IPs or truncate last octet)
3. Data export/deletion endpoints

## Monitoring & Alerts

### Set up alerts for:

1. **High error rates**
   ```javascript
   // Count 5xx errors in last hour
   db.api_request_logs.countDocuments({
     status_code: { $gte: 500 },
     timestamp: { $gte: new Date(Date.now() - 60 * 60 * 1000) }
   })
   ```

2. **Slow response times**
   ```javascript
   // Find requests taking > 5 seconds
   db.api_request_logs.find({
     processing_time_ms: { $gt: 5000 },
     timestamp: { $gte: new Date(Date.now() - 60 * 60 * 1000) }
   })
   ```

3. **Unusual traffic patterns**
   ```javascript
   // Requests per minute from single IP
   db.api_request_logs.aggregate([
     {
       $match: {
         timestamp: { $gte: new Date(Date.now() - 60 * 1000) }
       }
     },
     { $group: { _id: "$user_ip", count: { $sum: 1 } } },
     { $match: { count: { $gt: 100 } } }  // > 100 req/min
   ])
   ```

## Implementation Details

### Files Modified

1. **`backend/api/request_logging_middleware.py`** (NEW)
   - `RequestLoggingMiddleware` class - Main middleware implementation
   - `_get_real_ip()` - Extracts real IP from nginx headers
   - `_extract_query_params()` - Extracts query parameters
   - `_extract_headers()` - Extracts all request headers
   - `setup_request_logging()` - Registers middleware with FastAPI

2. **`backend/api/api.py`** (MODIFIED)
   - Line 53: Import `setup_request_logging`
   - Line 120: Call `setup_request_logging()` after MongoDB connection

### Middleware Order

```
Request
  ↓
CORS Middleware
  ↓
Request Logging Middleware  ← logs request details
  ↓
API Key Verification (if required)
  ↓
Route Handler
  ↓
Response
  ↓
Request Logging Middleware  ← logs response details
  ↓
CORS Middleware
  ↓
Client
```

## Testing

### Manual Testing

1. Start the API server
2. Make a test request:
   ```bash
   curl "http://localhost:8000/api/flights?origin=WRO&destination=BCN&min_price=10"
   ```

3. Check MongoDB for the log entry:
   ```javascript
   db.api_request_logs.find().sort({ timestamp: -1 }).limit(1)
   ```

### Verify Real IP Detection

1. Add test headers to your request:
   ```bash
   curl -H "X-Real-IP: 203.0.113.42" \
        "http://localhost:8000/api/flights?origin=WRO"
   ```

2. Check that the logged IP is `203.0.113.42`:
   ```javascript
   db.api_request_logs.find({ user_ip: "203.0.113.42" })
   ```

## Troubleshooting

### Logs not appearing in MongoDB

1. Check MongoDB connection is working
2. Check for errors in API logs: `docker logs <container_name>`
3. Verify middleware is registered: Check for "Request logging middleware enabled" message on startup

### Wrong IP addresses logged

1. Verify nginx is setting proxy headers correctly
2. Check nginx configuration has `proxy_set_header X-Real-IP $remote_addr;`
3. Test by sending request with custom X-Real-IP header

### Performance issues

1. Check index creation was successful
2. Monitor MongoDB CPU/memory usage
3. Consider adding TTL index to auto-delete old logs
4. Consider reducing logged data (e.g., exclude large headers)

## Future Enhancements

Potential improvements to consider:

1. **Request body logging** - Log POST/DELETE request bodies
2. **Response body logging** - Log response data (with size limits)
3. **Sampling** - Only log a percentage of requests for high-traffic endpoints
4. **Async insertion** - Use background tasks for logging to improve performance
5. **Log rotation** - Automatically archive old logs to separate collection
6. **Analytics dashboard** - Build a UI for visualizing request patterns
7. **Rate limiting** - Use logged data to implement rate limiting per IP
8. **Anomaly detection** - Alert on unusual traffic patterns
