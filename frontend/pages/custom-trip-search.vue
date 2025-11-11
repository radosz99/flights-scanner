<template>
  <div class="container dark:bg-gray-900 min-h-screen">
    <h1 class="text-gray-800 dark:text-gray-100 text-4xl font-bold mb-4">Custom Trip Search</h1>
    <p class="text-gray-600 dark:text-gray-300 text-lg mb-8">
      Search for one-way or round-trip flights with flexible origin and destination matching. Use batch search to efficiently find flights across multiple airports.
    </p>

    <!-- Loading with Progress Bar -->
    <div v-if="loading" class="mt-8">
      <div class="p-4 bg-yellow-50 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-md border border-yellow-200 dark:border-yellow-700 text-center text-lg">
        <div class="mb-3">{{ loadingMessage }}</div>
        <!-- Animated Progress Bar -->
        <div class="w-full bg-yellow-200 dark:bg-yellow-700 rounded-full h-2.5 overflow-hidden">
          <div class="bg-yellow-600 dark:bg-yellow-400 h-2.5 rounded-full animate-progress"></div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="error dark:bg-red-900 dark:text-red-200 dark:border-red-700"
    >
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Main Content: Filters + Results Side by Side on Desktop -->
    <div class="main-content">
      <!-- Search Form (Left Side on Desktop) -->
      <div class="search-form-container">
        <div class="search-form dark:bg-gray-800">
          <h2 class="dark:text-gray-100 dark:border-gray-700">Search Parameters</h2>

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

      <div class="form-grid">
        <!-- Origin Airports (Multi-select) - Polish airports only -->
        <div class="form-group">
          <label class="dark:text-gray-200">Origin Airports (Polish only)</label>
          <MultiSelectDropdown
            :options="polishAirportsOptions"
            :selected-values="searchParams.origins"
            @update:selected-values="searchParams.origins = $event"
            placeholder="Select Polish airports..."
            search-placeholder="Search airports..."
          />
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
          <MultiSelectDropdown
            :options="allAirportsOptions"
            :selected-values="searchParams.destinations"
            @update:selected-values="searchParams.destinations = $event"
            placeholder="Select destination airports..."
            search-placeholder="Search airports..."
          />
        </div>

        <!-- Destination Countries (Multi-select) -->
        <div v-if="destinationMode === 'country'" class="form-group">
          <label class="dark:text-gray-200">Destination Countries</label>
          <MultiSelectDropdown
            :options="countriesOptions"
            :selected-values="selectedCountries"
            @update:selected-values="selectAirportsByCountries"
            placeholder="Select countries..."
            search-placeholder="Search countries..."
          />
          <p v-if="selectedCountries.length > 0" class="selected-info dark:text-gray-400">
            {{ getTotalAirportsFromCountries() }} airports from {{ selectedCountries.length }} {{ selectedCountries.length === 1 ? 'country' : 'countries' }}
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
            <span class="info-icon" title="When checked, return flight can be to any selected origin airport">ℹ</span>
          </label>
        </div>

        <!-- Return from Same Airport Checkbox (only for two-way routes) -->
        <div v-if="searchParams.twoWayRoutes" class="form-group checkbox-group">
          <label class="checkbox-label dark:text-gray-200">
            <input
              v-model="searchParams.returnFromSameAirport"
              type="checkbox"
              class="checkbox"
            />
            <span>Return from same airport</span>
            <span class="info-icon" title="Uncheck to allow returns from different airports (e.g., fly to BCN, return from VLC)">ℹ</span>
          </label>
        </div>

        <!-- Return to Same Airport Checkbox (only for two-way routes) -->
        <div v-if="searchParams.twoWayRoutes" class="form-group checkbox-group">
          <label class="checkbox-label dark:text-gray-200">
            <input
              v-model="searchParams.returnToSameAirport"
              type="checkbox"
              class="checkbox"
            />
            <span>Return to same airport</span>
            <span class="info-icon" title="Uncheck to allow returns to different origin airports (e.g., fly from WRO, return to KRK)">ℹ</span>
          </label>
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

        <!-- Min Days (only for two-way routes) -->
        <div v-if="searchParams.twoWayRoutes" class="form-group">
          <label class="dark:text-gray-200">Minimum Trip Days</label>
          <input
            v-model.number="searchParams.minDays"
            type="number"
            min="1"
            max="365"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
          />
        </div>

        <!-- Max Days (only for two-way routes) -->
        <div v-if="searchParams.twoWayRoutes" class="form-group">
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

        <!-- Outbound Weekdays -->
        <div class="form-group">
          <label class="dark:text-gray-200">
            {{ searchParams.twoWayRoutes ? 'Outbound Flight Days' : 'Flight Days' }}
            <span class="info-icon" :title="'Select specific days of the week for ' + (searchParams.twoWayRoutes ? 'outbound' : '') + ' flights'">ℹ</span>
          </label>
          <MultiSelectDropdown
            :options="weekdayOptions"
            :selected-values="searchParams.outboundWeekdays"
            @update:selected-values="searchParams.outboundWeekdays = $event"
            placeholder="Any day"
            :searchable="false"
            :show-selected-items="false"
          />
        </div>

        <!-- Return Weekdays (only for two-way routes) -->
        <div v-if="searchParams.twoWayRoutes" class="form-group">
          <label class="dark:text-gray-200">
            Return Flight Days
            <span class="info-icon" title="Select specific days of the week for return flights">ℹ</span>
          </label>
          <MultiSelectDropdown
            :options="weekdayOptions"
            :selected-values="searchParams.returnWeekdays"
            @update:selected-values="searchParams.returnWeekdays = $event"
            placeholder="Any day"
            :searchable="false"
            :show-selected-items="false"
          />
        </div>
      </div>
        </div>
      </div>

      <!-- Results Section (Right Side on Desktop) -->
      <div class="results-container" :class="{ 'blur-sm opacity-60 pointer-events-none': loading && results }">
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
              <th class="dark:text-gray-200">{{ searchParams.twoWayRoutes ? 'Outbound' : 'Flight' }}</th>
              <th v-if="searchParams.twoWayRoutes" class="dark:text-gray-200">Return</th>
              <th class="dark:text-gray-200">{{ searchParams.twoWayRoutes ? 'Dates' : 'Date' }}</th>
              <th v-if="searchParams.twoWayRoutes" class="dark:text-gray-200">Duration</th>
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
              <!-- Outbound / One-way Flight -->
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
                    {{ formatPrice(searchParams.twoWayRoutes ? trip.outbound.current_price : trip.outbound.price_per_person) }}
                  </div>
                </div>
              </td>

              <!-- Return (only for two-way routes) -->
              <td v-if="searchParams.twoWayRoutes && trip.return" class="dark:text-gray-200 dark:bg-gray-800">
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
                  <div>{{ searchParams.twoWayRoutes ? 'Out: ' : '' }}{{ formatDate(trip.outbound.date_out) }}</div>
                  <div v-if="searchParams.twoWayRoutes && trip.return">Return: {{ formatDate(trip.return.date_out) }}</div>
                </div>
              </td>

              <!-- Duration (only for two-way routes) -->
              <td v-if="searchParams.twoWayRoutes" class="dark:text-gray-200 dark:bg-gray-800 text-center">
                <div class="duration-info">
                  <div><strong>{{ trip.trip_duration_days }}</strong> days</div>
                  <div class="stay-duration dark:text-gray-400">{{ trip.stay_duration }}</div>
                </div>
              </td>

              <!-- Total Price -->
              <td class="price-cell dark:bg-gray-800">
                <strong class="dark:text-green-400">{{ formatPrice(trip.total_price) }}</strong>
              </td>

              <!-- Details -->
              <td class="dark:text-gray-200 dark:bg-gray-800">
                <div class="details-info">
                  <div class="detail-row">
                    <span class="dark:text-gray-400">{{ searchParams.twoWayRoutes ? 'Flight durations:' : 'Duration:' }}</span>
                    <span v-if="searchParams.twoWayRoutes && trip.return">{{ trip.outbound.duration }} / {{ trip.return.duration }}</span>
                    <span v-else>{{ trip.outbound.duration }}</span>
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
          v-if="!loading && searched && (!results || results.trips.length === 0)"
          class="no-results dark:bg-gray-700 dark:text-gray-300"
        >
          <p>No trips found matching your criteria. Try adjusting your search parameters.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { formatPrice, formatDate, formatTime } from '~/utils/formatters'
