# Deployment Guide for wylot.eu

This is your customized deployment guide for deploying the Flights Scanner application to **wylot.eu** (IP: 162.55.46.15).

## Quick Reference

- **Domain**: wylot.eu
- **Server IP**: 162.55.46.15
- **Scan Until Days**: 140 days from each scan date

## Step-by-Step Deployment

### 1. Configure DNS

First, point your domain to your server:

1. Log in to your domain registrar (where you bought wylot.eu)
2. Go to DNS settings
3. Add/update an A record:
   ```
   Type: A
   Name: @ (or leave blank for root domain)
   Value: 162.55.46.15
   TTL: 3600 (or default)
   ```

4. If you want www subdomain, add another A record:
   ```
   Type: A
   Name: www
   Value: 162.55.46.15
   TTL: 3600
   ```

5. Wait for DNS propagation (5 minutes to 48 hours). Verify with:
   ```bash
   nslookup wylot.eu
   # Should return 162.55.46.15
   ```

### 2. Server Setup

SSH into your server at 162.55.46.15:

```bash
ssh root@162.55.46.15
# or
ssh your-username@162.55.46.15
```

#### Install Docker and Docker Compose

```bash
# Update system
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
# Allow SSH (IMPORTANT - don't lock yourself out!)
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### 3. Deploy the Application

#### Clone Repository

```bash
# Create application directory
mkdir -p /opt/flights-scanner
cd /opt/flights-scanner

# Clone your repository
git clone <your-repository-url> .
# Or if you have the code locally, upload it via scp
```

#### Configure Environment

1. **MongoDB configuration is now in .env`):
   ```bash
   # MongoDB configuration is now in .env
   ```

   Add:
   ```env
   # MongoDB Configuration
   MONGO_HOST=mongodb
   MONGO_PORT=27017
   MONGO_DATABASE=flights_scanner

   # IMPORTANT: Set strong passwords!
   MONGO_INITDB_ROOT_USERNAME=admin
   MONGO_INITDB_ROOT_PASSWORD=YOUR_STRONG_PASSWORD_HERE

   # MongoDB Connection String (use the same password as above)
   MONGO_URI=mongodb://admin:YOUR_STRONG_PASSWORD_HERE@mongodb:27017/

   # Airline IDs
   RYANAIR_AIRLINE_ID=39
   WIZZAIR_AIRLINE_IDS=52,6002,6092

   # Ryanair Scraping Configuration
   RYANAIR_REQUEST_DELAY=0.5
   RYANAIR_COOKIE_WAIT_TIME=30
   RYANAIR_COOKIE_CHECK_INTERVAL=0.5
   ```

2. **Create Frontend configuration** (`.env`):
   ```bash
   nano .env
   ```

   Add:
   ```env
   # Frontend Configuration
   NUXT_PUBLIC_API_BASE_URL=https://wylot.eu/api

   # Backend API Configuration
   BACKEND_PORT=8900

   # Frontend Configuration
   FRONTEND_PORT=8901
   API_BASE_URL=http://backend:8900

   # MongoDB External Port (comment out for production security)
   # MONGO_EXTERNAL_PORT=8902

   # Worker Configuration
   GUNICORN_WORKERS=4
   MAX_SCAN_WORKERS=4
   WORKER_TIMEOUT=300
   ```

3. **Set secure file permissions**:
   ```bash
   chmod 600 .env .env
   ```

### 4. Start the Application

#### Build and start services:

```bash
# Start all services (production mode with nginx)
docker-compose --profile production up -d

# View logs to ensure everything is starting correctly
docker-compose logs -f
```

Press `Ctrl+C` to stop following logs. The services will continue running.

#### Verify services are running:

```bash
docker-compose ps
```

All services should show "Up" and "healthy".

### 5. Set Up SSL/HTTPS

Once DNS is propagated and services are running, set up SSL:

```bash
# Run the automated SSL setup script
./init-letsencrypt.sh wylot.eu your-email@example.com
```

Replace `your-email@example.com` with your actual email address for certificate notifications.

This script will:
- Obtain SSL certificates from Let's Encrypt
- Configure nginx with HTTPS
- Set up automatic certificate renewal
- Redirect all HTTP traffic to HTTPS

### 6. Verify Deployment

After SSL setup completes:

1. **Test HTTPS access**:
   ```bash
   curl https://wylot.eu/api/health
   # Should return: {"status":"ok"}
   ```

2. **Open in browser**:
   - Navigate to https://wylot.eu
   - You should see the Flights Scanner interface with a valid SSL certificate

3. **Test API**:
   ```bash
   curl https://wylot.eu/api/airports
   # Should return a list of airports
   ```

## Configuration Details

### Scan Configuration

Your deployment is configured to scan flights for **140 days** from the current date:

- **trigger_scan.py**: SCAN_UNTIL_DAYS = 140 (default)
- **docker-compose.yml**: Scheduler uses SCAN_UNTIL_DAYS = 140

This means each automated scan will search for flights up to 140 days in the future.

### Automated Scanning

The scheduler service automatically triggers scans every 8 hours. No manual intervention needed.

## Maintenance Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f scheduler
docker-compose logs -f nginx
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Update Application

```bash
cd /opt/flights-scanner

# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose --profile production build
docker-compose --profile production up -d
```

### Backup Database

```bash
# Create backup
docker-compose exec mongodb mongodump \
  --username admin \
  --password YOUR_PASSWORD \
  --authenticationDatabase admin \
  --db flights_scanner \
  --out /tmp/backup

# Copy to host
docker cp flights-scanner-mongo:/tmp/backup ./backup-$(date +%Y%m%d)
```

## Monitoring

### Check Service Status

```bash
docker-compose ps
docker stats
```

### Check Health Endpoints

```bash
curl https://wylot.eu/api/health
```

### View Recent Errors

```bash
docker-compose logs --tail=100 | grep -i error
```

## Troubleshooting

### If services won't start:

```bash
# Check logs
docker-compose logs

# Check if ports are in use
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Restart from scratch
docker-compose down
docker-compose --profile production up -d
```

### If SSL certificate fails:

```bash
# Verify DNS is pointing to your server
nslookup wylot.eu
# Should return 162.55.46.15

# Check nginx logs
docker-compose logs nginx

# Manually test certificate
docker-compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  -d wylot.eu
```

### If database connection fails:

```bash
# Check MongoDB is running
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Verify credentials in .env match
# Restart MongoDB
docker-compose restart mongodb
```

## Security Checklist

- [x] Strong password set in .env
- [x] MongoDB external port disabled (not exposed publicly)
- [x] SSL/HTTPS enabled and working
- [x] Firewall configured (only ports 22, 80, 443 open)
- [x] Environment files have restricted permissions (600)
- [ ] Set up automated backups (optional)
- [ ] Set up monitoring/alerts (optional)

## Support

For more detailed information, see:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [README.md](README.md) - Application overview
- [SSL_SETUP.md](SSL_SETUP.md) - Detailed SSL setup guide

## Quick Commands Reference

```bash
# Start all services
docker-compose --profile production up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Update
git pull && docker-compose down && docker-compose --profile production build && docker-compose --profile production up -d

# Backup
docker-compose exec mongodb mongodump --username admin --password YOUR_PASSWORD --authenticationDatabase admin --db flights_scanner --out /tmp/backup
```

---

**Your application is now deployed at https://wylot.eu!** 🎉
