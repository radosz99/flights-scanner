# Docker Setup Guide

This guide explains how to run the Flights Scanner application using Docker.

## 🏗️ Architecture

The application consists of three services:

- **MongoDB** (Port 8902): Database for storing flight data
- **Backend API** (Port 8900): FastAPI REST API for flight queries
- **Frontend** (Port 8901): Nuxt 4 SSR application

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB of available RAM

## 🚀 Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd flights-scanner

# Copy environment example (optional)
cp .env.example .env

# Copy secrets example if needed
cp secrets.json.example secrets.json
```

### 2. Build and Run

Using Docker Compose:

```bash
# Build all images
make docker-build
# OR
docker compose build

# Start all services
make docker-up
# OR
docker compose up -d
```

### 3. Access the Application

- **Frontend**: http://localhost:8901
- **Backend API**: http://localhost:8900
- **API Docs**: http://localhost:8900/docs
- **MongoDB**: mongodb://localhost:8902

## 📝 Makefile Commands

The project includes a Makefile with convenient commands:

### Docker Commands

```bash
make docker-build      # Build all Docker images
make docker-up         # Start all services in detached mode
make docker-down       # Stop all services
make docker-logs       # View logs from all services
make docker-restart    # Restart all services
```

### Local Development Commands

```bash
make install-backend   # Install backend Python dependencies
make install-frontend  # Install frontend Node dependencies
make backend           # Run backend API locally (port 8900)
make frontend          # Run frontend dev server locally (port 8901)
make test              # Run backend tests
```

### Utility Commands

```bash
make clean            # Clean up temporary files and caches
make help             # Show all available commands
```

## 🔧 Configuration

### Environment Variables

You can configure the application using environment variables or the `secrets.json` file.

**Option 1: Environment Variables**

Create a `.env` file in the project root:

```env
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DATABASE=flights_scanner
MONGO_USERNAME=
MONGO_PASSWORD=
RYANAIR_AIRLINE_ID=39
WIZZAIR_AIRLINE_IDS=52,6002,6092
```

**Option 2: secrets.json**

Create a `secrets.json` file in the project root:

```json
{
  "MONGO_HOST": "mongodb",
  "MONGO_PORT": 27017,
  "MONGO_DATABASE": "flights_scanner",
  "MONGO_USERNAME": "",
  "MONGO_PASSWORD": "",
  "RYANAIR_AIRLINE_ID": 39,
  "WIZZAIR_AIRLINE_IDS": "52,6002,6092"
}
```

### Port Configuration

To change the default ports, edit `docker-compose.yml`:

```yaml
services:
  mongodb:
    ports:
      - "8902:27017"  # Change 8902 to your desired port

  backend:
    ports:
      - "8900:8900"   # Change 8900 to your desired port

  frontend:
    ports:
      - "8901:8901"   # Change 8901 to your desired port
```

## 🛠️ Development Mode

For development, you can mount local code into containers:

1. Uncomment the volumes section in `docker-compose.yml`:

```yaml
backend:
  volumes:
    - ./backend:/app  # Uncomment this line
```

2. Restart the services:

```bash
make docker-restart
```

## 📊 Monitoring

### View Logs

```bash
# All services
make docker-logs

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mongodb
```

### Check Service Status

```bash
docker compose ps
```

### Health Checks

All services include health checks:

- **Backend**: http://localhost:8900/health
- **Frontend**: http://localhost:8901 (returns 200 OK)
- **MongoDB**: Automated mongosh ping

## 🧪 Testing

### Run Backend Tests

```bash
# Inside Docker
docker compose exec backend python -m pytest test_*.py -v

# Or using Makefile (local)
make test
```

## 🗄️ Database Management

### Access MongoDB Shell

```bash
docker compose exec mongodb mongosh
```

### Backup Database

```bash
docker compose exec mongodb mongodump --out=/data/backup
```

### Restore Database

```bash
docker compose exec mongodb mongorestore /data/backup
```

## 🔍 Troubleshooting

### Services won't start

```bash
# Check logs
make docker-logs

# Check if ports are already in use
lsof -i :8900
lsof -i :8901
lsof -i :8902
```

### Backend can't connect to MongoDB

1. Check if MongoDB is healthy:
   ```bash
   docker compose ps
   ```

2. Verify connection settings in `secrets.json` or `.env`

3. Ensure `MONGO_HOST=mongodb` (not `localhost`)

### Frontend can't reach Backend

1. Check backend health:
   ```bash
   curl http://localhost:8900/health
   ```

2. Verify `API_BASE_URL` in frontend environment

### Reset Everything

```bash
# Stop and remove all containers, networks, and volumes
docker compose down -v

# Rebuild from scratch
make docker-build
make docker-up
```

## 🚢 Production Deployment

For production:

1. **Use proper secrets management**:
   - Don't commit `secrets.json` or `.env`
   - Use Docker secrets or environment variables

2. **Enable authentication**:
   - Set MongoDB username/password
   - Add API authentication

3. **Use reverse proxy**:
   - nginx or Traefik for SSL/TLS
   - Load balancing

4. **Configure resource limits**:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '1'
             memory: 1G
   ```

5. **Set up monitoring**:
   - Log aggregation (ELK, Loki)
   - Metrics (Prometheus)
   - Alerts

## 📁 Project Structure

```
flights-scanner/
├── backend/
│   ├── api/                 # FastAPI application
│   ├── scrapper/           # Flight scraping logic
│   ├── Dockerfile          # Multi-stage backend image
│   ├── requirements.txt    # Python dependencies
│   └── test_*.py          # Backend tests
├── frontend/
│   ├── pages/             # Nuxt pages
│   ├── Dockerfile         # Multi-stage frontend image
│   └── package.json       # Node dependencies
├── docker-compose.yml     # Service orchestration
├── Makefile              # Convenient commands
├── .env.example          # Environment template
└── secrets.json.example  # Secrets template
```

## 🆘 Support

For more information, see:
- Backend API documentation: `backend/API_USAGE.md`
- Cookie management: `backend/COOKIE_MANAGEMENT.md`
- Project structure: `backend/STRUCTURE.md`
