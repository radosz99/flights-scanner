<template>
  <div class="container dark:bg-gray-900">
    <h1 class="dark:text-gray-100">Flights Scanner</h1>
    <p class="dark:text-gray-300">Backend API: <code class="dark:bg-gray-700 dark:text-gray-200">{{ apiBaseUrl }}</code></p>

    <div v-if="loading" class="loading dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-700">
      {{ loadingMessage }}
    </div>

    <div v-if="error" class="error dark:bg-red-900 dark:text-red-200 dark:border-red-700">
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Database Statistics -->
    <div v-if="stats" class="stats-overview dark:bg-gradient-to-br dark:from-purple-900 dark:to-purple-700">
      <h2 class="dark:text-gray-100 dark:border-purple-600">Database Statistics</h2>
      <div class="stats-grid">
        <div class="stat-card dark:bg-purple-800/30 dark:border-purple-600">
          <div class="stat-value dark:text-gray-100">{{ stats.total_flights }}</div>
          <div class="stat-label dark:text-gray-200">Total Flights</div>
        </div>
        <div class="stat-card dark:bg-purple-800/30 dark:border-purple-600">
          <div class="stat-value dark:text-gray-100">{{ stats.unique_origins }}</div>
          <div class="stat-label dark:text-gray-200">Origins</div>
        </div>
        <div class="stat-card dark:bg-purple-800/30 dark:border-purple-600">
          <div class="stat-value dark:text-gray-100">{{ stats.unique_destinations }}</div>
          <div class="stat-label dark:text-gray-200">Destinations</div>
        </div>
        <div class="stat-card dark:bg-purple-800/30 dark:border-purple-600">
          <div class="stat-value dark:text-gray-100">{{ formatPrice(stats.average_price) }}</div>
          <div class="stat-label dark:text-gray-200">Avg Price</div>
        </div>
      </div>

      <div v-if="stats.cheapest_flight" class="flight-highlight dark:bg-purple-800/30 dark:border-purple-600">
        <h3 class="dark:text-gray-100">Cheapest Flight</h3>
        <p class="dark:text-gray-200">
          <strong class="dark:text-gray-100">{{ stats.cheapest_flight.route }}</strong> -
          {{ formatPrice(stats.cheapest_flight.price) }} on
          {{ formatDate(stats.cheapest_flight.date) }}
        </p>
      </div>
    </div>

    <!-- Flights Search and Filters -->
    <div class="flights-section dark:bg-gray-800">
      <h2 class="dark:text-gray-100 dark:border-gray-700">Search Flights</h2>

      <div class="filters dark:bg-gray-700">
        <div class="filter-row">
          <div class="filter-group">
            <label class="dark:text-gray-200">Origin</label>
            <select
              v-model="filters.origin"
              @change="onOriginChange"
              class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
            >
              <option value="">All origins</option>
              <option v-for="origin in filteredOriginsList" :key="origin.code" :value="origin.code">
                {{ origin.code }} - {{ origin.name }}
              </option>
            </select>
          </div>

          <div class="filter-group">
            <label class="dark:text-gray-200">Destination</label>
            <select
              v-model="filters.destination"
              @change="onDestinationChange"
              class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
            >
              <option value="">All destinations</option>
              <option v-for="dest in filteredDestinationsList" :key="dest.code" :value="dest.code">
                {{ dest.code }} - {{ dest.name }}
              </option>
            </select>
          </div>

          <div class="filter-group">
            <label class="dark:text-gray-200">Date From</label>
            <input
              v-model="filters.dateFrom"
              type="date"
              @change="searchFlights"
              class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
            />
          </div>

          <div class="filter-group">
            <label class="dark:text-gray-200">Date To</label>
            <input
              v-model="filters.dateTo"
              type="date"
              @change="searchFlights"
              class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
            />
          </div>
        </div>

        <div class="filter-row">
          <div class="filter-group">
            <label class="dark:text-gray-200">Min Price (PLN)</label>
            <input
              v-model.number="filters.minPrice"
              type="number"
              min="0"
              placeholder="Min"
              @input="debouncedSearch"
              class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500 dark:placeholder-gray-400"
            />
          </div>

          <div class="filter-group">
            <label class="dark:text-gray-200">Max Price (PLN)</label>
            <input
              v-model.number="filters.maxPrice"
              type="number"
              min="0"
              placeholder="Max"
              @input="debouncedSearch"
              class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500 dark:placeholder-gray-400"
            />
          </div>

          <div class="filter-group">
            <label class="dark:text-gray-200">Sort By</label>
            <select v-model="filters.sortBy" @change="searchFlights" class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500">
              <option value="price">Price (Low to High)</option>
              <option value="price_desc">Price (High to Low)</option>
              <option value="date">Date (Earliest)</option>
              <option value="duration">Duration</option>
            </select>
          </div>

          <div class="filter-group">
            <label class="dark:text-gray-200">Page Size</label>
            <select v-model="filters.pageSize" @change="searchFlights" class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500">
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
        </div>

        <div class="filter-actions">
          <button @click="searchFlights" class="btn-primary dark:bg-blue-600 dark:hover:bg-blue-700" :disabled="loading">
            Search Flights
          </button>
          <button @click="clearFilters" class="btn-secondary dark:bg-gray-600 dark:hover:bg-gray-700">
            Clear Filters
          </button>
        </div>
      </div>

      <!-- Flights Results -->
      <div v-if="flightsData" class="flights-results">
        <div class="results-header dark:border-gray-700">
          <h3 class="dark:text-gray-100">Found {{ flightsData.total }} flights</h3>
          <div class="pagination-info dark:text-gray-400">
            Page {{ flightsData.page }} of {{ Math.ceil(flightsData.total / flightsData.page_size) }}
          </div>
        </div>

        <div v-if="flightsData.flights.length === 0" class="no-results dark:bg-gray-700 dark:text-gray-300">
          No flights found matching your criteria.
        </div>

        <div v-else class="flights-table-container">
          <table class="flights-table">
            <thead class="dark:bg-gray-700 dark:border-gray-600">
              <tr>
                <th class="dark:text-gray-200">Route</th>
                <th class="dark:text-gray-200">Date</th>
                <th class="dark:text-gray-200">Time</th>
                <th class="dark:text-gray-200">Duration</th>
                <th class="dark:text-gray-200">Price</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="flight in flightsData.flights" :key="flight.flight_id" class="dark:border-gray-700 dark:hover:bg-gray-700">
                <td class="route-cell dark:text-gray-100">
                  <div class="route">
                    <strong>{{ flight.origin }}</strong> → <strong>{{ flight.destination }}</strong>
                  </div>
                  <div class="route-names dark:text-gray-400">
                    {{ flight.origin_name }} → {{ flight.destination_name }}
                  </div>
                </td>
                <td class="dark:text-gray-200">{{ formatDate(flight.date_out) }}</td>
                <td>
                  <div class="time-cell">
                    <div class="dark:text-gray-200">{{ formatTime(flight.departure_time) }}</div>
                    <div class="arrival-time dark:text-gray-400">{{ formatTime(flight.arrival_time) }}</div>
                  </div>
                </td>
                <td class="dark:text-gray-200">{{ flight.duration }}</td>
                <td class="price-cell dark:text-green-400">
                  <strong>{{ formatPrice(flight.current_price) }}</strong>
                  <div v-if="flight.price_history.length > 1" class="price-changes dark:text-gray-400">
                    {{ flight.price_history.length - 1 }} changes
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="flightsData.total > flightsData.page_size" class="pagination">
          <button
            @click="changePage(flightsData.page - 1)"
            :disabled="flightsData.page === 1"
            class="btn-secondary dark:bg-gray-600 dark:hover:bg-gray-700"
          >
            Previous
          </button>
          <span class="page-info dark:text-gray-300">
            Page {{ flightsData.page }} of {{ Math.ceil(flightsData.total / flightsData.page_size) }}
          </span>
          <button
            @click="changePage(flightsData.page + 1)"
            :disabled="flightsData.page >= Math.ceil(flightsData.total / flightsData.page_size)"
            class="btn-secondary dark:bg-gray-600 dark:hover:bg-gray-700"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Scan Status Section -->
    <div v-if="scanStatus" class="scan-status dark:bg-green-900 dark:text-green-100 dark:border-green-700">
      <h2 class="dark:text-green-100">Latest Scan Status</h2>

      <div class="scan-info">
        <div class="info-row">
          <strong>Status:</strong>
          <span :class="'status-badge status-' + scanStatus.status">{{ scanStatus.status.toUpperCase() }}</span>
        </div>

        <div class="info-row">
          <strong>Started:</strong> {{ formatDateTime(scanStatus.start_time) }}
        </div>

        <div v-if="scanStatus.end_time" class="info-row">
          <strong>Completed:</strong> {{ formatDateTime(scanStatus.end_time) }}
        </div>

        <div v-if="scanStatus.progress" class="progress-section">
          <h3>Progress</h3>

          <div class="progress-bar-container">
            <div class="progress-bar" :style="{ width: scanStatus.progress.percentage + '%' }">
              <span class="progress-text">{{ scanStatus.progress.percentage }}%</span>
            </div>
          </div>

          <div class="progress-details">
            <div class="info-row">
              <strong>Date Ranges:</strong>
              {{ scanStatus.progress.completed_date_ranges }} / {{ scanStatus.progress.total_date_ranges }}
            </div>

            <div v-if="scanStatus.progress.current_date_range" class="info-row">
              <strong>Current Range:</strong> {{ scanStatus.progress.current_date_range }}
            </div>
          </div>
        </div>

        <div class="stats-section">
          <h3>Statistics</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ scanStatus.stats.total_routes }}</div>
              <div class="stat-label">Total Routes</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ scanStatus.stats.successful_queries }}</div>
              <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ scanStatus.stats.failed_queries }}</div>
              <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ scanStatus.stats.flights_saved }}</div>
              <div class="stat-label">Flights Saved</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="actions">
      <button @click="loadAllData" :disabled="loading" class="btn-primary dark:bg-blue-600 dark:hover:bg-blue-700">
        {{ loading ? 'Loading...' : 'Refresh All Data' }}
      </button>

      <button @click="checkLatestScan" :disabled="loading" class="btn-secondary dark:bg-gray-600 dark:hover:bg-gray-700">
        {{ loading ? 'Checking...' : 'Check Latest Scan' }}
      </button>

      <button @click="triggerScan" :disabled="loading || scanning" class="btn-success dark:bg-green-600 dark:hover:bg-green-700">
        {{ scanning ? 'Starting Scan...' : 'Trigger New Scan' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatPrice, formatDate, formatDateTime, formatTime } from '~/utils/formatters'

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl
const scanStatus = ref(null)
const error = ref(null)
const loading = ref(false)
const scanning = ref(false)
const loadingMessage = ref('Loading...')
const stats = ref(null)
const flightsData = ref(null)
const originsList = ref([])
const destinationsList = ref([])
const allRoutes = ref([]) // Store all possible routes for filtering

// Filters - changed to single values instead of arrays
const filters = ref({
  origin: '',
  destination: '',
  dateFrom: '',
  dateTo: '',
  minPrice: null,
  maxPrice: null,
  sortBy: 'price',
  page: 1,
  pageSize: 50
})

// Computed filtered lists based on current selections
const filteredOriginsList = computed(() => {
  if (!filters.value.destination) {
    // No destination selected, show all origins
    return originsList.value
  }
  // Filter origins that have routes to the selected destination
  const validOrigins = new Set(
    allRoutes.value
      .filter(route => route.destination === filters.value.destination)
      .map(route => route.origin)
  )
  return originsList.value.filter(origin => validOrigins.has(origin.code))
})

const filteredDestinationsList = computed(() => {
  if (!filters.value.origin) {
    // No origin selected, show all destinations
    return destinationsList.value
  }
  // Filter destinations that have routes from the selected origin
  const validDestinations = new Set(
    allRoutes.value
      .filter(route => route.origin === filters.value.origin)
      .map(route => route.destination)
  )
  return destinationsList.value.filter(dest => validDestinations.has(dest.code))
})

// Debounce timer
let debounceTimer = null

const debouncedSearch = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    filters.value.page = 1 // Reset to page 1 on new search
    searchFlights()
  }, 500)
}

