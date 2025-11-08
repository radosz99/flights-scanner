# Automatic Flight Scanning Every 8 Hours

This guide explains how to set up automatic scanning every 8 hours (at 00:00, 08:00, and 16:00 daily).

## Configuration

Default scan parameters:
- **Trip Duration**: 7 days (changed from 4)
- **Flex Days**: 3 days before/after for both outbound and return (changed from 2)
- **Scan Until**: 365 days from now
- **Departure Airports**: All Polish airports

You can customize these via environment variables in `trigger_scan.py`:
```bash
export API_URL="http://localhost:8000"
export TRIP_DURATION_DAYS="7"
export SCAN_UNTIL_DAYS="365"
```

## Option 1: Systemd Timer (Recommended for Production)

**Best for**: Linux servers, production deployments
**Pros**: More reliable, better logging, survives reboots, resource-aware
**Cons**: Requires sudo/root access

### Setup
```bash
sudo ./setup_systemd.sh
```

### Useful Commands
```bash
# Check timer status
systemctl status flight-scanner.timer

# List next scheduled runs
systemctl list-timers

# View logs
journalctl -u flight-scanner.service -f

# Run manually now
sudo systemctl start flight-scanner.service

# Stop timer
sudo systemctl stop flight-scanner.timer

# Disable timer
sudo systemctl disable flight-scanner.timer
```

---

## Option 2: Cron Job (Simpler Setup)

**Best for**: Development, personal use, no sudo access
**Pros**: Simple, no root required, widely supported
**Cons**: Less robust, no built-in logging

### Setup
```bash
./setup_cron.sh
```

This will add a cron job to your user's crontab.

### Useful Commands
```bash
# View crontab
crontab -l

# Edit crontab manually
crontab -e

# View logs
tail -f logs/scan_trigger.log

# Remove cron job
crontab -e
# Delete the line containing 'trigger_scan.py'
```

---

## Option 3: Docker Compose with Scheduler

Add a scheduler service to your `docker-compose.yml`:

```yaml
services:
  # ... existing services ...

  scheduler:
    image: python:3.11-slim
    container_name: flights-scanner-scheduler
    volumes:
      - ./trigger_scan.py:/app/trigger_scan.py
      - ./logs:/app/logs
    environment:
      - API_URL=http://backend:8000
      - TRIP_DURATION_DAYS=7
      - SCAN_UNTIL_DAYS=365
    command: >
      sh -c "pip install requests loguru &&
             echo '0 0,8,16 * * * cd /app && python3 /app/trigger_scan.py >> /app/logs/scan.log 2>&1' | crontab - &&
             crond -f -l 2"
    depends_on:
      - backend
    restart: unless-stopped
```

Then run:
```bash
docker-compose up -d scheduler
```

---

## Option 4: Manual Trigger

You can also trigger scans manually:

### Via Python Script
```bash
python3 trigger_scan.py
```

### Via API Call
```bash
curl -X POST http://localhost:8000/scans/run \
  -H "Content-Type: application/json" \
  -d '{
    "trip_duration_days": 7,
    "scan_until_date": "2025-12-31"
  }'
```

### Via Frontend
Navigate to the main page and click "Trigger New Scan"

---

## Monitoring

### Check Latest Scan Status

**Via API:**
```bash
curl http://localhost:8000/scans/latest
```

**Via Frontend:**
Visit the homepage to see the latest scan status with progress, statistics, and date ranges.

### View Scan History
```bash
curl http://localhost:8000/scans?limit=10
```

---

## Logs

### Systemd Timer
```bash
journalctl -u flight-scanner.service -f
```

### Cron Job
```bash
tail -f logs/scan_trigger.log
```

### Docker
```bash
docker logs -f flights-scanner-scheduler
```

---

## Troubleshooting

### Scans Not Running

1. **Check if scheduler is active:**
   ```bash
   # Systemd
   systemctl status flight-scanner.timer

   # Cron
   crontab -l

   # Docker
   docker ps | grep scheduler
   ```

2. **Check logs for errors:**
   ```bash
   # Systemd
   journalctl -u flight-scanner.service --since "1 hour ago"

   # Cron
   tail -50 logs/scan_trigger.log
   ```

3. **Verify API is accessible:**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Test manual trigger:**
   ```bash
   python3 trigger_scan.py
   ```

### Scans Taking Too Long

The scanner processes all Polish airports and all their destinations. Expected duration:
- **Small dataset**: 15-30 minutes
- **Medium dataset**: 30-60 minutes
- **Large dataset**: 1-2 hours

Monitor progress at: `http://localhost:8000/scans/latest`

### High Resource Usage

If scans consume too many resources:

1. **Reduce scan frequency** (e.g., every 12 hours instead of 8):
   - Systemd: Edit timer to `OnCalendar=*-*-* 00,12:00:00`
   - Cron: Change to `0 0,12 * * *`

2. **Limit scan date range**:
   ```bash
   export SCAN_UNTIL_DAYS="180"  # 6 months instead of 12
   ```

3. **Add resource limits** (Docker):
   ```yaml
   scheduler:
     # ... other config ...
     deploy:
       resources:
         limits:
           cpus: '0.5'
           memory: 512M
   ```

---

## Schedule Examples

### Every 6 Hours
- Systemd: `OnCalendar=*-*-* 00,06,12,18:00:00`
- Cron: `0 0,6,12,18 * * *`

### Every 12 Hours
- Systemd: `OnCalendar=*-*-* 00,12:00:00`
- Cron: `0 0,12 * * *`

### Once Daily at 2 AM
- Systemd: `OnCalendar=*-*-* 02:00:00`
- Cron: `0 2 * * *`

### Twice Daily (Morning and Evening)
- Systemd: `OnCalendar=*-*-* 06,18:00:00`
- Cron: `0 6,18 * * *`
