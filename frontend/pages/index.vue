<template>
  <div class="max-w-full mx-auto p-4 md:p-8 min-h-screen dark:bg-gray-900">
    <h1 class="text-gray-800 dark:text-gray-100 text-2xl md:text-4xl font-bold mb-2 md:mb-4">Wyszukiwarka Lotów</h1>
    <p class="text-gray-600 dark:text-gray-300 text-sm md:text-lg mb-4 md:mb-8">
      Szukaj lotów w jedną stronę lub w obie strony z elastycznym dopasowaniem tras. Użyj wyszukiwania wsadowego, aby efektywnie znaleźć loty na wielu lotniskach.
    </p>

    <!-- Error -->
    <div
      v-if="error"
      class="mt-8 p-4 bg-red-50 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-md border border-red-200 dark:border-red-700"
    >
      <strong>Błąd:</strong> {{ error }}
    </div>

    <!-- Main Content: Filters + Results Side by Side on Desktop -->
    <div class="flex flex-col lg:flex-row lg:items-start gap-3 md:gap-6 mt-4 md:mt-8">
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
          :destination-mode="destinationMode"
          :selected-countries="selectedCountries"
          @update:filters="updateFilters"
          @update:destination-mode="destinationMode = $event"
          @update:selected-countries="selectedCountries = $event"
          @search="searchTrips"
          @clear="clearFilters"
        />
      </div>

      <!-- Results Section (Right Side on Desktop) -->
      <div class="lg:flex-1 lg:min-w-0 relative">
        <!-- Filters Changed Overlay -->
        <div
          v-if="filtersChanged && results"
          class="absolute inset-0 bg-gray-900/50 dark:bg-gray-950/70 backdrop-blur-sm z-20 flex items-start justify-center pt-16"
        >
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md mx-4">
            <h3 class="text-xl font-bold text-gray-800 dark:text-gray-100 mb-3">
              Filtry zostały zmienione
            </h3>
            <p class="text-gray-600 dark:text-gray-300 mb-4 text-sm">
              Twoje filtry zostały zmodyfikowane. Kliknij "Szukaj Lotów", aby zobaczyć zaktualizowane wyniki lub przywróć poprzednie filtry.
            </p>
            <div class="flex gap-3">
              <button
                @click="revertFilters"
                class="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 dark:bg-gray-600 dark:hover:bg-gray-700 text-white font-medium rounded-md transition-colors"
              >
                Cofnij Zmiany
              </button>
              <button
                @click="searchTrips"
                :disabled="!canSearch"
                class="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-medium rounded-md transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                Szukaj Teraz
              </button>
            </div>
          </div>
        </div>

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
      title="Przewiń do góry"
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
const loadingMessage = ref('Ładowanie...')
const error = ref(null)
const searched = ref(false)

const allAirports = ref([])
const countriesData = ref([])

// Destination mode state
const destinationMode = ref('airports')
const selectedCountries = ref([])

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

// Track last searched parameters to detect changes
const lastSearchedParams = ref(null)
const lastSearchedDestinationMode = ref(null)
const lastSearchedSelectedCountries = ref(null)

const results = ref(null)