const onOriginChange = async () => {
  // When origin changes, clear destination if it's no longer valid
  if (filters.value.origin && filters.value.destination) {
    const validDests = filteredDestinationsList.value.map(d => d.code)
    if (!validDests.includes(filters.value.destination)) {
      filters.value.destination = ''
    }
  }
  debouncedSearch()
}

const onDestinationChange = async () => {
  // When destination changes, clear origin if it's no longer valid
  if (filters.value.destination && filters.value.origin) {
    const validOrigins = filteredOriginsList.value.map(o => o.code)
    if (!validOrigins.includes(filters.value.origin)) {
      filters.value.origin = ''
    }
  }
  debouncedSearch()
}

const searchFlights = async () => {
  loading.value = true
  loadingMessage.value = 'Searching flights...'
  error.value = null

  try {
    // Build query params
    const params = new URLSearchParams()

    // Handle single origin and destination
    if (filters.value.origin) {
      params.append('origin', filters.value.origin)
    }
    if (filters.value.destination) {
      params.append('destination', filters.value.destination)
    }
    if (filters.value.dateFrom) params.append('date_from', filters.value.dateFrom)
    if (filters.value.dateTo) params.append('date_to', filters.value.dateTo)
    if (filters.value.minPrice) params.append('min_price', filters.value.minPrice)
    if (filters.value.maxPrice) params.append('max_price', filters.value.maxPrice)
    params.append('sort_by', filters.value.sortBy)
    params.append('page', filters.value.page)
    params.append('page_size', filters.value.pageSize)

    const response = await $fetch(`${apiBaseUrl}/flights?${params.toString()}`)
    flightsData.value = response
  } catch (e) {
    error.value = e.message || 'Failed to fetch flights'
    flightsData.value = null
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await $fetch(`${apiBaseUrl}/flights/stats/summary`)
    stats.value = response
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

const checkLatestScan = async () => {
  loading.value = true
  loadingMessage.value = 'Fetching latest scan status...'
  error.value = null
  scanStatus.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/scans/latest`)
    scanStatus.value = response
  } catch (e) {
    if (e.statusCode === 404) {
      error.value = 'No scans found. Trigger a new scan to get started.'
    } else {
      error.value = e.message || 'Failed to fetch scan status'
    }
  } finally {
    loading.value = false
  }
}

const triggerScan = async () => {
  scanning.value = true
  loading.value = true
  loadingMessage.value = 'Triggering new scan...'
  error.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/scans/run`, {
      method: 'POST',
      body: {
        trip_duration_days: 4,
        scan_until_date: '2025-12-31'
      }
    })

    // Show success and automatically check scan status
    setTimeout(() => {
      checkLatestScan()
    }, 2000)
  } catch (e) {
    error.value = e.message || 'Failed to trigger scan'
  } finally {
    scanning.value = false
    loading.value = false
  }
}

