<template>
  <div class="container dark:bg-gray-900 min-h-screen">
    <h1 class="text-gray-800 dark:text-gray-100 text-4xl font-bold mb-4">Custom Trip Search</h1>
    <p class="text-gray-600 dark:text-gray-300 text-lg mb-8">
      Advanced search for one-way and two-way routes with flexible origin and destination matching
    </p>

    <!-- Loading -->
    <div
      v-if="loading"
      class="loading dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-700"
    >
      {{ loadingMessage }}
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="error dark:bg-red-900 dark:text-red-200 dark:border-red-700"
    >
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Search Form -->
    <div class="search-form dark:bg-gray-800">
      <h2 class="dark:text-gray-100 dark:border-gray-700">Search Parameters</h2>

      <div class="form-grid">
        <!-- Origin Airports (Multi-select) -->
        <div class="form-group">
          <label class="dark:text-gray-200">Origin Airports</label>
          <select
            v-model="searchParams.origins"
            multiple
            class="multi-select dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          >
            <option v-for="airport in allAirports" :key="airport.code" :value="airport.code">
              {{ airport.code }} - {{ airport.name }}
            </option>
          </select>
          <p class="help-text dark:text-gray-400">Hold Ctrl/Cmd to select multiple</p>
        </div>

        <!-- Destination Selection Mode -->
        <div class="form-group">
          <label class="dark:text-gray-200">Destination Mode</label>
          <select
            v-model="destinationMode"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          >
            <option value="airports">Select Airports</option>
            <option value="country">Select by Country</option>
          </select>
        </div>

        <!-- Destination Airports (Multi-select) -->
        <div v-if="destinationMode === 'airports'" class="form-group">
          <label class="dark:text-gray-200">Destination Airports</label>
          <select
            v-model="searchParams.destinations"
            multiple
            class="multi-select dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          >
            <option v-for="airport in allAirports" :key="airport.code" :value="airport.code">
              {{ airport.code }} - {{ airport.name }}
            </option>
          </select>
          <p class="help-text dark:text-gray-400">Hold Ctrl/Cmd to select multiple</p>
        </div>

        <!-- Destination Country -->
        <div v-if="destinationMode === 'country'" class="form-group">
          <label class="dark:text-gray-200">Destination Country</label>
          <select
            v-model="selectedCountry"
            @change="selectAirportsByCountry"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          >
            <option value="">Select country...</option>
            <option v-for="country in countries" :key="country" :value="country">
              {{ country }}
            </option>
          </select>
          <p v-if="selectedCountry" class="help-text dark:text-gray-400">
            Selected {{ airportsByCountry[selectedCountry]?.length || 0 }} airports
          </p>
        </div>

        <!-- Two-Way Routes Checkbox -->
        <div class="form-group checkbox-group">
          <label class="checkbox-label dark:text-gray-200">
            <input
              v-model="searchParams.twoWayRoutes"
              type="checkbox"
              class="checkbox"
            />
            <span>Two-way routes (flexible matching)</span>
          </label>
          <p class="help-text dark:text-gray-400">
            When checked, return flight can be to any selected origin airport
          </p>
        </div>

        <!-- Date Range From -->
        <div class="form-group">
          <label class="dark:text-gray-200">Departure Date From</label>
          <input
            v-model="searchParams.dateFrom"
            type="date"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          />
        </div>

        <!-- Date Range To -->
        <div class="form-group">
          <label class="dark:text-gray-200">Departure Date To</label>
          <input
            v-model="searchParams.dateTo"
            type="date"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          />
        </div>

        <!-- Min Days -->
        <div class="form-group">
          <label class="dark:text-gray-200">Minimum Trip Days</label>
          <input
            v-model.number="searchParams.minDays"
            type="number"
            min="1"
            max="365"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          />
        </div>

        <!-- Max Days -->
        <div class="form-group">
          <label class="dark:text-gray-200">Maximum Trip Days</label>
          <input
            v-model.number="searchParams.maxDays"
            type="number"
            min="1"
            max="365"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          />
        </div>

        <!-- Min Price -->
        <div class="form-group">
          <label class="dark:text-gray-200">Min Total Price (PLN)</label>
          <input
            v-model.number="searchParams.minPrice"
            type="number"
            min="0"
            placeholder="No minimum"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          />
        </div>

        <!-- Max Price -->
        <div class="form-group">
          <label class="dark:text-gray-200">Max Total Price (PLN)</label>
          <input
            v-model.number="searchParams.maxPrice"
            type="number"
            min="0"
            placeholder="No maximum"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          />
        </div>

        <!-- Max Results -->
        <div class="form-group">
          <label class="dark:text-gray-200">Max Results</label>
          <input
            v-model.number="searchParams.limit"
            type="number"
            min="10"
            max="500"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          />
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button
          @click="searchTrips"
          :disabled="!canSearch || loading"
          class="btn-primary dark:bg-blue-600 dark:hover:bg-blue-700"
        >
          Search Trips
        </button>
        <button
          @click="clearFilters"
          class="btn-secondary dark:bg-gray-600 dark:hover:bg-gray-700"
        >
          Clear All
        </button>
      </div>
    </div>

    <!-- Results Summary -->
    <div v-if="results" class="results-summary dark:bg-gray-800">
      <h3 class="dark:text-gray-100">
        Found {{ results.total }} trips
        <span v-if="results.trips.length < results.total">
          (showing {{ results.trips.length }})
        </span>
      </h3>
    </div>

    <!-- Results Table -->
    <div v-if="results && results.trips.length > 0" class="results-section">
      <div class="table-container dark:bg-gray-800">
        <table class="trips-table">
          <thead class="dark:bg-gray-700 dark:border-gray-600">
            <tr>
              <th class="dark:text-gray-200">Outbound</th>
              <th class="dark:text-gray-200">Return</th>
              <th class="dark:text-gray-200">Dates</th>
              <th class="dark:text-gray-200">Duration</th>
              <th class="dark:text-gray-200">Total Price</th>
              <th class="dark:text-gray-200">Details</th>
            </tr>
          </thead>
          <tbody class="dark:bg-gray-800">
            <tr
              v-for="(trip, index) in results.trips"
              :key="index"
              class="dark:border-gray-700 dark:hover:bg-gray-700"
            >
              <!-- Outbound -->
              <td class="dark:text-gray-200 dark:bg-gray-800">
                <div class="flight-info">
                  <div class="route">
                    <strong>{{ trip.outbound.origin }}</strong> → <strong>{{ trip.outbound.destination }}</strong>
                  </div>
                  <div class="route-names dark:text-gray-400">
                    {{ trip.outbound.origin_name }} → {{ trip.outbound.destination_name }}
                  </div>
                  <div class="time-info dark:text-gray-400">
                    {{ formatTime(trip.outbound.departure_time) }} - {{ formatTime(trip.outbound.arrival_time) }}
                  </div>
                  <div class="price dark:text-green-400">
                    {{ formatPrice(trip.outbound.current_price) }}
                  </div>
                </div>
              </td>

              <!-- Return -->
              <td class="dark:text-gray-200 dark:bg-gray-800">
                <div class="flight-info">
                  <div class="route">
                    <strong>{{ trip.return.origin }}</strong> → <strong>{{ trip.return.destination }}</strong>
                  </div>
                  <div class="route-names dark:text-gray-400">
                    {{ trip.return.origin_name }} → {{ trip.return.destination_name }}
                  </div>
                  <div class="time-info dark:text-gray-400">
                    {{ formatTime(trip.return.departure_time) }} - {{ formatTime(trip.return.arrival_time) }}
                  </div>
                  <div class="price dark:text-green-400">
                    {{ formatPrice(trip.return.current_price) }}
                  </div>
                </div>
              </td>

              <!-- Dates -->
              <td class="dark:text-gray-200 dark:bg-gray-800">
                <div class="date-info">
                  <div>Out: {{ formatDate(trip.outbound.date_out) }}</div>
                  <div>Return: {{ formatDate(trip.return.date_out) }}</div>
                </div>
              </td>

              <!-- Duration -->
              <td class="dark:text-gray-200 dark:bg-gray-800 text-center">
                <strong>{{ trip.trip_duration_days }}</strong> days
              </td>

              <!-- Total Price -->
              <td class="price-cell dark:bg-gray-800">
                <strong class="dark:text-green-400">{{ formatPrice(trip.total_price) }}</strong>
              </td>

              <!-- Details -->
              <td class="dark:text-gray-200 dark:bg-gray-800">
                <div class="details-info">
                  <div class="detail-row">
                    <span class="dark:text-gray-400">Flight durations:</span>
                    <span>{{ trip.outbound.duration }} / {{ trip.return.duration }}</span>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- No Results -->
    <div
      v-if="searched && (!results || results.trips.length === 0)"
      class="no-results dark:bg-gray-700 dark:text-gray-300"
    >
      <p>No trips found matching your criteria. Try adjusting your search parameters.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { formatPrice, formatDate, formatTime } from '~/utils/formatters'

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

