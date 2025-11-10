<template>
  <div class="max-w-[1400px] mx-auto p-8 font-sans dark:bg-gray-900">
    <!-- Header -->
    <h1 class="text-gray-800 dark:text-gray-100 mb-2 text-4xl font-bold">Round Trip Search</h1>
    <p class="text-gray-600 dark:text-gray-400 text-lg mb-8">
      Find the best round trip deals with flexible duration
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
      class="mt-8 p-4 bg-red-50 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-md border border-red-200 dark:border-red-700"
    >
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Search Form -->
    <TripSearchForm
      v-model:origin="searchParams.origin"
      v-model:destination="searchParams.destination"
      v-model:min-days="searchParams.minDays"
      v-model:max-days="searchParams.maxDays"
      v-model:limit="searchParams.limit"
      v-model:return-from-same-airport="searchParams.returnFromSameAirport"
      v-model:outbound-weekdays="searchParams.outboundWeekdays"
      v-model:return-weekdays="searchParams.returnWeekdays"
      :origins="origins"
      :available-destinations="availableDestinations"
      :can-search="canSearch"
      @search="searchTrips"
      @clear="clearSearch"
    />

    <!-- Destinations Preview -->
    <DestinationsPreview
      :origin="searchParams.origin"
      :destinations="destinationsPreview"
      :min-days="searchParams.minDays"
      :max-days="searchParams.maxDays"
      :selected-destination="searchParams.destination"
      @select="selectDestination"
    />

    <!-- Example Routes -->
    <ExampleRoutes
      :routes="exampleRoutes"
      :origin="searchParams.origin"
      @select="selectExampleRoute"
    />

    <!-- View Toggle (only show when there are results or example routes) -->
    <div
      v-if="(results && results.trips.length > 0) || (exampleRoutes.length > 0)"
      class="mt-8 flex justify-center items-center gap-2"
    >
      <span class="text-gray-600 dark:text-gray-400 mr-2">View:</span>
      <div class="inline-flex rounded-lg shadow-sm" role="group">
        <button
          @click="viewMode = 'table'"
          :class="[
            'px-6 py-2.5 text-sm font-medium rounded-l-lg border transition-colors',
            viewMode === 'table'
              ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-500 dark:border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'
          ]"
        >
          <svg class="w-5 h-5 inline mr-1 -mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Table
        </button>
        <button
          @click="viewMode = 'map'"
          :class="[
            'px-6 py-2.5 text-sm font-medium rounded-r-lg border-t border-r border-b transition-colors',
            viewMode === 'map'
              ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-500 dark:border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'
          ]"
        >
          <svg class="w-5 h-5 inline mr-1 -mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          Map
        </button>
      </div>
    </div>

    <!-- Trips Table with blur effect when loading -->
    <div :class="{ 'blur-sm opacity-60 pointer-events-none': loading && results }">
      <TripsTable v-if="viewMode === 'table' && results && results.trips.length > 0" :results="results" />
    </div>

    <!-- Trips Map (Client-only to avoid SSR issues with Leaflet) with blur effect when loading -->
    <ClientOnly>
      <div :class="{ 'blur-sm opacity-60 pointer-events-none': loading && results }">
        <TripsMap
          v-if="viewMode === 'map' && ((results && results.trips.length > 0) || exampleRoutes.length > 0)"
          :results="results"
          :all-routes="exampleRoutes"
        />
      </div>
      <template #fallback>
        <div class="mt-8 p-8 bg-gray-100 dark:bg-gray-800 rounded-lg text-center">
          <p class="text-gray-600 dark:text-gray-400">Loading map...</p>
        </div>
      </template>
    </ClientOnly>

    <!-- Message when on table view but no results -->
    <div
      v-if="viewMode === 'table' && !results && exampleRoutes.length > 0"
      class="mt-8 p-8 bg-blue-50 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-lg text-center"
    >
      <p class="text-lg mb-2">Switch to Map view to see all available two-way routes!</p>
      <p class="text-sm">Or select an origin airport and search for specific trips to see results in table view.</p>
    </div>

    <!-- No Results -->
    <div
      v-if="!loading && searched && (!results || results.trips.length === 0)"
      class="mt-8 p-8 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-center text-lg"
    >
      <p>No round trips found matching your criteria. Try adjusting your search parameters.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

// State
const loading = ref(false)
const loadingMessage = ref('Loading...')
const error = ref(null)
const searched = ref(false)

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
  limit: 100,
  returnFromSameAirport: true,
  outboundWeekdays: [],
  returnWeekdays: []
})

const results = ref(null)
const viewMode = ref('table') // 'table' or 'map'

// Computed
const canSearch = computed(() => {
  return (
    searchParams.value.origin &&
    searchParams.value.minDays > 0 &&
    searchParams.value.maxDays > 0 &&
    searchParams.value.minDays <= searchParams.value.maxDays
  )
})

