<template>
  <div class="container">
    <h1>Round Trip Search</h1>
    <p class="subtitle">Find the best round trip deals with flexible duration</p>

    <div v-if="loading" class="loading">
      {{ loadingMessage }}
    </div>

    <div v-if="error" class="error">
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Search Form -->
    <div class="search-form">
      <h2>Search Parameters</h2>

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
              <div class="total-price">{{ trip.total_price }} {{ trip.currency }}</div>
              <div class="price-detail">{{ trip.price_per_person }} {{ trip.currency }} / person</div>
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
              <div class="flight-price">{{ trip.outbound_flight.price }} {{ trip.outbound_flight.currency }}</div>
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
              <div class="flight-price">{{ trip.return_flight.price }} {{ trip.return_flight.currency }}</div>
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

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

const loading = ref(false)
const loadingMessage = ref('Loading...')
const error = ref(null)
const searched = ref(false)

const origins = ref([])
const availableDestinations = ref([])

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

// Helper function to format date (YYYY-MM-DD or ISO string to readable date)
const formatDate = (dateStr) => {
  if (!dateStr) return ''

  // Handle both YYYY-MM-DD and ISO format
  const date = new Date(dateStr)

  // Format as: Mon, Jan 15, 2025
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

// Helper function to format time (extract HH:MM from ISO string)
const formatTime = (timeStr) => {
  if (!timeStr) return ''

  // Handle format: YYYY-MM-DDTHH:MM:SS.mmm
  // Extract just the time part and remove seconds
  const timePart = timeStr.split('T')[1]
  if (!timePart) return timeStr

  // Get HH:MM
  const [hours, minutes] = timePart.split(':')
  return `${hours}:${minutes}`
}

// Load origins on mount
onMounted(async () => {
  await loadOrigins()
})

// Auto-search when destination is selected
watch(() => searchParams.value.destination, (newDest, oldDest) => {
  if (newDest && newDest !== oldDest && canSearch.value) {
    searchTrips()
  }
})

const loadOrigins = async () => {
  loading.value = true
  loadingMessage.value = 'Loading airports...'
  error.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/airports/origins`)
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
    await loadDestinationsFromOrigin(searchParams.value.origin)
  } else {
    availableDestinations.value = []
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
