# Ryanair Scraper Performance Boost Analysis

## Current Implementation

### Overview
- **Current delay**: `RYANAIR_REQUEST_DELAY = 1.0` seconds (backend/config.py:47)
- **Problem**: Reducing delay to 0.5 seconds triggers **409 Conflict** errors
- **Location**: Request delay enforced in `ryanair.py:614` before each API call
- **Cookie**: Uses `fr-correlation-id` cookie for authentication

### Code Flow
```python
# ryanair.py:614
time.sleep(settings.RYANAIR_REQUEST_DELAY)  # Currently 1.0s
response = requests.get(url, params=params, headers=headers)
```

## What Triggers the Ban?

### 1. **Request Rate (Primary Factor)** 🚨
- **Evidence**: 409 Conflict when delay < 1.0s
- **Detection**: Ryanair tracks requests per time window
- **Likely implementation**:
  - Token bucket or sliding window rate limiter
  - ~1 request/second threshold per identifier
  - Burst detection (multiple quick requests)

### 2. **IP Address** 🌐
- **Likelihood**: **VERY HIGH**
- **How it works**:
  - Ryanair likely tracks request count per IP address
  - Single IP making hundreds of requests = bot behavior
- **Evidence**:
  - Standard practice for API protection
  - Most effective anti-scraping measure
  - Works even with cookie rotation

### 3. **fr-correlation-id Cookie** 🍪
- **Likelihood**: **HIGH**
- **How it works**:
  - Cookie identifies your session
  - Ryanair tracks requests per cookie
  - Multiple rapid requests with same cookie = suspicious
- **Current behavior**:
  - Cookie extracted from Selenium browser session
  - Same cookie reused for ALL requests in a scan
  - No cookie rotation implemented

### 4. **Request Patterns** 📊
- **Likelihood**: **MEDIUM**
- **Patterns Ryanair might detect**:
  - Sequential requests (WRO→ALC, WRO→BCN, WRO→MAD...)
  - Same date ranges across all routes
  - No pause between airports
  - Perfect timing intervals (exactly 1.0s)
  - Missing common browser behaviors (mouse movement, scrolling)

### 5. **User-Agent & Browser Fingerprinting** 🖥️
- **Likelihood**: **LOW-MEDIUM**
- **Current state**:
  - Using `requests` library (Python User-Agent)
  - No browser fingerprint spoofing
  - Missing headers like Accept-Language, Referer, etc.

### 6. **Session Correlation** 🔗
- **Likelihood**: **MEDIUM**
- **How it works**:
  - Ryanair links cookie extraction session to API usage
  - If same browser session extracts cookie and then hammers API = suspicious
  - Time correlation between cookie generation and heavy usage

## Possible Solutions

### ✅ Solution 1: IP Rotation (Most Effective)
**Impact**: 🟢 HIGH | **Complexity**: 🟡 MEDIUM | **Cost**: 💰 MEDIUM

#### Implementation Options:

#### A. Residential Proxy Pool
```python
# Use rotating residential proxies
PROXY_LIST = [
    "http://user:pass@proxy1.com:8080",
    "http://user:pass@proxy2.com:8080",
    # ... more proxies
]

# Rotate proxy for each request or each airport
current_proxy = random.choice(PROXY_LIST)
response = requests.get(url, proxies={"http": current_proxy, "https": current_proxy})
```

**Providers**:
- Bright Data (formerly Luminati)
- Smartproxy
- Oxylabs
- IPRoyal

**Cost**: $50-500/month depending on volume

#### B. Multiple VPN Connections
```python
# Rotate VPN connection every N requests
# Requires external VPN management (OpenVPN, WireGuard)
```

**Pros**:
- Distributes requests across multiple IPs
- Each IP appears as different user
- Most effective against IP-based rate limiting

**Cons**:
- Costs money
- Requires proxy management
- May violate Ryanair's Terms of Service

---

### ✅ Solution 2: Cookie Rotation
**Impact**: 🟡 MEDIUM | **Complexity**: 🟢 LOW | **Cost**: 💰 FREE

#### Implementation:
```python
# Extract multiple cookies in advance
cookies_pool = []
for i in range(10):
    cookie = extract_cookies_from_ryanair(save_to_db=True)
    cookies_pool.append(cookie)
    time.sleep(60)  # Wait between extractions

# Rotate during scraping
for route_idx, route in enumerate(routes):
    cookie = cookies_pool[route_idx % len(cookies_pool)]
    flights = get_ryanair_flights(..., cookies=cookie)
```

**Modification needed**:
```python
# ryanair_scanner.py - modify scan_flights() function
def scan_flights(departure_airports, date_out_str, date_in_str, cookie_pool, storage):
    for i, dest_code in enumerate(destinations):
        # Rotate cookie every N requests
        current_cookie = cookie_pool[i % len(cookie_pool)]
        flights = get_ryanair_flights(..., cookies=current_cookie)
```

