<template>
  <div class="mt-8">
    <div class="mb-6 pb-4 border-b-2 border-gray-200 dark:border-gray-700">
      <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100">
        <template v-if="results && results.trips.length > 0">
          Znaleziono {{ results.total_combinations }} Lotów w Obie Strony
        </template>
        <template v-else>
          Wszystkie Dostępne Trasy w Obie Strony
        </template>
      </h2>
      <p class="text-gray-600 dark:text-gray-400 mt-2">
        <template v-if="results && results.trips.length > 0">
          Pokazywanie {{ results.showing }} wyników dla
          <strong class="text-gray-900 dark:text-gray-200">
            {{ results.origin }} → {{ results.destination === 'ALL' ? 'Wszystkie Cele' : results.destination }}
          </strong>
          ({{ results.min_days }}-{{ results.max_days }} dni)
        </template>
        <template v-else>
          Pokazywanie wszystkich dostępnych tras w obie strony z polskich lotnisk z najniższymi cenami
        </template>
      </p>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="bg-gray-100 dark:bg-gray-800 rounded-xl shadow-md p-8 text-center">
      <p class="text-gray-600 dark:text-gray-400">Ładowanie danych mapy...</p>
    </div>

    <!-- Error state -->
    <div v-if="error" class="bg-red-50 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-xl shadow-md p-4">
      <strong>Błąd:</strong> {{ error }}
    </div>

    <!-- Map container -->
    <div v-show="!loading && !error" class="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
      <div id="map" class="h-[600px] w-full"></div>

      <!-- Selected trip details -->
      <div
        v-if="selectedTrip"
        class="p-4 border-t-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900"
      >
        <div class="flex justify-between items-start">
          <div class="flex-1">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">
              Szczegóły Podróży
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Destination -->
              <div v-if="results.destination === 'ALL'">
                <p class="text-sm text-gray-600 dark:text-gray-400">Cel Podróży</p>
                <p class="font-semibold text-gray-900 dark:text-gray-100">
                  {{ selectedTrip.destination }} - {{ selectedTrip.destination_name }}
                </p>
              </div>

              <!-- Duration -->
              <div>
                <p class="text-sm text-gray-600 dark:text-gray-400">Czas Trwania</p>
                <p class="font-semibold text-gray-900 dark:text-gray-100">
                  {{ selectedTrip.trip_duration_days }} dni
                </p>
              </div>

              <!-- Outbound Flight -->
              <div>
                <p class="text-sm text-gray-600 dark:text-gray-400">Lot Tam</p>
                <p class="font-medium text-gray-900 dark:text-gray-100">
                  {{ formatDate(selectedTrip.outbound_flight.date) }}
                </p>
                <p class="text-sm text-gray-600 dark:text-gray-400">
                  {{ selectedTrip.outbound_flight.flight_number }} • {{ selectedTrip.outbound_flight.duration }}
                </p>
                <p class="font-mono text-sm text-gray-900 dark:text-gray-200">
                  {{ formatTime(selectedTrip.outbound_flight.departure_time) }}
                  <span class="text-blue-500 dark:text-blue-400">→</span>
                  {{ formatTime(selectedTrip.outbound_flight.arrival_time) }}
                </p>
              </div>

              <!-- Return Flight -->
              <div>
                <p class="text-sm text-gray-600 dark:text-gray-400">Lot Powrotny</p>
                <p class="font-medium text-gray-900 dark:text-gray-100">
                  {{ formatDate(selectedTrip.return_flight.date) }}
                </p>
                <p class="text-sm text-gray-600 dark:text-gray-400">
                  {{ selectedTrip.return_flight.flight_number }} • {{ selectedTrip.return_flight.duration }}
                </p>
                <p class="font-mono text-sm text-gray-900 dark:text-gray-200">
                  {{ formatTime(selectedTrip.return_flight.departure_time) }}
                  <span class="text-blue-500 dark:text-blue-400">→</span>
                  {{ formatTime(selectedTrip.return_flight.arrival_time) }}
                </p>
              </div>

              <!-- Price -->
              <div>
                <p class="text-sm text-gray-600 dark:text-gray-400">Total Price</p>
                <p class="text-2xl font-bold text-green-600 dark:text-green-400">
                  {{ formatPrice(selectedTrip.total_price) }}
                </p>
                <p class="text-sm text-gray-600 dark:text-gray-400">
                  {{ formatPrice(selectedTrip.price_per_person) }} per person
                </p>
              </div>
            </div>
          </div>

          <button
            @click="selectedTrip = null"
            class="ml-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { formatPrice, formatDate, formatTime } from '~/utils/formatters'
