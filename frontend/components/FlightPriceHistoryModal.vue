<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
        @click.self="closeModal"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 dark:bg-black/70"></div>

        <!-- Modal Content -->
        <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
          <!-- Header -->
          <div class="sticky top-0 z-10 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-between items-center">
            <div>
              <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100">
                Historia Cen Konkretnego Lotu
              </h2>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {{ origin }} → {{ destination }} | {{ selectedDate }}
              </p>
            </div>
            <button
              @click="closeModal"
              class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Zamknij"
            >
              <svg class="w-6 h-6 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Content -->
          <div class="p-6">
            <!-- Flight Selector - only show if more than one flight -->
            <div v-if="availableFlights.length > 1" class="mb-6">
              <label for="modal-flight-select" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Wybierz Lot (dostępne: {{ availableFlights.length }})
              </label>
              <select
                id="modal-flight-select"
                v-model="selectedFlightId"
                class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                @change="loadFlightPriceHistory"
              >
                <option value="">-- Wybierz lot --</option>
                <option
                  v-for="flight in availableFlights"
                  :key="flight.flight_id"
                  :value="flight.flight_id"
                >
                  {{ flight.flight_number }} | {{ formatTime(flight.departure_time) }} - {{ formatTime(flight.arrival_time) }} | {{ flight.duration }} | {{ flight.current_price }} {{ flight.currency }} | Skanów: {{ flight.scan_count }}
                </option>
              </select>
            </div>

            <!-- No flights message -->
            <div
              v-if="!loadingFlights && availableFlights.length === 0"
              class="p-4 bg-yellow-50 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-lg border border-yellow-200 dark:border-yellow-700"
            >
              Brak lotów dla tej daty. Spróbuj wybrać inną datę.
            </div>

            <!-- Loading -->
            <div
              v-if="loadingFlights || loadingHistory"
              class="p-4 bg-blue-50 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-lg border border-blue-200 dark:border-blue-700 text-center"
            >
              {{ loadingFlights ? 'Ładowanie lotów...' : 'Ładowanie historii cen...' }}
            </div>

            <!-- Error -->
            <div
              v-if="error"
              class="p-4 bg-red-50 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-lg border border-red-200 dark:border-red-700"
            >
              <strong>Błąd:</strong> {{ error }}
            </div>

            <!-- Flight Info Card -->
            <div
              v-if="flightHistory"
              class="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
            >
              <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">
                Szczegóły Lotu
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div>
                  <span class="font-medium text-gray-700 dark:text-gray-300">Lot:</span>
                  <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.flight_number }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700 dark:text-gray-300">Trasa:</span>
                  <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.origin }} → {{ flightHistory.destination }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700 dark:text-gray-300">Data:</span>
                  <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.date_out }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700 dark:text-gray-300">Godzina:</span>
                  <span class="ml-2 text-gray-900 dark:text-gray-100">{{ formatTime(flightHistory.departure_time) }} - {{ formatTime(flightHistory.arrival_time) }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700 dark:text-gray-300">Czas lotu:</span>
                  <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.duration }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700 dark:text-gray-300">Aktualna cena:</span>
                  <span class="ml-2 text-gray-900 dark:text-gray-100 font-semibold">{{ flightHistory.current_price }} {{ flightHistory.currency }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700 dark:text-gray-300">Łącznie skanów:</span>
                  <span class="ml-2 text-gray-900 dark:text-gray-100">{{ flightHistory.scan_count }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700 dark:text-gray-300">Punkty cenowe:</span>
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
              Brak dostępnej historii cen dla tego lotu. Lot musi być wielokrotnie skanowany, aby zbudować historię cen.
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  isOpen: Boolean,
  origin: String,
  destination: String,
  selectedDate: String
})

const emit = defineEmits(['close'])

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

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
  const match = timeStr.match(/T(\d{2}:\d{2})/)
  return match ? match[1] : timeStr
}

