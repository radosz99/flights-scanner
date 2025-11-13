<template>
  <div v-if="show" class="mt-8 p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
        Flight Price History
      </h2>
      <p class="text-sm text-gray-600 dark:text-gray-400">
        View price changes for a specific flight across multiple scans
      </p>
    </div>

    <!-- Date and Flight Selection -->
    <div class="mb-6 space-y-4">
      <!-- Date Input -->
      <div>
        <label for="date-input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Date
        </label>
        <input
          id="date-input"
          v-model="selectedDate"
          type="date"
          class="w-full md:w-auto px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          @change="loadFlightsForDate"
        >
      </div>

      <!-- Flight Selector -->
      <div v-if="availableFlights.length > 0">
        <label for="flight-select" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Flight ({{ availableFlights.length }} available)
        </label>
        <select
          id="flight-select"
          v-model="selectedFlightId"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          @change="loadFlightPriceHistory"
        >
          <option value="">-- Select a flight --</option>
          <option
            v-for="flight in availableFlights"
            :key="flight.flight_id"
            :value="flight.flight_id"
          >
            {{ flight.flight_number }} | {{ formatTime(flight.departure_time) }} - {{ formatTime(flight.arrival_time) }} | {{ flight.duration }} | {{ flight.current_price }} {{ flight.currency }} | Scans: {{ flight.scan_count }}
          </option>
        </select>
      </div>

      <!-- No flights message -->
      <div
        v-if="selectedDate && !loadingFlights && availableFlights.length === 0"
        class="p-4 bg-yellow-50 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-lg border border-yellow-200 dark:border-yellow-700"
      >
        No flights found for this date. Try selecting a different date.
      </div>
    </div>

    <!-- Loading -->
    <div
      v-if="loadingFlights || loadingHistory"
      class="p-4 bg-blue-50 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-lg border border-blue-200 dark:border-blue-700 text-center"
    >
      {{ loadingFlights ? 'Loading flights...' : 'Loading price history...' }}
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="p-4 bg-red-50 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-lg border border-red-200 dark:border-red-700"
    >
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Flight Info Card -->
    <div
      v-if="flightHistory"
      class="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
    >
      <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">
        Flight Details
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
        <div>
          <span class="font-medium text-gray-700 dark:text-gray-300">Flight:</span>
          <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.flight_number }}</span>
        </div>
        <div>
          <span class="font-medium text-gray-700 dark:text-gray-300">Route:</span>
          <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.origin }} → {{ flightHistory.destination }}</span>
        </div>
        <div>
          <span class="font-medium text-gray-700 dark:text-gray-300">Date:</span>
          <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.date_out }}</span>
        </div>
        <div>
          <span class="font-medium text-gray-700 dark:text-gray-300">Time:</span>
          <span class="ml-2 text-gray-900 dark:text-gray-100">{{ formatTime(flightHistory.departure_time) }} - {{ formatTime(flightHistory.arrival_time) }}</span>
        </div>
        <div>
          <span class="font-medium text-gray-700 dark:text-gray-300">Duration:</span>
          <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.duration }}</span>
        </div>
        <div>
          <span class="font-medium text-gray-700 dark:text-gray-300">Current Price:</span>
          <span class="ml-2 text-gray-900 dark:text-gray-100 font-semibold">{{ flightHistory.current_price }} {{ flightHistory.currency }}</span>
        </div>
        <div>
          <span class="font-medium text-gray-700 dark:text-gray-300">Total Scans:</span>
          <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.scan_count }}</span>
        </div>
        <div>
          <span class="font-medium text-gray-700 dark:text-gray-300">Price Points:</span>
          <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.price_history.length }}</span>
        </div>
      </div>
    </div>

    <!-- Price History Chart -->
    <div v-if="flightHistory && flightHistory.price_history.length > 0" class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <canvas ref="historyChartCanvas"></canvas>
    </div>

    <!-- No price history message -->
    <div
      v-if="flightHistory && flightHistory.price_history.length === 0"
      class="p-4 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-center"
    >
      No price history available for this flight yet. The flight needs to be scanned multiple times to build price history.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  show: {
    type: Boolean,
    default: true
  },
  origin: String,
  destination: String
})

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

