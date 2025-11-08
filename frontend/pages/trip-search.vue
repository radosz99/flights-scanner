<template>
  <div class="max-w-[1400px] mx-auto p-8 font-sans dark:bg-gray-900">
    <!-- Header -->
    <h1 class="text-gray-800 dark:text-gray-100 mb-2 text-4xl font-bold">Round Trip Search</h1>
    <p class="text-gray-600 dark:text-gray-400 text-lg mb-8">
      Find the best round trip deals with flexible duration
    </p>

    <!-- Loading -->
    <div
      v-if="loading"
      class="mt-8 p-4 bg-yellow-50 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-md border border-yellow-200 dark:border-yellow-700 text-center text-lg"
    >
      {{ loadingMessage }}
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

    <!-- Trips Table -->
    <TripsTable :results="results" />

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
  limit: 100
})

const results = ref(null)

// Computed
const canSearch = computed(() => {
  return (
    searchParams.value.origin &&
    searchParams.value.minDays > 0 &&
    searchParams.value.maxDays > 0 &&
    searchParams.value.minDays <= searchParams.value.maxDays
  )
})

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadOrigins(),
    loadExampleRoutes()
  ])
})

// Watchers
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
  searchParams.value.destination = ''
  results.value = null
  searched.value = false

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

// Watch origin changes
watch(() => searchParams.value.origin, onOriginChange)

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

const searchTrips = async () => {
  if (!canSearch.value) {
    error.value = 'Please select an origin and specify trip duration'
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
    const params = {
      origin: searchParams.value.origin,
      min_days: searchParams.value.minDays,
      max_days: searchParams.value.maxDays,
      passengers: searchParams.value.passengers,
      limit: searchParams.value.limit
    }

    if (searchParams.value.destination) {
      params.destination = searchParams.value.destination
    }

    const response = await $fetch(`${apiBaseUrl}/flights/round-trips`, {
      params: params
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
  searchParams.value.origin = route.origin

  await Promise.all([
    loadDestinationsFromOrigin(route.origin),
    loadDestinationsPreview()
  ])

  searchParams.value.destination = route.destination

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