// State
const loading = ref(false)
const loadingMessage = ref('Loading...')
const error = ref(null)
const searched = ref(false)

const allAirports = ref([])
const destinationMode = ref('airports')
const selectedCountry = ref('')

// Search Parameters
const searchParams = ref({
  origins: [],
  destinations: [],
  twoWayRoutes: true,
  dateFrom: '',
  dateTo: '',
  minDays: 3,
  maxDays: 7,
  minPrice: null,
  maxPrice: null,
  limit: 100
})

const results = ref(null)

// Computed
const canSearch = computed(() => {
  const hasOrigins = searchParams.value.origins.length > 0
  const hasDestinations = searchParams.value.destinations.length > 0
  const validDuration = searchParams.value.minDays > 0 &&
                        searchParams.value.maxDays > 0 &&
                        searchParams.value.minDays <= searchParams.value.maxDays

  return hasOrigins && hasDestinations && validDuration
})

// Group airports by country (inferred from airport name)
const airportsByCountry = computed(() => {
  const grouped = {}

  allAirports.value.forEach(airport => {
    // Try to extract country from airport name
    // This is a simple heuristic - you might want to improve this
    const country = extractCountry(airport.name)

    if (!grouped[country]) {
      grouped[country] = []
    }
    grouped[country].push(airport)
  })

  return grouped
})