// Methods (defined before watchers to avoid initialization errors)
const onOriginChange = async () => {
  searchParams.value.destination = ''
  results.value = null
  searched.value = false

  if (searchParams.value.origin) {
    await Promise.all([
      loadDestinationsFromOrigin(searchParams.value.origin),
      loadDestinationsPreview(),
      loadExampleRoutes()
    ])
  } else {
    availableDestinations.value = []
    destinationsPreview.value = []
    await loadExampleRoutes()
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

const loadDestinationsPreview = async () => {
  if (!searchParams.value.origin) {
    destinationsPreview.value = []
    return
  }

  try {
    const params = {
      origin: searchParams.value.origin,
      min_days: searchParams.value.minDays,
      max_days: searchParams.value.maxDays,
      return_from_same_airport: searchParams.value.returnFromSameAirport
    }

    // Add weekday filters if they are selected
    if (searchParams.value.outboundWeekdays.length > 0) {
      params.outbound_weekdays = searchParams.value.outboundWeekdays.join(',')
    }
    if (searchParams.value.returnWeekdays.length > 0) {
      params.return_weekdays = searchParams.value.returnWeekdays.join(',')
    }

    const response = await $fetch(`${apiBaseUrl}/flights/round-trips/preview`, { params })
    destinationsPreview.value = response.destinations || []
  } catch (e) {
    console.error('Failed to load destinations preview:', e)
  }
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadOrigins(),
    loadExampleRoutes()
  ])
})

// Watchers
watch(() => searchParams.value.origin, onOriginChange)

watch(() => searchParams.value.destination, (newDest, oldDest) => {
  if (newDest && newDest !== oldDest && canSearch.value) {
    searchTrips()
  }
})

watch(() => [searchParams.value.minDays, searchParams.value.maxDays], () => {
  if (searchParams.value.origin) {
    loadDestinationsPreview()
  }

  if (results.value && canSearch.value) {
    searchTrips()
  }
})

// Watch min/max days for validation
watch(() => searchParams.value.minDays, (newVal) => {
  if (newVal > searchParams.value.maxDays) {
    searchParams.value.maxDays = newVal
  }
})

watch(() => searchParams.value.maxDays, (newVal) => {
  if (newVal < searchParams.value.minDays) {
    searchParams.value.minDays = newVal
  }
})

// Methods
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

const searchTrips = async () => {
  if (!canSearch.value) {
    error.value = 'Please select an origin and specify trip duration'
    return
  }

  loading.value = true
  loadingMessage.value = 'Searching for trips...'
  error.value = null
  // Don't clear results.value here - keep old results visible but blurred
  searched.value = true

  try {
    const params = {
      origin: searchParams.value.origin,
      min_days: searchParams.value.minDays,
      max_days: searchParams.value.maxDays,
      passengers: searchParams.value.passengers,
      limit: searchParams.value.limit,
      return_from_same_airport: searchParams.value.returnFromSameAirport
    }

    if (searchParams.value.destination) {
      params.destination = searchParams.value.destination
    }

    // Add weekday filters if they are selected
    if (searchParams.value.outboundWeekdays.length > 0) {
      params.outbound_weekdays = searchParams.value.outboundWeekdays.join(',')
    }
    if (searchParams.value.returnWeekdays.length > 0) {
      params.return_weekdays = searchParams.value.returnWeekdays.join(',')
    }

    const newResults = await $fetch(`${apiBaseUrl}/flights/round-trips`, { params })
    // Only update results after successful fetch
    results.value = newResults
  } catch (e) {
    // Handle different error types
    if (e.statusCode === 400) {
      // Extract the detailed error message from the backend
      const errorDetail = e.data?.detail || e.message || 'Request parameters exceed processing limits'
      error.value = errorDetail
    } else if (e.statusCode === 404) {
      error.value = 'No round trips found for the selected criteria'
    } else {
      error.value = e.message || 'Failed to search trips'
    }
    // Clear results on error
    results.value = null
  } finally {
    loading.value = false
  }
}

const loadExampleRoutes = async () => {
  try {
    const params = { limit: 200 }

    // If origin is selected, filter routes by origin
    if (searchParams.value.origin) {
      params.origin = searchParams.value.origin
    }

    const response = await $fetch(`${apiBaseUrl}/airports/two-way-routes`, { params })
    exampleRoutes.value = response.routes || []
  } catch (e) {
    console.error('Failed to load example routes:', e)
  }
}

const selectExampleRoute = async (route) => {
  searchParams.value.origin = route.origin
  await Promise.all([loadDestinationsFromOrigin(route.origin), loadDestinationsPreview()])
  searchParams.value.destination = route.destination
}

const selectDestination = (dest) => {
  searchParams.value.destination = dest.destination
}

const clearSearch = () => {
  searchParams.value = {
    origin: '',
    destination: '',
    minDays: 3,
    maxDays: 7,
    passengers: 1,
    limit: 100,
    returnFromSameAirport: true,
    outboundWeekdays: [],
    returnWeekdays: []
  }
  availableDestinations.value = []
  results.value = null
  error.value = null
  searched.value = false
}
</script>

<style scoped>
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