import MultiSelectDropdown from '~/components/MultiSelectDropdown.vue'

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

// List of Polish airport codes
const POLISH_AIRPORT_CODES = [
  'BZG', // Bydgoszcz
  'GDN', // Gdańsk
  'KRK', // Krakow
  'KTW', // Katowice
  'LCJ', // Lodz
  'LUZ', // Lublin
  'POZ', // Poznań
  'RZE', // Rzeszów
  'SZY', // Olsztyn-Mazury
  'SZZ', // Szczecin
  'WAW', // Warsaw (Chopin)
  'WMI', // Warsaw (Modlin)
  'WRO'  // Wroclaw
]

// State
const loading = ref(false)
const loadingMessage = ref('Loading...')
const error = ref(null)
const searched = ref(false)

const allAirports = ref([])
const destinationMode = ref('airports')
const selectedCountries = ref([])
const countriesData = ref([])

// Get today's date in YYYY-MM-DD format
const getTodayDate = () => {
  const today = new Date()
  return today.toISOString().split('T')[0]
}

// Search Parameters
const searchParams = ref({
  origins: [],
  destinations: [],
  twoWayRoutes: true,
  returnFromSameAirport: true,
  returnToSameAirport: true,
  dateFrom: getTodayDate(),
  dateTo: '',
  minDays: 3,
  maxDays: 7,
  minPrice: null,
  maxPrice: null,
  limit: 100,
  outboundWeekdays: [],
  returnWeekdays: []
})