const countries = computed(() => {
  return Object.keys(airportsByCountry.value).sort()
})

// Methods
const extractCountry = (airportName) => {
  // Simple heuristic to extract country from airport name
  // For better accuracy, you'd need a proper mapping

  // Common patterns: "City, Country" or "Airport Name (Country)"
  const patterns = [
    /,\s*([A-Z][a-zA-Z\s]+)$/,  // Matches ", Country"
    /\(([A-Z][a-zA-Z\s]+)\)$/,   // Matches "(Country)"
  ]

  for (const pattern of patterns) {
    const match = airportName.match(pattern)
    if (match) {
      return match[1].trim()
    }
  }

  // Fallback: use first word if it looks like a country
  const words = airportName.split(/[\s,-]/)
  if (words.length > 1) {
    // Check for common European countries
    const commonCountries = ['Poland', 'Germany', 'Spain', 'Italy', 'France', 'UK', 'Greece', 'Portugal']
    for (const word of words) {
      if (commonCountries.includes(word)) {
        return word
      }
    }
  }

  // If airport name contains country codes, map them
  if (airportName.includes('Poland') || airportName.includes('Polish')) return 'Poland'
  if (airportName.includes('Spain') || airportName.includes('Spanish')) return 'Spain'
  if (airportName.includes('Italy') || airportName.includes('Italian')) return 'Italy'
  if (airportName.includes('France') || airportName.includes('French')) return 'France'
  if (airportName.includes('Germany') || airportName.includes('German')) return 'Germany'
  if (airportName.includes('Greece') || airportName.includes('Greek')) return 'Greece'
  if (airportName.includes('Portugal') || airportName.includes('Portuguese')) return 'Portugal'
  if (airportName.includes('UK') || airportName.includes('United Kingdom') || airportName.includes('England') || airportName.includes('Scotland')) return 'United Kingdom'

  // Fallback
  return 'Other'
}

