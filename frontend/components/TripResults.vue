<template>
  <div class="relative">
    <!-- Loading Overlay -->
    <div v-if="loading" class="absolute inset-0 flex items-start justify-center pt-8 z-10">
      <div class="w-full max-w-[70%] p-4 bg-yellow-50 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-md border border-yellow-200 dark:border-yellow-700 text-center text-lg shadow-lg">
        <div class="mb-3">{{ loadingMessage }}</div>
        <div class="w-full bg-yellow-200 dark:bg-yellow-700 rounded-full h-2.5 overflow-hidden">
          <div class="bg-yellow-600 dark:bg-yellow-400 h-2.5 rounded-full animate-progress"></div>
        </div>
      </div>
    </div>

    <!-- Results Content (blurred when loading) -->
    <div :class="{ 'blur-sm opacity-60 pointer-events-none': loading && results }">
      <!-- Initial State Message -->
      <div v-if="!searched" class="p-8 bg-blue-50 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-lg border-2 border-blue-200 dark:border-blue-700 text-center">
        <div class="text-2xl mb-3">🔍</div>
        <h3 class="text-xl font-semibold mb-2">Ready to Search</h3>
        <p class="text-base">Please select your origin, destination, and other filters, then click "Search Trips" to find available flights.</p>
      </div>

      <!-- Results Table -->
      <div v-if="results && results.trips.length > 0" class="mt-4">
        <div class="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg shadow-md w-full">
          <table class="w-full border-collapse text-sm">
            <thead class="bg-gray-50 dark:bg-gray-700 border-b-2 border-gray-200 dark:border-gray-600">
              <tr>
                <th class="p-3 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                  Destination
                </th>
                <th class="p-3 text-center font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                  Date Range
                </th>
                <th class="p-3 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                  Flight Info
                </th>
                <th class="p-3 text-center font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                  Total Price
                </th>
                <th v-if="twoWayRoutes" class="p-3 text-center font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                  Duration
                </th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800">
              <template v-for="(trip, index) in paginatedTrips" :key="index">
                <!-- Outbound / One-way Flight Row -->
                <tr
                  class="border-b border-gray-200 dark:border-gray-700 transition-colors group"
                  :class="{ 'bg-gray-50 dark:bg-gray-700': hoveredTripIndex === index }"
                  @mouseenter="hoveredTripIndex = index"
                  @mouseleave="hoveredTripIndex = null"
                >
                  <td :rowspan="twoWayRoutes && trip.return ? 2 : 1" class="p-3 text-center align-middle font-bold text-gray-800 dark:text-gray-200 border-r-2 border-gray-300 dark:border-gray-600">
                    <template v-if="twoWayRoutes && trip.return && trip.outbound.destination !== trip.return.origin">
                      <!-- Show both airports when they're different -->
                      <div class="text-sm">{{ trip.outbound.destination }} / {{ trip.return.origin }}</div>
                      <div class="text-xs font-normal text-gray-600 dark:text-gray-400">
                        {{ trip.outbound.destination_name }} / {{ trip.return.origin_name }}
                      </div>
                    </template>
                    <template v-else>
                      <!-- Show single airport -->
                      <div class="text-lg">{{ trip.outbound.destination }}</div>
                      <div class="text-xs font-normal text-gray-600 dark:text-gray-400">{{ trip.outbound.destination_name }}</div>
                    </template>
                  </td>
                  <td :rowspan="twoWayRoutes && trip.return ? 2 : 1" class="p-3 text-center align-middle text-gray-800 dark:text-gray-200">
                    <div class="text-sm font-semibold">{{ formatDateRange(trip) }}</div>
                  </td>
                  <td class="p-3 text-gray-800 dark:text-gray-200">
                    <div class="flex flex-col gap-1">
                      <div class="flex items-center gap-2">
                        <a
                          :href="buildRyanairUrl(trip.outbound)"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                          title="Book on Ryanair"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                        <span class="text-sm font-bold">
                          {{ trip.outbound.origin }} → {{ trip.outbound.destination }}
                        </span>
                        <span class="text-xs text-gray-500 dark:text-gray-400">
                          {{ formatDate(trip.outbound.date_out) }}
                        </span>
                      </div>
                      <div class="text-xs text-gray-600 dark:text-gray-400 ml-7">
                        {{ trip.outbound.origin_name }} → {{ trip.outbound.destination_name }}
                      </div>
                      <div class="flex items-center gap-3 ml-7 text-xs">
                        <span class="text-gray-700 dark:text-gray-300">
                          {{ formatTime(trip.outbound.departure_time) }} - {{ formatTime(trip.outbound.arrival_time) }}
                        </span>
                        <span class="text-gray-500 dark:text-gray-400">
                          {{ trip.outbound.duration }}
                        </span>
                        <span class="text-green-600 dark:text-green-400 font-semibold">
                          {{ formatPrice(twoWayRoutes ? trip.outbound.current_price : trip.outbound.price_per_person) }}
                        </span>
                      </div>
                      <div v-if="trip.outbound.last_seen" class="ml-7 text-xs text-gray-500 dark:text-gray-400">
                        Last updated: {{ formatDateTime(trip.outbound.last_seen) }}
                      </div>
                    </div>
                  </td>
                  <td :rowspan="twoWayRoutes && trip.return ? 2 : 1" class="p-3 text-center align-middle border-l border-gray-200 dark:border-gray-700">
                    <strong class="text-lg text-green-600 dark:text-green-400">{{ formatPrice(trip.total_price) }}</strong>
                  </td>
                  <td v-if="twoWayRoutes" :rowspan="trip.return ? 2 : 1" class="p-3 text-center align-middle border-l border-gray-200 dark:border-gray-700">
                    <div class="flex flex-col gap-1">
                      <div class="text-base font-bold text-gray-800 dark:text-gray-200">{{ trip.trip_duration_days }} days</div>
                      <div class="text-xs text-gray-600 dark:text-gray-400">{{ trip.stay_duration }}</div>
                    </div>
                  </td>
                </tr>

                <!-- Return Flight Row (only for two-way routes) -->
                <tr
                  v-if="twoWayRoutes && trip.return"
                  class="border-b-4 border-gray-400 dark:border-gray-500 transition-colors"
                  :class="{ 'bg-gray-50 dark:bg-gray-700': hoveredTripIndex === index }"
                  @mouseenter="hoveredTripIndex = index"
                  @mouseleave="hoveredTripIndex = null"
                >
                  <td class="p-3 text-gray-800 dark:text-gray-200">
                    <div class="flex flex-col gap-1">
                      <div class="flex items-center gap-2">
                        <a
                          :href="buildRyanairUrl(trip.return)"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                          title="Book on Ryanair"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                        <span class="text-sm font-bold">
                          {{ trip.return.origin }} → {{ trip.return.destination }}
                        </span>
                        <span class="text-xs text-gray-500 dark:text-gray-400">
                          {{ formatDate(trip.return.date_out) }}
                        </span>
                      </div>
                      <div class="text-xs text-gray-600 dark:text-gray-400 ml-7">
                        {{ trip.return.origin_name }} → {{ trip.return.destination_name }}
                      </div>
                      <div class="flex items-center gap-3 ml-7 text-xs">
                        <span class="text-gray-700 dark:text-gray-300">
                          {{ formatTime(trip.return.departure_time) }} - {{ formatTime(trip.return.arrival_time) }}
                        </span>
                        <span class="text-gray-500 dark:text-gray-400">
                          {{ trip.return.duration }}
                        </span>
                        <span class="text-green-600 dark:text-green-400 font-semibold">
                          {{ formatPrice(trip.return.current_price) }}
                        </span>
                      </div>
                      <div v-if="trip.return.last_seen" class="ml-7 text-xs text-gray-500 dark:text-gray-400">
                        Last updated: {{ formatDateTime(trip.return.last_seen) }}
                      </div>
                    </div>
                  </td>
                </tr>

                <!-- One-way flight wider separation -->
                <tr v-if="!twoWayRoutes" class="h-3 bg-gray-100 dark:bg-gray-900">
                  <td colspan="4" class="p-0"></td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-6">
          <button
            @click="$emit('update:current-page', 1)"
            :disabled="currentPage === 1"
            class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            ««
          </button>
          <button
            @click="$emit('update:current-page', currentPage - 1)"
            :disabled="currentPage === 1"
            class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            «
          </button>
          <span class="px-4 py-2 text-gray-700 dark:text-gray-200">
            Page {{ currentPage }} of {{ totalPages }}
          </span>
          <button
            @click="$emit('update:current-page', currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            »
          </button>
          <button
            @click="$emit('update:current-page', totalPages)"
            :disabled="currentPage === totalPages"
            class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            »»
          </button>
        </div>
      </div>

      <!-- No Results -->
      <div
        v-if="!loading && searched && (!results || results.trips.length === 0)"
        class="p-8 text-center bg-gray-50 dark:bg-gray-700 rounded-lg text-gray-600 dark:text-gray-300 text-lg"
      >
        <p>No trips found matching your criteria. Try adjusting your search parameters.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { formatPrice, formatDate, formatTime, formatDateTime } from '~/utils/formatters'

