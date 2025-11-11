# Flights Scanner - Deployment Guide

This guide provides comprehensive instructions for deploying the Flights Scanner application on a VPS with a custom domain.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Production Deployment](#production-deployment)
  - [1. Server Setup](#1-server-setup)
  - [2. Domain Configuration](#2-domain-configuration)
  - [3. Application Setup](#3-application-setup)
  - [4. Environment Configuration](#4-environment-configuration)
  - [5. Starting the Application](#5-starting-the-application)
  - [6. SSL/HTTPS Setup](#6-sslhttps-setup)
- [Maintenance](#maintenance)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Backup and Recovery](#backup-and-recovery)

## Prerequisites

- VPS or dedicated server with:
  - Ubuntu 20.04+ or Debian 11+ (recommended)
  - Minimum 2GB RAM (4GB+ recommended for production)
  - 20GB+ available disk space
  - Root or sudo access
- Domain name pointing to your server's IP address
- Docker and Docker Compose installed

## Architecture Overview

The application consists of five services orchestrated with Docker Compose:

1. **nginx** - Reverse proxy and SSL termination (port 80/443)
2. **frontend** - Nuxt.js web application (internal port 8901)
3. **backend** - FastAPI REST API (internal port 8900)
4. **mongodb** - Database (internal port 27017, optional external 8902)
5. **scheduler** - Automated scan scheduler (runs every 8 hours)

```
Internet → nginx (80/443) → frontend (8901)
                           → backend (8900) → mongodb (27017)
                                            ↑
                           scheduler --------
```

## Quick Start

For local testing without SSL:

```bash
# Clone the repository
git clone <repository-url>
cd flights-scanner

# Copy environment files
cp .env.example .env
cp mongo.env.example mongo.env

# Start all services
docker-compose up -d

# Access the application
open http://localhost
```

## Production Deployment

### 1. Server Setup

#### Install Docker

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### Configure Firewall

```bash
# Allow SSH (important - don't lock yourself out!)
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### 2. Domain Configuration

Point your domain's DNS A record to your server's IP address:

```
Type: A
Name: @ (or your subdomain)
Value: <your-server-ip>
TTL: 3600
```

Wait for DNS propagation (can take up to 48 hours, usually faster).

Verify DNS is working:
```bash
nslookup your-domain.com
# Should return your server's IP address
```

### 3. Application Setup

#### Clone and Configure

```bash
# Create application directory
mkdir -p /opt/flights-scanner
cd /opt/flights-scanner

# Clone repository
git clone <repository-url> .

# Create environment files from examples
cp .env.example .env
cp mongo.env.example mongo.env
```

#### Edit Environment Files

**Edit `.env`** (Frontend configuration):

```bash
nano .env
```

Update the following variables:

```env
# Backend API URL - use your domain
NUXT_PUBLIC_API_BASE_URL=https://your-domain.com/api

# Optional: Analytics, monitoring, etc.
```

**Edit `mongo.env`** (Database configuration):

```bash
nano mongo.env
```

Update MongoDB credentials:

```env
# MongoDB Authentication
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=<strong-password-here>

# MongoDB Connection String
MONGO_URI=mongodb://admin:<strong-password-here>@mongodb:27017/
MONGO_DATABASE=flights_scanner

# IMPORTANT: Use strong passwords in production!
```

**Edit `.env` for Docker Compose** (Optional):

```bash
# Add these to .env or create a separate file
nano .env
```

```env
# Port Configuration (defaults shown)
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
BACKEND_PORT=8900  # Internal only with nginx
FRONTEND_PORT=8901 # Internal only with nginx
MONGO_EXTERNAL_PORT=8902  # Remove or set to comment out for production

# Worker Configuration
GUNICORN_WORKERS=4
MAX_SCAN_WORKERS=4
WORKER_TIMEOUT=300
```

### 4. Environment Configuration

#### Security Hardening

1. **Disable MongoDB external port in production**:

   Edit `docker-compose.yml` and comment out the MongoDB ports section:

   ```yaml
   # Comment these lines for production:
   # ports:
   #   - "${MONGO_EXTERNAL_PORT:-8902}:27017"
   ```

2. **Use strong passwords** in `mongo.env`

3. **Set appropriate file permissions**:
   ```bash
   chmod 600 .env mongo.env
   ```

#### Performance Tuning

For production workloads, adjust worker settings in `.env`:

```env
# For high-traffic scenarios
GUNICORN_WORKERS=8
MAX_SCAN_WORKERS=6

# For memory-constrained environments
GUNICORN_WORKERS=2
MAX_SCAN_WORKERS=2
```

### 5. Starting the Application

#### Build and Start Services

```bash
# Build all images
docker-compose build

# Start all services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

#### Verify Deployment

1. **Check all services are running**:
   ```bash
   docker-compose ps
   # All services should show "Up" and "healthy"
   ```

2. **Test health endpoints**:
   ```bash
   # Via nginx (external, HTTP for now)
   curl http://your-domain.com/api/health

   # Should return: {"status":"ok"}
   ```

3. **Access the web interface**:
   - Navigate to `http://your-domain.com`
   - You should see the Flights Scanner interface

4. **Test API**:
   ```bash
   curl http://your-domain.com/api/airports
   # Should return a list of airports
   ```

### 6. SSL/HTTPS Setup

**For production, you should enable SSL/HTTPS.** This has been fully automated!

Simply run:

```bash
./init-letsencrypt.sh your-domain.com your-email@example.com
```

This single command will:
- Automatically obtain SSL certificates from Let's Encrypt
- Configure nginx with HTTPS and security best practices
- Set up automatic certificate renewal (every 60 days)
- Redirect all HTTP traffic to HTTPS

**For detailed SSL setup instructions and troubleshooting, see [SSL_SETUP.md](SSL_SETUP.md)**

After running the script, verify HTTPS is working:

```bash
# Test HTTPS
curl https://your-domain.com/api/health

# Verify HTTP redirects to HTTPS
curl -I http://your-domain.com
# Should return 301 redirect to https://
```

**Note:** If you don't need SSL (e.g., for local development or testing), you can skip this step entirely. The application works fine over HTTP.

## Maintenance

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f nginx
docker-compose logs -f scheduler

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Updating the Application

```bash
cd /opt/flights-scanner

# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Clean up old images
docker image prune -f
```

### Managing Services

```bash
# Stop all services
docker-compose down

# Stop specific service
docker-compose stop backend

# Restart specific service
docker-compose restart backend

# Restart all services
docker-compose restart

# View resource usage
docker stats
```

### Database Management

#### Backup MongoDB

```bash
# Create backup directory
mkdir -p backups

# Backup database
docker-compose exec mongodb mongodump \
  --username admin \
  --password <your-password> \
  --authenticationDatabase admin \
  --db flights_scanner \
  --out /tmp/backup

# Copy backup to host
docker cp flights-scanner-mongo:/tmp/backup ./backups/backup-$(date +%Y%m%d-%H%M%S)

# Create automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/flights-scanner/backups"
DATE=$(date +%Y%m%d-%H%M%S)
mkdir -p $BACKUP_DIR

docker-compose exec -T mongodb mongodump \
  --username admin \
  --password <your-password> \
  --authenticationDatabase admin \
  --db flights_scanner \
  --archive=/tmp/backup-$DATE.gz \
  --gzip

docker cp flights-scanner-mongo:/tmp/backup-$DATE.gz $BACKUP_DIR/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup-*.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# Schedule daily backups at 3 AM
(crontab -l 2>/dev/null; echo "0 3 * * * cd /opt/flights-scanner && ./backup.sh >> /var/log/flights-scanner-backup.log 2>&1") | crontab -
```

#### Restore MongoDB

```bash
# Stop the backend and scheduler
docker-compose stop backend scheduler

# Restore from backup
docker-compose exec -T mongodb mongorestore \
  --username admin \
  --password <your-password> \
  --authenticationDatabase admin \
  --db flights_scanner \
  --archive=/tmp/backup.gz \
  --gzip \
  --drop

# Restart services
docker-compose start backend scheduler
```

## Monitoring

### Health Checks

Create a monitoring script:

```bash
cat > monitor.sh << 'EOF'
#!/bin/bash

echo "=== Service Status ==="
docker-compose ps

echo ""
echo "=== Health Checks ==="
curl -f https://your-domain.com/api/health && echo " ✓ API healthy" || echo " ✗ API unhealthy"

echo ""
echo "=== Resource Usage ==="
docker stats --no-stream

echo ""
echo "=== Disk Usage ==="
df -h | grep -E "Filesystem|/dev/"

echo ""
echo "=== Recent Errors (last 50 lines) ==="
docker-compose logs --tail=50 | grep -i error || echo "No recent errors"
EOF

chmod +x monitor.sh

# Run monitoring
./monitor.sh
```

### Setup Monitoring Alerts (Optional)

For production, consider integrating:
- **Prometheus** + **Grafana** for metrics
- **Uptime Robot** or **Pingdom** for uptime monitoring
- **Sentry** for error tracking

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Check if port is already in use
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### SSL Certificate Issues

```bash
# Test certificate
docker-compose exec certbot certbot certificates

# Renew manually
docker-compose exec certbot certbot renew --force-renewal
docker-compose exec nginx nginx -s reload

# Check nginx configuration
docker-compose exec nginx nginx -t
```

For more SSL troubleshooting, see [SSL_SETUP.md](SSL_SETUP.md#troubleshooting)

### Database Connection Issues

```bash
# Check if MongoDB is running
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Check connection string in mongo.env
# Verify username/password are correct

# Restart MongoDB
docker-compose restart mongodb
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Reduce workers in .env
GUNICORN_WORKERS=2
MAX_SCAN_WORKERS=2

# Restart
docker-compose restart backend
```

### Scanner Not Working

```bash
# Check scheduler logs
docker-compose logs scheduler

# Check backend logs
docker-compose logs backend | grep -i scan

# Manually trigger a scan via API
curl -X POST https://your-domain.com/api/scans/run \
  -H "Content-Type: application/json" \
  -d '{"trip_duration_days": 7}'

# Check scan status
curl https://your-domain.com/api/scans/latest
```

## Backup and Recovery

### Complete System Backup

```bash
# Create backup directory
mkdir -p /backup/flights-scanner

# Backup configuration
cp -r /opt/flights-scanner/.env /backup/flights-scanner/
cp -r /opt/flights-scanner/mongo.env /backup/flights-scanner/
cp -r /opt/flights-scanner/nginx /backup/flights-scanner/

# Backup database
./backup.sh

# Backup SSL certificates (if using SSL)
cp -r certbot/conf /backup/flights-scanner/certbot-conf
```

### Disaster Recovery

```bash
# On new server, follow server setup steps 1-2

# Restore application
cd /opt
git clone <repository-url> flights-scanner
cd flights-scanner

# Restore configuration
cp /backup/flights-scanner/.env .
cp /backup/flights-scanner/mongo.env .
cp -r /backup/flights-scanner/nginx .

# Restore SSL certificates (if you have a backup)
cp -r /backup/flights-scanner/certbot-conf certbot/conf

# OR set up SSL fresh (recommended)
# See step 6 in production deployment or run:
# ./init-letsencrypt.sh your-domain.com your-email@example.com

# Start services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Restore database
docker cp /backup/flights-scanner/backups/latest.gz flights-scanner-mongo:/tmp/
docker-compose exec -T mongodb mongorestore \
  --username admin \
  --password <password> \
  --authenticationDatabase admin \
  --db flights_scanner \
  --archive=/tmp/latest.gz \
  --gzip
```

## Performance Optimization

### For High-Traffic Deployments

1. **Increase Nginx worker connections**:

   Edit `nginx/nginx.conf`:
   ```nginx
   events {
       worker_connections 2048;
   }
   ```

2. **Scale workers**:

   Edit `.env`:
   ```env
   GUNICORN_WORKERS=16
   MAX_SCAN_WORKERS=8
   ```

3. **Enable Redis caching** (future enhancement):
   - Add Redis service to `docker-compose.yml`
   - Configure backend to use Redis for caching

4. **Setup CDN** (optional):
   - Use Cloudflare or similar CDN
   - Configure nginx to set appropriate cache headers

## Security Checklist

- [ ] Strong passwords in `mongo.env`
- [ ] MongoDB external port disabled in production
- [ ] SSL/TLS certificates configured and auto-renewing
- [ ] Firewall configured (only 22, 80, 443 open)
- [ ] Environment files have restricted permissions (600)
- [ ] Regular backups scheduled
- [ ] Monitoring and alerting configured
- [ ] System packages kept up to date
- [ ] Docker images kept up to date

## Support and Resources

- **Repository**: <repository-url>
- **Issues**: <repository-url>/issues
- **Documentation**: See README.md for application details

## License

See LICENSE file in the repository.