const selectAirportsByCountry = () => {
  if (!selectedCountry.value) {
    return
  }

  const airportsInCountry = airportsByCountry.value[selectedCountry.value] || []
  searchParams.value.destinations = airportsInCountry.map(a => a.code)
}

const loadAirports = async () => {
  loading.value = true
  loadingMessage.value = 'Loading airports...'
  error.value = null

  try {
    // Load all airports (both origins and destinations)
    const [originsResponse, destinationsResponse] = await Promise.all([
      $fetch(`${apiBaseUrl}/airports/origins`),
      $fetch(`${apiBaseUrl}/airports/destinations`)
    ])

    // Combine and deduplicate
    const airportsMap = new Map()

    ;[...(originsResponse.origins || []), ...(destinationsResponse.destinations || [])].forEach(airport => {
      if (!airportsMap.has(airport.code)) {
        airportsMap.set(airport.code, airport)
      }
    })

    allAirports.value = Array.from(airportsMap.values()).sort((a, b) =>
      a.code.localeCompare(b.code)
    )
  } catch (e) {
    error.value = e.message || 'Failed to load airports'
  } finally {
    loading.value = false
  }
}

const searchTrips = async () => {
  if (!canSearch.value) {
    error.value = 'Please select origin(s), destination(s), and specify trip duration'
    return
  }

  loading.value = true
  loadingMessage.value = 'Searching for trips...'
  error.value = null
  results.value = null
  searched.value = true

  try {
    if (searchParams.value.twoWayRoutes) {
      // Two-way routes with flexible matching
      await searchTwoWayTrips()
    } else {
      // One-way routes
      await searchOneWayTrips()
    }
  } catch (e) {
    error.value = e.statusCode === 404
      ? 'No trips found for the selected criteria'
      : e.message || 'Failed to search trips'
    results.value = null
  } finally {
    loading.value = false
  }
}

const searchTwoWayTrips = async () => {
  // Use the efficient batch endpoint that handles multiple origins and destinations
  // in a single request with flexible two-way matching

  try {
    const params = {
      origins: searchParams.value.origins.join(','),
      destinations: searchParams.value.destinations.join(','),
      min_days: searchParams.value.minDays,
      max_days: searchParams.value.maxDays,
      passengers: 1, // Default to 1 passenger for price display
      limit: searchParams.value.limit
    }

    // Add optional filters
    if (searchParams.value.dateFrom) params.date_from = searchParams.value.dateFrom
    if (searchParams.value.dateTo) params.date_to = searchParams.value.dateTo
    if (searchParams.value.minPrice !== null) params.min_price = searchParams.value.minPrice
    if (searchParams.value.maxPrice !== null) params.max_price = searchParams.value.maxPrice

    const response = await $fetch(`${apiBaseUrl}/flights/round-trips-batch`, { params })

    results.value = {
      total: response.total,
      trips: response.trips
    }
  } catch (e) {
    console.error('Failed to search trips:', e)
    throw e
  }
}