// Hover state for highlighting trip rows
const hoveredTripIndex = ref(null)

const props = defineProps({
  results: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  loadingMessage: {
    type: String,
    default: 'Loading...'
  },
  searched: {
    type: Boolean,
    default: false
  },
  twoWayRoutes: {
    type: Boolean,
    default: true
  },
  currentPage: {
    type: Number,
    default: 1
  },
  itemsPerPage: {
    type: Number,
    default: 50
  }
})

const emit = defineEmits(['update:current-page'])

// Pagination computed properties
const totalPages = computed(() => {
  if (!props.results || !props.results.trips) return 0
  return Math.ceil(props.results.trips.length / props.itemsPerPage)
})

const pageStart = computed(() => {
  return (props.currentPage - 1) * props.itemsPerPage
})

const pageEnd = computed(() => {
  const end = props.currentPage * props.itemsPerPage
  return Math.min(end, props.results?.trips.length || 0)
})

const paginatedTrips = computed(() => {
  if (!props.results || !props.results.trips) return []
  return props.results.trips.slice(pageStart.value, pageEnd.value)
})

// Methods
const formatDateRange = (trip) => {
  const formatDateLocal = (dateStr) => {
    const date = new Date(dateStr)
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    return `${day}.${month}.${year}`
  }

  const outboundDate = formatDateLocal(trip.outbound.date_out)

  if (props.twoWayRoutes && trip.return) {
    const returnDate = formatDateLocal(trip.return.date_out)
    return `${outboundDate}-${returnDate}`
  }

  return outboundDate
}

const buildRyanairUrl = (flight) => {
  const dateOnly = flight.date_out.split('T')[0]

  const params = new URLSearchParams({
    adults: '1',
    teens: '0',
    children: '0',
    infants: '0',
    dateOut: dateOnly,
    dateIn: '',
    isConnectedFlight: 'false',
    discount: '0',
    promoCode: '',
    isReturn: 'false',
    originIata: flight.origin,
    destinationIata: flight.destination,
    tpAdults: '1',
    tpTeens: '0',
    tpChildren: '0',
    tpInfants: '0',
    tpStartDate: dateOnly,
    tpEndDate: '',
    tpDiscount: '0',
    tpPromoCode: '',
    tpOriginIata: flight.origin,
    tpDestinationIata: flight.destination
  })

  return `https://www.ryanair.com/hr/en/trip/flights/select?${params.toString()}`
}
</script>

<style scoped>
/* Only animation keyframes needed for progress bar */
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