const results = ref(null)

// Computed
const canSearch = computed(() => {
  const hasOrigins = searchParams.value.origins.length > 0
  const hasDestinations = searchParams.value.destinations.length > 0

  // For two-way routes, validate trip duration
  if (searchParams.value.twoWayRoutes) {
    const validDuration = searchParams.value.minDays > 0 &&
                          searchParams.value.maxDays > 0 &&
                          searchParams.value.minDays <= searchParams.value.maxDays
    return hasOrigins && hasDestinations && validDuration
  }

  // For one-way routes, just need origins and destinations
  return hasOrigins && hasDestinations
})

// Options formatted for MultiSelectDropdown component (countries)
const countriesOptions = computed(() => {
  return countriesData.value.map(countryData => ({
    value: countryData.country,
    label: `${countryData.country} (${countryData.airport_count} airports)`
  }))
})

// Computed property for Polish airports only (for origin selection)
const polishAirports = computed(() => {
  return allAirports.value.filter(airport => {
    return POLISH_AIRPORT_CODES.includes(airport.code)
  }).sort((a, b) => a.code.localeCompare(b.code))
})

// Options formatted for MultiSelectDropdown component
const polishAirportsOptions = computed(() => {
  return polishAirports.value.map(airport => ({
    value: airport.code,
    label: `${airport.code} - ${airport.name}`
  }))
})

const allAirportsOptions = computed(() => {
  return allAirports.value.map(airport => ({
    value: airport.code,
    label: `${airport.code} - ${airport.name}`
  }))
})

// Weekday options (0=Monday, 6=Sunday)
const weekdayOptions = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' }
]

// Methods
const selectAirportsByCountries = (countries) => {
  selectedCountries.value = countries

  if (countries.length === 0) {
    searchParams.value.destinations = []
    return
  }

  // Find all airports from selected countries
  const airportCodes = []
  countries.forEach(country => {
    const countryData = countriesData.value.find(c => c.country === country)
    if (countryData && countryData.airports) {
      airportCodes.push(...countryData.airports.map(a => a.code))
    }
  })

  searchParams.value.destinations = airportCodes
}

const getTotalAirportsFromCountries = () => {
  let total = 0
  selectedCountries.value.forEach(country => {
    const countryData = countriesData.value.find(c => c.country === country)
    if (countryData) {
      total += countryData.airport_count
    }
  })
  return total
}

const loadAirports = async () => {
  loading.value = true
  loadingMessage.value = 'Loading airports...'
  error.value = null

  try {
    // Load all airports (both origins and destinations) and countries
    const [originsResponse, destinationsResponse, countriesResponse] = await Promise.all([
      $fetch(`${apiBaseUrl}/airports/origins`),
      $fetch(`${apiBaseUrl}/airports/destinations`),
      $fetch(`${apiBaseUrl}/airports/countries?airline=ryanair`)
    ])

    // Combine and deduplicate airports
    const airportsMap = new Map()

    ;[...(originsResponse.origins || []), ...(destinationsResponse.destinations || [])].forEach(airport => {
      if (!airportsMap.has(airport.code)) {
        airportsMap.set(airport.code, airport)
      }
    })

    allAirports.value = Array.from(airportsMap.values()).sort((a, b) =>
      a.code.localeCompare(b.code)
    )

    // Store countries data
    countriesData.value = countriesResponse.countries || []
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
      limit: searchParams.value.limit,
      return_from_same_airport: searchParams.value.returnFromSameAirport,
      return_to_same_airport: searchParams.value.returnToSameAirport
    }

    // Add optional filters
    if (searchParams.value.dateFrom) params.date_from = searchParams.value.dateFrom
    if (searchParams.value.dateTo) params.date_to = searchParams.value.dateTo
    if (searchParams.value.minPrice !== null) params.min_price = searchParams.value.minPrice
    if (searchParams.value.maxPrice !== null) params.max_price = searchParams.value.maxPrice

    // Add weekday filters if they are selected
    if (searchParams.value.outboundWeekdays.length > 0) {
      params.outbound_weekdays = searchParams.value.outboundWeekdays.join(',')
    }
    if (searchParams.value.returnWeekdays.length > 0) {
      params.return_weekdays = searchParams.value.returnWeekdays.join(',')
    }

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
  // Use the efficient batch endpoint for one-way flights
  try {
    const params = {
      origins: searchParams.value.origins.join(','),
      destinations: searchParams.value.destinations.join(','),
      passengers: 1, // Default to 1 passenger for price display
      limit: searchParams.value.limit
    }

    // Add optional filters
    if (searchParams.value.dateFrom) params.date_from = searchParams.value.dateFrom
    if (searchParams.value.dateTo) params.date_to = searchParams.value.dateTo
    if (searchParams.value.minPrice !== null) params.min_price = searchParams.value.minPrice
    if (searchParams.value.maxPrice !== null) params.max_price = searchParams.value.maxPrice

    // Add weekday filter if selected
    if (searchParams.value.outboundWeekdays.length > 0) {
      params.outbound_weekdays = searchParams.value.outboundWeekdays.join(',')
    }

    const response = await $fetch(`${apiBaseUrl}/flights/one-way-batch`, { params })

    results.value = {
      total: response.total,
      trips: response.flights.map(flight => ({
        outbound: flight,
        return: null,
        trip_duration_days: null,
        stay_duration: null,
        total_price: flight.total_price
      }))
    }
  } catch (e) {
    console.error('Failed to search one-way trips:', e)
    throw e
  }
}