import L from 'leaflet'

const props = defineProps({
  results: Object,
  allRoutes: Array
})

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

const loading = ref(true)
const error = ref(null)
const map = ref(null)
const airportCoordinates = ref({})
const selectedTrip = ref(null)
const routeLayers = ref([])

const initMap = async () => {
  // Only run on client side
  if (!process.client) return

  // Wait for the DOM to be ready
  await nextTick()

  // Check if map element exists
  const mapElement = document.getElementById('map')
  if (!mapElement) {
    console.error('Map element not found')
    loading.value = false
    return
  }

  try {
    // Fix Leaflet default marker icon issue with Vite/Nuxt
    if (L.Icon?.Default) {
      delete L.Icon.Default.prototype._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      })
    }

    // Initialize map centered on Europe
    map.value = L.map('map').setView([50.0, 15.0], 5)

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(map.value)
  } catch (e) {
    console.error('Failed to initialize map:', e)
    error.value = 'Failed to initialize map'
  }
}

const loadAirportCoordinates = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/airports/coordinates`, {
      params: {
        airline: 'ryanair',
        format: 'simple'
      }
    })

    if (response && response.airports) {
      // Create a map of airport code to coordinates
      response.airports.forEach(airport => {
        airportCoordinates.value[airport.code] = {
          lat: airport.latitude,
          lon: airport.longitude,
          name: airport.name
        }
      })
    }
  } catch (e) {
    error.value = e.message || 'Failed to load airport coordinates'
    console.error('Failed to load airport coordinates:', e)
  } finally {
    loading.value = false
  }
}

const plotAllRoutes = () => {
  if (!process.client || !map.value || !props.allRoutes || !props.allRoutes.length) {
    return
  }

  // Clear existing route layers
  routeLayers.value.forEach(layer => map.value.removeLayer(layer))
  routeLayers.value = []

  const bounds = []
  const prices = props.allRoutes.map(r => r.cheapest_price).filter(p => p !== undefined)
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)

  // Plot each route
  props.allRoutes.forEach(route => {
    // Check if we have coordinates from the backend
    const originCoords = route.origin_coordinates
    const destCoords = route.destination_coordinates

    if (!originCoords || !destCoords) {
      console.warn(`Missing coordinates for ${route.origin} or ${route.destination}`)
      return
    }

    const originLatLng = [originCoords.latitude, originCoords.longitude]
    const destLatLng = [destCoords.latitude, destCoords.longitude]

    bounds.push(originLatLng, destLatLng)

    // Create a curved line between airports
    const curve = createCurvedLine(originLatLng, destLatLng)

    // Determine color based on price
    const priceRatio = (route.cheapest_price - minPrice) / (maxPrice - minPrice)
    const color = getPriceColor(priceRatio)

    // Draw the route line
    const polyline = L.polyline(curve, {
      color: color,
      weight: 3,
      opacity: 0.6,
      className: 'route-line'
    }).addTo(map.value)

    // Add popup to the line
    polyline.bindPopup(`
      <div style="min-width: 200px;">
        <strong style="font-size: 14px;">${route.origin} → ${route.destination}</strong><br>
        <span style="font-size: 12px; color: #666;">${route.origin_name} → ${route.destination_name}</span><br>
        <span style="color: #16a34a; font-weight: bold; font-size: 16px;">${route.cheapest_price.toFixed(2)} ${route.currency}</span><br>
        <span style="font-size: 12px; color: #666;">Cheapest round-trip price</span>
      </div>
    `)

    routeLayers.value.push(polyline)

    // Add markers for origin and destination
    const originMarker = L.circleMarker(originLatLng, {
      radius: 5,
      fillColor: '#3b82f6',
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.8
    }).addTo(map.value)

    originMarker.bindPopup(`
      <strong>${route.origin}</strong><br>
      ${route.origin_name}
    `)

    // Create custom marker with price label for destination
    const priceLabel = `${route.cheapest_price.toFixed(0)} ${route.currency}`
    const destIcon = L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="
            background-color: #ef4444;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            border: 2px solid white;
          ">${priceLabel}</div>
          <div style="
            width: 0;
            height: 0;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 6px solid white;
            margin-top: -2px;
          "></div>
          <div style="
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #ef4444;
            margin-top: -6px;
          "></div>
        </div>
      `,
      iconSize: [60, 30],
      iconAnchor: [30, 30]
    })

    const destMarker = L.marker(destLatLng, { icon: destIcon }).addTo(map.value)

    destMarker.bindPopup(`
      <strong>${route.destination}</strong><br>
      ${route.destination_name}<br>
      <span style="color: #16a34a; font-weight: bold;">${route.cheapest_price.toFixed(2)} ${route.currency}</span>
    `)

    routeLayers.value.push(originMarker, destMarker)
  })

  // Fit map to show all routes
  if (bounds.length > 0) {
    map.value.fitBounds(bounds, { padding: [50, 50] })
  }
}

