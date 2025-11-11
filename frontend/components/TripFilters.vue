<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md flex flex-col max-h-[calc(100vh-6rem)]">
    <!-- Header and Buttons (Sticky) -->
    <div class="p-6 pb-4 sticky top-0 bg-white dark:bg-gray-800 z-10 rounded-t-lg">
      <!-- Action Buttons -->
      <div class="flex gap-2 pb-4 border-b border-gray-200 dark:border-gray-700">
        <button
          @click="$emit('search')"
          :disabled="!canSearch || loading"
          class="flex-1 py-2 px-4 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-medium rounded-md transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed hover:shadow-lg hover:-translate-y-0.5 text-sm"
        >
          Search Trips
        </button>
        <button
          @click="$emit('clear')"
          class="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-700 dark:bg-gray-600 dark:hover:bg-gray-700 text-white font-medium rounded-md transition-all duration-200 text-sm"
        >
          Clear All
        </button>
      </div>
    </div>

    <!-- Scrollable Filters -->
    <div class="overflow-y-auto px-6 pb-6">
      <div class="flex flex-col gap-4 pt-4">
        <!-- Trip Type Toggle -->
        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">Trip Type</label>
          <div class="inline-flex rounded-md shadow-sm" role="group">
            <button
              type="button"
              @click="updateFilter('twoWayRoutes', false)"
              :class="[
                'flex-1 px-4 py-2.5 text-sm font-medium border-2 rounded-l-md transition-all duration-200',
                !filters.twoWayRoutes
                  ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
              ]"
            >
              One-way
            </button>
            <button
              type="button"
              @click="updateFilter('twoWayRoutes', true)"
              :class="[
                'flex-1 px-4 py-2.5 text-sm font-medium border-2 border-l-0 rounded-r-md transition-all duration-200',
                filters.twoWayRoutes
                  ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
              ]"
            >
              Round-trip
            </button>
          </div>
        </div>

        <!-- Origin Airports (Multi-select) - Polish airports only -->
        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">From</label>
          <MultiSelectDropdown
            :options="polishAirportsOptions"
            :selected-values="filters.origins"
            @update:selected-values="updateFilter('origins', $event)"
            placeholder="Select Polish airports..."
            search-placeholder="Search airports..."
          />
        </div>

        <!-- Destination Selection Mode -->
        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">To</label>
          <div class="inline-flex rounded-md shadow-sm mb-2" role="group">
            <button
              type="button"
              @click="updateDestinationMode('airports')"
              :class="[
                'flex-1 px-4 py-2.5 text-sm font-medium border-2 rounded-l-md transition-all duration-200',
                destinationMode === 'airports'
                  ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
              ]"
            >
              Airports
            </button>
            <button
              type="button"
              @click="updateDestinationMode('country')"
              :class="[
                'flex-1 px-4 py-2.5 text-sm font-medium border-2 border-l-0 rounded-r-md transition-all duration-200',
                destinationMode === 'country'
                  ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
              ]"
            >
              Countries
            </button>
          </div>

          <!-- Destination Airports (Multi-select) -->
          <div v-if="destinationMode === 'airports'">
            <MultiSelectDropdown
              :options="allAirportsOptions"
              :selected-values="filters.destinations"
              @update:selected-values="updateFilter('destinations', $event)"
              placeholder="Select destination airports..."
              search-placeholder="Search airports..."
            />
          </div>

          <!-- Destination Countries (Multi-select) -->
          <div v-if="destinationMode === 'country'">
            <MultiSelectDropdown
              :options="countriesOptions"
              :selected-values="selectedCountries"
              @update:selected-values="selectAirportsByCountries"
              placeholder="Select countries..."
              search-placeholder="Search countries..."
            />
            <p v-if="selectedCountries.length > 0" class="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {{ getTotalAirportsFromCountries() }} airports from {{ selectedCountries.length }} {{ selectedCountries.length === 1 ? 'country' : 'countries' }}
            </p>
          </div>

          <!-- Anywhere Button -->
          <button
            type="button"
            @click="selectAnywhere"
            :disabled="filters.origins.length !== 1"
            :class="[
              'w-full px-4 py-2.5 text-sm font-medium border-2 rounded-md transition-all duration-200 mt-2',
              filters.origins.length === 1
                ? 'bg-purple-600 text-white border-purple-600 hover:bg-purple-700 dark:bg-purple-600 dark:border-purple-600 dark:hover:bg-purple-700 cursor-pointer'
                : 'bg-gray-300 text-gray-500 border-gray-300 cursor-not-allowed dark:bg-gray-600 dark:text-gray-400 dark:border-gray-600'
            ]"
            :title="filters.origins.length !== 1 ? 'Select exactly one origin airport to search anywhere' : 'Search all destinations from selected origin'"
          >
            🌍 Anywhere
          </button>
          <p v-if="filters.origins.length !== 1" class="mt-1 text-xs text-gray-500 dark:text-gray-400 text-center">
            Select one origin to search anywhere
          </p>
        </div>

        <!-- Return from Same Airport Checkbox (only for two-way routes) -->
        <div v-if="filters.twoWayRoutes" class="flex items-start">
          <label class="flex items-start gap-2 cursor-pointer text-gray-700 dark:text-gray-200 text-sm">
            <input
              :checked="filters.returnFromSameAirport"
              @change="updateFilter('returnFromSameAirport', $event.target.checked)"
              type="checkbox"
              class="w-4 h-4 mt-0.5 cursor-pointer"
            />
            <span class="flex items-center gap-1">
              <span>Return from same airport</span>
              <span class="inline-flex items-center justify-center w-4 h-4 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                    title="Uncheck to allow returns from different airports (e.g., fly to BCN, return from VLC)">ℹ</span>
            </span>
          </label>
        </div>

        <!-- Return to Same Airport Checkbox (only for two-way routes) -->
        <div v-if="filters.twoWayRoutes" class="flex items-start">
          <label class="flex items-start gap-2 cursor-pointer text-gray-700 dark:text-gray-200 text-sm">
            <input
              :checked="filters.returnToSameAirport"
              @change="updateFilter('returnToSameAirport', $event.target.checked)"
              type="checkbox"
              class="w-4 h-4 mt-0.5 cursor-pointer"
            />
            <span class="flex items-center gap-1">
              <span>Return to same airport</span>
              <span class="inline-flex items-center justify-center w-4 h-4 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                    title="Uncheck to allow returns to different origin airports (e.g., fly from WRO, return to KRK)">ℹ</span>
            </span>
          </label>
        </div>

        <!-- Date Range (Start Date and End Date on same line) -->
        <div class="flex gap-2">
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">Start Date</label>
            <input
              :value="filters.dateFrom"
              @input="updateFilter('dateFrom', $event.target.value)"
              type="date"
              class="p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">End Date</label>
            <input
              :value="filters.dateTo"
              @input="updateFilter('dateTo', $event.target.value)"
              type="date"
              class="p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>
        </div>

        <!-- Min/Max Days (on same line, only for two-way routes) -->
        <div v-if="filters.twoWayRoutes" class="flex gap-2">
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">Min Days</label>
            <input
              :value="filters.minDays"
              @input="updateFilter('minDays', parseInt($event.target.value))"
              type="number"
              min="1"
              max="365"
              class="p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">Max Days</label>
            <input
              :value="filters.maxDays"
              @input="updateFilter('maxDays', parseInt($event.target.value))"
              type="number"
              min="1"
              max="365"
              class="p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>
        </div>

        <!-- Outbound and Return Weekdays (on same line for two-way, single for one-way) -->
        <div v-if="filters.twoWayRoutes" class="flex gap-2">
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm flex items-center gap-1">
              Outbound Days
              <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                    title="Select specific days of the week for outbound flights">ℹ</span>
            </label>
            <MultiSelectDropdown
              :options="weekdayOptions"
              :selected-values="filters.outboundWeekdays"
              @update:selected-values="updateFilter('outboundWeekdays', $event)"
              placeholder="Any day"
              :searchable="false"
              :show-selected-items="false"
            />
          </div>
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm flex items-center gap-1">
              Return Days
              <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                    title="Select specific days of the week for return flights">ℹ</span>
            </label>
            <MultiSelectDropdown
              :options="weekdayOptions"
              :selected-values="filters.returnWeekdays"
              @update:selected-values="updateFilter('returnWeekdays', $event)"
              placeholder="Any day"
              :searchable="false"
              :show-selected-items="false"
            />
          </div>
        </div>

        <!-- One-way Flight Days (single column) -->
        <div v-if="!filters.twoWayRoutes" class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm flex items-center gap-1">
            Flight Days
            <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                  title="Select specific days of the week for flights">ℹ</span>
          </label>
          <MultiSelectDropdown
            :options="weekdayOptions"
            :selected-values="filters.outboundWeekdays"
            @update:selected-values="updateFilter('outboundWeekdays', $event)"
            placeholder="Any day"
            :searchable="false"
            :show-selected-items="false"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import MultiSelectDropdown from './MultiSelectDropdown.vue'

