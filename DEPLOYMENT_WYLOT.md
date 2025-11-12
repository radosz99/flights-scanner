# Deployment Guide for wylot.eu

This guide assumes you have:
- ✅ Server at 162.55.46.15 with Docker and Docker Compose installed
- ✅ DNS configured (wylot.eu → 162.55.46.15)
- ✅ Repository already cloned to `/opt/flights-scanner`

**Domain**: wylot.eu | **Server IP**: 162.55.46.15 | **Scan Period**: 140 days

---

## 1. Configure Environment

Navigate to your application directory:

```bash
cd /opt/flights-scanner
```

### Create .env file

Copy the example file and edit it:

```bash
cp .env.example .env
nano .env
```

### Configure Required Settings

Update the following sections in your `.env` file:

#### MongoDB Authentication (IMPORTANT - Set Strong Passwords!)

```env
# MongoDB Authentication
MONGO_USERNAME=admin
MONGO_PASSWORD=YOUR_STRONG_PASSWORD_HERE
```

**⚠️ Security Note**: Replace `YOUR_STRONG_PASSWORD_HERE` with a strong password. Never commit this file to version control!

#### Port Configuration

For production deployment, verify these ports are correct:

```env
# Ports
BACKEND_PORT=8900
FRONTEND_PORT=8901
MONGO_EXTERNAL_PORT=8902  # Optional: comment out to disable external MongoDB access
```

#### Worker Configuration (Optional)

Adjust based on your server resources:

```env
# Performance Tuning
GUNICORN_WORKERS=4        # Number of API workers
MAX_SCAN_WORKERS=4        # Background scan threads
WORKER_TIMEOUT=300        # Request timeout in seconds
```

#### Scheduler Configuration

Already configured for wylot.eu (140 days scan period):

```env
# Scheduler (pre-configured for wylot.eu)
SCAN_UNTIL_DAYS=140
TRIP_DURATION_DAYS=7
```

### Secure Your Environment File

```bash
chmod 600 .env
```

---

## 2. Start the Application

### Start Production Services

Start all services including nginx reverse proxy:

```bash
docker-compose --profile production up -d
```

### Monitor Startup

Watch the logs to ensure everything starts correctly:

```bash
docker-compose logs -f
```

Press `Ctrl+C` to stop following logs (services continue running).

### Verify All Services Are Running

```bash
docker-compose ps
```

Expected output - all services should show "Up" status:
```
NAME                          STATUS
flights-scanner-backend       Up (healthy)
flights-scanner-certbot       Up
flights-scanner-frontend      Up (healthy)
flights-scanner-mongo         Up (healthy)
flights-scanner-nginx         Up (healthy)
flights-scanner-scheduler     Up
```

---

## 3. Set Up SSL/HTTPS

Once DNS is propagated and services are running, obtain SSL certificate:

```bash
./init-letsencrypt.sh wylot.eu your-email@example.com
```

Replace `your-email@example.com` with your actual email for certificate notifications.

**This script will:**
- Obtain SSL certificates from Let's Encrypt
- Configure nginx with HTTPS
- Set up automatic certificate renewal (every 12 hours)
- Redirect all HTTP traffic to HTTPS

---

## 4. Verify Deployment

### Test API Health

```bash
curl https://wylot.eu/api/health
```

Expected response:
```json
{"status":"healthy","database":"connected","collections":{"flights":0,"scan_iterations":0}}
```

### Test in Browser

1. Navigate to: **https://wylot.eu**
2. You should see the Flights Scanner interface
3. Check for valid SSL certificate (padlock icon)

### Test API Endpoints

```bash
# Get available origins
curl https://wylot.eu/api/airports/origins

# Get flight statistics
curl https://wylot.eu/api/flights/stats/summary
```

---

## 5. Initial Data Population (Optional)

Populate airport databases for map visualizations and route data:

```bash
# Trigger airport population via API
curl -X POST https://wylot.eu/api/airports/populate

# Update airport coordinates
curl -X POST https://wylot.eu/api/airports/update-coordinates \
  -H "Content-Type: application/json" \
  -d '{"airline": "ryanair"}'
```

Check backend logs to monitor progress:

```bash
docker-compose logs -f backend
```

---

## 6. Trigger First Flight Scan

The scheduler runs automatically every 8 hours, but you can trigger a manual scan immediately:

```bash
curl -X POST https://wylot.eu/api/scans/run \
  -H "Content-Type: application/json" \
  -d '{
    "trip_duration_days": 7,
    "scan_until_date": "2026-05-31"
  }'
```

Check scan progress:

```bash
# Get latest scan status
curl https://wylot.eu/api/scans/latest

# Watch backend logs
docker-compose logs -f backend
```

---

## Maintenance Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific services
docker-compose logs -f backend
docker-compose logs -f scheduler
docker-compose logs -f nginx
docker-compose logs -f mongodb
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart scheduler
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes database!)
docker-compose down -v
```

### Update Application

```bash
cd /opt/flights-scanner

# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose --profile production build --no-cache
docker-compose --profile production up -d
```

### Backup Database

```bash
# Create backup directory
mkdir -p ~/backups

# Backup MongoDB
docker-compose exec mongodb mongodump \
  --username admin \
  --password YOUR_PASSWORD \
  --authenticationDatabase admin \
  --db flights_scanner \
  --out /tmp/backup

