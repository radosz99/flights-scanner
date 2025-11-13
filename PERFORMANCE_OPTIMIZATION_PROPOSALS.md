# Performance Optimization Proposals for `/flights/round-trips-batch` Endpoint

## Executive Summary

This document outlines performance improvement proposals for the `/flights/round-trips-batch` endpoint based on detailed code analysis. The endpoint performs round-trip flight matching by combining outbound and return flights, which can be computationally expensive with large datasets.

**Current Implementation Location:** `backend/api/custom_search.py:252` (`find_round_trips_batch` method)

## Performance Logging Added

Comprehensive performance logging has been added to measure:
- Database query times for outbound and return flights
- Matching/analysis loop execution time
- Sorting time
- Detailed counters for filtering operations
- Percentage breakdown of time spent in each phase

## Current Bottlenecks Identified

### 1. **Database Queries (Lines 316, 322)**
**Current Behavior:**
- Two separate MongoDB `find()` queries fetch ALL matching flights into memory
- All results are converted to Python lists immediately
- Sorting is done in MongoDB (`sort("departure_time", ASCENDING)`)

**Potential Issues:**
- Large result sets consume significant memory
- Network transfer overhead for large datasets
- No pagination or streaming

### 2. **Nested Loop Matching (Lines 365-458) - O(n × m) Complexity**
**Current Behavior:**
- Outer loop iterates through all outbound flights (~10,000 max)
- Inner loop iterates through all return flights (~10,000 max)
- Maximum theoretical iterations: 100,000,000 (controlled by `MAX_TOTAL_COMBINATIONS`)

**Potential Issues:**
- Quadratic time complexity
- Repeated date parsing and datetime operations in inner loop
- Multiple filtering checks for each combination

### 3. **Repeated Date/Time Parsing (Lines 367, 388, 410-411)**
**Current Behavior:**
```python
outbound_date = datetime.strptime(outbound_date_str.split('T')[0], "%Y-%m-%d")  # Outer loop
return_date = datetime.strptime(return_date_str.split('T')[0], "%Y-%m-%d")      # Inner loop
outbound_arrival = datetime.fromisoformat(...)                                    # Inner loop
return_departure = datetime.fromisoformat(...)                                    # Inner loop
```

**Potential Issues:**
- String parsing is expensive and repeated millions of times
- Same outbound flight date parsed once per return flight

### 4. **Stay Duration Calculation (Lines 410-418)**
**Current Behavior:**
- Complex datetime arithmetic for every valid match
- String formatting for stay duration

**Potential Issues:**
- Performed for every valid match in inner loop
- Could be deferred or optimized

### 5. **In-Memory Sorting (Line 474)**
**Current Behavior:**
- Python's built-in sort on entire result set
- Sorts by total_price after all matches found

**Potential Issues:**
- With large result sets, sorting can be expensive
- If only top N results needed, this is wasteful

## Optimization Proposals

### 🚀 **Priority 1: Database Query Optimization**

#### **Option 1A: Add Database Indexes**
**Impact:** HIGH | **Effort:** LOW | **Risk:** LOW

```javascript
// MongoDB indexes to add
db.ryanair_flights.createIndex({ "origin": 1, "date_out": 1, "departure_time": 1 })
db.ryanair_flights.createIndex({ "destination": 1, "date_out": 1, "departure_time": 1 })
db.ryanair_flights.createIndex({ "origin": 1, "destination": 1, "date_out": 1 })
```

**Benefits:**
- Faster query execution
- Better query planning by MongoDB
- Reduced I/O operations

**Estimated Improvement:** 30-50% reduction in query time

---

#### **Option 1B: Use MongoDB Aggregation Pipeline**
**Impact:** HIGH | **Effort:** MEDIUM | **Risk:** MEDIUM

Instead of fetching all flights and matching in Python, push the matching logic to MongoDB:

