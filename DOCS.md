# Flights Scanner Documentation

## Overview

Flights Scanner is a full-stack application for tracking and analyzing flight prices from Polish airports. The system continuously scans flight data, stores it in MongoDB, and provides a web interface for searching and analyzing flight deals.

## Architecture

The application consists of four main components:

1. **Backend API** - FastAPI REST API for data access
2. **Scrapper** - Flight data collection from airline APIs
3. **Database** - MongoDB for data storage
4. **Frontend** - Nuxt.js web application

```
┌─────────────────┐
│    Frontend     │
│   (Nuxt.js)     │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐      ┌──────────────┐
│   Backend API   │◄─────┤   MongoDB    │
│   (FastAPI)     │      │   Database   │
└────────▲────────┘      └──────────────┘
         │                       ▲
         │                       │
┌────────┴────────┐              │
│    Scrapper     │──────────────┘
│   (Ryanair)     │
└─────────────────┘
```

## Component Documentation

- [MongoDB Schema](./MONGO.md) - Database structure and collections
- [Backend API](./API.md) - REST API endpoints and responses
- [Scrapper](./SCRAPPER.md) - Flight data collection architecture
- [Frontend](./FRONTEND.md) - Web application structure

## Key Features

- **Real-time Price Tracking**: Continuous monitoring of flight prices
- **Round Trip Search**: Find best round trip combinations with flexible duration
- **Price Charts**: Visualize price trends over time for specific routes
- **Polish Airports Focus**: Specialized for flights from Polish airports

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, PyMongo
- **Scrapper**: Python 3.11+, Requests, Loguru
- **Database**: MongoDB
- **Frontend**: Nuxt.js 3, Vue 3, Chart.js
- **Containerization**: Docker, Docker Compose

## Development

See individual component documentation for detailed development guidelines.

## Important Note

**When making changes to any component, please update the corresponding documentation file:**
- Database changes → Update `MONGO.md`
- API changes → Update `API.md`
- Scrapper changes → Update `SCRAPPER.md`
- Frontend changes → Update `FRONTEND.md`
- Architecture changes → Update `DOCS.md`
