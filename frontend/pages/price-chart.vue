<template>
  <div class="max-w-[1400px] mx-auto p-8 font-sans dark:bg-gray-900">
    <!-- Header -->
    <h1 class="text-gray-800 dark:text-gray-100 mb-2 text-4xl font-bold">Wykres Cen Lotów</h1>
    <p class="text-gray-600 dark:text-gray-400 text-lg mb-8">
      Zobacz trendy cenowe dla wybranej trasy w pełnym zakresie dat
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
      <strong>Błąd:</strong> {{ error }}
    </div>

    <!-- Route Selector -->
    <RouteSelector
      v-model:origin="selectedOrigin"
      v-model:destination="selectedDestination"
      :origins="origins"
      :available-destinations="availableDestinations"
      :loading="loading"
      @load="loadChartData"
      @clear="clearSelection"
    />

    <!-- Price Chart -->
    <PriceChart :chart-data="chartData" />

    <!-- Price Stats Table -->
    <PriceStatsTable :chart-data="chartData" />

    <!-- Flight Price History -->
    <FlightPriceHistory
      v-if="chartData && chartData.data && chartData.data.length > 0"
      :show="true"
      :origin="selectedOrigin"
      :destination="selectedDestination"
    />

    <!-- No Data Message -->
    <div
      v-if="!loading && selectedOrigin && selectedDestination && (!chartData || !chartData.data || chartData.data.length === 0)"
      class="mt-8 p-8 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-center text-lg"
    >
      Brak danych cenowych dla wybranej trasy. Spróbuj wybrać inną trasę.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl
const route = useRoute()
const router = useRouter()

const loading = ref(false)
const loadingMessage = ref('Loading...')
const error = ref(null)

const origins = ref([])
const availableDestinations = ref([])
const selectedOrigin = ref('')
const selectedDestination = ref('')
const chartData = ref(null)

// Initialize from URL query parameters
const initFromUrl = () => {
  if (route.query.skad) {
    selectedOrigin.value = route.query.skad.toString().toUpperCase()
  }
  if (route.query.do) {
    selectedDestination.value = route.query.do.toString().toUpperCase()
  }
}

// Update URL when selections change
const updateUrl = () => {
  const query = {}
  if (selectedOrigin.value) {
    query.skad = selectedOrigin.value
  }
  if (selectedDestination.value) {
    query.do = selectedDestination.value
  }
  router.push({ query })
}

// Load origins on mount
onMounted(async () => {
  await loadAirports()
  initFromUrl()

  // If both origin and destination are in URL, load destinations and chart
  if (selectedOrigin.value) {
    await loadDestinationsFromOrigin(selectedOrigin.value)
    if (selectedDestination.value) {
      await loadChartData()
    }
  }
})

const loadAirports = async () => {
  loading.value = true
  loadingMessage.value = 'Loading airports...'
  error.value = null

  try {
    const originsResponse = await $fetch(`${apiBaseUrl}/airports/origins`)
    origins.value = originsResponse.origins || []
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

// Watch origin changes
watch(() => selectedOrigin.value, async (newOrigin) => {
  selectedDestination.value = ''
  chartData.value = null

  if (newOrigin) {
    await loadDestinationsFromOrigin(newOrigin)
  } else {
    availableDestinations.value = []
  }

  updateUrl()
})

// Watch destination changes - auto-load when both are selected
watch(() => selectedDestination.value, (newDest) => {
  if (newDest && selectedOrigin.value) {
    loadChartData()
  }

  updateUrl()
})

const loadChartData = async () => {
  if (!selectedOrigin.value || !selectedDestination.value) {
    error.value = 'Please select both origin and destination'
    return
  }

  loading.value = true
  loadingMessage.value = 'Loading price data...'
  error.value = null
  chartData.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/flights/price-chart`, {
      params: {
        origin: selectedOrigin.value,
        destination: selectedDestination.value
      }
    })

    chartData.value = response
  } catch (e) {
    if (e.statusCode === 404) {
      error.value = `No flights found for route ${selectedOrigin.value} → ${selectedDestination.value}`
    } else {
      error.value = e.message || 'Failed to load price chart data'
    }
    chartData.value = null
  } finally {
    loading.value = false
  }
}

const clearSelection = () => {
  selectedOrigin.value = ''
  selectedDestination.value = ''
  availableDestinations.value = []
  chartData.value = null
  error.value = null
}
</script>