const searchOneWayTrips = async () => {
  // For one-way trips, we search each origin-destination pair independently
  const allTrips = []

  for (const origin of searchParams.value.origins) {
    for (const destination of searchParams.value.destinations) {
      try {
        const params = {
          origin: origin,
          destination: destination
        }

        if (searchParams.value.dateFrom) params.date_from = searchParams.value.dateFrom
        if (searchParams.value.dateTo) params.date_to = searchParams.value.dateTo
        if (searchParams.value.minPrice) params.min_price = searchParams.value.minPrice
        if (searchParams.value.maxPrice) params.max_price = searchParams.value.maxPrice

        const response = await $fetch(`${apiBaseUrl}/flights`, { params })

        if (response.flights && response.flights.length > 0) {
          allTrips.push(...response.flights)
        }
      } catch (e) {
        console.error(`Failed to search ${origin} to ${destination}:`, e)
      }
    }
  }

  // Sort by price and limit results
  allTrips.sort((a, b) => a.current_price - b.current_price)
  const limitedTrips = allTrips.slice(0, searchParams.value.limit)

  results.value = {
    total: allTrips.length,
    trips: limitedTrips.map(flight => ({
      outbound: flight,
      return: null,
      trip_duration_days: null,
      total_price: flight.current_price
    }))
  }
}

const clearFilters = () => {
  searchParams.value = {
    origins: [],
    destinations: [],
    twoWayRoutes: true,
    dateFrom: '',
    dateTo: '',
    minDays: 3,
    maxDays: 7,
    minPrice: null,
    maxPrice: null,
    limit: 100
  }
  destinationMode.value = 'airports'
  selectedCountry.value = ''
  results.value = null
  error.value = null
  searched.value = false
}

// Lifecycle
onMounted(async () => {
  await loadAirports()
})
</script>

<style scoped>
.container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, -apple-system, sans-serif;
}

h1 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
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
  margin: 0;
  font-size: 1.2rem;
}

.loading {
  margin-top: 2rem;
  padding: 1rem;
  background: #fff3cd;
  color: #856404;
  border-radius: 5px;
  border: 1px solid #ffeaa7;
  text-align: center;
}

.error {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8d7da;
  color: #721c24;
  border-radius: 5px;
  border: 1px solid #f5c6cb;
}

.search-form {
  margin-top: 2rem;
  padding: 2rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #495057;
  font-size: 0.95rem;
}

.form-group input,
.form-group select {
  padding: 0.6rem;
  border: 2px solid #ced4da;
  border-radius: 5px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.multi-select {
  min-height: 150px;
  cursor: pointer;
}

.multi-select option {
  padding: 0.5rem;
  border-radius: 3px;
  margin: 2px 0;
  cursor: pointer;
}

.multi-select option:hover {
  background: #e7f3ff;
}

.multi-select option:checked {
  background: #007bff;
  color: white;
}

.checkbox-group {
  justify-content: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: 600;
}

.checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.help-text {
  margin-top: 0.25rem;
  font-size: 0.85rem;
  color: #6c757d;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
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

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
}

.btn-secondary:hover {
  background: #545b62;
}

.results-summary {
  margin-top: 2rem;
  padding: 1rem 2rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.results-section {
  margin-top: 2rem;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.trips-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.trips-table thead {
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
}

.trips-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #495057;
  white-space: nowrap;
}

.trips-table tbody tr {
  border-bottom: 1px solid #dee2e6;
  transition: background-color 0.2s;
}

.trips-table tbody tr:hover {
  background: #f8f9fa;
}

.trips-table td {
  padding: 1rem;
  vertical-align: top;
}

.flight-info {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.route {
  font-size: 1rem;
  font-weight: 600;
}

.route-names {
  font-size: 0.8rem;
  color: #6c757d;
}

.time-info {
  font-size: 0.85rem;
  color: #6c757d;
}

.price {
  font-size: 0.95rem;
  color: #28a745;
  font-weight: 600;
}

.date-info {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.9rem;
}

.price-cell {
  font-size: 1.2rem;
  color: #28a745;
  text-align: center;
}

.details-info {
  font-size: 0.85rem;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  margin-bottom: 0.5rem;
}

.no-results {
  margin-top: 2rem;
  padding: 2rem;
  text-align: center;
  background: #f8f9fa;
  border-radius: 10px;
  color: #6c757d;
  font-size: 1.1rem;
}
</style>