const props = defineProps({
  filters: {
    type: Object,
    required: true
  },
  polishAirportsOptions: {
    type: Array,
    required: true
  },
  allAirportsOptions: {
    type: Array,
    required: true
  },
  countriesOptions: {
    type: Array,
    required: true
  },
  countriesData: {
    type: Array,
    required: true
  },
  canSearch: {
    type: Boolean,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  destinationMode: {
    type: String,
    default: 'airports'
  },
  selectedCountries: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:filters', 'update:destination-mode', 'update:selected-countries', 'search', 'clear'])

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
const updateFilter = (key, value) => {
  emit('update:filters', { ...props.filters, [key]: value })
}

const updateDestinationMode = (mode) => {
  emit('update:destination-mode', mode)
  if (mode === 'airports') {
    emit('update:selected-countries', [])
  }
}

const selectAnywhere = () => {
  // Clear destinations to trigger "anywhere" search
  emit('update:destination-mode', 'airports')
  emit('update:selected-countries', [])
  updateFilter('destinations', [])
  // Trigger search immediately
  emit('search')
}

const selectAirportsByCountries = (countries) => {
  emit('update:selected-countries', countries)

  if (countries.length === 0) {
    updateFilter('destinations', [])
    return
  }

  // Find all airports from selected countries
  const airportCodes = []
  countries.forEach(country => {
    const countryData = props.countriesData.find(c => c.country === country)
    if (countryData && countryData.airports) {
      airportCodes.push(...countryData.airports.map(a => a.code))
    }
  })

  updateFilter('destinations', airportCodes)
}

const getTotalAirportsFromCountries = () => {
  let total = 0
  props.selectedCountries.forEach(country => {
    const countryData = props.countriesData.find(c => c.country === country)
    if (countryData) {
      total += countryData.airport_count
    }
  })
  return total
}
</script>