# Copy to host
docker cp flights-scanner-mongo:/tmp/backup ~/backups/backup-$(date +%Y%m%d-%H%M%S)

# Compress backup
cd ~/backups
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz backup-$(date +%Y%m%d-%H%M%S)
```

### Restore Database

```bash
# Extract backup
cd ~/backups
tar -xzf backup-YYYYMMDD-HHMMSS.tar.gz

# Copy to container
docker cp backup-YYYYMMDD-HHMMSS flights-scanner-mongo:/tmp/restore

# Restore
docker-compose exec mongodb mongorestore \
  --username admin \
  --password YOUR_PASSWORD \
  --authenticationDatabase admin \
  --db flights_scanner \
  /tmp/restore/flights_scanner
```

---

## Monitoring

### Check Service Health

```bash
# Container status
docker-compose ps

# Resource usage
docker stats

# Disk usage
docker system df
```

### Health Endpoints

```bash
# Backend health
curl https://wylot.eu/api/health

# Check latest scan
curl https://wylot.eu/api/scans/latest
```

### View Recent Errors

```bash
# All errors
docker-compose logs --tail=100 | grep -i error

# Backend errors only
docker-compose logs backend --tail=100 | grep -i error
```

### Monitor Scheduler

```bash
# View scheduler logs
docker-compose logs -f scheduler

# Check when next scan will run (runs every 8 hours)
docker-compose logs scheduler --tail=50 | grep "TRIGGERING FLIGHT SCAN"
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check what's using your ports
sudo netstat -tulpn | grep -E ':80|:443|:8900|:8901'

# Check detailed logs
docker-compose logs

# Restart from scratch
docker-compose down
docker-compose --profile production up -d
```

### Database Connection Fails

```bash
# Test MongoDB connection
docker-compose exec mongodb mongosh \
  -u admin \
  -p YOUR_PASSWORD \
  --authenticationDatabase admin \
  --eval "db.adminCommand('ping')"

# Check MongoDB logs
docker-compose logs mongodb

# Verify .env credentials match
grep MONGO .env

# Restart MongoDB
docker-compose restart mongodb
```

### SSL Certificate Issues

```bash
# Verify DNS points to your server
nslookup wylot.eu
dig wylot.eu

# Check nginx configuration
docker-compose exec nginx nginx -t

# Check certbot logs
docker-compose logs certbot

# Manually request certificate
docker-compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d wylot.eu
```

### Backend API Not Responding

```bash
# Check if backend is healthy
docker-compose ps backend

# Check backend logs
docker-compose logs backend --tail=100

# Test internal connection
docker-compose exec nginx curl http://backend:8900/health

# Restart backend
docker-compose restart backend
```

### Scheduler Not Running Scans

```bash
# Check scheduler logs
docker-compose logs scheduler --tail=50

# Verify scheduler is running
docker-compose ps scheduler

# Check scheduler environment variables
docker-compose exec scheduler env | grep -E 'API_URL|TRIP_DURATION|SCAN_UNTIL'

# Manually trigger scan
curl -X POST https://wylot.eu/api/scans/run \
  -H "Content-Type: application/json" \
  -d '{"trip_duration_days": 7}'
```

---

## Configuration Reference

### Automated Scanning Schedule

The scheduler automatically triggers flight scans:
- **Frequency**: Every 8 hours (00:00, 08:00, 16:00 UTC)
- **Scan Period**: 140 days from scan date
- **Trip Duration**: 7 days
- **Airports**: All Polish airports (GDN, SZN, KRK, KTW, WRO, POZ, WMI, WAW, LCJ, LUZ, RZE, SZY, BZG)

### Environment Variables Reference

For complete list of available configuration options, see `.env.example`:

```bash
cat .env.example
```

Key sections:
- **MongoDB Configuration**: Database connection and authentication
- **Ryanair Scraping Configuration**: Cookie extraction, request delays
- **Backend API Configuration**: Worker processes, timeouts, scan threads
- **Scheduler Configuration**: Scan frequency and duration

---

## Security Checklist

- ✅ Strong password set in `.env` for MongoDB
- ✅ `.env` file has restricted permissions (600)
- ✅ MongoDB external port disabled (or firewalled)
- ✅ SSL/HTTPS enabled and working
- ✅ Firewall configured (only ports 22, 80, 443 open)
- ✅ Automated SSL certificate renewal configured
- ⬜ Set up automated database backups (recommended)
- ⬜ Set up monitoring/alerts (recommended)

---

## Quick Commands Reference

```bash
# Start production services
docker-compose --profile production up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart all services
docker-compose restart

# Update application
cd /opt/flights-scanner && git pull && docker-compose down && docker-compose --profile production build && docker-compose --profile production up -d

# Backup database
docker-compose exec mongodb mongodump --username admin --password YOUR_PASSWORD --authenticationDatabase admin --db flights_scanner --out /tmp/backup && docker cp flights-scanner-mongo:/tmp/backup ~/backups/backup-$(date +%Y%m%d)

# Check health
curl https://wylot.eu/api/health

# Trigger manual scan
curl -X POST https://wylot.eu/api/scans/run -H "Content-Type: application/json" -d '{"trip_duration_days": 7}'

# View scan status
curl https://wylot.eu/api/scans/latest
```

---

## Additional Resources

- [.env.example](.env.example) - Complete configuration reference
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [README.md](README.md) - Application overview

---

**🎉 Your application is now deployed at https://wylot.eu!**