const closeModal = () => {
  emit('close')
  // Reset state
  selectedFlightId.value = ''
  availableFlights.value = []
  flightHistory.value = null
  error.value = null
  if (historyChartInstance) {
    historyChartInstance.destroy()
    historyChartInstance = null
  }
}

const loadFlightsForDate = async () => {
  if (!props.selectedDate || !props.origin || !props.destination) {
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
        date: props.selectedDate
      }
    })

    availableFlights.value = response.flights || []

    // Auto-select and load if only one flight
    if (availableFlights.value.length === 1) {
      selectedFlightId.value = availableFlights.value[0].flight_id
      await loadFlightPriceHistory()
    }
  } catch (e) {
    if (e.statusCode === 404) {
      error.value = `Brak lotów dla ${props.origin} → ${props.destination} w dniu ${props.selectedDate}`
    } else {
      error.value = e.message || 'Nie udało się załadować lotów'
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

    await nextTick()
    renderHistoryChart()
  } catch (e) {
    if (e.statusCode === 404) {
      error.value = 'Lot nie został znaleziony'
    } else {
      error.value = e.message || 'Nie udało się załadować historii cen'
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

  // Detect dark mode
  const isDark = document.documentElement.classList.contains('dark')

  // Define colors based on theme
  const colors = {
    line: isDark ? '#60a5fa' : '#007bff',
    lineBackground: isDark ? 'rgba(96, 165, 250, 0.1)' : 'rgba(0, 123, 255, 0.1)',
    text: isDark ? '#e5e7eb' : '#374151',
    grid: isDark ? 'rgba(107, 114, 128, 0.3)' : 'rgba(0, 0, 0, 0.1)',
    tooltipBg: isDark ? 'rgba(31, 41, 55, 0.95)' : 'rgba(0, 0, 0, 0.8)'
  }

  const ctx = historyChartCanvas.value.getContext('2d')

  historyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Cena',
          data: prices,
          borderColor: colors.line,
          backgroundColor: colors.lineBackground,
          borderWidth: 3,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: colors.line,
          pointBorderColor: colors.line,
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
            color: colors.text,
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
          text: `Historia cen: ${flightHistory.value.flight_number} (${flightHistory.value.origin} → ${flightHistory.value.destination})`,
          color: colors.text,
          font: {
            size: 16,
            weight: 'bold'
          },
          padding: 20
        },
        tooltip: {
          backgroundColor: colors.tooltipBg,
          titleColor: '#ffffff',
          bodyColor: '#ffffff',
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
              return `Cena: ${price.toFixed(2)} ${flightHistory.value.currency}${changeText}`
            }
          }
        }
      },
      scales: {
        x: {
          display: true,
          grid: {
            color: colors.grid
          },
          ticks: {
            color: colors.text,
            maxRotation: 45,
            minRotation: 45,
            font: {
              size: 10
            }
          },
          title: {
            display: true,
            text: 'Czas skanowania',
            color: colors.text,
            font: {
              size: 14,
              weight: 'bold'
            }
          }
        },
        y: {
          display: true,
          grid: {
            color: colors.grid
          },
          ticks: {
            color: colors.text,
            font: {
              size: 12
            },
            callback: function(value) {
              return value.toFixed(2) + ` ${flightHistory.value.currency}`
            }
          },
          title: {
            display: true,
            text: `Cena (${flightHistory.value.currency})`,
            color: colors.text,
            font: {
              size: 14,
              weight: 'bold'
            }
          },
          beginAtZero: false
        }
      }
    }
  })
}

// Watch for modal open/close and load flights
watch(() => props.isOpen, (newVal) => {
  if (newVal && props.selectedDate) {
    loadFlightsForDate()
  }
})

// Watch for date changes when modal is open
watch(() => props.selectedDate, (newDate) => {
  if (props.isOpen && newDate) {
    loadFlightsForDate()
  }
})

onBeforeUnmount(() => {
  if (historyChartInstance) {
    historyChartInstance.destroy()
  }
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.3s ease;
}

.modal-enter-from .relative,
.modal-leave-to .relative {
  transform: scale(0.9);
}
</style>