const clearFilters = () => {
  filters.value = {
    origin: '',
    destination: '',
    dateFrom: '',
    dateTo: '',
    minPrice: null,
    maxPrice: null,
    sortBy: 'price',
    page: 1,
    pageSize: 50
  }
  searchFlights()
}

const loadAirportsLists = async () => {
  try {
    // Load all origins
    const originsResponse = await $fetch(`${apiBaseUrl}/airports/origins`)
    originsList.value = originsResponse.origins || []

    // Load all destinations
    const destsResponse = await $fetch(`${apiBaseUrl}/airports/destinations`)
    destinationsList.value = destsResponse.destinations || []

    // Load all routes to enable smart filtering
    const routesResponse = await $fetch(`${apiBaseUrl}/airports/routes`)
    allRoutes.value = routesResponse.routes || []
  } catch (e) {
    console.error('Failed to load airports lists:', e)
  }
}

const changePage = (newPage) => {
  filters.value.page = newPage
  searchFlights()
}

const loadAllData = async () => {
  loading.value = true
  loadingMessage.value = 'Loading all data...'
  error.value = null

  try {
    await Promise.all([
      loadAirportsLists(),
      loadStats(),
      searchFlights(),
      checkLatestScan()
    ])
  } catch (e) {
    error.value = e.message || 'Failed to load data'
  } finally {
    loading.value = false
  }
}

