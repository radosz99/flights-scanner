# Secrets and Configuration Guide

This document describes all environment variables and configuration files needed to run the Flights Scanner application.

## Configuration Files Overview

The application uses multiple configuration files for different deployment scenarios:

| File | Purpose | Location |
|------|---------|----------|
| `.env` | Main environment configuration for Docker Compose | Project root |
| `mongo.env` | MongoDB-specific configuration for Docker | Project root |
| `secrets.json` | Local development secrets (Python backend) | Project root |

## Required Configuration Files

### 1. `.env` (Main Configuration)

Primary configuration file for Docker Compose and frontend.

```bash
# MongoDB Configuration
MONGO_HOST=mongodb                    # Docker: 'mongodb' | Local: 'localhost'
MONGO_PORT=27017                      # MongoDB port (default: 27017)
MONGO_DATABASE=flights_scanner        # Database name
MONGO_USERNAME=                       # Optional: MongoDB username (leave empty for no auth)
MONGO_PASSWORD=                       # Optional: MongoDB password (leave empty for no auth)

# Airline IDs
RYANAIR_AIRLINE_ID=39                 # Ryanair airline ID (fixed value)
WIZZAIR_AIRLINE_IDS=52,6002,6092      # Wizz Air airline IDs (comma-separated)

# Ryanair Scraping Configuration
RYANAIR_REQUEST_DELAY=0.5             # Delay between API requests (seconds) - avoid rate limiting
RYANAIR_COOKIE_WAIT_TIME=30           # Max wait time for cookie extraction (seconds)
RYANAIR_COOKIE_CHECK_INTERVAL=0.5     # Cookie extraction check interval (seconds)

# Backend API Configuration
BACKEND_PORT=8900                     # Backend API port (default: 8900)

# Frontend Configuration
FRONTEND_PORT=8901                    # Frontend port (default: 8901)
API_BASE_URL=http://backend:8900      # Docker: 'http://backend:8900' | Local: 'http://localhost:8900'

# MongoDB External Port
MONGO_EXTERNAL_PORT=8902              # External MongoDB port for host access (default: 8902)

# Optional: Gunicorn/Worker Configuration (Docker only)
GUNICORN_WORKERS=4                    # Number of API worker processes (default: 4)
MAX_SCAN_WORKERS=4                    # Thread pool size for background scans (default: 4)
WORKER_TIMEOUT=300                    # Worker timeout in seconds (default: 300)
```

### 2. `mongo.env` (MongoDB Docker Configuration)

MongoDB-specific configuration for Docker container.

```bash
MONGO_HOST=mongodb                    # Docker service name for MongoDB
MONGO_PORT=27017                      # MongoDB port
MONGO_DATABASE=flights_scanner        # Database name
MONGO_USERNAME=                       # Optional: Leave empty for no authentication
MONGO_PASSWORD=                       # Optional: Leave empty for no authentication
```

### 3. `secrets.json` (Local Development Only)

For running backend locally without Docker. Used by `backend/scrapper/config.py` only.

```json
{
  "MONGO_HOST": "localhost",
  "MONGO_PORT": 27017,
  "MONGO_DATABASE": "flights_scanner",
  "MONGO_USERNAME": "",
  "MONGO_PASSWORD": "",
  "RYANAIR_AIRLINE_ID": 39,
  "WIZZAIR_AIRLINE_IDS": "52,6002,6092"
}
```

## Configuration Priority

The backend configuration system (`backend/config.py`) loads settings in this order:
1. Environment variables (highest priority)
2. `.env` file
3. Default values in code (lowest priority)

The scrapper configuration (`backend/scrapper/config.py`) loads:
1. Environment variables (highest priority)
2. `.env` file
3. `secrets.json` file
4. Default values (lowest priority)

## Deployment Scenarios

### Docker Deployment (Production)

**Required files:**
- `.env` - main configuration
- `mongo.env` - MongoDB configuration

**Start services:**
```bash
docker-compose up -d
```

**Access points:**
- Frontend: http://localhost:8901
- Backend API: http://localhost:8900
- MongoDB: mongodb://localhost:8902

### Local Development

**Required files:**
- `.env` or `secrets.json` - backend configuration

**Setup:**

1. Start MongoDB:
```bash
docker run -d -p 27017:27017 --name mongodb mongo:7.0
```