const plotRoutes = () => {
  if (!process.client || !map.value || !props.results || !props.results.trips.length) {
    return
  }

  // Clear existing route layers
  routeLayers.value.forEach(layer => map.value.removeLayer(layer))
  routeLayers.value = []

  const bounds = []
  const routesMap = new Map() // Group trips by route

  // Group trips by origin-destination pair
  props.results.trips.forEach(trip => {
    const origin = trip.outbound_flight.origin
    const destination = trip.outbound_flight.destination
    const key = `${origin}-${destination}`

    if (!routesMap.has(key)) {
      routesMap.set(key, [])
    }
    routesMap.get(key).push(trip)
  })

  // Plot each unique route
  routesMap.forEach((trips, routeKey) => {
    const [origin, destination] = routeKey.split('-')
    const trip = trips[0] // Use first trip for this route

    const originCoords = airportCoordinates.value[origin]
    const destCoords = airportCoordinates.value[destination]

    if (!originCoords || !destCoords) {
      console.warn(`Missing coordinates for ${origin} or ${destination}`)
      return
    }

    const originLatLng = [originCoords.lat, originCoords.lon]
    const destLatLng = [destCoords.lat, destCoords.lon]

    bounds.push(originLatLng, destLatLng)

    // Create a curved line between airports
    const curve = createCurvedLine(originLatLng, destLatLng)

    // Determine color based on price
    const minPrice = Math.min(...props.results.trips.map(t => t.total_price))
    const maxPrice = Math.max(...props.results.trips.map(t => t.total_price))
    const priceRatio = (trip.total_price - minPrice) / (maxPrice - minPrice)
    const color = getPriceColor(priceRatio)

    // Draw the route line
    const polyline = L.polyline(curve, {
      color: color,
      weight: 3,
      opacity: 0.7,
      className: 'route-line'
    }).addTo(map.value)

    // Make the line clickable - select the first trip for this route
    polyline.on('click', () => {
      selectedTrip.value = trip
      // Highlight selected line
      routeLayers.value.forEach(layer => {
        if (layer instanceof L.Polyline) {
          layer.setStyle({ weight: 3, opacity: 0.7 })
        }
      })
      polyline.setStyle({ weight: 5, opacity: 1 })
    })

    routeLayers.value.push(polyline)

    // Add markers for origin and destination
    const originMarker = L.circleMarker(originLatLng, {
      radius: 6,
      fillColor: '#3b82f6',
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.8
    }).addTo(map.value)

    originMarker.bindPopup(`
      <strong>${origin}</strong><br>
      ${originCoords.name}
    `)

    // Create custom marker with price label for destination
    const priceLabel = formatPrice(trip.total_price)
    const destIcon = L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="
            background-color: #ef4444;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            border: 2px solid white;
          ">${priceLabel}</div>
          <div style="
            width: 0;
            height: 0;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 6px solid white;
            margin-top: -2px;
          "></div>
          <div style="
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #ef4444;
            margin-top: -6px;
          "></div>
        </div>
      `,
      iconSize: [60, 30],
      iconAnchor: [30, 30]
    })

    const destMarker = L.marker(destLatLng, { icon: destIcon }).addTo(map.value)

    destMarker.bindPopup(`
      <strong>${destination}</strong><br>
      ${destCoords.name}<br>
      <span style="color: #16a34a; font-weight: bold;">${formatPrice(trip.total_price)}</span><br>
      ${trips.length} trip${trips.length > 1 ? 's' : ''} available
    `)

    // Make markers clickable too
    const clickHandler = () => {
      selectedTrip.value = trip
      routeLayers.value.forEach(layer => {
        if (layer instanceof L.Polyline) {
          layer.setStyle({ weight: 3, opacity: 0.7 })
        }
      })
      polyline.setStyle({ weight: 5, opacity: 1 })
    }

    originMarker.on('click', clickHandler)
    destMarker.on('click', clickHandler)

    routeLayers.value.push(originMarker, destMarker)
  })

  // Fit map to show all routes
  if (bounds.length > 0) {
    map.value.fitBounds(bounds, { padding: [50, 50] })
  }
}

const createCurvedLine = (start, end) => {
  // Create a simple curved line by adding a midpoint offset
  const midLat = (start[0] + end[0]) / 2
  const midLon = (start[1] + end[1]) / 2

  // Calculate perpendicular offset for curve
  const dx = end[1] - start[1]
  const dy = end[0] - start[0]
  const distance = Math.sqrt(dx * dx + dy * dy)

  // Curve intensity based on distance
  const curveOffset = distance * 0.15

  const offsetLat = midLat - (dx / distance) * curveOffset
  const offsetLon = midLon + (dy / distance) * curveOffset

  return [
    start,
    [offsetLat, offsetLon],
    end
  ]
}

const getPriceColor = (ratio) => {
  // Green for cheap, yellow for medium, red for expensive
  if (ratio < 0.33) return '#16a34a' // green
  if (ratio < 0.66) return '#eab308' // yellow
  return '#ef4444' // red
}

// Initialize map on mount (client-side only)
onMounted(async () => {
  if (!process.client) {
    loading.value = false
    return
  }

  await initMap()
  await loadAirportCoordinates()

  // Plot specific results or all routes
  if (props.results && props.results.trips.length > 0) {
    plotRoutes()
  } else if (props.allRoutes && props.allRoutes.length > 0) {
    plotAllRoutes()
  }
})

// Watch for results changes
watch(() => props.results, async (newResults) => {
  if (!process.client) return

  selectedTrip.value = null

  // Ensure map is initialized
  if (!map.value) {
    await initMap()
    await loadAirportCoordinates()
  }

  if (newResults && newResults.trips.length > 0) {
    plotRoutes()
  } else if (props.allRoutes && props.allRoutes.length > 0) {
    plotAllRoutes()
  }
}, { deep: true })

// Watch for allRoutes changes
watch(() => props.allRoutes, async (newRoutes) => {
  if (!process.client) return

  // Only plot all routes if we don't have specific search results
  if (!props.results || !props.results.trips || props.results.trips.length === 0) {
    if (!map.value) {
      await initMap()
      await loadAirportCoordinates()
    }

    if (newRoutes && newRoutes.length > 0) {
      plotAllRoutes()
    }
  }
}, { deep: true })
</script>

<style scoped>
/* Ensure map container has explicit height */
#map {
  min-height: 600px;
}

/* Add hover effect to route lines */
:deep(.route-line) {
  cursor: pointer;
  transition: all 0.2s ease;
}

:deep(.route-line:hover) {
  opacity: 1 !important;
  filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.5));
}

/* Custom marker styles */
:deep(.custom-marker) {
  background: transparent !important;
  border: none !important;
  cursor: pointer;
}

:deep(.custom-marker:hover) {
  transform: scale(1.05);
  transition: transform 0.2s ease;
}
</style>
