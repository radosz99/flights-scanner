<template>
  <div class="container">
    <h1>Flights Scanner</h1>
    <p>Backend API: <code>{{ apiBaseUrl }}</code></p>

    <div v-if="loading" class="loading">
      {{ loadingMessage }}
    </div>

    <div v-if="error" class="error">
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Database Statistics -->
    <div v-if="stats" class="stats-overview">
      <h2>Database Statistics</h2>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_flights }}</div>
          <div class="stat-label">Total Flights</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.unique_origins }}</div>
          <div class="stat-label">Origins</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.unique_destinations }}</div>
          <div class="stat-label">Destinations</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.average_price.toFixed(2) }}€</div>
          <div class="stat-label">Avg Price</div>
        </div>
      </div>

      <div v-if="stats.cheapest_flight" class="flight-highlight">
        <h3>Cheapest Flight</h3>
        <p>
          <strong>{{ stats.cheapest_flight.route }}</strong> -
          {{ stats.cheapest_flight.price }} {{ stats.cheapest_flight.currency }} on
          {{ stats.cheapest_flight.date }}
        </p>
      </div>
    </div>

    <!-- Flights Search and Filters -->
    <div class="flights-section">
      <h2>Search Flights</h2>

      <div class="filters">
        <div class="filter-row">
          <div class="filter-group">
            <label>Origin</label>
            <input
              v-model="filters.origin"
              type="text"
              placeholder="e.g. WRO, KRK"
              @input="debouncedSearch"
            />
          </div>

          <div class="filter-group">
            <label>Destination</label>
            <input
              v-model="filters.destination"
              type="text"
              placeholder="e.g. BCN, ALC"
              @input="debouncedSearch"
            />
          </div>

          <div class="filter-group">
            <label>Date From</label>
            <input
              v-model="filters.dateFrom"
              type="date"
              @change="searchFlights"
            />
          </div>

          <div class="filter-group">
            <label>Date To</label>
            <input
              v-model="filters.dateTo"
              type="date"
              @change="searchFlights"
            />
          </div>
        </div>

        <div class="filter-row">
          <div class="filter-group">
            <label>Min Price (€)</label>
            <input
              v-model.number="filters.minPrice"
              type="number"
              min="0"
              placeholder="Min"
              @input="debouncedSearch"
            />
          </div>

          <div class="filter-group">
            <label>Max Price (€)</label>
            <input
              v-model.number="filters.maxPrice"
              type="number"
              min="0"
              placeholder="Max"
              @input="debouncedSearch"
            />
          </div>

          <div class="filter-group">
            <label>Sort By</label>
            <select v-model="filters.sortBy" @change="searchFlights">
              <option value="price">Price (Low to High)</option>
              <option value="price_desc">Price (High to Low)</option>
              <option value="date">Date (Earliest)</option>
              <option value="duration">Duration</option>
            </select>
          </div>

          <div class="filter-group">
            <label>Page Size</label>
            <select v-model="filters.pageSize" @change="searchFlights">
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
        </div>

        <div class="filter-actions">
          <button @click="searchFlights" class="btn-primary" :disabled="loading">
            Search Flights
          </button>
          <button @click="clearFilters" class="btn-secondary">
            Clear Filters
          </button>
        </div>
      </div>

      <!-- Flights Results -->
      <div v-if="flightsData" class="flights-results">
        <div class="results-header">
          <h3>Found {{ flightsData.total }} flights</h3>
          <div class="pagination-info">
            Page {{ flightsData.page }} of {{ Math.ceil(flightsData.total / flightsData.page_size) }}
          </div>
        </div>

        <div v-if="flightsData.flights.length === 0" class="no-results">
          No flights found matching your criteria.
        </div>

        <div v-else class="flights-table-container">
          <table class="flights-table">
            <thead>
              <tr>
                <th>Route</th>
                <th>Date</th>
                <th>Time</th>
                <th>Duration</th>
                <th>Price</th>
                <th>Seats Left</th>
                <th>Flight #</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="flight in flightsData.flights" :key="flight.flight_id">
                <td class="route-cell">
                  <div class="route">
                    <strong>{{ flight.origin }}</strong> → <strong>{{ flight.destination }}</strong>
                  </div>
                  <div class="route-names">
                    {{ flight.origin_name }} → {{ flight.destination_name }}
                  </div>
                </td>
                <td>{{ flight.date_out }}</td>
                <td>
                  <div class="time-cell">
                    <div>{{ flight.departure_time }}</div>
                    <div class="arrival-time">{{ flight.arrival_time }}</div>
                  </div>
                </td>
                <td>{{ flight.duration }}</td>
                <td class="price-cell">
                  <strong>{{ flight.current_price }} {{ flight.currency }}</strong>
                  <div v-if="flight.price_history.length > 1" class="price-changes">
                    {{ flight.price_history.length - 1 }} changes
                  </div>
                </td>
                <td>{{ flight.fares_left }}</td>
                <td>
                  <code>{{ flight.flight_number }}</code>
                  <div class="operator">{{ flight.operator }}</div>
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
            class="btn-secondary"
          >
            Previous
          </button>
          <span class="page-info">
            Page {{ flightsData.page }} of {{ Math.ceil(flightsData.total / flightsData.page_size) }}
          </span>
          <button
            @click="changePage(flightsData.page + 1)"
            :disabled="flightsData.page >= Math.ceil(flightsData.total / flightsData.page_size)"
            class="btn-secondary"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Scan Status Section -->
    <div v-if="scanStatus" class="scan-status">
      <h2>Latest Scan Status</h2>

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
      <button @click="loadAllData" :disabled="loading" class="btn-primary">
        {{ loading ? 'Loading...' : 'Refresh All Data' }}
      </button>

      <button @click="checkLatestScan" :disabled="loading" class="btn-secondary">
        {{ loading ? 'Checking...' : 'Check Latest Scan' }}
      </button>

      <button @click="triggerScan" :disabled="loading || scanning" class="btn-success">
        {{ scanning ? 'Starting Scan...' : 'Trigger New Scan' }}
      </button>
    </div>
  </div>
</template>

<script setup>
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl
const scanStatus = ref(null)
const error = ref(null)
const loading = ref(false)
const scanning = ref(false)
const loadingMessage = ref('Loading...')
const stats = ref(null)
const flightsData = ref(null)

// Filters
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

// Debounce timer
let debounceTimer = null

const debouncedSearch = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    filters.value.page = 1 // Reset to page 1 on new search
    searchFlights()
  }, 500)
}

const searchFlights = async () => {
  loading.value = true
  loadingMessage.value = 'Searching flights...'
  error.value = null

  try {
    // Build query params
    const params = new URLSearchParams()

    if (filters.value.origin) params.append('origin', filters.value.origin)
    if (filters.value.destination) params.append('destination', filters.value.destination)
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

// Format datetime for display
const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleString()
}

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