const clearFilters = () => {
  searchParams.value = {
    origins: [],
    destinations: [],
    twoWayRoutes: true,
    returnFromSameAirport: true,
    dateFrom: '',
    dateTo: '',
    minDays: 3,
    maxDays: 7,
    minPrice: null,
    maxPrice: null,
    limit: 100,
    outboundWeekdays: [],
    returnWeekdays: []
  }
  destinationMode.value = 'airports'
  selectedCountries.value = []
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
  max-width: 100%;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, -apple-system, sans-serif;
}

/* Main content layout: side-by-side on desktop */
.main-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Desktop layout: filters left, results right */
@media (min-width: 1024px) {
  .main-content {
    flex-direction: row;
    align-items: flex-start;
    gap: 1.5rem;
  }

  .search-form-container {
    flex: 0 0 30%;
    max-width: 30%;
    position: sticky;
    top: 2rem;
    max-height: calc(100vh - 4rem);
    overflow-y: auto;
  }

  .results-container {
    flex: 1;
    min-width: 0; /* Allow flexbox to shrink */
  }
}

/* Scrollbar styling for sticky sidebar */
.search-form-container::-webkit-scrollbar {
  width: 8px;
}

.search-form-container::-webkit-scrollbar-track {
  background: transparent;
}

.search-form-container::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

.search-form-container::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

h1 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

h2 {
  color: #34495e;
  margin-bottom: 1rem;
  font-size: 1.25rem;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 0.5rem;
}

@media (min-width: 1024px) {
  h2 {
    font-size: 1.125rem;
  }
}

h3 {
  color: #34495e;
  margin: 0;
  font-size: 1.2rem;
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
  padding: 1.5rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
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

.selected-info {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: #6c757d;
}

.info-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  margin-left: 0.5rem;
  font-size: 0.85rem;
  font-weight: bold;
  color: #007bff;
  background: rgba(0, 123, 255, 0.1);
  border-radius: 50%;
  cursor: help;
  transition: all 0.2s;
  flex-shrink: 0;
}

.info-icon:hover {
  background: rgba(0, 123, 255, 0.2);
  transform: scale(1.1);
}

.dark .info-icon {
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.15);
}

.dark .info-icon:hover {
  background: rgba(96, 165, 250, 0.25);
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.dark .action-buttons {
  border-bottom-color: #4a5568;
}

@media (min-width: 768px) and (max-width: 1023px) {
  .action-buttons {
    flex-direction: row;
  }
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
  padding: 1rem 2rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
}

.results-section {
  margin-top: 1rem;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
}

/* Better scrolling for table */
@media (min-width: 1024px) {
  .table-container {
    max-width: 100%;
  }
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

.duration-info {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.stay-duration {
  font-size: 0.8rem;
  color: #6c757d;
  font-weight: normal;
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
  padding: 2rem;
  text-align: center;
  background: #f8f9fa;
  border-radius: 10px;
  color: #6c757d;
  font-size: 1.1rem;
}

/* Ensure results container takes full width */
.results-container {
  width: 100%;
}

/* Progress bar animation */
@keyframes progress {
  0% {
    width: 0%;
  }
  50% {
    width: 70%;
  }
  100% {
    width: 100%;
  }
}

.animate-progress {
  animation: progress 2s ease-in-out infinite;
}
</style>
