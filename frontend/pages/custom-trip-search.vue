<template>
  <div class="max-w-full mx-auto p-8 min-h-screen dark:bg-gray-900">
    <h1 class="text-gray-800 dark:text-gray-100 text-4xl font-bold mb-4">Custom Trip Search</h1>
    <p class="text-gray-600 dark:text-gray-300 text-lg mb-8">
      Search for one-way or round-trip flights with flexible origin and destination matching. Use batch search to efficiently find flights across multiple airports.
    </p>

    <!-- Error -->
    <div
      v-if="error"
      class="mt-8 p-4 bg-red-50 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-md border border-red-200 dark:border-red-700"
    >
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Main Content: Filters + Results Side by Side on Desktop -->
    <div class="flex flex-col lg:flex-row lg:items-start gap-6 mt-8">
      <!-- Search Form (Left Side on Desktop) -->
      <div class="lg:w-[30%] lg:sticky lg:top-8">
        <TripFilters
          :filters="searchParams"
          :polish-airports-options="polishAirportsOptions"
          :all-airports-options="allAirportsOptions"
          :countries-options="countriesOptions"
          :countries-data="countriesData"
          :can-search="canSearch"
          :loading="loading"
          @update:filters="updateFilters"
          @search="searchTrips"
          @clear="clearFilters"
        />
      </div>

      <!-- Results Section (Right Side on Desktop) -->
      <div class="lg:flex-1 lg:min-w-0">
        <TripResults
          :results="results"
          :loading="loading"
          :loading-message="loadingMessage"
          :searched="searched"
          :two-way-routes="searchParams.twoWayRoutes"
          :current-page="currentPage"
          :items-per-page="itemsPerPage"
          @update:current-page="currentPage = $event"
        />
      </div>
    </div>

    <!-- Scroll to Top Button -->
    <button
      v-if="showScrollTop"
      @click="scrollToTop"
      class="fixed bottom-8 right-8 p-4 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-full shadow-lg transition-all duration-300 hover:scale-110 z-50"
      title="Scroll to top"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import TripFilters from '~/components/TripFilters.vue'
import TripResults from '~/components/TripResults.vue'

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl
const router = useRouter()
const route = useRoute()

// Scroll to top state
const showScrollTop = ref(false)

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
const countriesData = ref([])

// Pagination
const currentPage = ref(1)
const itemsPerPage = 50

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

// Options formatted for MultiSelectDropdown component (countries)
const countriesOptions = computed(() => {
  return countriesData.value.map(countryData => ({
    value: countryData.country,
    label: `${countryData.country} (${countryData.airport_count} airports)`
  }))
})

// URL Parameter Sync Methods
const parseUrlParams = () => {
  const query = route.query

  if (Object.keys(query).length === 0) {
    return // No URL params, use defaults
  }

  // Parse origins
  if (query.origins) {
    searchParams.value.origins = query.origins.split(',').filter(Boolean)
  }

  // Parse destinations
  if (query.destinations) {
    searchParams.value.destinations = query.destinations.split(',').filter(Boolean)
  }

  // Parse boolean flags
  if (query.twoWayRoutes !== undefined) {
    searchParams.value.twoWayRoutes = query.twoWayRoutes === 'true'
  }

  if (query.returnFromSameAirport !== undefined) {
    searchParams.value.returnFromSameAirport = query.returnFromSameAirport === 'true'
  }

  if (query.returnToSameAirport !== undefined) {
    searchParams.value.returnToSameAirport = query.returnToSameAirport === 'true'
  }

  // Parse dates
  if (query.dateFrom) {
    searchParams.value.dateFrom = query.dateFrom
  }

  if (query.dateTo) {
    searchParams.value.dateTo = query.dateTo
  }

  // Parse numbers
  if (query.minDays) {
    searchParams.value.minDays = parseInt(query.minDays)
  }

  if (query.maxDays) {
    searchParams.value.maxDays = parseInt(query.maxDays)
  }

  // Parse weekday arrays
  if (query.outboundWeekdays) {
    searchParams.value.outboundWeekdays = query.outboundWeekdays.split(',').map(Number).filter(n => !isNaN(n))
  }

  if (query.returnWeekdays) {
    searchParams.value.returnWeekdays = query.returnWeekdays.split(',').map(Number).filter(n => !isNaN(n))
  }
}

const updateUrlParams = () => {
  const query = {}

  // Add origins
  if (searchParams.value.origins.length > 0) {
    query.origins = searchParams.value.origins.join(',')
  }

  // Add destinations
  if (searchParams.value.destinations.length > 0) {
    query.destinations = searchParams.value.destinations.join(',')
  }

  // Add boolean flags
  query.twoWayRoutes = searchParams.value.twoWayRoutes.toString()
  query.returnFromSameAirport = searchParams.value.returnFromSameAirport.toString()
  query.returnToSameAirport = searchParams.value.returnToSameAirport.toString()

  // Add dates
  if (searchParams.value.dateFrom) {
    query.dateFrom = searchParams.value.dateFrom
  }

  if (searchParams.value.dateTo) {
    query.dateTo = searchParams.value.dateTo
  }

  // Add numbers
  if (searchParams.value.minDays) {
    query.minDays = searchParams.value.minDays.toString()
  }

  if (searchParams.value.maxDays) {
    query.maxDays = searchParams.value.maxDays.toString()
  }

  // Add weekday arrays
  if (searchParams.value.outboundWeekdays.length > 0) {
    query.outboundWeekdays = searchParams.value.outboundWeekdays.join(',')
  }

  if (searchParams.value.returnWeekdays.length > 0) {
    query.returnWeekdays = searchParams.value.returnWeekdays.join(',')
  }

  // Update URL without triggering navigation
  router.replace({ query })
}

// Watch for changes to searchParams and update URL
watch(searchParams, () => {
  updateUrlParams()
}, { deep: true })

// Methods
const updateFilters = (newFilters) => {
  searchParams.value = { ...newFilters }
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
  currentPage.value = 1 // Reset to first page on new search

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
      limit: 1000, // Backend maximum limit
      return_from_same_airport: searchParams.value.returnFromSameAirport,
      return_to_same_airport: searchParams.value.returnToSameAirport
    }

    // Add optional filters
    if (searchParams.value.dateFrom) params.date_from = searchParams.value.dateFrom
    if (searchParams.value.dateTo) params.date_to = searchParams.value.dateTo

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
      limit: 1000 // Backend maximum limit
    }

    // Add optional filters
    if (searchParams.value.dateFrom) params.date_from = searchParams.value.dateFrom
    if (searchParams.value.dateTo) params.date_to = searchParams.value.dateTo

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
    returnToSameAirport: true,
    dateFrom: getTodayDate(),
    dateTo: '',
    minDays: 3,
    maxDays: 7,
    outboundWeekdays: [],
    returnWeekdays: []
  }
  results.value = null
  error.value = null
  searched.value = false
  currentPage.value = 1
}

// Scroll to top functionality
const handleScroll = () => {
  showScrollTop.value = window.scrollY > 300
}

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

// Lifecycle
onMounted(async () => {
  await loadAirports()
  parseUrlParams() // Load filters from URL
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>