2. Configure connection:
```bash
# .env file
MONGO_HOST=localhost
MONGO_PORT=27017
API_BASE_URL=http://localhost:8900
```

3. Run backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn api.api:app --host 0.0.0.0 --port 8900
```

4. Run frontend:
```bash
cd frontend
npm install
npm run dev
```

## Environment Variable Details

### MongoDB Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGO_HOST` | Yes | localhost | MongoDB hostname |
| `MONGO_PORT` | Yes | 27017 | MongoDB port |
| `MONGO_DATABASE` | Yes | flights_scanner | Database name |
| `MONGO_USERNAME` | No | - | Authentication username (optional) |
| `MONGO_PASSWORD` | No | - | Authentication password (optional) |

### Application Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKEND_PORT` | No | 8900 | Backend API port |
| `FRONTEND_PORT` | No | 8901 | Frontend port |
| `API_BASE_URL` | Yes | - | Backend API URL for frontend |
| `MONGO_EXTERNAL_PORT` | No | 8902 | MongoDB external port for host |

### Scraper Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RYANAIR_AIRLINE_ID` | No | 39 | Ryanair airline identifier |
| `WIZZAIR_AIRLINE_IDS` | No | 52,6002,6092 | Wizz Air airline identifiers |
| `RYANAIR_REQUEST_DELAY` | No | 0.5 | Delay between requests (seconds) |
| `RYANAIR_COOKIE_WAIT_TIME` | No | 30 | Cookie extraction timeout (seconds) |
| `RYANAIR_COOKIE_CHECK_INTERVAL` | No | 0.5 | Cookie check interval (seconds) |

### Performance Configuration (Docker)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GUNICORN_WORKERS` | No | 4 | API worker processes |
| `MAX_SCAN_WORKERS` | No | 4 | Background scan thread pool size |
| `WORKER_TIMEOUT` | No | 300 | Worker timeout (seconds) |

## Security Notes

1. **Never commit** `.env` or `secrets.json` files to git (already in `.gitignore`)
2. Use `.env.example` and `secrets.json.example` as templates
3. For production with authentication:
   ```bash
   MONGO_USERNAME=your_username
   MONGO_PASSWORD=your_strong_password
   ```
4. Change default ports if running multiple instances
5. In production, set specific CORS origins in `backend/api/api.py`

## Troubleshooting

### MongoDB Connection Issues

**Error:** `Failed to connect to MongoDB`

**Solution:** Check MongoDB is running and credentials are correct
```bash
# Test connection
docker exec flights-scanner-backend python -c "from config import settings; print(settings.mongo_uri)"
```

### Frontend Cannot Reach Backend

**Error:** `Network Error` or `CORS Error`

**Solution:** Verify `API_BASE_URL` in frontend configuration
```bash
# Docker: should be internal service name
API_BASE_URL=http://backend:8900

# Local dev: should be localhost
API_BASE_URL=http://localhost:8900
```

### Cookie Extraction Timeout

**Error:** `Cookie extraction timeout`

**Solution:** Increase wait time or check ChromeDriver installation
```bash
RYANAIR_COOKIE_WAIT_TIME=60
```

## Example Configurations

### Minimal Docker Setup (No Authentication)

```bash
# .env
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DATABASE=flights_scanner
BACKEND_PORT=8900
FRONTEND_PORT=8901
API_BASE_URL=http://backend:8900
```

### Production Docker Setup (With Authentication)

```bash
# .env
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DATABASE=flights_scanner
MONGO_USERNAME=admin
MONGO_PASSWORD=SecurePassword123!
BACKEND_PORT=8900
FRONTEND_PORT=8901
API_BASE_URL=http://backend:8900
GUNICORN_WORKERS=8
MAX_SCAN_WORKERS=4
```

### Local Development Setup

```bash
# .env
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=flights_scanner
API_BASE_URL=http://localhost:8900
RYANAIR_REQUEST_DELAY=0.5
```

## Quick Start Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Copy `secrets.json.example` to `secrets.json` (local dev only)
- [ ] Update `MONGO_HOST` based on deployment (mongodb for Docker, localhost for local)
- [ ] Update `API_BASE_URL` based on deployment
- [ ] Set MongoDB credentials if using authentication
- [ ] Adjust ports if defaults are already in use
- [ ] Verify `.env` and `secrets.json` are in `.gitignore`