const selectedDate = ref('')
const selectedFlightId = ref('')
const availableFlights = ref([])
const flightHistory = ref(null)
const loadingFlights = ref(false)
const loadingHistory = ref(false)
const error = ref(null)

const historyChartCanvas = ref(null)
let historyChartInstance = null

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  // Extract time from ISO format (YYYY-MM-DDTHH:MM:SS)
  const match = timeStr.match(/T(\d{2}:\d{2})/)
  return match ? match[1] : timeStr
}

const loadFlightsForDate = async () => {
  if (!selectedDate.value || !props.origin || !props.destination) {
    return
  }

  loadingFlights.value = true
  error.value = null
  availableFlights.value = []
  selectedFlightId.value = ''
  flightHistory.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/flights/for-date`, {
      params: {
        origin: props.origin,
        destination: props.destination,
        date: selectedDate.value
      }
    })

    availableFlights.value = response.flights || []
  } catch (e) {
    if (e.statusCode === 404) {
      error.value = `No flights found for ${props.origin} → ${props.destination} on ${selectedDate.value}`
    } else {
      error.value = e.message || 'Failed to load flights'
    }
    availableFlights.value = []
  } finally {
    loadingFlights.value = false
  }
}

const loadFlightPriceHistory = async () => {
  if (!selectedFlightId.value) {
    flightHistory.value = null
    return
  }

  loadingHistory.value = true
  error.value = null
  flightHistory.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/flights/price-history/${selectedFlightId.value}`)
    flightHistory.value = response

    // Render chart after data is loaded
    await nextTick()
    renderHistoryChart()
  } catch (e) {
    if (e.statusCode === 404) {
      error.value = 'Flight not found'
    } else {
      error.value = e.message || 'Failed to load price history'
    }
    flightHistory.value = null
  } finally {
    loadingHistory.value = false
  }
}

const renderHistoryChart = () => {
  if (!historyChartCanvas.value || !flightHistory.value || !flightHistory.value.price_history.length) {
    return
  }

  // Destroy existing chart if any
  if (historyChartInstance) {
    historyChartInstance.destroy()
  }

  const priceHistory = flightHistory.value.price_history
  const labels = priceHistory.map(entry => {
    const date = new Date(entry.timestamp)
    return date.toLocaleString('pl-PL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  })
  const prices = priceHistory.map(entry => entry.price)
  const changes = priceHistory.map(entry => entry.change)

  const ctx = historyChartCanvas.value.getContext('2d')

  historyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Price',
          data: prices,
          borderColor: '#007bff',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          borderWidth: 3,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.1,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 2,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            font: {
              size: 14,
              weight: '600'
            },
            usePointStyle: true,
            padding: 20
          }
        },
        title: {
          display: true,
          text: `Price History: ${flightHistory.value.flight_number} (${flightHistory.value.origin} → ${flightHistory.value.destination})`,
          font: {
            size: 16,
            weight: 'bold'
          },
          padding: 20
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 13
          },
          padding: 12,
          displayColors: true,
          callbacks: {
            label: function(context) {
              const index = context.dataIndex
              const price = context.parsed.y
              const change = changes[index]
              let changeText = ''
              if (change > 0) {
                changeText = ` (+${change.toFixed(2)} ${flightHistory.value.currency})`
              } else if (change < 0) {
                changeText = ` (${change.toFixed(2)} ${flightHistory.value.currency})`
              }
              return `Price: ${price.toFixed(2)} ${flightHistory.value.currency}${changeText}`
            }
          }
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Scan Time',
            font: {
              size: 14,
              weight: 'bold'
            }
          },
          ticks: {
            maxRotation: 45,
            minRotation: 45,
            font: {
              size: 10
            }
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: `Price (${flightHistory.value.currency})`,
            font: {
              size: 14,
              weight: 'bold'
            }
          },
          beginAtZero: false,
          ticks: {
            font: {
              size: 12
            },
            callback: function(value) {
              return value.toFixed(2) + ` ${flightHistory.value.currency}`
            }
          }
        }
      }
    }
  })
}

watch(() => flightHistory.value, async (newData) => {
  if (newData && newData.price_history && newData.price_history.length > 0) {
    await nextTick()
    renderHistoryChart()
  }
}, { deep: true })

onBeforeUnmount(() => {
  if (historyChartInstance) {
    historyChartInstance.destroy()
  }
})
</script>