// Computed
const canSearch = computed(() => {
  const hasOrigins = searchParams.value.origins.length > 0
  // Allow empty destinations for "anywhere" search, but only with exactly one origin
  const hasDestinations = searchParams.value.destinations.length > 0 ||
                          (searchParams.value.destinations.length === 0 && searchParams.value.origins.length === 1)

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

// Check if filters have changed since last search
const filtersChanged = computed(() => {
  if (!lastSearchedParams.value) return false

  const paramsMatch = JSON.stringify(searchParams.value) === JSON.stringify(lastSearchedParams.value)
  const modeMatch = destinationMode.value === lastSearchedDestinationMode.value
  const countriesMatch = JSON.stringify(selectedCountries.value) === JSON.stringify(lastSearchedSelectedCountries.value)

  return !paramsMatch || !modeMatch || !countriesMatch
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

// LocalStorage Methods
const saveFiltersToLocalStorage = () => {
  try {
    const filtersData = {
      searchParams: searchParams.value,
      destinationMode: destinationMode.value,
      selectedCountries: selectedCountries.value
    }
    localStorage.setItem('flightFilters', JSON.stringify(filtersData))
  } catch (e) {
    console.error('Failed to save filters to localStorage:', e)
  }
}

const loadFiltersFromLocalStorage = () => {
  try {
    const savedFilters = localStorage.getItem('flightFilters')
    if (savedFilters) {
      const filtersData = JSON.parse(savedFilters)

      // Load search params
      if (filtersData.searchParams) {
        searchParams.value = { ...searchParams.value, ...filtersData.searchParams }
      }

      // Load destination mode
      if (filtersData.destinationMode) {
        destinationMode.value = filtersData.destinationMode
      }

      // Load selected countries
      if (filtersData.selectedCountries) {
        selectedCountries.value = filtersData.selectedCountries
      }

      return true
    }
    return false
  } catch (e) {
    console.error('Failed to load filters from localStorage:', e)
    return false
  }
}

// URL Parameter Sync Methods (with Polish param names)
const parseUrlParams = () => {
  const query = route.query

  if (Object.keys(query).length === 0) {
    return false // No URL params
  }

  // Parse origins (skąd)
  if (query.skad) {
    searchParams.value.origins = query.skad.split(',').filter(Boolean)
  }

  // Parse destination mode and destinations
  if (query.trybCelu === 'gdziekolwiek') {
    // Anywhere mode - no destinations specified
    destinationMode.value = 'anywhere'
    selectedCountries.value = []
    searchParams.value.destinations = []
  } else if (query.krajeCelu) {
    // Country mode - parse countries and convert to airports
    destinationMode.value = 'country'
    selectedCountries.value = query.krajeCelu.split(',').filter(Boolean)

    // Convert countries to airport codes
    const airportCodes = []
    selectedCountries.value.forEach(country => {
      const countryData = countriesData.value.find(c => c.country === country)
      if (countryData && countryData.airports) {
        airportCodes.push(...countryData.airports.map(a => a.code))
      }
    })
    searchParams.value.destinations = airportCodes
  } else if (query.dokad) {
    // Airport mode - use airport codes directly
    destinationMode.value = 'airports'
    selectedCountries.value = []
    searchParams.value.destinations = query.dokad.split(',').filter(Boolean)
  }

  // Parse boolean flags
  if (query.wObieSstrony !== undefined) {
    searchParams.value.twoWayRoutes = query.wObieSstrony === 'true'
  }

  if (query.powrotZTegoSamegoLotniska !== undefined) {
    searchParams.value.returnFromSameAirport = query.powrotZTegoSamegoLotniska === 'true'
  }

  if (query.powrotNaToSamoLotnisko !== undefined) {
    searchParams.value.returnToSameAirport = query.powrotNaToSamoLotnisko === 'true'
  }

  // Parse dates
  if (query.dataOd) {
    searchParams.value.dateFrom = query.dataOd
  }

  if (query.dataDo) {
    searchParams.value.dateTo = query.dataDo
  }

  // Parse numbers
  if (query.minDni) {
    searchParams.value.minDays = parseInt(query.minDni)
  }

  if (query.maxDni) {
    searchParams.value.maxDays = parseInt(query.maxDni)
  }

  // Parse weekday arrays
  if (query.dniWylotu) {
    searchParams.value.outboundWeekdays = query.dniWylotu.split(',').map(Number).filter(n => !isNaN(n))
  }

  if (query.dniPowrotu) {
    searchParams.value.returnWeekdays = query.dniPowrotu.split(',').map(Number).filter(n => !isNaN(n))
  }

  return true // URL params were loaded
}

const updateUrlParams = () => {
  const query = {}

  // Add origins (skąd - from where)
  if (searchParams.value.origins.length > 0) {
    query.skad = searchParams.value.origins.join(',')
  }

  // Add destinations based on mode
  if (destinationMode.value === 'anywhere') {
    // Anywhere mode - save mode only, no destinations
    query.trybCelu = 'gdziekolwiek'
  } else if (destinationMode.value === 'country' && selectedCountries.value.length > 0) {
    // Country mode - save country names
    query.krajeCelu = selectedCountries.value.join(',')
  } else if (destinationMode.value === 'airports' && searchParams.value.destinations.length > 0) {
    // Airport mode - save airport codes (dokąd - to where)
    query.dokad = searchParams.value.destinations.join(',')
  }

  // Add boolean flags
  query.wObieSstrony = searchParams.value.twoWayRoutes.toString()
  query.powrotZTegoSamegoLotniska = searchParams.value.returnFromSameAirport.toString()
  query.powrotNaToSamoLotnisko = searchParams.value.returnToSameAirport.toString()

  // Add dates
  if (searchParams.value.dateFrom) {
    query.dataOd = searchParams.value.dateFrom
  }

  if (searchParams.value.dateTo) {
    query.dataDo = searchParams.value.dateTo
  }

  // Add numbers
  if (searchParams.value.minDays) {
    query.minDni = searchParams.value.minDays.toString()
  }

  if (searchParams.value.maxDays) {
    query.maxDni = searchParams.value.maxDays.toString()
  }

  // Add weekday arrays
  if (searchParams.value.outboundWeekdays.length > 0) {
    query.dniWylotu = searchParams.value.outboundWeekdays.join(',')
  }

  if (searchParams.value.returnWeekdays.length > 0) {
    query.dniPowrotu = searchParams.value.returnWeekdays.join(',')
  }

  // Save to localStorage whenever URL is updated
  saveFiltersToLocalStorage()

  // Update URL without triggering navigation
  router.replace({ query })
}

// Methods
const updateFilters = (newFilters) => {
  searchParams.value = { ...newFilters }
  saveFiltersToLocalStorage()
}

const loadAirports = async () => {
  loading.value = true
  loadingMessage.value = 'Ładowanie lotnisk...'
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
    error.value = e.message || 'Nie udało się załadować lotnisk'
  } finally {
    loading.value = false
  }
}

const searchTrips = async () => {
  if (!canSearch.value) {
    error.value = 'Proszę wybrać lotnisko(a) wylotu, lotnisko(a) docelowe i określić czas trwania podróży'
    return
  }

  loading.value = true
  loadingMessage.value = 'Wyszukiwanie lotów...'
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

    // Save last searched params for change detection
    lastSearchedParams.value = JSON.parse(JSON.stringify(searchParams.value))
    lastSearchedDestinationMode.value = destinationMode.value
    lastSearchedSelectedCountries.value = JSON.parse(JSON.stringify(selectedCountries.value))

    // Update URL only after successful search
    updateUrlParams()
  } catch (e) {
    error.value = e.statusCode === 404
      ? 'Nie znaleziono lotów dla wybranych kryteriów'
      : e.message || 'Nie udało się wyszukać lotów'
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
      min_days: searchParams.value.minDays,
      max_days: searchParams.value.maxDays,
      passengers: 1, // Default to 1 passenger for price display
      limit: 1000, // Backend maximum limit
      return_from_same_airport: searchParams.value.returnFromSameAirport,
      return_to_same_airport: searchParams.value.returnToSameAirport
    }

    // Add destinations only if not empty (for "anywhere" search, destinations is empty)
    if (searchParams.value.destinations.length > 0) {
      params.destinations = searchParams.value.destinations.join(',')
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
      passengers: 1, // Default to 1 passenger for price display
      limit: 1000 // Backend maximum limit
    }

    // Add destinations only if not empty (for "anywhere" search, destinations is empty)
    if (searchParams.value.destinations.length > 0) {
      params.destinations = searchParams.value.destinations.join(',')
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
  destinationMode.value = 'airports'
  selectedCountries.value = []
  results.value = null
  error.value = null
  searched.value = false
  currentPage.value = 1

  // Save cleared state to localStorage
  saveFiltersToLocalStorage()

  // Clear URL params
  router.replace({ query: {} })
}

// Revert to last searched filters
const revertFilters = () => {
  if (lastSearchedParams.value) {
    searchParams.value = JSON.parse(JSON.stringify(lastSearchedParams.value))
    destinationMode.value = lastSearchedDestinationMode.value
    selectedCountries.value = JSON.parse(JSON.stringify(lastSearchedSelectedCountries.value))
  }
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

  // Try to load from URL first, then fall back to localStorage
  const hasUrlParams = parseUrlParams()

  if (!hasUrlParams) {
    // No URL params, try to load from localStorage
    loadFiltersFromLocalStorage()
  }

  // Auto-search if URL has valid search parameters
  if (route.query && Object.keys(route.query).length > 0 && canSearch.value) {
    await searchTrips()
  }

  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

// Watch for filter changes and save to localStorage
watch([searchParams, destinationMode, selectedCountries], () => {
  saveFiltersToLocalStorage()
}, { deep: true })
</script>