**Pros**:
- Easy to implement
- No cost
- Distributes requests across multiple sessions

**Cons**:
- Limited effectiveness if IP tracking is primary factor
- Need to extract multiple cookies
- Cookies expire

---

### ✅ Solution 3: Request Randomization
**Impact**: 🟡 MEDIUM | **Complexity**: 🟢 LOW | **Cost**: 💰 FREE

#### Implementation:
```python
import random

# Randomize delay (0.8s - 1.5s instead of exactly 1.0s)
delay = random.uniform(0.8, 1.5)
time.sleep(delay)

# Randomize route order (don't scan alphabetically)
destinations = list(database.get_connections_from(airport_code))
random.shuffle(destinations)

# Add random pauses between airports
if airport_idx % 3 == 0:  # Every 3 airports
    pause = random.uniform(30, 90)  # 30-90 second break
    logger.info(f"Taking a break for {pause:.0f} seconds...")
    time.sleep(pause)
```

**Pros**:
- Easy to implement
- Makes pattern detection harder
- More human-like behavior
- Free

**Cons**:
- Limited impact on rate limiting
- Doesn't solve IP/cookie tracking

---

### ✅ Solution 4: Distributed Scraping
**Impact**: 🟢 HIGH | **Complexity**: 🔴 HIGH | **Cost**: 💰 MEDIUM-HIGH

#### Architecture:
```
┌─────────────┐
│   Master    │  Coordinates scanning tasks
│  Scheduler  │
└──────┬──────┘
       │
       ├─────────┬─────────┬─────────┐
       │         │         │         │
   ┌───▼───┐ ┌──▼────┐ ┌──▼────┐ ┌──▼────┐
   │Worker1│ │Worker2│ │Worker3│ │Worker4│
   │(IP 1) │ │(IP 2) │ │(IP 3) │ │(IP 4) │
   └───────┘ └───────┘ └───────┘ └───────┘
```

#### Implementation:
```python
# Use task queue (Celery, RQ, or simple Redis queue)
# Each worker on different machine/container with different IP

# Master
for route in all_routes:
    queue.enqueue(scrape_route, route)

# Worker (runs on separate machine)
def scrape_route(route):
    cookie = get_valid_cookie()
    flights = get_ryanair_flights(route.origin, route.dest, ...)
    save_to_mongodb(flights)
```

**Deployment**:
- Multiple Docker containers across different hosts
- Different cloud providers (AWS, GCP, Azure, DigitalOcean)
- Each worker has different public IP

**Pros**:
- Natural IP distribution
- Parallel processing (faster overall)
- Each worker can have own rate limit

**Cons**:
- Complex infrastructure
- Higher costs
- Requires orchestration

---

### ✅ Solution 5: Time-Based Distribution
**Impact**: 🟢 MEDIUM-HIGH | **Complexity**: 🟢 LOW | **Cost**: 💰 FREE

#### Implementation:
```python
# Instead of scanning all routes at once, distribute over time

# Current: Scan all 300 routes in 5 minutes (1s delay)
# Better: Scan 300 routes over 1 hour (12s average delay)

# Modify RYANAIR_REQUEST_DELAY dynamically
base_delay = 1.0
routes_count = len(all_routes)
time_budget = 3600  # 1 hour

delay_per_route = time_budget / routes_count  # e.g., 12 seconds

# Or: Scan smaller batches more frequently
# Instead of: 1 big scan every 1 hour
# Do: 6 small scans every 10 minutes (50 routes each)
```

**Pros**:
- Simple to implement
- Respects rate limits naturally
- No additional costs
- Less likely to trigger anti-bot measures

**Cons**:
- Slower overall scanning
- Data freshness reduced

---

### ✅ Solution 6: Enhanced Browser Headers
**Impact**: 🟡 LOW-MEDIUM | **Complexity**: 🟢 LOW | **Cost**: 💰 FREE

#### Implementation:
```python
# Add more realistic browser headers
headers = {
    'Cookie': cookies,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9,pl;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.ryanair.com/',
    'Origin': 'https://www.ryanair.com',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Connection': 'keep-alive',
}
```

**Pros**:
- Easy to implement
- More realistic requests
- May bypass simple bot detection

**Cons**:
- Limited impact on rate limiting
- Ryanair likely uses more sophisticated detection

---

### ✅ Solution 7: Respect Rate Limits + Optimize Other Factors
**Impact**: 🟢 MEDIUM | **Complexity**: 🟢 LOW | **Cost**: 💰 FREE

