<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md flex flex-col max-h-[calc(100vh-6rem)]">
    <!-- Desktop: Buttons at top (Sticky) -->
    <div class="hidden md:block p-3 md:p-6 pb-2 md:pb-4 sticky top-0 bg-white dark:bg-gray-800 z-10 rounded-t-lg">
      <!-- Action Buttons -->
      <div class="flex gap-2 md:gap-3 pb-2 md:pb-4 border-b border-gray-200 dark:border-gray-700">
        <button
          @click="$emit('search')"
          :disabled="!canSearch || loading"
          class="flex-1 py-2 md:py-3 px-3 md:px-6 bg-green-600 hover:bg-green-700 dark:bg-green-600 dark:hover:bg-green-700 text-white font-semibold rounded-lg transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed hover:shadow-lg hover:-translate-y-0.5 text-sm md:text-base"
        >
          🔍 Szukaj Lotów
        </button>
        <button
          @click="$emit('clear')"
          class="flex-1 py-2 md:py-3 px-3 md:px-6 bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700 text-white font-semibold rounded-lg transition-all duration-200 hover:shadow-lg text-sm md:text-base"
        >
          🗑️ Wyczyść
        </button>
      </div>
    </div>

    <!-- Scrollable Filters -->
    <div class="overflow-y-auto px-3 md:px-6 pb-3 md:pb-6 pt-3 md:pt-0">
      <div class="flex flex-col gap-3 md:gap-4 pt-2 md:pt-4">
        <!-- Trip Type Toggle -->
        <div class="flex flex-col">
          <label class="font-semibold mb-1.5 md:mb-2 text-gray-700 dark:text-gray-200 text-xs md:text-sm">Typ Lotu</label>
          <div class="inline-flex rounded-md shadow-sm" role="group">
            <button
              type="button"
              @click="updateFilter('twoWayRoutes', false)"
              :class="[
                'flex-1 px-2 md:px-4 py-1.5 md:py-2.5 text-xs md:text-sm font-medium border-2 rounded-l-md transition-all duration-200',
                !filters.twoWayRoutes
                  ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
              ]"
            >
              W jedną stronę
            </button>
            <button
              type="button"
              @click="updateFilter('twoWayRoutes', true)"
              :class="[
                'flex-1 px-2 md:px-4 py-1.5 md:py-2.5 text-xs md:text-sm font-medium border-2 border-l-0 rounded-r-md transition-all duration-200',
                filters.twoWayRoutes
                  ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
              ]"
            >
              W obie strony
            </button>
          </div>
        </div>

        <!-- Origin Airports (Multi-select) - Polish airports only -->
        <div class="flex flex-col">
          <label class="font-semibold mb-1.5 md:mb-2 text-gray-700 dark:text-gray-200 text-xs md:text-sm">Z</label>
          <MultiSelectDropdown
            :options="polishAirportsOptions"
            :selected-values="filters.origins"
            @update:selected-values="updateFilter('origins', $event)"
            placeholder="Wybierz polskie lotniska..."
            search-placeholder="Szukaj lotnisk..."
          />
        </div>

        <!-- Destination Selection Mode -->
        <div class="flex flex-col">
          <label class="font-semibold mb-1.5 md:mb-2 text-gray-700 dark:text-gray-200 text-xs md:text-sm">Do</label>
          <div class="inline-flex rounded-md shadow-sm mb-2" role="group">
            <button
              type="button"
              @click="updateDestinationMode('airports')"
              :class="[
                'flex-1 px-2 md:px-4 py-1.5 md:py-2.5 text-xs md:text-sm font-medium border-2 transition-all duration-200',
                filters.origins.length === 1 ? 'rounded-l-md' : 'rounded-l-md rounded-r-md',
                destinationMode === 'airports'
                  ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
              ]"
            >
              Lotniska
            </button>
            <button
              type="button"
              @click="updateDestinationMode('country')"
              :class="[
                'flex-1 px-4 py-2.5 text-sm font-medium border-2 border-l-0 transition-all duration-200',
                filters.origins.length === 1 ? '' : 'rounded-r-md',
                destinationMode === 'country'
                  ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
              ]"
            >
              Kraje
            </button>
            <button
              v-if="filters.origins.length === 1"
              type="button"
              @click="updateDestinationMode('anywhere')"
              :class="[
                'flex-1 px-4 py-2.5 text-sm font-medium border-2 border-l-0 rounded-r-md transition-all duration-200',
                destinationMode === 'anywhere'
                  ? 'bg-purple-600 text-white border-purple-600 dark:bg-purple-600 dark:border-purple-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
              ]"
              title="Szukaj wszystkich miejsc docelowych z wybranego lotniska"
            >
              Gdziekolwiek
            </button>
          </div>

          <!-- Destination Airports (Multi-select) -->
          <div v-if="destinationMode === 'airports'">
            <MultiSelectDropdown
              :options="allAirportsOptions"
              :selected-values="filters.destinations"
              @update:selected-values="updateFilter('destinations', $event)"
              placeholder="Wybierz lotniska docelowe..."
              search-placeholder="Szukaj lotnisk..."
            />
          </div>

          <!-- Destination Countries (Multi-select) -->
          <div v-if="destinationMode === 'country'">
            <MultiSelectDropdown
              :options="countriesOptions"
              :selected-values="selectedCountries"
              @update:selected-values="selectAirportsByCountries"
              placeholder="Wybierz kraje..."
              search-placeholder="Szukaj krajów..."
            />
            <p v-if="selectedCountries.length > 0" class="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {{ getTotalAirportsFromCountries() }} lotnisk z {{ selectedCountries.length }} {{ selectedCountries.length === 1 ? 'kraju' : 'krajów' }}
            </p>
          </div>

          <!-- Anywhere Mode Info -->
          <div v-if="destinationMode === 'anywhere'">
            <p class="text-sm text-gray-600 dark:text-gray-300 text-center py-2">
              Wyszukiwanie wszystkich miejsc docelowych z wybranego lotniska
            </p>
          </div>

          <!-- Warning when anywhere is hidden -->
          <p v-if="filters.origins.length > 1" class="mt-1 text-xs text-gray-500 dark:text-gray-400 text-center">
            Tryb "Gdziekolwiek" wymaga dokładnie jednego lotniska wylotu
          </p>
        </div>

        <!-- Return from Same Airport Checkbox (only for two-way routes) -->
        <div v-if="filters.twoWayRoutes" class="flex items-start">
          <label class="flex items-start gap-1.5 md:gap-2 cursor-pointer text-gray-700 dark:text-gray-200 text-xs md:text-sm">
            <input
              :checked="filters.returnFromSameAirport"
              @change="updateFilter('returnFromSameAirport', $event.target.checked)"
              type="checkbox"
              class="w-3.5 h-3.5 md:w-4 md:h-4 mt-0.5 cursor-pointer"
            />
            <span class="flex items-center gap-0.5 md:gap-1">
              <span>Powrót z tego samego lotniska</span>
              <span class="inline-flex items-center justify-center w-3.5 h-3.5 md:w-4 md:h-4 text-[0.6rem] md:text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                    title="Odznacz, aby zezwolić na powroty z innych lotnisk (np. przelecieć do BCN, wrócić z VLC)">ℹ</span>
            </span>
          </label>
        </div>

        <!-- Return to Same Airport Checkbox (only for two-way routes) -->
        <div v-if="filters.twoWayRoutes" class="flex items-start">
          <label class="flex items-start gap-1.5 md:gap-2 cursor-pointer text-gray-700 dark:text-gray-200 text-xs md:text-sm">
            <input
              :checked="filters.returnToSameAirport"
              @change="updateFilter('returnToSameAirport', $event.target.checked)"
              type="checkbox"
              class="w-3.5 h-3.5 md:w-4 md:h-4 mt-0.5 cursor-pointer"
            />
            <span class="flex items-center gap-0.5 md:gap-1">
              <span>Powrót na to samo lotnisko</span>
              <span class="inline-flex items-center justify-center w-3.5 h-3.5 md:w-4 md:h-4 text-[0.6rem] md:text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                    title="Odznacz, aby zezwolić na powroty na inne lotniska wylotu (np. lecieć z WRO, wrócić do KRK)">ℹ</span>
            </span>
          </label>
        </div>

        <!-- Date Range (Start Date and End Date on same line) -->
        <div class="flex gap-1.5 md:gap-2">
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-1 md:mb-2 text-gray-700 dark:text-gray-200 text-xs md:text-sm">Data Od</label>
            <input
              :value="filters.dateFrom"
              @input="updateFilter('dateFrom', $event.target.value)"
              type="date"
              class="p-1.5 md:p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-xs md:text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-1 md:mb-2 text-gray-700 dark:text-gray-200 text-xs md:text-sm">Data Do</label>
            <input
              :value="filters.dateTo"
              @input="updateFilter('dateTo', $event.target.value)"
              type="date"
              class="p-1.5 md:p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-xs md:text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>
        </div>

        <!-- Min/Max Days (on same line, only for two-way routes) -->
        <div v-if="filters.twoWayRoutes" class="flex gap-1.5 md:gap-2">
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-1 md:mb-2 text-gray-700 dark:text-gray-200 text-xs md:text-sm">Min. Dni</label>
            <input
              :value="filters.minDays"
              @input="updateFilter('minDays', parseInt($event.target.value))"
              type="number"
              min="1"
              max="365"
              class="p-1.5 md:p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-xs md:text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-1 md:mb-2 text-gray-700 dark:text-gray-200 text-xs md:text-sm">Maks. Dni</label>
            <input
              :value="filters.maxDays"
              @input="updateFilter('maxDays', parseInt($event.target.value))"
              type="number"
              min="1"
              max="365"
              class="p-1.5 md:p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-xs md:text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>
        </div>

        <!-- Outbound and Return Weekdays (on same line for two-way, single for one-way) -->
        <div v-if="filters.twoWayRoutes" class="flex gap-1.5 md:gap-2">
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-1 md:mb-2 text-gray-700 dark:text-gray-200 text-xs md:text-sm flex items-center gap-0.5 md:gap-1">
              <span class="hidden md:inline">Dni Tygodnia (Tam)</span>
              <span class="md:hidden">Tam</span>
              <span class="inline-flex items-center justify-center w-3.5 h-3.5 md:w-5 md:h-5 text-[0.6rem] md:text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                    title="Wybierz konkretne dni tygodnia dla lotów tam">ℹ</span>
            </label>
            <MultiSelectDropdown
              :options="weekdayOptions"
              :selected-values="filters.outboundWeekdays"
              @update:selected-values="updateFilter('outboundWeekdays', $event)"
              placeholder="Dowolny dzień"
              :searchable="false"
              :show-selected-items="false"
            />
          </div>
          <div class="flex flex-col flex-1">
            <label class="font-semibold mb-1 md:mb-2 text-gray-700 dark:text-gray-200 text-xs md:text-sm flex items-center gap-0.5 md:gap-1">
              <span class="hidden md:inline">Dni Tygodnia (Powrót)</span>
              <span class="md:hidden">Powrót</span>
              <span class="inline-flex items-center justify-center w-3.5 h-3.5 md:w-5 md:h-5 text-[0.6rem] md:text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                    title="Wybierz konkretne dni tygodnia dla lotów powrotnych">ℹ</span>
            </label>
            <MultiSelectDropdown
              :options="weekdayOptions"
              :selected-values="filters.returnWeekdays"
              @update:selected-values="updateFilter('returnWeekdays', $event)"
              placeholder="Dowolny dzień"
              :searchable="false"
              :show-selected-items="false"
            />
          </div>
        </div>

        <!-- One-way Flight Days (single column) -->
        <div v-if="!filters.twoWayRoutes" class="flex flex-col">
          <label class="font-semibold mb-1 md:mb-2 text-gray-700 dark:text-gray-200 text-xs md:text-sm flex items-center gap-0.5 md:gap-1">
            Dni Tygodnia
            <span class="inline-flex items-center justify-center w-3.5 h-3.5 md:w-5 md:h-5 text-[0.6rem] md:text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                  title="Wybierz konkretne dni tygodnia dla lotów">ℹ</span>
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

        <!-- Mobile: Action Buttons at bottom -->
        <div class="md:hidden flex gap-2 pt-3 mt-3 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="$emit('search')"
            :disabled="!canSearch || loading"
            class="flex-1 py-2 px-3 bg-green-600 hover:bg-green-700 dark:bg-green-600 dark:hover:bg-green-700 text-white font-semibold rounded-lg transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed text-sm"
          >
            🔍 Szukaj Lotów
          </button>
          <button
            @click="$emit('clear')"
            class="flex-1 py-2 px-3 bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700 text-white font-semibold rounded-lg transition-all duration-200 text-sm"
          >
            🗑️ Wyczyść
          </button>
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
  { value: 0, label: 'Poniedziałek' },
  { value: 1, label: 'Wtorek' },
  { value: 2, label: 'Środa' },
  { value: 3, label: 'Czwartek' },
  { value: 4, label: 'Piątek' },
  { value: 5, label: 'Sobota' },
  { value: 6, label: 'Niedziela' }
]

// Methods
const updateFilter = (key, value) => {
  const updatedFilters = { ...props.filters, [key]: value }

  // Validation: Ensure minDays never exceeds maxDays
  if (key === 'minDays' && value > props.filters.maxDays) {
    // If user increases minDays beyond maxDays, increase maxDays to match
    updatedFilters.maxDays = value
  } else if (key === 'maxDays' && value < props.filters.minDays) {
    // If user decreases maxDays below minDays, decrease minDays to match
    updatedFilters.minDays = value
  }

  // If user adds a second origin while in "anywhere" mode, switch to airports mode
  if (key === 'origins' && value.length > 1 && props.destinationMode === 'anywhere') {
    emit('update:destination-mode', 'airports')
  }

  emit('update:filters', updatedFilters)
}

const updateDestinationMode = (mode) => {
  emit('update:destination-mode', mode)
  if (mode === 'airports') {
    emit('update:selected-countries', [])
  } else if (mode === 'anywhere') {
    // Clear destinations and countries to trigger "anywhere" search
    emit('update:selected-countries', [])
    updateFilter('destinations', [])
  }
}

const selectAnywhere = () => {
  // Legacy method - now handled by updateDestinationMode('anywhere')
  updateDestinationMode('anywhere')
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