```python
pipeline = [
    # Stage 1: Match outbound flights
    {"$match": outbound_query},
    {"$addFields": {
        "outbound_date": {"$dateFromString": {"dateString": {"$substr": ["$date_out", 0, 10]}}},
        "outbound_weekday": {"$dayOfWeek": {"$dateFromString": {"dateString": "$date_out"}}}
    }},

    # Stage 2: Lookup return flights (self-join)
    {"$lookup": {
        "from": "ryanair_flights",
        "let": {
            "out_destination": "$destination",
            "out_origin": "$origin",
            "out_date": "$outbound_date"
        },
        "pipeline": [
            {"$match": {
                "$expr": {
                    "$and": [
                        {"$eq": ["$origin", "$$out_destination"]},
                        {"$eq": ["$destination", "$$out_origin"]},
                        # Add date range logic here
                    ]
                }
            }}
        ],
        "as": "return_flights"
    }},

    # Stage 3: Unwind and filter
    {"$unwind": "$return_flights"},

    # Stage 4: Calculate and filter by trip duration
    {"$addFields": {
        "trip_duration": {
            "$dateDiff": {
                "startDate": "$outbound_date",
                "endDate": {"$dateFromString": {"dateString": "$return_flights.date_out"}},
                "unit": "day"
            }
        }
    }},
    {"$match": {
        "trip_duration": {"$gte": min_days, "$lte": max_days}
    }},

    # Stage 5: Sort by total price
    {"$addFields": {
        "total_price": {
            "$multiply": [
                {"$add": ["$current_price", "$return_flights.current_price"]},
                passengers
            ]
        }
    }},
    {"$sort": {"total_price": 1}},

    # Stage 6: Limit results
    {"$limit": 1000}
]
```

**Benefits:**
- Database does the heavy lifting
- Only matched results transferred over network
- Can leverage database indexes
- Built-in sorting and limiting

**Estimated Improvement:** 60-80% reduction in total time

---

### 🚀 **Priority 2: Pre-compute and Cache**

#### **Option 2A: Pre-parse Dates**
**Impact:** MEDIUM | **Effort:** LOW | **Risk:** LOW

```python
# Before loops, parse all dates once
outbound_dates = {}
for flight in outbound_flights:
    date_str = flight["date_out"].split('T')[0]
    outbound_dates[flight["flight_id"]] = datetime.strptime(date_str, "%Y-%m-%d")

return_dates = {}
for flight in return_flights:
    date_str = flight["date_out"].split('T')[0]
    return_dates[flight["flight_id"]] = datetime.strptime(date_str, "%Y-%m-%d")
```

**Benefits:**
- Eliminates repeated parsing in inner loop
- Reduces CPU usage significantly

**Estimated Improvement:** 10-15% reduction in matching phase time

---

#### **Option 2B: Build Return Flight Index**
**Impact:** MEDIUM | **Effort:** MEDIUM | **Risk:** LOW

```python
# Index return flights by origin and destination for O(1) lookup
return_index = {}
for flight in return_flights:
    key = (flight["origin"], flight["destination"])
    if key not in return_index:
        return_index[key] = []
    return_index[key].append(flight)

# Then in matching loop:
for outbound in outbound_flights:
    key = (outbound["destination"], outbound["origin"])
    matching_returns = return_index.get(key, [])
    for return_flight in matching_returns:
        # Process only relevant returns
```

**Benefits:**
- Reduces inner loop iterations dramatically
- Only processes flights that could match
- Especially effective when `return_from_same_airport=True`

**Estimated Improvement:** 40-60% reduction in matching phase time

---

### 🚀 **Priority 3: Algorithm Optimization**

#### **Option 3A: Early Termination with Heap**
**Impact:** MEDIUM | **Effort:** MEDIUM | **Risk:** LOW

If only top N results are needed (common case with `limit` parameter):

```python
import heapq

# Use min-heap to keep only top N results
max_results = 1000  # or from limit parameter
top_trips = []  # heap of (total_price, trip_data)

for outbound in outbound_flights:
    for return_flight in return_flights:
        # ... matching logic ...
        if valid_match:
            if len(top_trips) < max_results:
                heapq.heappush(top_trips, (-total_price, trip_data))
            elif total_price < -top_trips[0][0]:  # Better than worst in heap
                heapq.heapreplace(top_trips, (-total_price, trip_data))

# Extract results
round_trips = [trip for _, trip in sorted(top_trips, key=lambda x: -x[0])]
```

**Benefits:**
- Constant memory usage (only stores top N)
- No need to sort full result set
- Can stop early if prices exceed threshold

**Estimated Improvement:** 20-30% reduction in memory and sorting time

---

#### **Option 3B: Parallel Processing**
**Impact:** HIGH | **Effort:** HIGH | **Risk:** MEDIUM

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def process_outbound_chunk(outbound_chunk, return_flights, params):
    """Process a chunk of outbound flights in parallel"""
    results = []
    for outbound in outbound_chunk:
        # ... matching logic ...
    return results

# Split outbound flights into chunks
num_workers = multiprocessing.cpu_count()
chunk_size = len(outbound_flights) // num_workers
chunks = [outbound_flights[i:i+chunk_size]
          for i in range(0, len(outbound_flights), chunk_size)]

# Process in parallel
with ProcessPoolExecutor(max_workers=num_workers) as executor:
    futures = [executor.submit(process_outbound_chunk, chunk, return_flights, params)
               for chunk in chunks]
    all_results = []
    for future in futures:
        all_results.extend(future.result())
