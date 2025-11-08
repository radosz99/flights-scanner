<template>
  <div class="container dark:bg-gray-900">
    <h1 class="dark:text-gray-100">Round Trip Search</h1>
    <p class="subtitle dark:text-gray-400">Find the best round trip deals with flexible duration</p>

    <div v-if="loading" class="loading">
      {{ loadingMessage }}
    </div>

    <div v-if="error" class="error">
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Search Form -->
    <div class="search-form dark:bg-gray-800">
      <h2 class="dark:text-gray-100 dark:border-gray-700">Search Parameters</h2>

      <div class="form-grid">
        <div class="form-group">
          <label>Departure Airport</label>
          <select v-model="searchParams.origin" @change="onOriginChange">
            <option value="">Select departure...</option>
            <option v-for="origin in origins" :key="origin.code" :value="origin.code">
              {{ origin.code }} - {{ origin.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Destination Airport</label>
          <select
            v-model="searchParams.destination"
            :disabled="!searchParams.origin || availableDestinations.length === 0"
          >
            <option value="">{{ searchParams.origin ? 'Select destination...' : 'Select departure first' }}</option>
            <option v-for="dest in availableDestinations" :key="dest.code" :value="dest.code">
              {{ dest.code }} - {{ dest.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Minimum Days</label>
          <input
            type="number"
            v-model.number="searchParams.minDays"
            min="1"
            max="365"
            placeholder="e.g., 3"
            @input="onMinDaysChange"
          />
        </div>

        <div class="form-group">
          <label>Maximum Days</label>
          <input
            type="number"
            v-model.number="searchParams.maxDays"
            min="1"
            max="365"
            placeholder="e.g., 7"
            @input="onMaxDaysChange"
          />
        </div>

        <div class="form-group">
          <label>Max Results</label>
          <input
            type="number"
            v-model.number="searchParams.limit"
            min="10"
            max="500"
            placeholder="e.g., 100"
          />
        </div>
      </div>

      <div class="action-buttons">
        <button
          @click="clearSearch"
          class="btn-secondary"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Destinations Preview -->
    <div v-if="searchParams.origin && destinationsPreview.length > 0" class="destinations-preview dark:from-blue-900 dark:to-blue-800 dark:border-blue-700">
      <h2>Available Destinations from {{ searchParams.origin }}</h2>
      <p class="preview-subtitle">Showing lowest round-trip prices ({{ searchParams.minDays }}-{{ searchParams.maxDays }} days)</p>
      <div class="destinations-grid">
        <div
          v-for="dest in destinationsPreview"
          :key="dest.destination"
          class="destination-card"
          :class="{ 'selected': searchParams.destination === dest.destination }"
          @click="selectDestination(dest)"
        >
          <div class="destination-info">
            <div class="destination-code">
              <strong>{{ dest.destination }}</strong>
            </div>
            <div class="destination-name">{{ dest.destination_name }}</div>
          </div>
          <div class="destination-price">
            <div class="price-label">From</div>
            <div class="price-value">{{ formatPrice(dest.min_total_price) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Example Routes -->
    <div v-if="exampleRoutes.length > 0 && !searchParams.origin" class="example-routes dark:bg-gray-800">
      <div class="collapsible-header" @click="toggleExampleRoutes">
        <h2 class="dark:text-gray-100 dark:border-gray-700">Popular Round Trip Routes</h2>
        <button class="toggle-btn" :aria-label="showExampleRoutes ? 'Collapse' : 'Expand'">
          {{ showExampleRoutes ? '▼' : '▶' }}
        </button>
      </div>
      <div v-if="showExampleRoutes">
        <p class="example-subtitle">Click on a route to search for round trips</p>
        <div class="routes-grid">
        <div
          v-for="route in exampleRoutes"
          :key="`${route.origin}-${route.destination}`"
          class="route-card"
          @click="selectExampleRoute(route)"
        >
          <div class="route-info">
            <div class="route-airports">
              <strong>{{ route.origin }}</strong> ⇄ <strong>{{ route.destination }}</strong>
            </div>
            <div class="route-names">
              {{ route.origin_name }} ⇄ {{ route.destination_name }}
            </div>
          </div>
          <div class="route-stats">
            <div class="stat-item">
              <span class="stat-label">Outbound:</span>
              <span class="stat-value">{{ route.outbound_flights || 0 }} flights</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Return:</span>
              <span class="stat-value">{{ route.return_flights || 0 }} flights</span>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="results && results.trips.length > 0" class="results-section">
      <div class="results-header">
        <h2>Found {{ results.total_combinations }} Round Trips</h2>
        <p class="results-info">
          Showing {{ results.showing }} results for
          <strong>{{ results.origin }} → {{ results.destination }}</strong>
          ({{ results.min_days }}-{{ results.max_days }} days)
        </p>
      </div>

      <!-- Trip Cards -->
      <div class="trips-grid">
        <div v-for="(trip, index) in results.trips" :key="index" class="trip-card">
          <div class="trip-header">
            <div class="trip-price">
              <div class="total-price">{{ formatPrice(trip.total_price) }}</div>
              <div class="price-detail">{{ formatPrice(trip.price_per_person) }} / person</div>
            </div>
            <div class="trip-duration">
              <strong>{{ trip.trip_duration_days }}</strong> days
            </div>
          </div>

          <!-- Outbound Flight -->
          <div class="flight-segment outbound">
            <div class="segment-header">
              <span class="segment-label">Outbound</span>
              <span class="segment-date">{{ formatDate(trip.outbound_flight.date) }}</span>
            </div>
            <div class="flight-details">
              <div class="flight-time">
                <div class="time">{{ formatTime(trip.outbound_flight.departure_time) }}</div>
                <div class="arrow">→</div>
                <div class="time">{{ formatTime(trip.outbound_flight.arrival_time) }}</div>
              </div>
              <div class="flight-info">
                <span class="flight-number">{{ trip.outbound_flight.flight_number }}</span>
                <span class="duration">{{ trip.outbound_flight.duration }}</span>
              </div>
              <div class="flight-price">{{ formatPrice(trip.outbound_flight.price) }}</div>
            </div>
          </div>

          <!-- Return Flight -->
          <div class="flight-segment return">
            <div class="segment-header">
              <span class="segment-label">Return</span>
              <span class="segment-date">{{ formatDate(trip.return_flight.date) }}</span>
            </div>
            <div class="flight-details">
              <div class="flight-time">
                <div class="time">{{ formatTime(trip.return_flight.departure_time) }}</div>
                <div class="arrow">→</div>
                <div class="time">{{ formatTime(trip.return_flight.arrival_time) }}</div>
              </div>
              <div class="flight-info">
                <span class="flight-number">{{ trip.return_flight.flight_number }}</span>
                <span class="duration">{{ trip.return_flight.duration }}</span>
              </div>
              <div class="flight-price">{{ formatPrice(trip.return_flight.price) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!loading && searched" class="no-results">
      <p>No round trips found matching your criteria. Try adjusting your search parameters.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { formatPrice, formatDate, formatTime } from '~/utils/formatters'

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

const loading = ref(false)
const loadingMessage = ref('Loading...')
const error = ref(null)
const searched = ref(false)
const showExampleRoutes = ref(false)

const origins = ref([])
const availableDestinations = ref([])
const exampleRoutes = ref([])
const destinationsPreview = ref([])

const searchParams = ref({
  origin: '',
  destination: '',
  minDays: 3,
  maxDays: 7,
  passengers: 1,
  limit: 100
})

const results = ref(null)

const canSearch = computed(() => {
  return (
    searchParams.value.origin &&
    searchParams.value.destination &&
    searchParams.value.minDays > 0 &&
    searchParams.value.maxDays > 0 &&
    searchParams.value.minDays <= searchParams.value.maxDays
  )
})

// Note: formatDate, formatTime, and formatPrice are now imported from utils/formatters.js

// Load origins and example routes on mount
onMounted(async () => {
  await Promise.all([
    loadOrigins(),
    loadExampleRoutes()
  ])
})

// Auto-search when destination is selected
watch(() => searchParams.value.destination, (newDest, oldDest) => {
  if (newDest && newDest !== oldDest && canSearch.value) {
    searchTrips()
  }
})

// Refetch destinations preview when min/max days change
watch(() => [searchParams.value.minDays, searchParams.value.maxDays], () => {
  if (searchParams.value.origin) {
    loadDestinationsPreview()
  }

  // If we already have results, refetch them with new day range
  if (results.value && canSearch.value) {
    searchTrips()
  }
})

const loadOrigins = async () => {
  loading.value = true
  loadingMessage.value = 'Loading airports...'
  error.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/airports/polish-origins`)
    origins.value = response.origins || []
  } catch (e) {
    error.value = e.message || 'Failed to load airports'
  } finally {
    loading.value = false
  }
}

const loadDestinationsFromOrigin = async (origin) => {
  if (!origin) {
    availableDestinations.value = []
    return
  }

  loading.value = true
  loadingMessage.value = 'Loading destinations...'
  error.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/airports/origins/${origin}/destinations`)
    availableDestinations.value = response.destinations || []
  } catch (e) {
    error.value = e.message || 'Failed to load destinations'
    availableDestinations.value = []
  } finally {
    loading.value = false
  }
}

const onOriginChange = async () => {
  // Clear destination and results when origin changes
  searchParams.value.destination = ''
  results.value = null
  searched.value = false

  // Load destinations for selected origin
  if (searchParams.value.origin) {
    await Promise.all([
      loadDestinationsFromOrigin(searchParams.value.origin),
      loadDestinationsPreview()
    ])
  } else {
    availableDestinations.value = []
    destinationsPreview.value = []
  }
}

const onMinDaysChange = () => {
  // Ensure minDays doesn't exceed maxDays
  if (searchParams.value.minDays > searchParams.value.maxDays) {
    searchParams.value.maxDays = searchParams.value.minDays
  }
}

const onMaxDaysChange = () => {
  // Ensure maxDays is at least minDays
  if (searchParams.value.maxDays < searchParams.value.minDays) {
    searchParams.value.minDays = searchParams.value.maxDays
  }
}

const searchTrips = async () => {
  if (!canSearch.value) {
    error.value = 'Please fill in all required fields'
    return
  }

  if (searchParams.value.minDays > searchParams.value.maxDays) {
    error.value = 'Minimum days must be less than or equal to maximum days'
    return
  }

  loading.value = true
  loadingMessage.value = 'Searching for trips...'
  error.value = null
  results.value = null
  searched.value = true

  try {
    const response = await $fetch(`${apiBaseUrl}/flights/round-trips`, {
      params: {
        origin: searchParams.value.origin,
        destination: searchParams.value.destination,
        min_days: searchParams.value.minDays,
        max_days: searchParams.value.maxDays,
        passengers: searchParams.value.passengers,
        limit: searchParams.value.limit
      }
    })

    results.value = response
  } catch (e) {
    if (e.statusCode === 404) {
      error.value = `No round trips found for the selected criteria`
      results.value = null
    } else {
      error.value = e.message || 'Failed to search trips'
    }
  } finally {
    loading.value = false
  }
}

const loadExampleRoutes = async () => {
  try {
    const response = await $fetch(`${apiBaseUrl}/airports/two-way-routes`, {
      params: { limit: 20 }
    })
    exampleRoutes.value = response.routes || []
  } catch (e) {
    console.error('Failed to load example routes:', e)
    exampleRoutes.value = []
  }
}

const selectExampleRoute = async (route) => {
  // Set the origin
  searchParams.value.origin = route.origin

  // Load destinations for this origin
  await Promise.all([
    loadDestinationsFromOrigin(route.origin),
    loadDestinationsPreview()
  ])

  // Set the destination
  searchParams.value.destination = route.destination

  // Trigger search automatically
  if (canSearch.value) {
    searchTrips()
  }
}

const loadDestinationsPreview = async () => {
  if (!searchParams.value.origin) {
    destinationsPreview.value = []
    return
  }

  try {
    // Fetch round trips summary for this origin
    const response = await $fetch(`${apiBaseUrl}/flights/round-trips/preview`, {
      params: {
        origin: searchParams.value.origin,
        min_days: searchParams.value.minDays,
        max_days: searchParams.value.maxDays
      }
    })

    destinationsPreview.value = response.destinations || []
  } catch (e) {
    console.error('Failed to load destinations preview:', e)
    destinationsPreview.value = []
  }
}

const selectDestination = (dest) => {
  searchParams.value.destination = dest.destination
  // Auto-search will be triggered by the watch on destination
}

const toggleExampleRoutes = () => {
  showExampleRoutes.value = !showExampleRoutes.value
}

const clearSearch = () => {
  searchParams.value = {
    origin: '',
    destination: '',
    minDays: 3,
    maxDays: 7,
    passengers: 1,
    limit: 100
  }
  availableDestinations.value = []
  results.value = null
  error.value = null
  searched.value = false
}
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
  margin-bottom: 0.5rem;
  font-size: 2.5rem;
}

.subtitle {
  color: #6c757d;
  font-size: 1.1rem;
  margin-bottom: 2rem;
}

h2 {
  color: #34495e;
  margin-bottom: 1rem;
  font-size: 1.5rem;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 0.5rem;
}

.loading {
  margin-top: 2rem;
  padding: 1rem;
  background: #fff3cd;
  color: #856404;
  border-radius: 5px;
  border: 1px solid #ffeaa7;
  text-align: center;
  font-size: 1.1rem;
}

.error {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8d7da;
  color: #721c24;
  border-radius: 5px;
  border: 1px solid #f5c6cb;
}

.no-results {
  margin-top: 2rem;
  padding: 2rem;
  background: #f8f9fa;
  color: #6c757d;
  border-radius: 8px;
  text-align: center;
  font-size: 1.1rem;
}

/* Search Form */
.search-form {
  margin-top: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #495057;
  font-size: 1rem;
}

.form-group select,
.form-group input {
  padding: 0.75rem;
  border: 2px solid #ced4da;
  border-radius: 5px;
  font-size: 1rem;
  background: white;
  transition: border-color 0.2s;
}

.form-group select {
  cursor: pointer;
}

.form-group select:focus,
.form-group input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.form-group select:disabled {
  background: #e9ecef;
  cursor: not-allowed;
  opacity: 0.6;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

/* Destinations Preview */
.destinations-preview {
  margin-top: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 2px solid #2196f3;
}

.preview-subtitle {
  color: #1565c0;
  font-size: 0.95rem;
  margin-top: -0.5rem;
  margin-bottom: 1rem;
  font-weight: 500;
}

.destinations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.destination-card {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.destination-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.2);
  border-color: #007bff;
}

.destination-card.selected {
  background: linear-gradient(135deg, #e7f1ff 0%, #cfe2ff 100%);
  border-color: #007bff;
  border-width: 3px;
}

.destination-info {
  margin-bottom: 0.75rem;
}

.destination-code {
  font-size: 1.3rem;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.destination-name {
  font-size: 0.8rem;
  color: #6c757d;
  line-height: 1.3;
}

.destination-price {
  padding-top: 0.75rem;
  border-top: 1px solid #e0e0e0;
  text-align: center;
}

.price-label {
  font-size: 0.75rem;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.25rem;
}

.price-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: #28a745;
}

/* Example Routes */
.example-routes {
  margin-top: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.collapsible-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.collapsible-header:hover h2 {
  color: #007bff;
}

.toggle-btn {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  color: #495057;
  cursor: pointer;
  padding: 0.5rem;
  transition: transform 0.2s;
}

.toggle-btn:hover {
  color: #007bff;
  transform: scale(1.1);
}

.example-subtitle {
  color: #6c757d;
  font-size: 0.95rem;
  margin-top: -0.5rem;
  margin-bottom: 1rem;
}

.routes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.route-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 2px solid #dee2e6;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.route-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  border-color: #007bff;
  background: linear-gradient(135deg, #e7f1ff 0%, #cfe2ff 100%);
}

.route-info {
  margin-bottom: 0.75rem;
}

.route-airports {
  font-size: 1.1rem;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.route-names {
  font-size: 0.8rem;
  color: #6c757d;
  line-height: 1.3;
}

.route-stats {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding-top: 0.75rem;
  border-top: 1px solid #dee2e6;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
}

.stat-label {
  color: #6c757d;
}

.stat-value {
  color: #495057;
  font-weight: 600;
}

/* Results Section */
.results-section {
  margin-top: 2rem;
}

.results-header {
  margin-bottom: 1.5rem;
}

.results-info {
  color: #6c757d;
  font-size: 1rem;
  margin-top: 0.5rem;
}

.trips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

/* Trip Card */
.trip-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  min-width: 0;
}

.trip-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.trip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.trip-price {
  display: flex;
  flex-direction: column;
}

.total-price {
  font-size: 1.75rem;
  font-weight: 700;
}

.price-detail {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-top: 0.25rem;
}

.trip-duration {
  text-align: right;
  font-size: 1.5rem;
}

/* Flight Segment */
.flight-segment {
  padding: 1.25rem;
  border-bottom: 1px solid #e9ecef;
}

.flight-segment:last-child {
  border-bottom: none;
}

.segment-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.segment-label {
  font-weight: 600;
  color: #495057;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.segment-date {
  color: #6c757d;
  font-size: 0.85rem;
  font-weight: 500;
  text-align: right;
  line-height: 1.3;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.flight-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.flight-time {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  flex-wrap: nowrap;
}

.time {
  font-family: 'Courier New', monospace;
  white-space: nowrap;
  min-width: 3.5rem;
}

.arrow {
  color: #007bff;
  font-size: 1.5rem;
}

.flight-info {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #6c757d;
}

.flight-number {
  font-weight: 600;
}

.duration {
  color: #495057;
}

.flight-price {
  font-size: 1.1rem;
  font-weight: 700;
  color: #28a745;
  margin-top: 0.25rem;
}

.outbound {
  background: #f8f9fa;
}

.return {
  background: white;
}

/* Buttons */
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

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsive Design */
@media (max-width: 768px) {
  .container {
    padding: 1rem;
  }

  h1 {
    font-size: 2rem;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .trips-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }

  .trip-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }

  .trip-duration {
    text-align: center;
  }

  .flight-time {
    font-size: 1rem;
    gap: 0.5rem;
  }

  .segment-date {
    font-size: 0.8rem;
  }

  .time {
    min-width: 3rem;
  }
}
</style>
