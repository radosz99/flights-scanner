# Frontend Documentation

## Architecture

**Framework**: Nuxt.js 3 (Vue 3)
**Location**: `/frontend/`
**Port**: 3000

## Structure

```
frontend/
├── pages/
│   ├── index.vue           # Homepage
│   ├── price-chart.vue     # Price trends visualization
│   └── trip-search.vue     # Round trip search
├── components/
│   └── AppHeader.vue       # Navigation header
├── nuxt.config.ts          # Nuxt configuration
└── package.json
```

## Pages

### 1. Homepage (`index.vue`)
Landing page with navigation to main features.

### 2. Price Chart (`price-chart.vue`)
**Purpose**: Visualize price trends for one-way routes

**Features**:
- Cascading dropdowns (origin → destination)
- Line chart with min/avg/max prices
- Price statistics table
- Date range analysis

**API Calls**:
- `GET /airports/origins` - Load origins
- `GET /airports/origins/{origin}/destinations` - Load destinations
- `GET /flights/price-chart` - Load chart data

**Data Displayed**:
- Uses `departure_time` and `arrival_time`
- Groups by date extracted from `departure_time`

### 3. Trip Search (`trip-search.vue`)
**Purpose**: Find best round trip deals

**Features**:
- Origin/destination selection
- Trip duration range (min/max days)
- Passenger count
- Results sorted by total price
- Trip cards with flight details

**API Calls**:
- `GET /airports/origins` - Load origins
- `GET /airports/origins/{origin}/destinations` - Load destinations
- `GET /flights/round-trips` - Search trips

**Data Displayed**:
- Date formatting: "Mon, Jan 15, 2025"
- Time formatting: "HH:MM" (no seconds)
- Responsive trip tiles

## Date/Time Formatting

**Helper Functions** (in `trip-search.vue`):

```javascript
formatDate(dateStr) {
  // Converts "2025-01-15" or ISO to "Mon, Jan 15, 2025"
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

formatTime(timeStr) {
  // Extracts "HH:MM" from "YYYY-MM-DDTHH:MM:SS.mmm"
  const [hours, minutes] = timeStr.split('T')[1].split(':')
  return `${hours}:${minutes}`
}
```

**Important**: Always use `departure_time` and `arrival_time`, never `date_out`.

## Styling

- **Framework**: Custom CSS (no Tailwind yet, but planned)
- **Design**: Responsive with mobile-first approach
- **Charts**: Chart.js for visualizations

## Configuration

`nuxt.config.ts`:
```typescript
runtimeConfig: {
  public: {
    apiBaseUrl: 'http://localhost:8000'  // Backend API URL
  }
}
```

Override via environment:
```bash
NUXT_PUBLIC_API_BASE_URL=http://api.example.com
```

## API Integration

Uses Nuxt's built-in `$fetch`:
```javascript
const response = await $fetch(`${apiBaseUrl}/flights/round-trips`, {
  params: { origin, destination, min_days, max_days }
})
```

## Development

```bash
cd frontend
npm install
npm run dev      # Dev server on port 3000
npm run build    # Production build
```

## Docker

Frontend runs in hot-reload mode in development:
```yaml
command: npm run dev
ports:
  - "3000:3000"
```