// Note: formatDateTime is now imported from utils/formatters.js

// Load data on mount (client-side only)
onMounted(() => {
  loadAllData()
})
</script>

<style scoped>
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, -apple-system, sans-serif;
}

h1 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

h2 {
  color: #34495e;
  margin-bottom: 1rem;
  font-size: 1.5rem;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 0.5rem;
}

h3 {
  color: #34495e;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
}

code {
  background: #f4f4f4;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.loading {
  margin-top: 2rem;
  padding: 1rem;
  background: #fff3cd;
  color: #856404;
  border-radius: 5px;
  border: 1px solid #ffeaa7;
}

.error {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8d7da;
  color: #721c24;
  border-radius: 5px;
  border: 1px solid #f5c6cb;
}

/* Statistics Overview */
.stats-overview {
  margin-top: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stats-overview h2 {
  color: white;
  border-bottom: 2px solid rgba(255, 255, 255, 0.3);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 1.25rem;
  border-radius: 8px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stats-overview .stat-card {
  background: rgba(255, 255, 255, 0.15);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: inherit;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.9);
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.flight-highlight {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.flight-highlight h3 {
  color: white;
  margin-bottom: 0.5rem;
}

.flight-highlight p {
  margin: 0;
  font-size: 1.1rem;
}

/* Flights Section */
.flights-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Filters */
.filters {
  margin-top: 1rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
}

.filter-group label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #495057;
  font-size: 0.9rem;
}

.filter-group input,
.filter-group select {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.filter-group select[multiple] {
  padding: 0.25rem;
  min-height: 120px;
  cursor: pointer;
}

.filter-group select[multiple] option {
  padding: 0.5rem;
  border-radius: 3px;
  margin: 2px 0;
  cursor: pointer;
}

.filter-group select[multiple] option:hover {
  background: #e7f3ff;
}

.filter-group select[multiple] option:checked {
  background: #007bff;
  color: white;
}

.filter-group input:focus,
.filter-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.filter-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

/* Flights Results */
.flights-results {
  margin-top: 1.5rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e0e0e0;
}

.results-header h3 {
  margin: 0;
  color: #2c3e50;
}

.pagination-info {
  color: #6c757d;
  font-size: 0.9rem;
}

.no-results {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
  font-size: 1.1rem;
}

.flights-table-container {
  overflow-x: auto;
}

.flights-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.flights-table thead {
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
}

.flights-table th {
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #495057;
  white-space: nowrap;
}

.flights-table tbody tr {
  border-bottom: 1px solid #dee2e6;
  transition: background-color 0.2s;
}

.flights-table tbody tr:hover {
  background: #f8f9fa;
}

.flights-table td {
  padding: 0.75rem;
}

.route-cell .route {
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.route-cell .route-names {
  font-size: 0.75rem;
  color: #6c757d;
}

.time-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.arrival-time {
  font-size: 0.85rem;
  color: #6c757d;
}

.price-cell {
  font-size: 1.1rem;
  color: #28a745;
}

.price-changes {
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: normal;
}

.operator {
  font-size: 0.75rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.page-info {
  font-weight: 600;
  color: #495057;
}

/* Scan Status */
.scan-status {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #d4edda;
  color: #155724;
  border-radius: 10px;
  border: 1px solid #c3e6cb;
}

.scan-info {
  margin-top: 0.5rem;
}

.info-row {
  margin: 0.75rem 0;
  font-size: 0.95rem;
}

.info-row strong {
  display: inline-block;
  min-width: 140px;
  color: #2c3e50;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
}

.status-running {
  background: #fff3cd;
  color: #856404;
}

.status-completed {
  background: #d4edda;
  color: #155724;
}

.status-failed {
  background: #f8d7da;
  color: #721c24;
}

.progress-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.progress-bar-container {
  width: 100%;
  height: 30px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 15px;
  overflow: hidden;
  margin: 1rem 0;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #20c997);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.3s ease;
  min-width: 40px;
}

.progress-text {
  color: white;
  font-weight: 600;
  font-size: 0.85rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.progress-details {
  margin-top: 0.5rem;
}

.stats-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.stats-section .stats-grid {
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
}

.stats-section .stat-card {
  background: rgba(0, 0, 0, 0.03);
}

.stats-section .stat-value {
  color: #2c3e50;
}

.stats-section .stat-label {
  color: #6c757d;
}

/* Action Buttons */
.actions {
  margin-top: 2rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

button {
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 5px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.btn-primary {
  background: #007bff;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

.btn-secondary {
  background: #6c757d;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-success {
  background: #28a745;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