#### Keep 1.0s delay but optimize:
```python
# 1. Parallel cookie extraction (prepare pool in advance)
# 2. Cache database queries (don't reload DB each time)
# 3. Batch MongoDB writes (reduce I/O)
# 4. Skip unnecessary date ranges (past dates, too far future)
# 5. Smart scanning (only scan routes with history of good prices)
```

**Pros**:
- Safe and compliant
- No risk of getting banned
- Can still optimize total time

**Cons**:
- Won't get below 1s per request
- Limited speed improvement

---

## Recommended Strategy

### 🎯 Tier 1: Quick Wins (Implement First)
**Estimated time**: 2-4 hours | **Risk**: Low | **Cost**: Free

1. **Request randomization** (Solution 3)
   - Random delays (0.8-1.5s)
   - Shuffle route order
   - Add breaks between airports

2. **Enhanced headers** (Solution 6)
   - Add realistic browser headers
   - Rotate User-Agent strings

3. **Cookie rotation** (Solution 2)
   - Extract 5-10 cookies upfront
   - Rotate during scanning

### 🎯 Tier 2: Significant Impact (If Tier 1 isn't enough)
**Estimated time**: 1-2 days | **Risk**: Medium | **Cost**: $50-200/month

4. **IP Rotation with residential proxies** (Solution 1)
   - Start with small proxy pool (10-20 IPs)
   - Rotate per airport or per N requests
   - Monitor for 409 errors

5. **Time-based distribution** (Solution 5)
   - Spread scans over longer periods
   - Multiple smaller scans vs one big scan

### 🎯 Tier 3: Enterprise Scale (For serious production use)
**Estimated time**: 1-2 weeks | **Risk**: Low | **Cost**: $200-1000/month

6. **Distributed scraping** (Solution 4)
   - Deploy workers on multiple cloud providers
   - Each worker: different IP + own cookies
   - Central coordination via task queue

---

## Testing Methodology

### Experiment to find the ban threshold:

```python
# Test script
delays = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
results = {}

for delay in delays:
    settings.RYANAIR_REQUEST_DELAY = delay
    success_count = 0
    error_count = 0

    for i in range(20):  # Test with 20 requests
        try:
            flights = get_ryanair_flights(...)
            success_count += 1
        except Exception as e:
            if '409' in str(e):
                error_count += 1
                break  # Stop on first 409

    results[delay] = {
        'success': success_count,
        'errors': error_count,
        'ban_threshold': error_count > 0
    }

    print(f"Delay {delay}s: {success_count} success, {error_count} 409 errors")
    time.sleep(300)  # 5 min cooldown between tests
```

### Metrics to track:
- Delay where 409 first appears
- Number of successful requests before ban
- Recovery time after 409
- Impact of different solutions on success rate

---

## Legal & Ethical Considerations

⚠️ **Important**: Web scraping may violate Ryanair's Terms of Service

### Alternatives to consider:
1. **Official API**: Check if Ryanair offers a partner API
2. **Affiliate programs**: Join Ryanair affiliate program for legitimate access
3. **Rate-limited scraping**: Stay well under abuse thresholds (current 1.0s is good)
4. **Respect robots.txt**: Check Ryanair's robots.txt for allowed/disallowed paths
5. **Terms of Service**: Review Ryanair's ToS regarding automated access

### Best practices:
- Identify your bot (custom User-Agent with contact email)
- Implement exponential backoff on errors
- Don't resell Ryanair's data without permission
- Cache aggressively to minimize requests
- Consider reaching out to Ryanair for permission

---

## Conclusion

### What's causing the 409 ban?
**Primary factors (in order)**:
1. **Request rate from single IP** (most likely)
2. **Cookie-based session tracking** (likely)
3. **Request patterns** (moderate)
4. **Browser fingerprinting** (less likely)

### Best approach to boost without ban:

**Conservative approach (recommended)**:
- Keep 1.0s delay (respect rate limits)
- Implement cookie rotation
- Add request randomization
- Consider time-based distribution

**Aggressive approach (higher risk)**:
- Implement IP rotation via proxies
- Combine with cookie rotation
- Add randomization
- Monitor closely for bans

**Enterprise approach (production-ready)**:
- Distributed architecture
- Multiple IPs across cloud providers
- Sophisticated retry logic
- Monitoring and alerting

### My recommendation:
Start with **Tier 1 solutions** (free, low risk). If you need more speed and willing to pay, add **residential proxies** (Tier 2). The combination of IP rotation + cookie rotation + randomization should allow you to reduce delay to 0.5s or even lower without triggering bans.

---

**Questions to guide your decision**:
1. How much faster do you need? (2x, 5x, 10x?)
2. What's your budget? ($0, $50/month, $500/month?)
3. What's your risk tolerance? (Don't want to get banned vs willing to test limits)
4. Is this for personal use or commercial?

Based on your answers, I can provide more specific implementation guidance.
