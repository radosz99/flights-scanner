# Project Structure

This project is organized into three main directories:

## Directory Structure

```
flights-scanner/
├── backend/
│   ├── api/           # REST API endpoints
│   └── scrapper/      # Flight scraping logic
├── frontend/          # Nuxt 4 SSR application
└── scrapper/          # (deprecated - use backend/scrapper)
```

## Backend

### `/backend/api/`
Contains the REST API implementation:
- `api.py` - FastAPI application with flight filtering endpoints

### `/backend/scrapper/`
Contains all flight scraping logic:
- `ryanair_scanner.py` - Main Ryanair flight scanner
- `ryanair.py` - Ryanair API client
- `ryanair_models.py` - Data models for Ryanair flights
- `flight_connector.py` - Flight connection logic
- `wizz_air.py` - Wizz Air API client
- `wizz_air_models.py` - Data models for Wizz Air flights
- `main.py` - Scanner entry point
- `config.py` - Configuration management
- `find_valid_cookie.py` - Cookie validation utilities
- `populate_databases.py` - Database population scripts
- `query_databases.py` - Database query utilities

## Frontend

### `/frontend/`
Nuxt 4 application with full SSR support:
- **Framework**: Nuxt 4 with Vue 3
- **Rendering**: Server-Side Rendering (SSR) enabled
- **Features**:
  - Simple homepage showing backend API endpoint
  - Health check integration with backend

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

### Frontend Configuration

- SSR is enabled by default in `nuxt.config.ts`
- The application is configured to use Node.js server preset for production

## Development

### Backend API
The backend API should be running on http://localhost:8000 for the frontend to connect to it.

### Frontend Development
The frontend connects to the backend API to display flight information and health status.