```

**Benefits:**
- Utilizes multiple CPU cores
- Significant speedup for CPU-bound matching

**Drawbacks:**
- More complex code
- Memory overhead for process spawning
- May not be compatible with all deployment environments

**Estimated Improvement:** 2-4x speedup (depending on CPU cores)

---

### 🚀 **Priority 4: Caching Strategy**

#### **Option 4A: Redis Caching**
**Impact:** HIGH | **Effort:** MEDIUM | **Risk:** LOW

```python
import redis
import hashlib
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cache_key(params):
    """Generate cache key from search parameters"""
    key_data = json.dumps(params, sort_keys=True)
    return f"round_trips:{hashlib.md5(key_data.encode()).hexdigest()}"

def find_round_trips_batch_cached(...):
    cache_key = get_cache_key({
        "origins": origins,
        "destinations": destinations,
        # ... other params
    })

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        logger.info("[CACHE] Cache hit!")
        return json.loads(cached)

    # Compute results
    results = find_round_trips_batch(...)

    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(results))

    return results
```

**Benefits:**
- Near-instant response for repeated queries
- Reduces database load
- Especially effective for popular routes

**Estimated Improvement:** 99% reduction for cached queries

---

### 🚀 **Priority 5: Response Optimization**

#### **Option 5A: Lazy Data Loading**
**Impact:** LOW | **Effort:** LOW | **Risk:** LOW

Don't compute `stay_duration` and other derived fields until actually needed:

```python
# Instead of computing immediately:
trip_data = {
    "outbound": outbound_data,
    "return": return_data,
    # Defer expensive computations
}
```

Add a separate endpoint or compute on-demand in frontend.

**Benefits:**
- Faster response for large result sets
- Reduced CPU usage

**Estimated Improvement:** 5-10% reduction in matching phase

---

#### **Option 5B: Implement Pagination at Database Level**
**Impact:** MEDIUM | **Effort:** LOW | **Risk:** LOW

```python
# Add to MongoDB aggregation
{"$skip": (page - 1) * page_size},
{"$limit": page_size}
```

**Benefits:**
- Faster response times
- Lower memory usage
- Better user experience

**Estimated Improvement:** Response time proportional to page_size

---

## Recommended Implementation Plan

### Phase 1: Quick Wins (1-2 days)
1. ✅ Add performance logging (DONE)
2. Add database indexes (Option 1A)
3. Pre-parse dates (Option 2A)
4. Build return flight index (Option 2B)

**Expected Total Improvement:** 50-70% faster

### Phase 2: Major Optimization (1 week)
1. Implement MongoDB aggregation pipeline (Option 1B)
2. Add Redis caching (Option 4A)
3. Implement pagination (Option 5B)

**Expected Total Improvement:** 80-90% faster for most queries, 99% for cached

### Phase 3: Advanced (2+ weeks)
1. Parallel processing (Option 3B) - if needed
2. Machine learning-based result ranking - if needed

## Monitoring & Validation

After implementing optimizations:

1. **Compare Performance Metrics**
   - Log query times before/after
   - Monitor database query execution plans
   - Track cache hit rates

2. **Load Testing**
   - Simulate concurrent requests
   - Test with various data sizes
   - Measure 95th percentile response times

3. **A/B Testing**
   - Run old and new implementations in parallel
   - Compare results for correctness
   - Measure real-world performance

## Potential Risks

1. **MongoDB Aggregation Complexity**
   - Complex pipelines can be hard to debug
   - May need MongoDB expertise
   - Mitigation: Thorough testing, keep old implementation as fallback

2. **Caching Staleness**
   - Cached results may become outdated
   - Mitigation: Short TTL, cache invalidation on data updates

3. **Index Overhead**
   - Indexes consume disk space
   - Slower writes (inserts/updates)
   - Mitigation: Monitor disk usage, selective indexing

## Conclusion

The `/flights/round-trips-batch` endpoint has significant optimization opportunities. The combination of database-level optimizations (indexes, aggregation) and application-level improvements (caching, pre-parsing) can yield 80-90% performance improvements.

**Priority order:**
1. Database indexes (quick, safe, high impact)
2. Pre-parsing and indexing (medium effort, high impact)
3. MongoDB aggregation pipeline (higher effort, highest impact)
4. Caching (medium effort, very high impact for repeated queries)

---

**Document Version:** 1.0
**Date:** 2025-11-12
**Author:** Performance Analysis
**File:** `/home/user/flights-scanner/PERFORMANCE_OPTIMIZATION_PROPOSALS.md`
